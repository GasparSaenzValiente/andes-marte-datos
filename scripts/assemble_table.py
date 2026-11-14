"""One analysis-ready table per glacier-target, without duplicated geometry."""
from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1];O=R/'data/processed'
e=pd.read_csv(O/'earth_features.csv');s=pd.read_csv(O/'scores.csv');u=pd.read_csv(O/'earth_uncertainty.csv')
w=u.pivot(index='glacier_id',columns='feature',values=['p05','median','p95'])
w.columns=[f'{feature}_{q}' for q,feature in w.columns];w=w.reset_index()
a=s.merge(e,on='glacier_id',validate='many_to_one').merge(w,on='glacier_id',validate='many_to_one')
sen=pd.read_csv(O/'weight_sensitivity.csv');a=a.merge(sen,on=['glacier_id','target_id'],validate='one_to_one')
a.to_csv(O/'earth_mars_ready.csv',index=False)
a.to_parquet(O/'earth_mars_ready.parquet',index=False)
print('Saved',len(a),'rows and',len(a.columns),'columns')
