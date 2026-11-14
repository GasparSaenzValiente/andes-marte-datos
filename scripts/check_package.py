from pathlib import Path
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
R=Path(__file__).resolve().parents[1];O=R/'data/processed'
e=gpd.read_file(O/'earth_entities.gpkg');s=pd.read_csv(O/'scores.csv');u=pd.read_csv(O/'earth_uncertainty.csv')
assert len(e)==7719 and e.glacier_id.is_unique and e.is_valid.all()
assert e.geometry.notna().all() and (e.area_km2>0).all() and (e.length_m>0).all()
assert s[['glacier_id','target_id']].duplicated().sum()==0 and len(s)==2*len(e)
assert s.glacier_id.isin(e.glacier_id).all() and u.glacier_id.isin(e.glacier_id).all()
assert (s.score_p05<=s.score_median).all() and (s.score_median<=s.score_p95).all()
assert s[['score_p05','score_median','score_p95']].ge(0).all().all() and s[['score_p05','score_median','score_p95']].le(100).all().all()
assert s.p_top10.between(0,1).all() and s.score_full_operational.isna().all()
assert e.pi_plastic.isna().all() and e.accessibility_factor.isna().all()
assert (u.p05<=u['median']).all() and (u['median']<=u.p95).all()
assert (e[e.glacier_id=='G697821O302447S'].activity=='GEA').all()
assert len(pd.read_csv(O/'earth_copernicus_pilot.csv'))==62
for name in ['deuteronilus','arcadia']:
 with rasterio.open(R/f'data/raw/mola_{name}.tif') as ds:
  assert ds.shape==(256,256) and ds.crs.to_epsg()!=4326
  assert np.isfinite(ds.read(1)).all()
for name in ['Arcadia','Onilus']:
 with rasterio.open(R/f'data/raw/{name}_Ci.tif') as ds:
  a=ds.read(1,masked=True);assert a.min()>=-1.001 and a.max()<=1.001
assert (R/'mapa.html').stat().st_size>10000 and (R/'pca.svg').exists()
print('PASS: unique keys, exact geometries, joins, ranks, quantiles, missing-data semantics, DEM pilot, planetary CRS and SWIM range')

n=pd.read_csv(O/'earth_copernicus_national.csv');assert len(n)==len(e) and n.n_pixels.notna().all()
assert e.terrain_source.str.contains('Copernicus').all()
for _,group in s.groupby('target_id'):
 assert set(group.rank_by_median)==set(range(1,len(e)+1))
 assert abs(group.p_top10.sum()-10)<1e-8
a=pd.read_parquet(O/'earth_mars_ready.parquet');assert len(a)==len(s) and not a[['glacier_id','target_id']].duplicated().any()
print('PASS: national DEM completeness, complete rankings, top10 mass and integrated table')
