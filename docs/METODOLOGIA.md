# Datos Tierra–Marte: alcance y decisiones

El paquete entrega datos reales, una transformación reproducible y resultados exploratorios. No es una recomendación de sitio para una base ni una demostración de similitud reológica completa. Fecha de consulta: 14 de noviembre de 2026. Las referencias y condiciones de uso están en `sources.csv`.

## Tierra

La descarga oficial nacional `00-Shapefile-Argentina.zip` contiene 18.046 registros. Se seleccionan **5.593 GEA y 2.469 GEI**: 8.062 partes. No son 16.000 glaciares de roca. Los tipos GD, GC, GCGE y MN quedan fuera del conjunto solicitado. Los complejos mixtos GCGE merecen una ampliación posterior con otra regla explícita.

Hay transiciones activo/inactivo con el mismo `ID_local`. Se conserva una tabla de partes sin perder su clase y se unen las geometrías por identificador para obtener **7.719 entidades**. De ellas, 5.262 son GEA, 2.139 GEI y 318 contienen ambas clases. Agrupar no implica que todas las partes tengan la misma actividad.

Se calcula área geodésica WGS84 después de reparar geometrías. Los atributos originales permanecen en el GeoPackage de partes. Las medias de pendiente y altitud se agregan con pesos por área inventariada; los extremos usan mínimo/máximo. Estos resúmenes originales se conservan para control. El resultado final los reemplaza por una nueva extracción nacional Copernicus cuando hay datos válidos (en esta entrega, para las 7.719 entidades). La fuente DEM original de esos atributos no se identifica aquí. Las fechas de imágenes originales se conservan: la fecha de descarga no es la fecha de observación y no se afirma que este ZIP sea la versión nacional más reciente.

El largo utiliza el máximo `Largo_tota` por entidad cuando existe: es una longitud informada para el conjunto, no se suman largos repetidos por parte. Para 2.662 entidades falta el largo y se usa el eje mayor del rectángulo orientado en UTM local. Es un **proxy geométrico**, no una línea central de flujo. El ancho se define como área/largo y también es un proxy. Los puntos de etiqueta son puntos interiores, no coordenadas de mediciones de campo.

Se descargó Copernicus GLO-30 sin credenciales desde AWS. Dos recortes cubren Dos Lenguas y el entorno de Morenas Coloradas. Se obtuvieron estadísticas para **62 entidades completamente contenidas** (27 y 35). La pendiente se deriva antes de enmascarar el polígono, con distancias métricas locales y promedio por centro de píxel. La orientación es circular, con su resultante: valores pequeños indican una orientación media poco representativa. Copernicus es un DSM; su resolución nominal de 30 m limita la descripción de cuerpos pequeños. No se rellena una entidad sin píxeles con una elevación inventada. Los recortes y los conteos están incluidos. El ranking final usa una extracción nacional homogénea de Copernicus: **55 teselas, 7.719 entidades con píxeles válidos, cero descargas fallidas y ~1,99 GB transferidos**. Se calcula primero la derivada y después la máscara por polígono. Los polígonos que cruzan teselas acumulan sumas y conteos, sin promediar las medias sin pesos. En los bordes de tesela se usan diferencias de un lado, registradas como píxeles de borde. Se distribuyen estadísticas y manifiesto completo; las teselas completas se eliminan tras el procesamiento. **1.167 entidades tienen menos de 20 píxeles**. La mediana de la diferencia absoluta de pendientes entre ING y Copernicus es 3,27° y su p95 es 13,12°: son diferencias entre productos y épocas, no una validación contra terreno. Las orientaciones finales de mayor resolución están en la tabla nacional; `aspect_source` conserva las clases ING.

En Dos Lenguas la pendiente ING es 16,85° y el promedio Copernicus es 14,11°. La diferencia de 2,74° muestra que el prior angular ±2° del ranking debe ampliarse en una siguiente calibración. Ese prior es de trabajo, **no una incertidumbre validada**.

## Parámetros físicos y adimensionales

Se distingue la fracción volumétrica de hielo `ice_fraction` de un ángulo de fricción. Aquí φ significa **fracción de hielo**. El inventario no mide φ ni un ángulo de fricción interna. Ninguno se deduce automáticamente de la clasificación GEA/GEI.

