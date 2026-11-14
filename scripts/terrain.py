"""Download real Copernicus pilot DEMs, MOLA crops, SWIM map and derive terrain.
No Earth Engine credentials required. Everything is cached; full terrestrial tiles are
kept in a caller-selected cache and only small pilot crops are distributed.
"""
from pathlib import Path
import sys,json,hashlib,zipfile,io,concurrent.futures
import numpy as np
import pandas as pd
import geopandas as gpd
import requests
import rasterio
from rasterio.mask import mask
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds,Window
from rasterio.transform import from_origin
from shapely.geometry import box,Point
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'data/raw';OUT=ROOT/'data/processed'
CACHE=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'.cache'
CACHE.mkdir(parents=True,exist_ok=True)
AOIS={'dos_lenguas':(-69.85,-30.30,-69.70,-30.18),'morenas_coloradas_region':(-69.50,-33.0,-69.25,-32.90)}

def download(u,p):
 if not p.exists():
  r=requests.get(u,timeout=180);r.raise_for_status();p.write_bytes(r.content)
 return p

def copernicus():
 records=[]
 for name,bounds in AOIS.items():
  lat=int(np.floor((bounds[1]+bounds[3])/2));lon=int(np.floor((bounds[0]+bounds[2])/2))
  stem=f'Copernicus_DSM_COG_10_S{abs(lat):02d}_00_W{abs(lon):03d}_00_DEM'
  url=f'https://copernicus-dem-30m.s3.amazonaws.com/{stem}/{stem}.tif';p=download(url,CACHE/(stem+'.tif'))
  with rasterio.open(p) as src:
   a,tr=mask(src,[box(*bounds)],crop=True);meta=src.meta.copy();meta.update(width=a.shape[2],height=a.shape[1],transform=tr,compress='deflate')
   dest=RAW/f'copernicus_{name}.tif'
   with rasterio.open(dest,'w',**meta) as dst:dst.write(a)
  records.append(dict(name=name,url=url,bounds=bounds,cache_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),crop=dest.name))
 (RAW/'copernicus_provenance.json').write_text(json.dumps(records,indent=2))

