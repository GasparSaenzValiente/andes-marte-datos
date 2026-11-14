"""Optional local demo. Data pipeline and static map work without Streamlit."""
from pathlib import Path
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
R=Path(__file__).resolve().parent;O=R/'data/processed'
st.set_page_config(page_title='Andes → Marte',layout='wide')
st.title('Andes → Marte · candidatos exploratorios')
st.caption('Datos ING + Copernicus + NASA MOLA + SWIM. Scores condicionados a parámetros estimados.')
st.warning('Validación incompleta: Dos Lenguas está dentro del 5% superior, fuera del top 10. Morenas Coloradas no tiene correspondencia confirmada. Accesibilidad y Π plástico: sin datos.')
@st.cache_data
def load():
 return pd.read_csv(O/'earth_features.csv'),pd.read_csv(O/'scores.csv'),pd.read_csv(O/'earth_uncertainty.csv')
e,s,u=load();target=st.selectbox('Blanco',s.target_id.unique())
r=s[s.target_id==target].merge(e,on='glacier_id');province=st.multiselect('Provincias',sorted(e.province.unique()))
if province:r=r[r.province.isin(province)]
st.dataframe(r.sort_values('rank_by_median')[['rank_by_median','name','province','activity','score_median','score_p05','score_p95','p_top10','glacier_id']],hide_index=True)
st.download_button('Descargar selección CSV',r.to_csv(index=False).encode('utf-8'),file_name=f'{target}.csv',mime='text/csv')
id=st.selectbox('Ficha de glaciar',r.glacier_id.tolist()) if len(r) else None
if id:
 st.dataframe(u[u.glacier_id==id],hide_index=True)
 st.json(r[r.glacier_id==id].iloc[0].to_dict())
with st.expander('Mapa nacional',expanded=True):
 st.caption('El selector de capas del mapa permite cambiar de blanco independientemente de la tabla.')
 components.html((R/'mapa.html').read_text(),height=720,scrolling=True)
st.image((R/'pca.svg').read_bytes())
st.markdown((R/'docs/METODOLOGIA.md').read_text())
