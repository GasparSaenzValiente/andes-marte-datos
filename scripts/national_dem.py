"""National Copernicus GLO-30 zonal statistics without Google credentials.
Downloads 55 source tiles, processes each once and discards newly downloaded
full tiles (small pilot rasters stay in data/raw). ~2 GB network traffic.
"""
from pathlib import Path
import json,hashlib,concurrent.futures,time
import numpy as np
import pandas as pd
import geopandas as gpd
import requests,rasterio
from rasterio.windows import from_bounds,Window
from rasterio.features import geometry_mask
from shapely.geometry import box
R=Path(__file__).resolve().parents[1];O=R/'data/processed';CACHE=R/'.cache/national';CACHE.mkdir(parents=True,exist_ok=True)

def process(tile,g):
 lat,lon=tile;stem=f'Copernicus_DSM_COG_10_{"S" if lat<0 else "N"}{abs(lat):02d}_00_{"W" if lon<0 else "E"}{abs(lon):03d}_00_DEM'
 url=f'https://copernicus-dem-30m.s3.amazonaws.com/{stem}/{stem}.tif';p=CACHE/(stem+'.tif');rows=[]
 meta=dict(lat=lat,lon=lon,url=url,status='pending')
 try:
  for attempt in range(3):
   try:
    if not p.exists():
     resp=requests.get(url,timeout=120);resp.raise_for_status();p.write_bytes(resp.content)
    break
   except requests.RequestException:
    if attempt==2:raise
  meta.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
  with rasterio.open(p) as src:
   subset=g[g.geometry.intersects(box(*src.bounds))]
   for _,r in subset.iterrows():
    geom=r.geometry.intersection(box(*src.bounds))
    if geom.is_empty or geom.area==0:continue
    w=from_bounds(*geom.bounds,src.transform)
    x0=max(0,int(np.floor(w.col_off))-2);y0=max(0,int(np.floor(w.row_off))-2)
    x1=min(src.width,int(np.ceil(w.col_off+w.width))+2);y1=min(src.height,int(np.ceil(w.row_off+w.height))+2)
    win=Window(x0,y0,x1-x0,y1-y0);a=src.read(1,window=win,masked=True).astype(float).filled(np.nan);tr=src.window_transform(win)
    if min(a.shape)<3:continue
    mask=geometry_mask([geom],a.shape,tr,invert=True)&np.isfinite(a)
    n=int(mask.sum())
    if not n:continue
    clat=tr.f+tr.e*a.shape[0]/2;dy=abs(tr.e)*111132;dx=tr.a*111320*np.cos(np.deg2rad(clat))
    gy,gx=np.gradient(a,dy,dx);sl=np.degrees(np.arctan(np.hypot(gx,gy)));asp=np.arctan2(-gx,-gy)
    tm=mask&np.isfinite(sl);nt=int(tm.sum())
    rows.append(dict(glacier_id=r.glacier_id,tile=stem,n_pixels=n,n_terrain_pixels=nt,elev_sum=float(a[mask].sum()),elevation_min_m=float(a[mask].min()),elevation_max_m=float(a[mask].max()),slope_sum=float(sl[tm].sum()),aspect_sin_sum=float(np.sin(asp[tm]).sum()),aspect_cos_sum=float(np.cos(asp[tm]).sum()),edge_pixels=int((mask[:,0].sum()+mask[:,-1].sum()+mask[0,:].sum()+mask[-1,:].sum()))))
  meta.update(status='ok',polygon_intersections=len(rows));print('OK',stem,len(rows),flush=True)
 except Exception as ex:meta.update(status='error',error=str(ex));print('ERROR',stem,str(ex),flush=True)
 finally:
  if p.exists():p.unlink()
 return rows,meta

def main():
 g=gpd.read_file(O/'earth_entities.gpkg');tiles=set()
 for b in g.geometry.bounds.to_numpy():
  for lat in range(int(np.floor(b[1])),int(np.floor(b[3]))+1):
   for lon in range(int(np.floor(b[0])),int(np.floor(b[2]))+1):tiles.add((lat,lon))
 allrows=[];metadata=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
  fs=[ex.submit(process,t,g) for t in sorted(tiles)]
  for f in concurrent.futures.as_completed(fs):
   rows,meta=f.result();allrows.extend(rows);metadata.append(meta)
 pd.DataFrame(metadata).sort_values(['lat','lon']).to_csv(O/'copernicus_national_sources.csv',index=False)
 parts=pd.DataFrame(allrows);parts.to_csv(O/'copernicus_tile_statistics.csv',index=False)
 a=parts.groupby('glacier_id').agg(n_pixels=('n_pixels','sum'),n_terrain_pixels=('n_terrain_pixels','sum'),elev_sum=('elev_sum','sum'),elevation_min_m=('elevation_min_m','min'),elevation_max_m=('elevation_max_m','max'),slope_sum=('slope_sum','sum'),aspect_sin_sum=('aspect_sin_sum','sum'),aspect_cos_sum=('aspect_cos_sum','sum'),n_tiles=('tile','nunique'),edge_pixels=('edge_pixels','sum')).reset_index()
 a['elevation_mean_m']=a.elev_sum/a.n_pixels;a['slope_mean_deg']=a.slope_sum/a.n_terrain_pixels
 a['aspect_circular_deg']=np.degrees(np.arctan2(a.aspect_sin_sum,a.aspect_cos_sum))%360
 a['aspect_resultant']=np.hypot(a.aspect_sin_sum,a.aspect_cos_sum)/a.n_terrain_pixels
 a=a.drop(columns=['elev_sum','slope_sum','aspect_sin_sum','aspect_cos_sum'])
 base=g[['glacier_id']].copy()
 base['inventory_slope_deg']=g['inventory_slope_deg'] if 'inventory_slope_deg' in g else g.slope_deg
 base['inventory_elevation_mean_m']=g['inventory_elevation_mean_m'] if 'inventory_elevation_mean_m' in g else g.elevation_mean_m
 a=base.merge(a,on='glacier_id',how='left')
 a['dem_status']=np.where(a.n_pixels.notna(),'ok','no_valid_pixel_or_failed_tile');a['low_resolution_flag']=a.n_pixels.fillna(0)<20
 a['slope_difference_deg']=a.slope_mean_deg-a.inventory_slope_deg;a['elevation_difference_m']=a.elevation_mean_m-a.inventory_elevation_mean_m
 a['dem_source']='Copernicus GLO-30 DSM';a.to_csv(O/'earth_copernicus_national.csv',index=False)
 report=dict(entities=len(g),entities_with_pixels=int(a.n_pixels.notna().sum()),tiles=len(tiles),tiles_failed=sum(m['status']!='ok' for m in metadata),network_bytes=sum(m.get('bytes',0) for m in metadata),small_entities_under20_pixels=int(a.low_resolution_flag.sum()),median_abs_slope_difference_deg=float(a.slope_difference_deg.abs().median()),p95_abs_slope_difference_deg=float(a.slope_difference_deg.abs().quantile(.95)),statistics='pixel centers; derivatives before polygon masking; latitude-adjusted metric spacing; one-sided differences at tile edges; DSM not ice thickness')
 (O/'copernicus_national_report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