def mola(name,lat,lon):
 west=int(lon//90)*90;north=44 if lat<44 else 88;stem=f'megt{north:02d}n{west:03d}hb';base='https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg128/'
 if (RAW/f'mola_{name}.tif').exists():return
 download(base+stem+'.lbl',RAW/(stem+'.lbl'))
 r0=int((north-(lat+1))*128);cols=11520;start=r0*cols*2;end=(r0+256)*cols*2-1
 r=requests.get(base+stem+'.img',headers={'Range':f'bytes={start}-{end}'},timeout=180);r.raise_for_status()
 buf=r.content if r.status_code==206 else r.content[start:end+1]
 a=np.frombuffer(buf,dtype='>i2').reshape(256,cols);c0=int((lon-1-west)*128);a=a[:,c0:c0+256].astype('int16')
 with rasterio.open(RAW/f'mola_{name}.tif','w',driver='GTiff',width=256,height=256,count=1,dtype='int16',crs='+proj=longlat +a=3396000 +b=3396000 +no_defs',transform=from_origin(west+c0/128,north-r0/128,1/128,1/128),compress='deflate') as dst:dst.write(a,1)
 (RAW/f'mola_{name}_provenance.json').write_text(json.dumps(dict(url=base+stem+'.img',range_start=start,range_end=end,http_status=r.status_code,lat=lat,lon_east=lon,description='Contexto regional; no es contorno de glaciar ni espesor de hielo'),indent=2))

def swim():
 p=RAW/'SWIM_LPSC2019_consistency.zip'
 if not p.exists():
  r=requests.get('https://swim.psi.edu/LPSCProducts.php',params={'C_i-GeoTIFF':'True','DL-Sel':'True'},timeout=120);r.raise_for_status()
  if not r.content.startswith(b'PK'):raise ValueError('SWIM download did not return ZIP')
  p.write_bytes(r.content)
 with zipfile.ZipFile(p) as z:
  for name in ['Arcadia_Ci.tif','Onilus_Ci.tif']:
   (RAW/name).write_bytes(z.read(name))
 (RAW/'swim_provenance.json').write_text(json.dumps(dict(url='https://swim.psi.edu/LPSCProducts.php',params={'C_i-GeoTIFF':'True','DL-Sel':'True'},release='LPSC2019 legacy, not latest SWIM',meaning='consistency [-1,1], NOT calibrated probability, NOT local ice depth',sha256=hashlib.sha256(p.read_bytes()).hexdigest()),indent=2))

def terrain_stats():
 e=gpd.read_file(OUT/'earth_entities.gpkg');earth=[];mars=[]
 for name in AOIS:
  with rasterio.open(RAW/f'copernicus_{name}.tif') as src:
   a=src.read(1).astype(float);lat=(src.bounds.top+src.bounds.bottom)/2
   # Local metric spacings for geographic DEM, adequate for small AOIs.
   dy=abs(src.transform.e)*111132;dx=src.transform.a*111320*np.cos(np.deg2rad(lat))
   gy,gx=np.gradient(a,dy,dx);slope=np.rad2deg(np.arctan(np.hypot(gx,gy)))
   aspect=np.arctan2(-gx,-gy)%(2*np.pi)
   selected=e[e.geometry.within(box(*src.bounds))]
   for _,r in selected.iterrows():
    m=geometry_mask([r.geometry],a.shape,src.transform,invert=True)&np.isfinite(a)
    if src.nodata is not None:m&=(a!=src.nodata)
    count=int(m.sum())
    if count<3:continue
    deg=float(np.degrees(np.arctan2(np.mean(np.sin(aspect[m])),np.mean(np.cos(aspect[m]))))%360)
    earth.append(dict(glacier_id=r.glacier_id,aoi=name,n_pixels=count,dem_source='Copernicus GLO-30 DSM',elevation_mean_m=float(a[m].mean()),elevation_min_m=float(a[m].min()),elevation_max_m=float(a[m].max()),slope_mean_deg=float(slope[m].mean()),aspect_circular_deg=deg,aspect_resultant=float(np.hypot(np.sin(aspect[m]).mean(),np.cos(aspect[m]).mean())),inventory_slope_deg=r.get('inventory_slope_deg',r.slope_deg),slope_difference_deg=float(slope[m].mean()-r.get('inventory_slope_deg',r.slope_deg)),low_resolution_flag=count<20))
 for name in ['deuteronilus','arcadia']:
  with rasterio.open(RAW/f'mola_{name}.tif') as src:
   a=src.read(1).astype(float);lat=(src.bounds.top+src.bounds.bottom)/2
   dy=np.deg2rad(abs(src.transform.e))*3396000;dx=np.deg2rad(src.transform.a)*3396000*np.cos(np.deg2rad(lat))
   gy,gx=np.gradient(a,dy,dx);slope=np.degrees(np.arctan(np.hypot(gx,gy)))
   mars.append(dict(region=name,west=src.bounds.left,east=src.bounds.right,south=src.bounds.bottom,north=src.bounds.top,elevation_min_m=a.min(),elevation_mean_m=a.mean(),elevation_max_m=a.max(),slope_median_deg=np.median(slope[1:-1,1:-1]),slope_p95_deg=np.quantile(slope[1:-1,1:-1],.95),spacing_north_south_m=dy,status='regional_context_not_glacier_slope_or_ice_thickness'))
 pd.DataFrame(earth).to_csv(OUT/'earth_copernicus_pilot.csv',index=False);pd.DataFrame(mars).to_csv(OUT/'mars_mola_context.csv',index=False)
 # Correct planetary coordinates: transform Mars lon/lat to raster CRS, not WGS84.
 from pyproj import Transformer,CRS
 summary=[]
 for name,lat,lon in [('Arcadia',40,200),('Onilus',42.5,25)]:
  with rasterio.open(RAW/f'{name}_Ci.tif') as src:
   sphere=CRS.from_proj4('+proj=longlat +a=3396190 +b=3396190 +no_defs')
   transf=Transformer.from_crs(sphere,src.crs,always_xy=True)
   x,y=transf.transform(lon if lon<=180 else lon-360,lat)
   v=next(src.sample([(x,y)],masked=True))[0]
   summary.append(dict(region=name,latitude=lat,longitude_east=lon,consistency=None if np.ma.is_masked(v) else float(v),nodata=None if src.nodata is None else float(src.nodata),raster_crs=src.crs.to_wkt(),release='LPSC2019',status='point_context_not_probability_or_target_footprint'))
 pd.DataFrame(summary).to_csv(OUT/'mars_swim_point_context.csv',index=False)
 print('Copernicus pilot polygons',len(earth));print(pd.DataFrame(mars).to_string(index=False));print(pd.DataFrame(summary).drop(columns='raster_crs').to_string(index=False))

if __name__=='__main__':
 copernicus();mola('deuteronilus',42.5,25);mola('arcadia',40,200);swim();terrain_stats()
