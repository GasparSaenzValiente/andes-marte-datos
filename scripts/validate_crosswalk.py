from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
R=Path(__file__).resolve().parents[1];O=R/'data/processed'
g=gpd.read_file(O/'earth_entities.gpkg');utm=g.to_crs(32719)
rows=[]
sites=[('Balcon I literature',-(69+22/60+19/3600),-(32+57/60+43/3600),'S13'),('Balcon II GTNP',-69.380278,-32.934722,'https://gtnpdatabase.org/boreholes/view/517')]
for name,lon,lat,source in sites:
 p=Point(lon,lat);up=gpd.GeoSeries([p],crs=4326).to_crs(32719).iloc[0];d=utm.distance(up)
 for i in d.nsmallest(5).index:
  rows.append(dict(site=name,longitude=lon,latitude=lat,source=source,candidate_glacier_id=g.glacier_id.iloc[i],activity=g.activity.iloc[i],distance_m=d.iloc[i],point_inside=g.geometry.iloc[i].covers(p),confirmed_match=False,note='Candidate only; do not assign name or validation label automatically'))
pd.DataFrame(rows).to_csv(O/'morenas_crosswalk_candidates.csv',index=False)
print('Saved 10 candidates, no confirmed Morenas match')
