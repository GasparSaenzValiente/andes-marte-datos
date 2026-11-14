from pathlib import Path
import json,html,os,tempfile,re,hashlib
import requests
os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"andes_mars_mpl"))
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
from branca.colormap import linear
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/processed'

def main():
 e=gpd.read_file(OUT/'earth_entities.gpkg');s=pd.read_csv(OUT/'scores.csv');u=pd.read_csv(OUT/'earth_uncertainty.csv')
 uncertainty=u.pivot(index='glacier_id',columns='feature',values='median')
 e=e.merge(uncertainty.reset_index(),on='glacier_id')
 m=folium.Map(location=[-31.5,-69],zoom_start=6,tiles='OpenStreetMap',prefer_canvas=True)
 context=ROOT/'data/raw/south_america_context.geojson'
 if not context.exists():
  response=requests.get('https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson',timeout=60);response.raise_for_status()
  geo=response.json();geo['features']=[f for f in geo['features'] if f['properties'].get('CONTINENT')=='South America'];context.write_text(json.dumps(geo))
 folium.GeoJson(json.loads(context.read_text()),name='Contexto Natural Earth (offline)',style_function=lambda f:{'color':'#859296','weight':1,'fillColor':'#f3f0e8','fillOpacity':.7},tooltip=folium.GeoJsonTooltip(fields=['ADMIN'],aliases=['País'])).add_to(m)
 c=linear.viridis.scale(0,60);c.caption='Similitud exploratoria 0-100 (colores 0-60); no probabilidad'
 for target,title in [('deuteronilus_lda','Deuteronilus: flujo LDA'),('arcadia_ice_sheet','Arcadia: hielo enterrado')]:
  g=e.merge(s[s.target_id==target],on='glacier_id').copy()
  # Simplified display only. Exact analysis polygons remain in GeoPackage.
  g.geometry=g.to_crs(6933).simplify(20,preserve_topology=True).to_crs(4326)
  cols=['glacier_id','name','province','activity','area_km2','length_m','length_source','slope_deg','H_est_m','H_over_L','debris_over_H','ice_fraction','skin_over_H','tau_driving_pa','score_median','score_p05','score_p95','rank_by_median','p_top10','score_with_slope_depth_median','geometry']
  for f in g.select_dtypes(include='number').columns:g[f]=g[f].round(5)
  group=folium.FeatureGroup(name=title,show=target=='deuteronilus_lda')
  folium.GeoJson(g[cols].to_json(),name=title,style_function=lambda f:{'fillColor':c(f['properties']['score_median']),'color':'#304256','weight':.5,'fillOpacity':.8},highlight_function=lambda f:{'weight':3},tooltip=folium.GeoJsonTooltip(fields=['name','activity','score_median','rank_by_median'],aliases=['Glaciar','Clase','Score exploratorio','Ranking']),popup=folium.GeoJsonPopup(fields=[k for k in cols if k!='geometry'],labels=True,max_width=600)).add_to(group)
  points=g[['glacier_id','name','score_median','score_p05','score_p95','rank_by_median','H_over_L','debris_over_H','ice_fraction','skin_over_H','tau_driving_pa','geometry']].copy()
  points.geometry=points.geometry.representative_point()
  fields=[f for f in points.columns if f!='geometry']
  folium.GeoJson(points.to_json(),marker=folium.CircleMarker(radius=3,fill=True,fill_opacity=.85),style_function=lambda f:{'color':c(f['properties']['score_median']),'fillColor':c(f['properties']['score_median']),'weight':1},tooltip=folium.GeoJsonTooltip(fields=['name','score_median','rank_by_median']),popup=folium.GeoJsonPopup(fields=fields,max_width=600)).add_to(group)
  group.add_to(m)
  top=s[s.target_id.eq(target)].nsmallest(30,'rank_by_median').merge(e.drop(columns='geometry'),on='glacier_id')
  top.to_csv(OUT/f'top30_{target}.csv',index=False)
 folium.CircleMarker([-30.2447,-69.7821],radius=8,tooltip='Dos Lenguas: identificacion confirmada',color='red',fill=True).add_to(m)
 folium.CircleMarker([-(32+57/60+43/3600),-(69+22/60+19/3600)],radius=8,tooltip='Morenas Coloradas: Balcon I, punto de literatura; correspondencia de poligono pendiente',color='orange',fill=True).add_to(m)
 folium.LayerControl(collapsed=False).add_to(m);c.add_to(m)
 note='''<div style="position:fixed;bottom:25px;left:15px;z-index:9999;background:white;padding:12px;max-width:430px;border:1px solid #777;font:13px sans-serif"><b>Andes → Marte · datos exploratorios</b><br>7.719 entidades del inventario ING; cambie el blanco en las capas.<br>Scores condicionados a supuestos: no indican aptitud de una base.<br>Los intervalos son percentiles Monte Carlo p05–p95.<br>Accesibilidad y Π plástico: sin datos. Morenas Coloradas: pendiente.<br>Use los CSV para la precisión completa; polígonos aquí simplificados.</div>'''
 m.get_root().html.add_child(folium.Element(note))
 raw=m.get_root().render();vendor=ROOT/'vendor';vendor.mkdir(exist_ok=True);manifest=[]
 def fetch_asset(url):
  ext='.css' if '.css' in url else '.js';p=vendor/(hashlib.sha256(url.encode()).hexdigest()[:16]+ext)
  if not p.exists():
   response=requests.get(url,timeout=60);response.raise_for_status();p.write_bytes(response.content)
  content=p.read_text();manifest.append(dict(url=url,file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
  return content
 def script(match):return '<script>'+fetch_asset(match.group(1)).replace('</script','<\\/script')+'</script>'
 def style(match):return '<style>'+fetch_asset(match.group(1))+'</style>'
 raw=re.sub(r'<script src="([^"]+)"></script>',script,raw)
 raw=re.sub(r'<link rel="stylesheet" href="([^"]+)"\s*/?>',style,raw)
 (ROOT/'mapa.html').write_text(raw)
 (vendor/'manifest.json').write_text(json.dumps(manifest,indent=2))
 # Standalone PCA SVG using standard plotting, not a website.
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 p=pd.read_csv(OUT/'pca_earth.csv').merge(e[['glacier_id','activity']],on='glacier_id');t=pd.read_csv(OUT/'pca_mars_draws.csv');meta=json.loads((OUT/'pca_metadata.json').read_text())
 fig,ax=plt.subplots(figsize=(9,6))
 for cl,col in [('GEA','#177d9e'),('GEI','#e19c36'),('GEA+GEI','#777777')]:
  q=p[p.activity==cl];ax.scatter(q.pc1,q.pc2,s=5,alpha=.3,color=col,label=cl)
 ax.scatter(t.pc1,t.pc2,s=10,alpha=.25,color='#c82956',label='Deuteronilus: realizaciones del escenario')
 d=p[p.glacier_id.eq('G697821O302447S')];ax.scatter(d.pc1,d.pc2,marker='*',s=150,color='black',label='Dos Lenguas')
 ax.set(xlabel=f"PC1 ({meta['explained_variance_ratio'][0]:.1%})",ylabel=f"PC2 ({meta['explained_variance_ratio'][1]:.1%})",title='Espacio exploratorio de parámetros adimensionales')
 ax.legend(fontsize=8);fig.text(.1,.01,'PCA descriptivo; variables comparten H estimado. Arcadia no tiene vector de flujo completo.',fontsize=8);fig.tight_layout(rect=(0,.03,1,1));fig.savefig(ROOT/'pca.svg');plt.close(fig)
 print('Generated mapa.html, pca.svg and top30 tables')
if __name__=='__main__':main()
