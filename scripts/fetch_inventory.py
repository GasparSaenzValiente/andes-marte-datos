from pathlib import Path
import requests,hashlib,json
root=Path(__file__).resolve().parents[1]
u='https://www.glaciaresargentinos.gob.ar/wp-content/uploads/shapes/00-Shapefile-Argentina.zip'
p=root/'data/raw/ING_Argentina.zip';p.parent.mkdir(parents=True,exist_ok=True)
if not p.exists():
 r=requests.get(u,timeout=180);r.raise_for_status()
 if not r.content.startswith(b'PK'):raise ValueError('El servidor no devolvio ZIP')
 p.write_bytes(r.content)
print(hashlib.sha256(p.read_bytes()).hexdigest(),p)