| Cantidad | Definición y unidades | Evidencia |
|---|---|---|
| A | Área geodésica, km² | Geometría ING |
| H | 50 × (A en km²)^0,2, en m | Relación empírica atribuida a Brenning; espesor medio de permafrost rico en hielo, no profundidad a su techo |
| ρ | 917 φ + 2700(1−φ), kg/m³ | Mezcla bifásica asumida, sin poros de aire/agua |
| τd | ρ g H sin θ, Pa | Esfuerzo motor estimado; aproximación de placa, sin carga adicional del detrito |
| Πd | τd/(ρgH) = sin θ | Adimensional; g se cancela, no implica equivalencia de esfuerzos absolutos |
| H/L | Razón de aspecto | H estimado y L informado/proxy |
| hd/H | Cobertura de detrito / H | hd no se ha medido por entidad |
| δ/H | sqrt(κP/π)/H | Penetración conductiva estacional relativa; no mide el techo del hielo |
| Π plástico | τy/(ρgH sin θ) | **No calculable** sin esfuerzo de cedencia τy; se entrega nulo |

La relación área–espesor no es una ley universal ni equivale a medir hielo. El factor multiplicativo de H es lognormal con mediana 1 y sigma logarítmica 0,4214: aproximadamente 0,5–2 entre p05 y p95. Esa amplitud es un supuesto de análisis, no el error publicado de la relación. H no se aplica a Marte con la misma fórmula: allí se usan rangos independientes.

φ es uniforme 0,4–0,6 para GEA y 0,2–0,6 para GEI/mixtos. El primer rango está motivado por estimaciones habituales de glaciares de roca; el segundo es una envolvente asumida, no una inferencia de actividad. hd es uniforme 1–5 m para GEA y 1–8 m para GEI/mixtos. La difusividad κ es uniforme 0,3–1,5 ×10⁻⁶ m²/s. Todos estos priors se pueden cambiar en `config.json`. No hay estimaciones individuales de detrito o hielo ocultas como observaciones.

Para L se asume ±20% cuando está informado y ±40% cuando es geométrico. Se usa el año terrestre o marciano para P. El modelo térmico es conductivo y sinusoidal: no incorpora sublimación, agua líquida, convección, temperaturas absolutas, presión atmosférica ni calor latente. No prueba similitud térmica integral Tierra–Marte.

## Marte: observaciones y escenarios separados

`mars_parameters.csv` identifica para cada rango su fuente o su condición de supuesto. `mars_dimensionless.csv` contiene las distribuciones derivadas.

**Deuteronilus LDA.** SHARAD y la literatura sostienen depósitos dominados por hielo. Se usa la mediana regional publicada de ~433 m para motivar un escenario H=200–700 m; ese rango no es un intervalo de confianza de un glaciar. Los rangos φ=0,8–1 y hd=1–10 m son envolventes de síntesis regional. L=2–20 km, θ=1–10° y κ son supuestos de trabajo. No se afirma haber medido esas cantidades en el recorte MOLA.

**Arcadia.** La literatura resume un espesor de hielo de 30–80 m: **no es una profundidad de excavación de 30–80 m ni prueba que el techo esté a 0,1 m**. hd=0,1–2 m y φ=0,8–1 son escenarios sin verificación en nuestra coordenada. Arcadia se compara por cobertura relativa, fracción de hielo y escala térmica; no se le inventan largo de flujo o pendiente de glaciar.

Se entregan dos recortes **MOLA MEGDR de 128 píxeles/grado**: 24–26°E, 41,5–43,5°N y 199–201°E, 39–41°N. Las etiquetas PDS originales y las peticiones por rango de bytes documentan el recorte. La escala norte-sur es ~463 m y la coordenada es planetocéntrica marciana, nunca EPSG:4326 terrestre. MOLA informa topografía respecto del areoide: **no observa el lecho enterrado**. Las pendientes calculadas son contexto regional, no pendientes de dos LDAs delineados. El valor mediano regional de Deuteronilus es 1,49° y el de Arcadia 0,25°; no se usan para reemplazar las pendientes de una geoforma particular.

