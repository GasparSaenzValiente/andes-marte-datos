# Qué está resuelto y qué falta

**La capa de datos nacional está procesada**, con archivos listos para QGIS, Python y la demo. La física subsuperficial sigue teniendo parámetros no observados: los resultados se entregan como escenarios exploratorios.

| Componente | Entregado |
|---|---|
| Inventario oficial argentino | ZIP original y 8.062 partes GEA/GEI conservadas |
| Unidad de análisis | 7.719 entidades sin duplicar identificadores |
| DEM Tierra | Copernicus GLO-30 nacional: 55 teselas, cero fallos, 7.719 entidades con píxeles |
| Calidad de DEM | 1.167 entidades con menos de 20 píxeles, señaladas |
| Geometría y relieve | Área, largo/proxy, ancho/proxy, altitudes, pendiente y orientación circular |
| Marte | Dos blancos regionales, tabla de fuentes/rangos, dos recortes MOLA y mapas SWIM reales |
| Incertidumbre | 512 realizaciones por par Tierra–Marte, percentiles y ranking variable |
| Sensibilidad | 60 perturbaciones de pesos por blanco |
| Integración | 15.438 filas en earth_mars_ready.csv/parquet, clave glacier_id+target_id |
| Visualización | Mapa HTML con dos capas, fichas y PCA SVG; Streamlit opcional |
| Reproducción | Código, configuración, versiones, pruebas y manifiestos SHA256 |

La comparación de flujo se concentra en Deuteronilus. Arcadia usa dimensiones de hielo enterrado y no se equipara geométricamente a un glaciar de roca. Los datos MOLA y SWIM se separan de los parámetros asumidos: no se interpreta topografía como espesor enterrado ni consistencia SWIM como probabilidad.

El resultado nacional final coloca a Dos Lenguas en **119/7.719** para Deuteronilus y **307/7.719** para Arcadia. No queda en top 10. Morenas Coloradas requiere resolver su correspondencia con polígonos; se entregan puntos y vecinos para revisión, sin asignar una etiqueta por proximidad.

**No observados:** espesor de cada cuerpo, fracción de hielo, espesor de detrito, esfuerzo de cedencia y accesibilidad. H usa una relación publicada; φ, detrito y parte de los parámetros marcianos usan rangos explícitos. Π plástico y score operativo completo quedan nulos. La incertidumbre Monte Carlo es condicional a esos priors y no resuelve por sí misma su posible sesgo.

Para presentar al jurado: «Combinamos un inventario oficial de glaciares de roca con relieve de 30 m y evidencia orbital de Marte para explorar candidatos a análogos, haciendo visibles las incertidumbres y las limitaciones de validación». No afirmar que se reprodujeron ambos sitios expertos ni que el ranking ya determina el mejor análogo o una base segura.

Para usar los datos, empezar por `README.md` y `docs/DICCIONARIO.md`. Para revisar las decisiones físicas y las limitaciones, leer `docs/METODOLOGIA.md`.
