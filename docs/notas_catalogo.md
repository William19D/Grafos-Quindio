# Notas — Catálogo de lugares (sección 4 del enunciado)

Archivos: `data/catalogo.csv` (datos), `specs/catalogo.md` (especificación),
`experimentos/catalogo.py` (verificación geográfica y figura), `tests/test_catalogo.py` (pruebas),
`resultados/catalogo_verificacion.csv` (resultado de la verificación),
`resultados/figuras/catalogo.png` (mapa de comprobación).

## 1. El problema

El enunciado pide un catálogo de al menos 40 lugares reales del Quindío, en cuatro categorías,
con identificador, nombre, municipio, categoría, latitud y longitud. A cada atractivo turístico
se le añade la duración estimada de la visita (en minutos), que usa el requerimiento 4
(itinerario de un día de 11 h). Las cabeceras municipales se ubican en su plaza principal y la
plaza de Bolívar de Armenia (`ARM`) es el punto de salida y llegada por defecto.

El catálogo es la entrada de R1.4 (asociar cada lugar a su nodo más cercano), de la matriz de
tiempos de R2 (46 × 46) y de todos los experimentos de R4.

## 2. Contenido y formato

Columnas (el anexo permite ampliar columnas; se añadieron dos de fuentes):

`id,nombre,municipio,categoria,lat,lon,duracion_visita_min,fuente_duracion,fuente_coordenadas`

- `id`: tres letras en mayúsculas, único (Armenia = `ARM`, Salento = `SAL`, Parque del Café = `PDC`...).
- `categoria` ∈ {`cabecera`, `atractivo`, `finca`, `acopio`}.
- `lat`, `lon` en grados WGS 84.
- `duracion_visita_min` y `fuente_duracion`: solo en atractivos (vacías en el resto).
- `fuente_coordenadas`: cómo se obtuvo cada coordenada (consulta exacta a Nominatim/OSM o notebook base).

### Tabla resumen por categoría

| Categoría | Mínimo pedido | Lugares en el catálogo | Municipios cubiertos | Distancia a su cabecera, mediana (km) | Distancia máxima (km) |
|---|---|---|---|---|---|
| Cabeceras municipales | 12 | 12 | 12 | 0,00 | 0,00 |
| Atractivos turísticos | 15 | 17 | 7 | 3,36 | 15,01 (RECUCA) |
| Fincas cafeteras u hoteles rurales | 8 | 10 | 8 | 3,95 | 15,73 (Hacienda Bambusa) |
| Centros de acopio o trilladoras | 5 | 7 | 5 | 0,59 | 2,79 |
| **Total** | **40** | **46** | 12 | | |

(Distancias en línea recta, fórmula del semiverseno, tomadas de `resultados/catalogo_verificacion.csv`.)

### Lugares

- **Cabeceras (12)**: plaza principal de Armenia, Buenavista, Calarcá, Circasia, Córdoba, Filandia,
  Génova, La Tebaida, Montenegro, Pijao, Quimbaya y Salento.
- **Atractivos (17)**: Parque Nacional del Café (PDC), PANACA (PAN), Valle de Cocora (COC),
  Jardín Botánico del Quindío y Mariposario (JBQ), Museo del Oro Quimbaya (MOQ), RECUCA (REC),
  Mirador Colina Iluminada de Filandia (CIL), Parque de la Vida (PVI), Parque Los Arrieros (ARR),
  Mirador Alto de la Cruz (ACR), Calle Real de Salento (CRS), Cementerio Libre de Circasia (CLC),
  La Granja de Mamá Lulú (MML), Reserva Natural Barbas Bremen (BBR), Peñas Blancas (PBL),
  Parque de los Fundadores (FUN), Casa Museo Musical del Quindío (MMQ).
- **Fincas cafeteras / hoteles rurales (10)**: Finca El Ocaso (OCA), Finca de Don Elías (DEL),
  Café San Alberto (SAB), Hacienda Bambusa (BAM), Hotel Decameron Panaca (DPA), Finca Villa Nora (VNO),
  Combia Finca Hotel (CMB), Finca Cafetera La Granada (GRA), Eco Finca La María (LMA),
  Finca Hotel La Esperanza (FES).
- **Acopio / trilladoras (7)**: Almacafé Armenia (ALM), Trilladora Europa (TEU),
  Trilladora Goncheverry (TGO) y cuatro sedes de la Cooperativa de Caficultores del Quindío
  (Quimbaya CQB, Calarcá CCA, Génova CGE, Montenegro CMO).