Se descargaron además GeoTIFFs reales **SWIM LPSC 2019** de Arcadia y Onilus. Son una versión histórica explícita, no el producto más reciente. En los puntos de contexto (40°N,200°E) y (42,5°N,25°E), Ci es aproximadamente **0,3804 y 0,1520**. Son índices de consistencia: no porcentajes de probabilidad, pureza, espesor o profundidad. No se etiqueta ninguno como «alto hielo» por mera pertenencia regional. La transformación usa un CRS esférico marciano y reconoce el nodata −200.

## Score e incertidumbre

Hay 512 realizaciones Monte Carlo por entidad y blanco, con semilla fija. Cada realización calcula conjuntamente H/L, hd/H y δ/H a partir del mismo H: se conserva su dependencia. Los errores entre glaciares, la calibración global de la relación de H y las correlaciones entre φ, hd y actividad no están modelados; los rangos resultantes son **condicionales a estos supuestos**, no intervalos de confianza observacionales. Cada realización del blanco se comparte entre todos los candidatos para comparar sus posiciones bajo el mismo Marte.

La distancia es euclídea ponderada sobre log10(sin θ), log10(H/L), log10(hd/H), φ y log10(δ/H), con escalas explícitas en configuración. Arcadia usa solo las últimas tres variables. La similitud es `100 exp(−d²/2)`. No es una probabilidad ni una exactitud de clasificación. Los pesos y escalas son decisiones del MVP; la métrica no está calibrada con etiquetas independientes y tiene variables correlacionadas. Los scores de blancos con distintos subconjuntos no deben compararse como una escala universal.

Se entregan dos salidas distintas: similitud física exploratoria y similitud multiplicada por un proxy de pendiente y profundidad de detrito. **El score operativo completo queda nulo**, porque faltan caminos, tiempos de acceso, restricciones y profundidad real al hielo. Un dato faltante no equivale a accesibilidad perfecta.

Se prueban 60 perturbaciones lognormales de pesos por blanco, conservando realizaciones físicas. Se informa frecuencia en top 10 y solapamiento con el top 10 original. Este control analiza pesos; no sustituye sensibilidad a priors físicos, escalas y familias de modelos. El PCA es descriptivo, estandarizado y ajustado solo con la Tierra. Se proyectan realizaciones del blanco LDA; Arcadia no se proyecta con dimensiones de flujo imputadas. El PCA tampoco valida analogía: varias variables comparten H estimado.

## Validación y límites de la entrega

Dos Lenguas se identificó por nombre, clase y ubicación en San Juan: `G697821O302447S`. Existe un homónimo de hielo descubierto en Tierra del Fuego que se excluye correctamente. En la corrida final con pendientes Copernicus está en puestos **119/7.719 para Deuteronilus y 307/7.719 para Arcadia**, dentro del 1,54% y 3,98% superiores respectivamente, **pero no en el top 10**. No se modificaron los pesos para forzar ese resultado. El método no puede presentarse como «reproduce los elegidos por expertos».

Morenas Coloradas no aparece por nombre en el subconjunto. El punto Balcón I publicado no cae dentro de un polígono seleccionado; los más próximos quedan a cientos de metros. El registro GTN-P de Balcón II y una coordenada de literatura presentan diferencias que requieren revisar las figuras y el datum. `morenas_crosswalk_candidates.csv` permite revisar candidatos, sin afirmar que sean el complejo. Se necesita una correspondencia supervisada del contorno antes de asignar una posición en ranking. No se trata un caso sin correspondencia como falso negativo ni se elige el vecino más cercano para mejorar la validación.

Halla et al. estiman espesores por sectores de Dos Lenguas de aproximadamente 15±5, 20±5 y 22±7 m. El H área–espesor de ~38 m es mayor: sirve como advertencia independiente sobre el error del proxy. No se sustituyó por ese valor medido solo en este caso mientras se dejaba el resto sin mediciones.

La validación disponible son dos casos positivos, no una muestra de clasificación. Antes de afirmar rendimiento: resolver Morenas, añadir sitios contrastantes, separar calibración/evaluación y analizar sensibilidad a priors, resolución y contornos. Para un ranking operativo faltan accesibilidad, permisos de campaña y datos locales del subsuelo. El mapa permite explorar candidatos, no justifica intervenciones.
