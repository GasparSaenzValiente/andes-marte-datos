# Diccionario y contrato de datos

CSV UTF-8, decimal con punto y valores nulos vacíos. Identificadores son texto. Geometrías de Tierra: EPSG:4326 en los GeoPackages de salida; el ZIP original está en EPSG:32719. **No asignar EPSG:4326 a los raster de Marte**: leer su CRS embebido y su etiqueta PDS.

| Archivo/campo | Significado |
|---|---|
| earth_inventory_parts.gpkg / part_id | Clave de parte `ID_local__n`; conserva cada GEA/GEI y sus atributos originales |
| ID_local, ID_GLIMS | Identificadores originales. Conservar aun si algún GLIMS original tiene formato inconsistente |
| H_media_to, H_max_tota, H_min_tota | Elevaciones, m; **no espesor** |
| earth_entities.gpkg / glacier_id | ID_local agrupado, clave única de entidad |
| n_parts | Número de registros seleccionados agrupados |
| activity | GEA activo, GEI inactivo o GEA+GEI mixto |
| province, name | Provincia y nombre original, o ID si falta nombre |
| area_km2 | Área geodésica de unión reparada, km² |
| area_inventory_km2 | Suma de áreas originales seleccionadas, km²; sirve para comparar |
| length_m / length_source | Largo informado máximo por entidad, o eje de rectángulo orientado si falta, m |
| bbox_major_m | Eje mayor del rectángulo orientado en UTM local, m |
| width_proxy_m | Área/largo, m; no ancho de sección transversal medido |
| elevation_mean/min/max/range_m | Altitudes resumidas del inventario, m |
| slope_deg | Pendiente media Copernicus nacional en el resultado final, grados; fallback ING si falta DEM en otra ejecución |
| terrain_source | Fuente efectiva usada en cada entidad |
| inventory_slope_deg / inventory_elevation_* | Valores originales resumidos antes de reemplazar por Copernicus |
| dem_n_pixels / dem_low_resolution_flag | Conteo Copernicus y bandera de menos de 20 píxeles |
| earth_copernicus_national | Estadísticas nacionales independientes y diferencias contra ING |
| copernicus_national_sources | URL, SHA256, tamaño y estado de cada una de las 55 teselas |
| copernicus_tile_statistics | Sumas/conteos por intersección tesela-entidad, para auditar agregación |
| aspect_source | Clases cardinales originales, concatenadas; no promedio aritmético de ángulos |
| lon, lat | Punto interior de etiqueta WGS84, grados; no estación ni centro de masa |
| image_dates | Fechas de imágenes base del inventario; no fecha de descarga |
| H_est_m | 50 A^0,2, A en km², H en m; estimación empírica del cuerpo de permafrost |
| pi_plastic | Vacío por falta de esfuerzo de cedencia; ver pi_plastic_status |
| accessibility_factor | Vacío: sin información de accesibilidad vial |
| earth_uncertainty / feature | H_m, debris_m, tau_driving_pa, ice_volume_m3, H_over_L, debris_over_H, skin_over_H, sin_slope o ice_fraction |
| p05, median, p95 | Percentiles de 512 realizaciones, condicionados a priors, no IC observacionales |
| scores / target_id | deuteronilus_lda o arcadia_ice_sheet; define variables comparadas |
| score_median/p05/p95 | Similitud exploratoria 0–100; no probabilidad de ser análogo |
| score_with_slope_depth_* | Score × proxy operativo de pendiente y detrito; accesibilidad no incluida |
| score_full_operational | Vacío por falta de accesibilidad y profundidad observada |
| rank_by_median | Ranking descendente por mediana, 1 mejor, dentro de blanco |
| rank_p05/median/p95 | Cuantiles de posición entre realizaciones; pueden ser fraccionarios |
| p_top10 | Frecuencia Monte Carlo de estar entre los diez primeros; no probabilidad calibrada |
| weight_sensitivity / top10_frequency_weights | Fracción de 60 ensayos de pesos en que queda en top 10 |
| mean_top10_overlap | Promedio de fracción compartida con top 10 original, mismo valor por blanco |
| earth_copernicus_pilot / n_pixels | Centros de píxel válidos dentro del polígono; solo entidades totalmente contenidas en AOI |
| slope_mean_deg | Pendiente media del DSM Copernicus, grados, derivada con espaciado métrico local |
| aspect_circular_deg | Orientación de máxima bajada: 0=N,90=E,180=S,270=O |
| aspect_resultant | Concentración circular [0,1]; cerca de 0 indica orientación poco definida |
| low_resolution_flag | Menos de 20 píxeles; umbral de control asumido |
| mars_parameters / low,high | Rango de parámetro y unidad explícita; null si no se usa |
| evidence_status, source_ids | Separa literatura, envolvente regional y supuesto; enlaza sources.csv |
| mars_mola_context | Estadística de una caja de 2°×2°, no de un glaciar delineado |
| mars_swim_point_context / consistency | Índice Ci [-1,1]; nodata −200 se enmascara; no probabilidad |
| pca_earth / pc1,pc2 | Coordenadas estandarizadas del PCA descriptivo |
| pca_metadata.json | Medias, escalas, componentes y varianza explicada para reproducir la proyección |
| validation_morenas_coloradas | Estado explícito sin correspondencia confirmada, no un ranking inventado |
| morenas_crosswalk_candidates | Vecinos a puntos publicados, solo candidatos a revisión; distance_m usa UTM 19S |

`top30_*.csv` son vistas para consumo rápido. Los nombres `log10_*` solo aparecen en los metadatos del modelo: los valores en `earth_uncertainty.csv` y `mars_dimensionless.csv` se entregan en escala física/adimensional original.