## 3. Fuentes de las coordenadas

1. **Nominatim (geocodificador de OpenStreetMap)**, `https://nominatim.openstreetmap.org/search`,
   consultado el 2026-11-03 con un identificador de aplicación genérico, sin datos personales,
   con una pausa de 1,1 s entre peticiones (política de uso de Nominatim: máximo 1 petición por
   segundo) y restringido al rectángulo del Quindío (`viewbox=-75.95,4.75,-75.35,4.05`, `bounded=1`).
   Cada fila guarda en `fuente_coordenadas` la consulta exacta y el tipo de objeto OSM devuelto
   (por ejemplo `place=square`, `tourism=theme_park`, `tourism=hotel`). Datos © colaboradores de
   OpenStreetMap, licencia ODbL.
2. **Notebook base** (`AlgoritmosDikstra-FloydWarshall.ipynb`) para las plazas de Armenia, Pijao,
   Filandia, Buenavista y Quimbaya. Se verificaron contra Nominatim y coinciden a menos de 25 m:
   Pijao vs. "Parque Principal" (22,8 m), Filandia vs. "Parque Bolívar" (13,4 m),
   Buenavista vs. "Plaza de Bolívar" (14,0 m), Quimbaya vs. "Plaza de Bolívar" (6,3 m),
   Armenia (`config.PLAZA_BOLIVAR_ARMENIA`) vs. "Plaza de Bolívar" (17,9 m).

Decisiones de ubicación:

- **Cabeceras**: se tomó el objeto OSM de la plaza principal (`place=square` o `leisure=park`
  llamado "Plaza de Bolívar"). En Córdoba la plaza principal es el "Parque José María Córdoba"
  y en Circasia la "Plaza Simón Bolívar", frente a la parroquia Nuestra Señora de las Mercedes.
- **Valle de Cocora**: se usó la vereda Cocora (`place=village`), que es la entrada al valle donde
  terminan la vía y el transporte desde Salento. El polígono del valle (pastizal con palmas) está
  ~1 km al este y no tiene vía vehicular.
- **Parque Los Arrieros**: la dirección de OSM dice "Montenegro", pero el punto cae dentro del
  polígono municipal de Quimbaya; se registró Quimbaya (el parque se anuncia como ubicado en Quimbaya).
- **Hacienda Bambusa**: está en la vía a El Caimo; el punto cae en el polígono de Armenia
  (corregimiento El Caimo), por eso se registró Armenia.
- **Acopio**: Almacafé y las trilladoras Europa y Goncheverry están en la zona industrial de
  Armenia; las sedes de la Cooperativa de Caficultores del Quindío son puntos de compra de café
  pergamino en cada municipio.

## 4. Verificación de las coordenadas

`experimentos/catalogo.py` (se ejecuta con
`PYTHONPATH=src .venv/Scripts/python.exe experimentos/catalogo.py`) comprueba cada lugar:

1. **Dentro del departamento**: el punto está dentro del polígono de `ox.geocode_to_gdf("Quindío, Colombia")`
   (Shapely `contains`, solo como verificación). Resultado: **46 de 46 dentro**.
2. **Municipio correcto**: el punto está dentro del polígono OSM de su municipio
   (`ox.geocode_to_gdf("<municipio>, Quindío, Colombia")`). En la primera versión dos lugares no
   coincidieron (Parque Los Arrieros y Hacienda Bambusa) y se corrigió su municipio como se explica
   arriba. Resultado final: **46 de 46 en su municipio**.
3. **Distancia a la cabecera** de su municipio (semiverseno, R = 6371 km): máximo 15,73 km
   (Hacienda Bambusa, sur de Armenia); RECUCA está a 15,01 km de la plaza de Calarcá porque queda en
   la vereda Barcelona, al sur del municipio.
4. **Verificación visual**: `resultados/figuras/catalogo.png` dibuja el polígono del departamento y
   los 46 puntos coloreados por categoría, con su `id`. Todos caen dentro y cerca de su municipio.

