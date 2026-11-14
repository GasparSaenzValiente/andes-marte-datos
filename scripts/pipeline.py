"""Inventario oficial -> entidades -> fisica exploratoria -> ranking y PCA.
Run from project root: python scripts/pipeline.py
"""
from pathlib import Path
import json, hashlib, zipfile, argparse
import numpy as np
import pandas as pd
import geopandas as gpd
from pyproj import Geod
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data';OUT=DATA/'processed'
def polygonal(geom):
    if geom.geom_type in ('Polygon','MultiPolygon'):return geom
    from shapely import union_all
    return union_all([polygonal(g) for g in geom.geoms if g.geom_type in ('Polygon','MultiPolygon','GeometryCollection')])

FEATURES=['log10_sin_slope','log10_H_over_L','log10_debris_over_H','ice_fraction','log10_skin_over_H']

def earth_features():
    z=DATA/'raw/ING_Argentina.zip'
    with zipfile.ZipFile(z) as f:
        shp=next(n for n in f.namelist() if n.endswith('.shp'))
    g=gpd.read_file(f'/vsizip/{z}/{shp}',encoding='UTF-8').to_crs(4326)
    all_count=len(g)
    g=g[g.Tipo_geofo.isin(['GEA','GEI'])].copy().reset_index(drop=True)
    g['source_row']=g.index
    invalid=(~g.is_valid).sum();g['geometry']=g.geometry.make_valid().map(polygonal)
    g['part_id']=g.ID_local+'__'+g.groupby('ID_local').cumcount().astype(str)
    # Keep every original feature, including activity transitions, in a separate layer.
    g.to_file(OUT/'earth_inventory_parts.gpkg',layer='parts',driver='GPKG')
    rows=[];geod=Geod(ellps='WGS84')
    for ident,p in g.groupby('ID_local',sort=True):
        geom=p.geometry.union_all()
        classes='+'.join(sorted(p.Tipo_geofo.unique()))
        area=abs(geod.geometry_area_perimeter(geom)[0])/1e6
        # Geod signed areas can cancel on mixed ring orientations; use per-polygon absolute area.
        if geom.geom_type=='MultiPolygon':area=sum(abs(geod.geometry_area_perimeter(v)[0]) for v in geom.geoms)/1e6
        w=p.Area.astype(float).to_numpy();w=w/w.sum()
        def mean(c):return float(np.average(p[c].to_numpy(float),weights=w))
        names=p.Nombre_com.dropna().unique()
        lengths=pd.to_numeric(p.Largo_tota,errors='coerce');lengths=lengths[lengths>0]
        rows.append(dict(glacier_id=ident,name='; '.join(names) if len(names) else ident,
          province='; '.join(sorted(p.Provincia.unique())),activity=classes,n_parts=len(p),
          area_km2=area,area_inventory_km2=float(p.Area.sum()),length_m=float(lengths.max()) if len(lengths) else np.nan,
          length_source='ING_Largo_tota_max' if len(lengths) else 'geometry_proxy',
          elevation_mean_m=mean('H_media_to'),elevation_min_m=float(p.H_min_tota.min()),
          elevation_max_m=float(p.H_max_tota.max()),slope_deg=mean('Pendiente'),
          aspect_source='; '.join(sorted(p.Orientacio.dropna().unique())),
          image_dates='; '.join(sorted(p.Img_ba_F.dropna().unique())),geometry=geom))
    e=gpd.GeoDataFrame(rows,crs=4326)
    label_points=e.geometry.representative_point()
    e['lon']=label_points.x;e['lat']=label_points.y
    # Compute morphology in local UTM zones, not one national Web Mercator projection.
    e['utm_zone']=np.clip(((e.lon+180)//6+1).astype(int),1,60)
    for zone,p in e.groupby('utm_zone'):
        projected=p.to_crs(32700+int(zone))
        for i,geom in projected.geometry.items():
            xy=np.array(geom.minimum_rotated_rectangle.exterior.coords)
            major=float(np.linalg.norm(np.diff(xy,axis=0),axis=1).max())
            e.loc[i,'bbox_major_m']=major
            if not np.isfinite(e.loc[i,'length_m']):e.loc[i,'length_m']=major
    e['width_proxy_m']=e.area_km2*1e6/e.length_m
    e['elevation_range_m']=e.elevation_max_m-e.elevation_min_m
    e['H_est_m']=50*e.area_km2**0.2
    e['terrain_source']='ING supplied: original DEM not identified here'
    national=OUT/'earth_copernicus_national.csv'
    if national.exists():
        d=pd.read_csv(national).set_index('glacier_id')
        for col in ['slope_deg','elevation_mean_m','elevation_min_m','elevation_max_m']:
            e['inventory_'+col]=e[col]
            demcol='slope_mean_deg' if col=='slope_deg' else col
            vals=e.glacier_id.map(d[demcol]);valid=vals.notna()
            e.loc[valid,col]=vals[valid]
        valid=e.glacier_id.map(d['slope_mean_deg']).notna()
        e.loc[valid,'terrain_source']='Copernicus GLO-30 national pixel-center zonal statistics'
        e['dem_n_pixels']=e.glacier_id.map(d.n_pixels)
        e['dem_low_resolution_flag']=e.glacier_id.map(d.low_resolution_flag)
        e['elevation_range_m']=e.elevation_max_m-e.elevation_min_m
    e['analogue_status']='exploratory_priors_not_validated'
    e['pi_plastic']=np.nan;e['pi_plastic_status']='missing_yield_stress_tau_y'
    e['accessibility_factor']=np.nan
    e.to_file(OUT/'earth_entities.gpkg',layer='entities',driver='GPKG')
    e.drop(columns='geometry').to_csv(OUT/'earth_features.csv',index=False)
    return e,dict(inventory_rows=all_count,selected_parts=len(g),entities=len(e),invalid_parts_repaired=int(invalid),
        estimated_lengths=int((e.length_source=='geometry_proxy').sum()),
        classes_parts=g.Tipo_geofo.value_counts().to_dict(),classes_entities=e.activity.value_counts().to_dict())

def transform(h,l,slope,debris,phi,kappa,period):
    shape=np.broadcast_shapes(np.shape(h),np.shape(phi))
    skin=np.sqrt(kappa*period/np.pi)
    a=np.full(shape+(5,),np.nan)
    if slope is not None:a[...,0]=np.log10(np.sin(np.deg2rad(slope)))
    if l is not None:a[...,1]=np.log10(h/l)
    a[...,2]=np.log10(debris/h);a[...,3]=phi;a[...,4]=np.log10(skin/h)
    return a

def score_distance(x,y,scales,weights):
    return np.sqrt(np.sum(((x-y)/np.array(scales))**2*np.array(weights),axis=-1))

def simulate(e,cfg):
    rng=np.random.default_rng(cfg['seed']);n=len(e);m=cfg['draws'];ec=cfg['earth'];shape=(n,m)
    h=e.H_est_m.to_numpy()[:,None]*np.exp(rng.normal(0,ec['H_log_sigma'],shape))
    lp=np.where(e.length_source.eq('geometry_proxy'),.4,.2)[:,None]
    l=e.length_m.to_numpy()[:,None]*rng.uniform(1-lp,1+lp,shape)
    slope=np.clip(e.slope_deg.to_numpy()[:,None]+rng.uniform(-ec['slope_error_deg'],ec['slope_error_deg'],shape),.01,89)
    phi=np.empty(shape);debris=np.empty(shape)
    for cl in e.activity.unique():
        mask=e.activity.eq(cl).to_numpy();p=ec[cl]
        phi[mask]=rng.uniform(*p['ice_fraction'],(mask.sum(),m));debris[mask]=rng.uniform(*p['debris_m'],(mask.sum(),m))
    kappa=rng.uniform(*ec['kappa_m2_s'],shape)
    x=transform(h,l,slope,debris,phi,kappa,ec['year_s'])
    rho=phi*917+(1-phi)*2700
    tau=rho*ec['gravity_m_s2']*h*np.sin(np.deg2rad(slope))
    # Partial operational proxy: true road access is unknown, so no complete operational score.
    op=np.exp(-(slope/ec['operational_slope_scale_deg'])**2)*np.exp(-debris/ec['operational_depth_scale_m'])
    long=[];targets=[];draws={};unc=[]
    for j,f in enumerate(FEATURES):
        v=x[...,j] if j==3 else 10**x[...,j]
        qs=np.quantile(v,[.05,.5,.95],axis=1)
        for i in range(n):unc.append(dict(glacier_id=e.glacier_id.iloc[i],feature=f.replace('log10_',''),p05=qs[0,i],median=qs[1,i],p95=qs[2,i],status='conditional_on_assumptions'))
    for name,v in [('tau_driving_pa',tau),('H_m',h),('debris_m',debris),('ice_volume_m3',e.area_km2.to_numpy()[:,None]*1e6*h*phi)]:
        qs=np.quantile(v,[.05,.5,.95],axis=1)
        for i in range(n):unc.append(dict(glacier_id=e.glacier_id.iloc[i],feature=name,p05=qs[0,i],median=qs[1,i],p95=qs[2,i],status='conditional_on_assumptions'))
    sensitivity=[]
    for t in cfg['targets']:
        def u(key):return rng.uniform(*t[key],m)
        th=u('H_m');tp=u('ice_fraction');td=u('debris_m');tk=u('kappa_m2_s')
        tl=u('length_m') if t['length_m'] else None;ts=u('slope_deg') if t['slope_deg'] else None
        y=transform(th,tl,ts,td,tp,tk,t['year_s'])
        dims=t['dimensions'];xx=x[...,dims];yy=y[...,dims]
        # Same target realization for every Earth site within each draw.
        dist=score_distance(xx,yy,t['normalization_scales'],t['weights'])
        score=100*np.exp(-.5*dist**2);partial=score*op
        qs=np.quantile(score,[.05,.5,.95],axis=1);oq=np.quantile(partial,[.05,.5,.95],axis=1)
        rank=np.argsort(np.argsort(-score,axis=0),axis=0)+1
        rqs=np.quantile(rank,[.05,.5,.95],axis=1)
        frame=pd.DataFrame(dict(glacier_id=e.glacier_id,target_id=t['id'],score_p05=qs[0],score_median=qs[1],score_p95=qs[2],
             score_with_slope_depth_p05=oq[0],score_with_slope_depth_median=oq[1],score_with_slope_depth_p95=oq[2],
             score_full_operational=np.nan,rank_p05=rqs[0],rank_median=rqs[1],rank_p95=rqs[2],p_top10=(rank<=10).mean(axis=1),status=t['status']))
        frame['rank_by_median']=frame.score_median.rank(method='first',ascending=False).astype(int)
        long.append(frame);draws[t['id']]=y
        for j in dims:
            v=y[:,j] if j==3 else 10**y[:,j];q=np.quantile(v,[.05,.5,.95])
            targets.append(dict(target_id=t['id'],feature=FEATURES[j].replace('log10_',''),p05=q[0],median=q[1],p95=q[2],status=t['status']))
        # Sensitivity perturbs relative weights lognormally, holding physics draws fixed.
        base=set(np.argsort(-qs[1])[:10]);hits=np.zeros(n);overlaps=[]
        sq=((xx-yy)/np.array(t['normalization_scales']))**2
        for rep in range(60):
            w=np.array(t['weights'])*np.exp(rng.normal(0,.5,len(dims)));w/=w.sum()
            s=np.median(100*np.exp(-.5*np.sum(sq*w,axis=-1)),axis=1)
            top=np.argsort(-s)[:10];hits[top]+=1;overlaps.append(len(base&set(top))/10)
        for i in range(n):sensitivity.append(dict(glacier_id=e.glacier_id.iloc[i],target_id=t['id'],top10_frequency_weights=hits[i]/60,weight_trials=60,mean_top10_overlap=float(np.mean(overlaps))))
    pd.DataFrame(unc).to_csv(OUT/'earth_uncertainty.csv',index=False)
    pd.DataFrame(targets).to_csv(OUT/'mars_dimensionless.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(OUT/'weight_sensitivity.csv',index=False)
    scores=pd.concat(long,ignore_index=True);scores.to_csv(OUT/'scores.csv',index=False)
    med=np.median(x,axis=1);scaler=StandardScaler().fit(med);pca=PCA(n_components=2).fit(scaler.transform(med))
    coords=pca.transform(scaler.transform(med));pd.DataFrame(dict(glacier_id=e.glacier_id,pc1=coords[:,0],pc2=coords[:,1])).to_csv(OUT/'pca_earth.csv',index=False)
    # Only the complete flow target is projected; do not impute Arcadia flow dimensions.
    pcat=[]
    for tid,y in draws.items():
        if np.isfinite(y).all():
            v=pca.transform(scaler.transform(y))
            pcat+=list(pd.DataFrame(dict(target_id=tid,pc1=v[:,0],pc2=v[:,1])).to_dict('records'))
    pd.DataFrame(pcat).to_csv(OUT/'pca_mars_draws.csv',index=False)
    (OUT/'pca_metadata.json').write_text(json.dumps(dict(features=FEATURES,explained_variance_ratio=pca.explained_variance_ratio_.tolist(),standardization_mean=scaler.mean_.tolist(),standardization_scale=scaler.scale_.tolist(),components=pca.components_.tolist(),warning='Descriptivo; 3 variables comparten H. No valida similitud fisica.'),indent=2))
    return scores

def validate(e,scores):
    # Exact inventory identifier confirmed by name and location, not the homonymous GD in Tierra del Fuego.
    v=scores[scores.glacier_id.eq('G697821O302447S')].copy()
    v['site']='Dos Lenguas';v['match_status']='confirmed_inventory_name_location';v['percentile_from_top']=100*v.rank_by_median/len(e)
    v['passes_top10']=v.rank_by_median<=10
    v.to_csv(OUT/'validation_dos_lenguas.csv',index=False)
    pd.DataFrame([dict(site='Morenas Coloradas',match_status='unresolved_no_name_in_selected_inventory',glacier_id=None,passes_top10=None,reason='Require expert polygon/site crosswalk; do not assign nearest feature automatically')]).to_csv(OUT/'validation_morenas_coloradas.csv',index=False)
    return v[['target_id','rank_by_median','percentile_from_top','passes_top10']].to_dict('records')

def main():
    OUT.mkdir(parents=True,exist_ok=True);cfg=json.loads((ROOT/'config.json').read_text())
    args=argparse.ArgumentParser();args.add_argument('--features-only',action='store_true');options=args.parse_args()
    e,report=earth_features()
    if options.features_only:
        print(json.dumps(report,indent=2));return
    scores=simulate(e,cfg);report['validation_dos_lenguas']=validate(e,scores)
    report.update(terrain_sources=e.terrain_source.value_counts().to_dict(),seed=cfg['seed'],draws=cfg['draws'],full_operational_score_available=False,plastic_pi_available=False,ranking_status='exploratory_not_validated',inventory_sha256=hashlib.sha256((DATA/'raw/ING_Argentina.zip').read_bytes()).hexdigest())
    (OUT/'quality_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps(report,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
