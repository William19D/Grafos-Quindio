# Grafos-Quindío — Rutas del Paisaje Cultural Cafetero

Proyecto final de Teoría de Grafos: un sistema de planificación de rutas sobre la red vial real del
Quindío (OpenStreetMap, descargada con OSMnx el 2026-11-03) y el análisis teórico y experimental de
sus algoritmos:

- **R1** Modelo de la red: listas de adyacencia, pesos (distancia y tiempo), componente fuertemente
  conexa y asociación de 46 lugares del catálogo a su nodo más cercano.
- **R2** Caminos mínimos: Dijkstra con búsqueda lineal y con cola de prioridad (montículo propio),
  y la matriz de tiempos 46 × 46.
- **R3** Envolvente convexa de la red con QuickHull (divide y vencerás), comparada con SciPy.
- **R4** Ruta óptima (viajante asimétrico): fuerza bruta, Held-Karp y vecino más cercano, e
  itinerario de un día de 11 h.
- **R5** Aplicación web: backend FastAPI + frontend React, Tailwind CSS y Vite.

Todo está en Python. Los algoritmos propios están escritos en "método largo" (bucles explícitos y
pasos numerados) para poder explicarlos paso a paso; NetworkX, SciPy y Shapely solo se usan para
verificar.

## Estructura de carpetas

```
api/                 backend FastAPI (api/main.py)
web/                 frontend React + Tailwind CSS + Vite (diseño en web/DESIGN.md)
src/quindio/         paquete con los algoritmos y utilidades
  config.py          rutas y constantes (semilla 2026, límite de 5 min, UTM 18N)
  red.py             R1: pesos, memoria, nodo más cercano, cargar_grafo()
  estructuras.py     R2: montículo mínimo propio
  dijkstra.py        R2: Dijkstra lineal y con cola de prioridad
  envolvente.py      R3: QuickHull
  tsp.py             R4: permutaciones de Heap, fuerza bruta, Held-Karp, voraz, itinerario
  medicion.py        protocolo: 5 repeticiones, mediana, límite de 5 min, datos de la máquina
  descarga.py        descarga con servidores Overpass alternos
experimentos/        un script por experimento + reproducir.py
specs/               especificaciones (Spec-Driven Development) de cada requerimiento
tests/               pruebas con pytest
data/catalogo.csv    catálogo de 46 lugares
data/processed/      red procesada (grafo_scc.graphml, nodos.csv, aristas.csv, lugares_nodos.csv)
data/raw/            red cruda descargada (no se sube al repositorio)
resultados/          CSV y JSON de los experimentos, matriz_tiempos.csv, envolvente.json
resultados/figuras/  gráficas PNG generadas a partir de los CSV
docs/                documento técnico, notas por requerimiento y explicaciones paso a paso
AlgoritmosDikstra-FloydWarshall.ipynb   cuaderno base del proyecto
```

## Requisitos e instalación

- Python 3.11
- Node.js 18 o superior (solo para el frontend)

Con `venv` y `pip` (desde la raíz del repositorio):

```bash
python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Linux / macOS:         source .venv/bin/activate
pip install -r requirements.txt
```