Las pruebas `tests/test_catalogo.py` (8 pruebas, `.venv/Scripts/python.exe -m pytest -q tests/test_catalogo.py`
→ `8 passed`) revisan sin conexión: columnas exactas, mínimos por categoría y total ≥ 40, `id` únicos
y en mayúsculas, `ARM` con las coordenadas de `config.PLAZA_BOLIVAR_ARMENIA`, una cabecera por
municipio, todos dentro del rectángulo lat ∈ [4,05; 4,75], lon ∈ [−75,95; −75,35], duración entera
positiva con fuente en todos los atractivos (vacía en el resto), `fuente_coordenadas` en todos y
cada lugar a menos de 20 km de su cabecera. La función de distancia se valida con un caso a mano:
1° de latitud = 2π·6371/360 ≈ 111,19 km.

**Aviso para R1.4** (distancia al nodo más cercano de la componente, calculada con
`quindio.red.asociar_lugares` sobre `data/processed/nodos.csv`): mediana 75 m; siete lugares
quedan a más de 500 m porque están en zonas rurales servidas por caminos que no forman parte de
la red `drive` o de la componente fuertemente conexa: BBR (1178 m), COC (934 m), FES (801 m),
PBL (759 m), GRA (742 m), CMB (710 m) y REC (597 m). Los cuatro atractivos de esa lista son áreas
naturales o fincas a las que se llega a pie desde el final de la vía, así que el nodo más cercano
representa razonablemente el punto donde se deja el vehículo. El reporte oficial de esos casos lo
hace R1.4 (`resultados/r1_lugares_lejanos.csv`).

## 5. Criterio de las duraciones de visita

Para los cinco atractivos grandes se usó una fuente publicada. Para el resto se definió un
criterio por tipo de lugar, pensado para un visitante que recorre sin guía y sin comer en el sitio:

| Atractivo | Duración (min) | Justificación |
|---|---|---|
| Parque Nacional del Café (PDC) | 360 | Horario 9:00–18:00 (Semana, 2024, https://www.semana.com/turismo/articulo/parque-del-cafe-donde-queda-horarios-y-precios-de-entradas/202446/); se toman 6 h de las 9 h de apertura. |
| PANACA (PAN) | 360 | Tour de 6 h y entrada "pasaporte" de 7 h (Expedia, https://www.expedia.com/things-to-do/tour-panaca.a4974155.activity-details). |
| Valle de Cocora (COC) | 210 | Sendero corto de las palmas: 3 a 4 h (https://www.mochileandoporelmundo.com/trekking-por-el-valle-del-cocora-colombia/). |
| Jardín Botánico del Quindío (JBQ) | 150 | Recorrido guiado de 2,5 h según el jardín (Semana, https://www.semana.com/turismo/articulo/que-costo-tiene-la-entrada-y-que-se-puede-hacer-en-el-jardin-botanico-del-quindio/202549/). |
| RECUCA (REC) | 210 | Recorrido de 3 a 4 h (Pulzo, https://www.pulzo.com/vivir-bien/viajes-y-turismo/cuanto-vale-entrada-recuca-quindio-para-recorrido-cafe-unico-mundo-PP4364821). |

Criterios del grupo (cuando no hay una duración publicada confiable):

| Criterio | Tipo de lugar | Duración (min) | Atractivos |
|---|---|---|---|
| C1 | Mirador o punto de observación: llegar, recorrer el mirador y tomar fotos | 45 | CIL, ACR |
| C2 | Museo o sitio patrimonial pequeño: recorrido completo a pie | 90 | MOQ, CLC, MMQ |
| C3 | Parque urbano o calle patrimonial: paseo completo | 90 | PVI, CRS, FUN |
| C4 | Granja demostrativa pequeña: un ciclo de shows/actividades | 120 | MML |
| C5 | Parque temático de medio día (más pequeño que PDC o PAN) | 240 | ARR |
| C6 | Reserva o sendero natural corto: caminata guiada de ida y vuelta | 180 | BBR, PBL |

Resumen: 17 atractivos, duración mediana 120 min, mínima 45, máxima 360, suma 2640 min (44 h).
Como una jornada es de 11 h (660 min), un itinerario de 6 a 8 atractivos con PDC, PAN, COC o REC
casi nunca cabe; R4.4 debe quitar atractivos y esa justificación ya queda explicada por estas
duraciones.

## 6. Limitaciones

- Las coordenadas vienen de OSM, que es colaborativo: se validaron con los polígonos oficiales de
  OSM y con el mapa, pero un objeto mal ubicado en OSM se heredaría. Los puntos dudosos (municipio
  distinto) se revisaron uno por uno.
- Las duraciones son estimaciones para planificar, no tiempos medidos.
- Los centros de acopio son sedes urbanas; la compra en veredas (puntos móviles) no está en OSM.
