> **Descargar:** en este repositorio elegí **Code → Download ZIP**, descomprimilo y abrí `mapa.html` dentro de la carpeta descargada. También podés usar [la descarga directa del proyecto](https://github.com/GasparSaenzValiente/andes-marte-datos/archive/refs/heads/main.zip). Requiere iniciar sesión en GitHub porque el repositorio es privado.

# Andes → Marte · paquete de datos reproducible

Datos oficiales de glaciares de roca argentinos y datos orbitales de Marte, con geometrías, parámetros, procedencia, incertidumbre y ranking **exploratorio**. No se requiere Earth Engine para abrir los datos ni ejecutar el piloto.

## Abrir ahora

- `mapa.html`: mapa interactivo con ambos blancos y fichas; abrir en navegador; bibliotecas embebidas, mapa base requiere internet.
- `data/processed/earth_entities.gpkg`: 7.719 entidades, para QGIS, GeoPandas o la demo.
- `data/processed/earth_mars_ready.parquet` y `.csv`: tabla integrada, una fila por glaciar/blanco, con features e incertidumbre.
- `data/processed/earth_features.csv`: atributos nacionales y banderas de estimación.
- `data/processed/scores.csv`: 15.438 pares glaciar/blanco, percentiles p05/mediana/p95, rankings y frecuencia top 10.
- `data/processed/earth_uncertainty.csv`: incertidumbre por parámetro y entidad, formato largo.
- `data/processed/mars_parameters.csv`: valores/rangos marcianos y evidencia de cada uno.
- `data/processed/mars_dimensionless.csv`: vectores derivados por blanco, con rangos.
- `data/processed/earth_copernicus_national.csv`: estadísticas GLO-30 para las **7.719 entidades**, con 1.167 cuerpos de menos de 20 píxeles marcados.
- `data/processed/earth_copernicus_pilot.csv`: control adicional en 62 entidades con recortes raster incluidos.
- `data/raw/copernicus_*.tif`, `mola_*.tif`, `Arcadia_Ci.tif`, `Onilus_Ci.tif`: datos raster reales.
- `pca.svg`, `data/processed/pca_*.csv`: gráfico y coordenadas del PCA.
- `docs/METODOLOGIA.md`, `docs/DICCIONARIO.md`, `docs/sources.csv`: cómo interpretar, usar y citar los datos.
- `data/processed/quality_report.json`: conteos, faltantes, validación y hash de entrada.

**Resultado de validación:** Dos Lenguas queda en puesto **119/7.719** para Deuteronilus y **307/7.719** para Arcadia, pero no en el top 10. Morenas Coloradas requiere resolver su correspondencia con el inventario. El score no está validado. Los valores ausentes de accesibilidad y Π plástico permanecen vacíos.

## Reproducir

Python 3.12 probado, acceso a internet para descargas. Desde esta carpeta:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/fetch_inventory.py
python scripts/pipeline.py --features-only
python scripts/national_dem.py
python scripts/pipeline.py
python scripts/terrain.py
python scripts/validate_crosswalk.py
python scripts/build_deliverables.py
python scripts/assemble_table.py
python -m unittest discover -s tests -v
python scripts/check_package.py
```

El pipeline principal usa el inventario y las estadísticas nacionales locales y no necesita red. `national_dem.py` procesa 55 teselas (~1,99 GB de transferencia), calcula estadísticas por entidad y elimina las teselas completas después de usarlas. El manifiesto conserva URLs, hashes y tamaños. Hay 7.719 entidades con píxeles válidos, sin fallos de descarga; 1.167 tienen menos de 20 píxeles. Si se omite esta etapa, `pipeline.py` puede usar los atributos ING, pero el resultado no será el ranking final distribuido. `terrain.py` descarga dos teselas completas (~79 MB) a `.cache/` y conserva recortes pequeños en `data/raw/`. Las distribuciones y scores se pueden recalcular editando `config.json`; los valores científicos y su clasificación deben actualizarse juntos en `mars_parameters.csv` cuando se cambien los escenarios. Reejecutar `build_deliverables.py` después de cambiar resultados. Los CSV de incertidumbre pueden regenerarse sin guardar millones de realizaciones.

Para una demo Streamlit opcional:

```bash
python -m pip install -r requirements-demo.txt
streamlit run app.py
```

Como alternativa a la extracción nacional ya ejecutada se incluye `scripts/gee_export.js`. Requiere proyecto de Google Earth Engine habilitado y subir la capa de entidades a un asset propio. No se ejecutó el script de Earth Engine; la extracción nacional se realizó con Python/AWS. Se conserva la resolución de trabajo en el export.

## Contrato para la demo

La clave de unión es `glacier_id`; el ranking usa `(glacier_id,target_id)`. Abrir `earth_entities.gpkg` y unir `scores.csv` con `glacier_id`, filtrando primero `target_id`. No sumar partes duplicadas ni confundir `H_media_to` (elevación) con espesor de hielo. Las entidades mixtas tienen actividad `GEA+GEI`. Las unidades aparecen en el diccionario. Los valores nulos significan desconocido, no cero. Los scores se comparan **dentro del mismo blanco**.

## Publicación y alcance

Repositorio privado de entrega: https://github.com/GasparSaenzValiente/andes-marte-datos. La opción Code → Download ZIP descarga el proyecto completo. El mapa HTML se abre después de descomprimirlo; no se ha desplegado una demo pública. `requirements.txt` fija las dependencias directas probadas; no es un lock completo de dependencias transitivas. El mapa es una visualización de análisis, no una aplicación desplegada.

El código propio se distribuye con licencia MIT; los datos de terceros conservan sus condiciones originales. Ver `docs/sources.csv`: algunas licencias no están identificadas en las descargas, y acceso público no equivale por sí solo a una licencia abierta. Se conservan las fuentes para atribución y revisión antes de publicar redistribuciones.
