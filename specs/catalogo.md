# Especificación — Catálogo de lugares (sección 4 del enunciado)

Archivo: `data/catalogo.csv` (UTF-8, separado por comas, una fila por lugar).
Verificación y figura: `experimentos/catalogo.py`. Pruebas: `tests/test_catalogo.py`.
Notas: `docs/notas_catalogo.md`.

## Columnas (en este orden)

| Columna | Tipo | Regla |
|---|---|---|
| `id` | texto | corto, único, en mayúsculas (`[A-Z0-9_]+`). Armenia = `ARM`. |
| `nombre` | texto | nombre real del lugar. |
| `municipio` | texto | uno de los 12 municipios del Quindío. |
| `categoria` | texto | `cabecera`, `atractivo`, `finca` o `acopio`. |
| `lat`, `lon` | real | grados WGS 84 (EPSG:4326). |
| `duracion_visita_min` | entero | obligatoria (> 0) en `atractivo`; vacía en las demás categorías. |
| `fuente_duracion` | texto | obligatoria en `atractivo`: enlace o criterio (ver notas). |
| `fuente_coordenadas` | texto | cómo se obtuvo la coordenada (`Nominatim/OSM: <consulta>`, notebook base, etc.). |

## Contenido mínimo

| Categoría | Mínimo |
|---|---|
| cabecera | 12 (exactamente una por municipio, en la plaza principal) |
| atractivo | 15 |
| finca (fincas cafeteras u hoteles rurales) | 8 |
| acopio (centros de acopio o trilladoras de café) | 5 |
| total | 40 |

- La cabecera de Armenia tiene `id = ARM` y las coordenadas de la plaza de Bolívar
  `config.PLAZA_BOLIVAR_ARMENIA = (4.532571193032303, -75.6728794763243)`.

## Reglas de validez geográfica

1. Todo lugar cae dentro del rectángulo que contiene al Quindío:
   lat ∈ [4.05, 4.75], lon ∈ [-75.95, -75.35] (prueba rápida, sin red).
2. Todo lugar cae dentro del polígono del departamento (`ox.geocode_to_gdf("Quindío, Colombia")`),
   comprobado con Shapely en `experimentos/catalogo.py`.
3. El punto cae dentro del polígono OSM del municipio registrado
   (`ox.geocode_to_gdf("<municipio>, Quindío, Colombia")`), comprobado en `experimentos/catalogo.py`.
4. Control rápido sin red: cada lugar está a menos de 20 km en línea recta de la cabecera de su
   municipio (los municipios del Quindío miden menos de ~35 km de lado; Calarcá y Armenia llegan
   a ~16 km de su plaza por el sur).

## Casos de prueba (`tests/test_catalogo.py`)

- Columnas exactas y en orden.
- Mínimos por categoría y total ≥ 40; categorías solo de las cuatro válidas.
- `id` únicos, en mayúsculas; existe `ARM` con las coordenadas de la plaza de Bolívar.
- Hay una cabecera por cada uno de los 12 municipios.
- Todos dentro del rectángulo del Quindío.
- Todo atractivo tiene duración entera > 0 y fuente; los demás la tienen vacía.
- Todo lugar tiene `fuente_coordenadas`.
- Cada lugar a < 20 km de su cabecera (haversine escrito a mano, caso a mano: 1° de latitud ≈ 111,2 km).

## Salida visual

`resultados/figuras/catalogo.png`: polígono del Quindío y los lugares coloreados por categoría,
generada leyendo `data/catalogo.csv`.