O con `uv`:

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv -r requirements.txt
```

Los comandos de abajo suponen el entorno activado (`python` = el de `.venv`).

## Datos: descargar o reutilizar la red

No hace falta descargar nada para correr R2, R3, R4, las pruebas ni la aplicación: la red procesada
ya está en `data/processed/` y los resultados en `resultados/`.

Para regenerar todo desde cero se necesita la red cruda en `data/raw/quindio_drive.graphml`.
`python experimentos/reproducir.py` la descarga si falta, con
`ox.graph_from_place("Quindío, Colombia", network_type="drive")`. Una descarga nueva puede traer una
red un poco distinta (OpenStreetMap cambia), y con ella números distintos a los del documento.

## Reproducir los experimentos

Todo en orden (descarga la red si falta; tarda más de 20 minutos por la fuerza bruta de R4 y las
descargas de R1):

```bash
python experimentos/reproducir.py
python experimentos/reproducir.py --rapido   # omite catálogo, r1_red, r1_scc y r4_exactos
python experimentos/reproducir.py --listar   # muestra los pasos sin ejecutarlos
```

Cada script también se puede correr solo, con `src` en el `PYTHONPATH`:

```bash
# Linux / macOS / Git Bash
PYTHONPATH=src python experimentos/r2_dijkstra.py
# Windows PowerShell
$env:PYTHONPATH = "src"; python experimentos/r2_dijkstra.py
```

| Script | Qué genera |
|---|---|
| `experimentos/catalogo.py` | verificación de coordenadas y `figuras/catalogo.png` (usa internet) |
| `experimentos/r1_red.py` | pesos, componente y `data/processed/*`, `r1_tamano.csv`, `r1_velocidades.csv`, `r1_memoria.json` |
| `experimentos/r1_scc.py` | `r1_scc_tiempos.csv` (descarga las redes de 2, 5, 10 y 20 km) |
| `experimentos/r1_lugares.py` | `data/processed/lugares_nodos.csv`, `r1_lugares_lejanos.csv` |
| `experimentos/r2_dijkstra.py` | `r2_dijkstra.csv`, `r2_verificacion.csv`, `r2_cociente*.csv` |
| `experimentos/r2_matriz.py` | `matriz_tiempos.csv`, `r2_matriz_resumen.json` |
| `experimentos/r3_envolvente.py` | `r3_envolvente.csv`, `r3_niveles.csv`, `envolvente.json` |
| `experimentos/r4_exactos.py` | `r4_exactos.csv`, `r4_memoria.csv`, `r4_held_karp_extendido.csv` (~10 min o más) |
| `experimentos/r4_calidad.py` | `r4_calidad.csv`, `r4_calidad_detalle.csv`, `r4_voraz_vs_optimo.json` |
| `experimentos/r4_itinerario.py` | `r4_itinerario.csv`, `r4_itinerario.json` |
| `experimentos/r*_figuras.py` | las gráficas de `resultados/figuras/`, leyendo los CSV |

Protocolo: solo se mide el algoritmo, 5 repeticiones y mediana, tiempos en milisegundos, semilla
2026, límite de 5 minutos («no completada»). Los datos de la máquina quedan en
`resultados/maquina.json`.

## Pruebas

```bash
python -m pytest -q tests
```

## Aplicación (R5)

Desarrollo, en dos terminales:

```bash
# 1) backend, desde la raíz del repositorio
uvicorn api.main:app --reload --port 8000
# 2) frontend
cd web
npm install
npm run dev        # abrir la URL que muestra Vite
```

Un solo proceso (el backend sirve el frontend compilado):

```bash
cd web
npm install
npm run build
cd ..
uvicorn api.main:app --port 8000   # abrir http://localhost:8000
```

La aplicación permite ver la ruta entre dos lugares con su tiempo (Dijkstra con cola de prioridad,
calculado en el momento), la envolvente convexa sobre el mapa, el itinerario de un día con
Held-Karp y con la heurística voraz (tiempos y diferencia) y las tablas y gráficas de R1 a R4.

## Explicación paso a paso

Cada requerimiento tiene un ejemplo pequeño resuelto a mano y una demostración en consola que
imprime la traza del algoritmo (desde la raíz, con `PYTHONPATH=src`; en Windows conviene además
`PYTHONIOENCODING=utf-8`):

| Requerimiento | Explicación | Demostración |
|---|---|---|
| R1 nodo más cercano y pesos | [docs/paso_a_paso_R1.md](docs/paso_a_paso_R1.md) | `python -m quindio.red` |
| R2 Dijkstra y montículo | [docs/paso_a_paso_R2.md](docs/paso_a_paso_R2.md) | `python -m quindio.dijkstra`, `python -m quindio.estructuras` |
| R3 QuickHull | [docs/paso_a_paso_R3.md](docs/paso_a_paso_R3.md) | `python -m quindio.envolvente` |
| R4 Heap, fuerza bruta, Held-Karp y voraz | [docs/paso_a_paso_R4.md](docs/paso_a_paso_R4.md) | `python -m quindio.tsp` |

## Documentación

- Documento técnico: [docs/documento_tecnico.md](docs/documento_tecnico.md)
- Especificaciones: [specs/](specs/)
- Notas detalladas por requerimiento: `docs/notas_*.md`
- Resultados: [resultados/](resultados/) y [resultados/figuras/](resultados/figuras/)

## Agradecimientos

Agradecimientos a [Santiago Fiorino](https://youtu.be/oMgfGkFSgI0) por la ayuda en la creación.
