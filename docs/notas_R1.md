# Notas R1 — Modelo de la red vial

Código: `src/quindio/red.py` (funciones), `experimentos/r1_red.py` (pesos, componente y grafo
procesado), `experimentos/r1_scc.py` (tiempos de la componente), `experimentos/r1_figuras.py`
(gráfica), `experimentos/r1_lugares.py` (ubicación de lugares). Especificación: `specs/R1.md`.
Pruebas: `tests/test_r1.py`.

Datos: red vial de OpenStreetMap descargada con OSMnx 2.1.1 el **2026-11-03**
(`ox.graph_from_place("Quindío, Colombia", network_type="drive")`, servidor
`overpass-api.de`; metadatos en `data/processed/descarga.json`). Máquina de las mediciones en
`resultados/maquina.json` (Intel Core i5-12450H, 31.6 GB RAM, Windows 11, Python 3.11).

Cómo reproducir (desde la raíz del repositorio):

```
PYTHONPATH=src .venv/Scripts/python.exe experimentos/r1_red.py
PYTHONPATH=src .venv/Scripts/python.exe experimentos/r1_scc.py
PYTHONPATH=src .venv/Scripts/python.exe experimentos/r1_figuras.py
PYTHONPATH=src .venv/Scripts/python.exe experimentos/r1_lugares.py   # requiere data/catalogo.csv
.venv/Scripts/python.exe -m pytest -q tests/test_r1.py
```

---

## 1. Representación de la red

**Problema.** Elegir entre matriz de adyacencia y listas de adyacencia para un grafo dirigido
con V nodos y E aristas, cada arista con dos pesos (tiempo y distancia).

Según Cormen et al., *Introduction to Algorithms*, 3.ª ed., MIT Press, 2009, sección 22.1
("Representations of graphs"): la matriz de adyacencia ocupa Θ(V²) memoria
independientemente del número de aristas, y las listas de adyacencia ocupan Θ(V + E). Recorrer
los vecinos de un nodo cuesta Θ(V) con matriz y Θ(grado) con listas; preguntar si existe la
arista (u, v) cuesta O(1) con matriz y O(grado) con listas. Los mismos autores recomiendan las
listas para grafos dispersos (E mucho menor que V²).

**Supuestos del cálculo** (1 MB = 10⁶ bytes; guardado en `resultados/r1_memoria.json`):

- *Matriz, modelo de bajo nivel (C/C++)*: V·V celdas; cada celda guarda tiempo (`float32`, 4 B)
  y distancia (`float32`, 4 B) = 8 B. Las celdas sin arista guardan infinito.
- *Listas, modelo de bajo nivel*: E entradas de 12 B (vecino `int32` 4 B + tiempo 4 B +
  distancia 4 B) más un arreglo de V punteros/índices de 8 B al inicio de cada lista.
- *Matriz en Python*: lista de V listas, cada una con V punteros de 8 B (+56 B de cabecera por
  lista), sin contar los objetos `float` de las celdas que sí tienen arista. Se verificó
  midiendo con `sys.getsizeof` una matriz de 1000 × 1000 y escalando a V × V.
- *Listas en Python (medido)*: el `dict {nodo: [(vecino, tiempo_s, distancia_m), ...]}` que
  devuelve `cargar_grafo()`, medido con `sys.getsizeof` sumando el diccionario, cada lista,
  cada tupla y cada número.

**Resultados** con los V y E reales:

| Red | V | E | Matriz bajo nivel (MB) | Listas bajo nivel (MB) | Matriz Python (MB) | Listas Python medido (MB) |
|---|---|---|---|---|---|---|
| Red descargada | 8 808 | 20 157 | 620.65 | 0.31 | 621.14 | — |
| Componente fuertemente conexa | 8 792 | 20 136 | 618.39 | 0.31 | 618.89 (medido escalado: 623.41) | 4.22 |

(La medición en Python usa las 19 999 aristas que quedan tras quitar las paralelas, sección 5.)

**Elección: listas de adyacencia.** La red es muy dispersa: E/V ≈ 2.3 aristas por nodo,
mientras que la matriz reserva 8 792 celdas por nodo; solo el 0.026 % de las celdas tendría una
arista (20 136 / 8 792²). La matriz ocuparía unas 2 000 veces más memoria que las listas en el
modelo de bajo nivel (618 MB frente a 0.31 MB) y unas 150 veces más que el diccionario real de
Python (618 MB frente a 4.2 MB). Además, Dijkstra (R2) recorre los vecinos de cada nodo que
extrae: con listas el costo total de esos recorridos es Θ(V + E); con matriz sería Θ(V²). La
ventaja de la matriz (consultar una arista en O(1)) no la necesita ningún algoritmo del
proyecto. El costo real en Python es unas 13 veces el del modelo de bajo nivel porque cada
entero, flotante y tupla es un objeto con cabecera (24–64 B) y las listas guardan punteros.

---

## 2. Pesos: distancia y tiempo de viaje

Cada arista guarda:

- `distancia_m`: el atributo `length` de OSMnx (metros, longitud geodésica del tramo calculada
  por OSMnx al construir el grafo).
- `tiempo_s = distancia_m / (velocidad_kmh / 3.6)` (se pasa la velocidad a m/s). Ejemplo de la
  prueba: 1 000 m a 50 km/h → 72 s.

El tiempo así calculado es una **estimación del modelo** (velocidad de flujo libre igual al
límite del tramo), no el tiempo real: no considera semáforos, giros, pendientes, curvas ni
tráfico.

**Velocidad de cada tramo** (`asignar_pesos` en `red.py`, implementación propia):

1. *Se lee `maxspeed` de OSM* con `parsear_maxspeed`:
   - número como texto (`"30"`) o con unidad (`"30 km/h"`, `"kmh"`, `"kph"`) → km/h;
   - `"mph"` → se multiplica por 1.609344;
   - varios valores separados por `|` o `;` (velocidad por carril) → media;
   - **lista** (la simplificación de OSMnx fusiona varios tramos OSM en una arista y deja una
     lista, p. ej. `['60', '30']`) → media de los valores válidos;
   - valores no numéricos (p. ej. `"CO:urban"`, `"signals"`) o ausentes → sin velocidad.
   En la red descargada hubo 1 307 aristas con `maxspeed` (6.5 %), 30 de ellas con listas.
   Se verificó que el parseo coincide con la limpieza interna de OSMnx
   (`osmnx/routing.py: _clean_maxspeed` y `_collapse_multiple_maxspeed_values`) en todas esas
   aristas (prueba `test_parseo_igual_que_osmnx_en_la_red_real`).
2. *Tramo sin velocidad*: se imputa la **media de las velocidades leídas en los tramos del mismo
   tipo de vía** (`highway`; si es lista se toma el primer elemento, igual que OSMnx). Es la misma
   regla por defecto de `ox.add_edge_speeds` (documentada en su código fuente: "imputes free-flow
   travel speeds for all edges via the mean maxspeed value of the edges of each highway type"),
   pero escrita a mano para que la lógica quede explícita. La media se calcula sobre toda la red
   descargada (antes de filtrar la componente) para tener más datos.
3. *Tipo de vía sin ningún tramo con `maxspeed`*: tabla `VELOCIDAD_POR_TIPO` con valores dentro de
   la normativa colombiana: Ley 769 de 2002 (Código Nacional de Tránsito), arts. 106 y 107,
   modificados por la Ley 1239 de 2008 (zonas residenciales y escolares 30 km/h, vías urbanas
   máximo 80 km/h, carreteras máximo 120 km/h) y por la Ley 2251 de 2022 (vías urbanas máximo
   50 km/h, zonas escolares y residenciales 30 km/h). Se usaron valores conservadores:
   `primary_link` 40, `tertiary_link` 30, y 30 km/h (como vía residencial) para tipos no
   listados (`ladder`). OSMnx en cambio usaría la media de toda la red.

El cuaderno base usaba 40 km/h para todas las aristas; aquí cada tipo de vía tiene su velocidad.

**Velocidades usadas** (`resultados/r1_velocidades.csv`; aristas de la red descargada):

| Tipo de vía | Aristas | Con maxspeed | Velocidad para tramos sin dato (km/h) | Fuente |
|---|---|---|---|---|
| residential | 13 455 | 293 | 31.37 | media maxspeed del tipo |
| unclassified | 2 459 | 248 | 30.48 | media maxspeed del tipo |
| tertiary | 1 843 | 318 | 30.52 | media maxspeed del tipo |
| secondary | 1 282 | 157 | 36.31 | media maxspeed del tipo |
| primary | 564 | 166 | 44.16 | media maxspeed del tipo |
| trunk | 420 | 120 | 34.07 | media maxspeed del tipo |
| secondary_link | 48 | 4 | 30.00 | media maxspeed del tipo |
| trunk_link | 39 | 1 | 20.00 | media maxspeed del tipo |
| primary_link | 36 | 0 | 40 | tabla normativa |
| ladder | 6 | 0 | 30 | tabla normativa |
| tertiary_link | 5 | 0 | 30 | tabla normativa |

**Discusión.** El 93.5 % de las aristas de la componente (18 833 de 20 136) tiene velocidad
imputada, así que el modelo depende sobre todo de la imputación. Los tramos etiquetados en OSM
están concentrados en zonas urbanas (p. ej. en `trunk` hay 64 tramos a 30 km/h y solo 9 a
60 km/h), por eso las medias por tipo salen bajas (34 km/h para `trunk`) y los tiempos de los
trayectos largos por carretera probablemente quedan sobreestimados. La velocidad de las aristas
procesadas tiene mediana 31.4 km/h (mín. 20, máx. 60). Es una limitación que se declara: el
tiempo es una estimación relativa, útil para comparar rutas, no una predicción del tiempo real.

---

## 3. Componente fuertemente conexa

### 3.1 Qué hace `ox.truncate.largest_component(G, strongly=True)`

Código fuente de la versión instalada (OSMnx 2.1.1, archivo
`.venv/Lib/site-packages/osmnx/truncate.py`, función `largest_component`, líneas 164–201):

1. `nx.is_strongly_connected(G)`: si el grafo ya es fuertemente conexo lo devuelve tal cual.
   En NetworkX 3.6.1 (`networkx/algorithms/components/strongly_connected.py`,
   función `is_strongly_connected`) esto es
   `len(next(strongly_connected_components(G))) == len(G)`: genera solo la **primera**
   componente con el mismo algoritmo.
2. Si no lo es: `max(nx.strongly_connected_components(G), key=len)` recorre todas las
   componentes y se queda con la de más nodos.
3. `nx.MultiDiGraph(G.subgraph(largest_cc))`: crea una vista del subgrafo inducido y la
   **copia** en un grafo nuevo (nodos, aristas y diccionarios de atributos).

`strongly_connected_components` (mismo archivo de NetworkX, líneas 17–111) dice en su
documentación: "Uses Tarjan's algorithm with Nuutila's modifications. Nonrecursive version of
algorithm", citando a R. E. Tarjan, "Depth-first search and linear graph algorithms", *SIAM
Journal on Computing* 1(2):146–160, 1972, y a E. Nuutila y E. Soisalon-Soininen, "On finding the
strongly connected components in a directed graph", *Information Processing Letters*
49(1):9–14, 1994.

### 3.2 Cómo funciona (Tarjan con la modificación de Nuutila)

- Hace un recorrido en profundidad (DFS) **iterativo** (con una pila `queue` explícita en vez
  de recursión, para no desbordar la pila de Python en grafos grandes). A cada nodo le asigna
  su número de orden de descubrimiento `preorder[v]`.
- Cuando termina de explorar un nodo v calcula `lowlink[v]`: el menor número de orden que se
  alcanza desde el subárbol de v usando a lo sumo una arista hacia un nodo que todavía no tiene
  componente asignada (`lowlink[w]` si w es descendiente, `preorder[w]` si no).
- Si `lowlink[v] == preorder[v]`, v es la **raíz** de una componente: la componente es v más
  los nodos de la pila auxiliar `scc_queue` con número de orden mayor que el de v, que se sacan
  y se marcan en `scc_found`. Si no, v se apila en `scc_queue` y esperará a su raíz.
- La modificación de Nuutila consiste en que solo se apilan en `scc_queue` los nodos que **no**
  son raíz, lo que ahorra operaciones de pila respecto al algoritmo original de Tarjan.
- Correctitud (Tarjan 1972; Cormen et al., 2009, sec. 22.5): en un DFS, los nodos de cada
  componente fuertemente conexa forman un subárbol contiguo cuya raíz es el primer nodo
  descubierto de la componente, y esa raíz es exactamente el nodo con `lowlink = preorder`.

### 3.3 Complejidad

- **Tiempo Θ(V + E)** (Tarjan 1972, donde se demuestra que el algoritmo es lineal en el número
  de nodos y aristas; Cormen et al., 2009, sec. 22.5, obtiene la misma cota para las
  componentes fuertemente conexas calculadas con DFS; Sedgewick y Wayne, *Algorithms*, 4.ª ed.,
  Addison-Wesley, 2011, sec. 4.2, presentan Tarjan con tiempo proporcional a V + E): cada nodo entra y sale una vez de la pila del DFS y
  cada arista se examina un número constante de veces. En la implementación de NetworkX cada
  arista se mira dos veces (una al avanzar con el iterador `neighbors[v]` y otra al calcular
  `lowlink[v]` cuando v termina), lo que cambia la constante, no el orden.
- **Memoria Θ(V)** adicional al grafo: diccionarios `preorder`, `lowlink`, `neighbors` (un
  iterador por nodo), el conjunto `scc_found` y las pilas `queue` y `scc_queue`.
- La función completa de OSMnx suma: `is_strongly_connected` O(V + E) (en el peor caso),
  el cálculo de todas las componentes Θ(V + E), `max` O(número de componentes) y la copia del
  subgrafo Θ(V_c + E_c) en tiempo y memoria (V_c, E_c: tamaño de la componente). En total
  **Θ(V + E)** en tiempo y Θ(V + E) en memoria (por la copia), con una constante grande por la
  copia de los diccionarios de atributos de cada arista.

### 3.4 Medición

`experimentos/r1_scc.py`. Redes: `ox.graph_from_point(PLAZA_BOLIVAR_ARMENIA, dist=r,
network_type="drive")` con r = 2, 5, 10 y 20 km (descargadas el 2026-11-03 y guardadas en
`data/raw/armenia_r{r}km.graphml`; `dist` es la mitad del lado de un cuadrado centrado en la
plaza de Bolívar, por eso la de 20 km incluye vías de Valle del Cauca y Risaralda) y la red
completa del departamento. Se mide **solo la función** (la lectura del GraphML queda fuera),
5 repeticiones y mediana con `medicion.medir`, en milisegundos. También se mide aparte
`max(nx.strongly_connected_components(G), key=len)` (solo Tarjan, sin la copia) para separar
los dos costos. Antes de guardar cada fila se verifica que la componente devuelta sea
fuertemente conexa (`nx.is_strongly_connected`) y que tenga los mismos nodos que la de Tarjan.
Cada red se carga sola en memoria justo antes de medirla (ver discusión).

**Tiempo de obtener la componente** (`resultados/r1_scc_tiempos.csv`, tiempos en ms):

| Red | V | E | V + E | Tiempo (ms) | Solo Tarjan (ms) | Nodos componente | Aristas componente | Tiempo/(V+E) (µs) |
|---|---|---|---|---|---|---|---|---|
| Radio de 2 km | 1 648 | 3 657 | 5 305 | 91.61 | 7.47 | 1 579 | 3 538 | 17.3 |
| Radio de 5 km | 4 297 | 9 708 | 14 005 | 296.68 | 22.67 | 4 261 | 9 654 | 21.2 |
| Radio de 10 km | 5 943 | 13 405 | 19 348 | 377.65 | 27.92 | 5 911 | 13 355 | 19.5 |
| Radio de 20 km | 8 773 | 20 047 | 28 820 | 617.39 | 49.51 | 8 751 | 20 016 | 21.4 |
| Departamento completo | 8 808 | 20 157 | 28 965 | 643.63 | 49.33 | 8 792 | 20 136 | 22.2 |

Gráfica: `resultados/figuras/r1_scc.png` (tiempo en ms frente a V + E, generada desde el CSV
por `experimentos/r1_figuras.py`, con una recta de referencia t = c·(V + E) ajustada por mínimos
cuadrados, c ≈ 21.3 µs).

**Discusión.** Lo medido es compatible con la complejidad lineal Θ(V + E): al pasar de la red
de 2 km a la del departamento V + E crece 5.5 veces y el tiempo 7.0 veces (Tarjan solo: 6.6
veces); el tiempo por unidad de V + E se mantiene en un rango estrecho (17–22 µs para la
función completa, 1.4–1.7 µs para Tarjan) en vez de crecer proporcionalmente a V + E, como
pasaría con un algoritmo cuadrático. El ligero aumento del costo unitario con el tamaño se
explica por efectos de la memoria (los diccionarios del grafo, de decenas de MB, dejan de caber
en la caché del procesador) y por el recolector de basura de Python, que se activa más veces
mientras se crean los objetos de la copia. Las redes de 20 km y del departamento tienen casi el
mismo tamaño y tiempos muy parecidos, lo que confirma que el tiempo depende de V + E y no de la
zona. **El 92 % del tiempo de la función es la copia del subgrafo**
(`nx.MultiDiGraph(G.subgraph(...))`), no el algoritmo de Tarjan: copiar cada arista implica
crear un diccionario con sus atributos (en promedio 6.5 atributos por arista, algunos con la
geometría del tramo), mientras que Tarjan solo toca números y conjuntos. Ambas partes son
lineales, así que la suma también lo es, pero con una constante unas 13 veces mayor que la del
algoritmo solo.

*Nota sobre la variabilidad.* La máquina se usó en paralelo con otros procesos (≈24 % de uso de
CPU de fondo; el i5-12450H mezcla núcleos de rendimiento y de eficiencia), y entre ejecuciones
completas del experimento la mediana de una misma red varió hasta ±40 % (p. ej. la red de 20 km
dio 566 ms, 1 044 ms y 504 ms en tres ejecuciones con la versión anterior del script). En esa
versión las cinco redes estaban cargadas a la vez y la última medida (el departamento) salía
sistemáticamente más lenta que la de 20 km pese a tener el mismo tamaño, porque el recolector de
basura recorre todos los objetos vivos; por eso el script final carga una red a la vez. La tabla
corresponde a la última ejecución del script final; la ejecución anterior con el mismo script
dio 82, 284, 358, 634 y 543 ms, con la misma tendencia lineal.

### 3.5 Por qué trabajar solo con la componente

- En la componente fuertemente conexa existe un camino dirigido entre **todo par** de nodos.
  Como cada lugar del catálogo se asocia a un nodo de la componente (sección 4), toda consulta
  origen-destino del R2 tiene solución y la **matriz de tiempos queda finita** (sin infinitos).
- En la red cruda hay nodos sin salida (calles que terminan en el límite del departamento o
  sentidos únicos mal cortados) o sin entrada; un lugar asociado a uno de ellos dejaría rutas
  imposibles y Dijkstra exploraría toda la red para terminar sin encontrar el destino.
- En el R4 (viajante asimétrico) se necesita poder ir de cualquier lugar a cualquier otro y
  volver: con la matriz finita **todo recorrido tiene solución** y la fuerza bruta, Held-Karp
  y la heurística voraz no tienen que tratar casos sin solución.
- El costo es mínimo: se pierden 16 nodos (0.18 %) y 21 aristas (0.10 %).

---

## 4. Ubicación de los lugares

`asociar_lugares(catalogo_df, nodos)` en `red.py` (implementación propia):

1. Convierte (lat, lon) de cada lugar a metros en **UTM zona 18N (EPSG:32618)** con pyproj
   (`Transformer.from_crs("EPSG:4326", "EPSG:32618", always_xy=True)`). Las coordenadas UTM de
   los nodos de la componente ya están en `data/processed/nodos.csv` (`x_utm`, `y_utm`).
2. Para cada lugar recorre **todos** los nodos (búsqueda lineal) y se queda con el de menor
   distancia euclidiana `sqrt((x - x_i)² + (y - y_i)²)`; durante el recorrido se compara el
   cuadrado de la distancia para no calcular raíces.
3. Agrega `nodo`, `dist_nodo_m` y `lejano_500m` (= `dist_nodo_m > 500`).

- **Complejidad**: tiempo Θ(L · V) para L lugares (cada lugar compara contra los V nodos);
  memoria Θ(V + L) (las listas de coordenadas y el resultado). Con L ≈ 40 y V = 8 792 son unas
  350 000 comparaciones (menos de un segundo en Python). Una estructura espacial (árbol k-d,
  Bentley, "Multidimensional binary search trees used for associative searching",
  *Communications of the ACM* 18(9), 1975) bajaría cada consulta a O(log V) en promedio, pero
  no se justifica para 40 consultas; es lo que usa `ox.distance.nearest_nodes` en grafos
  proyectados (`scipy.spatial.cKDTree`).
- **Correctitud**: la búsqueda lineal revisa todos los candidatos, así que el mínimo encontrado
  es el mínimo global (invariante: después de revisar i nodos, `mejor` es el más cercano entre
  esos i).
- **Verificación**: (a) prueba con una cuadrícula sintética de 5 × 5 nodos separados 100 m y
  lugares puestos a mano (nodo y distancia esperados: 50 m, 0 m, 600 m); (b) 40 lugares al azar
  (semilla 2026) frente a `ox.distance.nearest_nodes` sobre un grafo en UTM: mismo nodo y misma
  distancia; (c) `experimentos/r1_lugares.py` vuelve a comparar con `nearest_nodes` sobre los
  nodos reales de la componente antes de guardar.
- **Lugares a más de 500 m**: se **conservan** asociados a su nodo más cercano y se listan en
  `resultados/r1_lugares_lejanos.csv`. Significa que el último tramo (camino privado,
  sendero o vía no clasificada como `drive` en OSM) no está modelado: el tiempo de las rutas
  hacia ese lugar es el tiempo hasta el nodo de la red. Antes de aceptarlos se revisan sus
  coordenadas en un mapa (un lugar a varios km suele indicar una coordenada mal copiada).

**Estado:** al cerrar este requerimiento `data/catalogo.csv` todavía no existía (lo arma otro
integrante). La función y el script están probados (pruebas sintéticas y una ejecución en seco
con un catálogo de 2 lugares: 0.07 km y 14.8 km del nodo más cercano, el segundo marcado como
lejano). Cuando exista el catálogo, ejecutar `experimentos/r1_lugares.py` y completar aquí la
tabla de lugares a más de 500 m con `resultados/r1_lugares_lejanos.csv`
(columnas `id,nombre,categoria,lat,lon,nodo,dist_nodo_m`).

---

## 5. Grafo procesado

Archivos generados por `experimentos/r1_red.py` (no hace falta volver a descargar):

- `data/processed/grafo_scc.graphml`: la componente con `length`, `speed_kph`, `travel_time`
  y `velocidad_imputada` en cada arista (al leerlo con `ox.load_graphml` este último atributo
  queda como texto `"True"/"False"`).
- `data/processed/nodos.csv`: `osmid,lat,lon,x_utm,y_utm` (8 792 filas).
- `data/processed/aristas.csv`: `u,v,distancia_m,tiempo_s,velocidad_kmh` (19 999 filas). La
  MultiDiGraph de OSMnx tiene 137 aristas **paralelas** (mismo u→v, distinto tramo físico, p. ej.
  dos calles que unen las mismas esquinas). Para caminos mínimos solo importa la más rápida, así
  que se conserva la de **menor tiempo** y se descartan las otras 137: 20 136 → 19 999.
- `data/processed/descarga.json`: fecha de descarga (2026-11-03), versión de OSMnx y servidor.
- `data/processed/lugares_nodos.csv`: `id,nombre,categoria,lat,lon,nodo,dist_nodo_m,lejano_500m`
  (+ las demás columnas del catálogo), generado por `experimentos/r1_lugares.py`.
- `cargar_grafo()` en `red.py` devuelve `(adj, coords)`: `adj[u] = [(v, tiempo_s, distancia_m),
  ...]` y `coords[u] = (lat, lon)`. Tarda 0.19 s (lectura con el módulo `csv`).

**Tamaño de la red antes y después de quedarse con la componente** (`resultados/r1_tamano.csv`):

| Red | Nodos | Aristas |
|---|---|---|
| Red descargada | 8 808 | 20 157 |
| Componente fuertemente conexa | 8 792 | 20 136 |

**Discusión.** La red descargada ya es casi fuertemente conexa: solo 16 nodos y 21 aristas
quedan fuera (tramos en los bordes del polígono del departamento y sentidos únicos que no
permiten volver). Filtrar no cambia el tamaño de forma apreciable pero garantiza que todas las
rutas existan (sección 3.5).

---

## 6. Verificación (pruebas en `tests/test_r1.py`)

| Prueba | Qué comprueba |
|---|---|
| `test_parsear_maxspeed_casos_a_mano` | números, unidades, mph, `|`, `;`, listas, valores no numéricos y nulos |
| `test_parseo_igual_que_osmnx_en_la_red_real` | el parseo propio coincide con el de OSMnx en las 1 307 aristas con `maxspeed` |
| `test_asignar_pesos_imputacion_y_tiempo` | tiempo = distancia / velocidad; imputación por media del tipo; tabla normativa; tipo desconocido |
| `test_estimar_memoria_caso_pequeno` | V = 2, E = 1 → matriz 32 B, listas 28 B |
| `test_asociar_lugares_cuadricula_a_mano` | nodo y distancia en una cuadrícula resuelta a mano, marca de > 500 m |
| `test_asociar_lugares_igual_que_nearest_nodes` | mismo resultado que `ox.distance.nearest_nodes` en UTM |
| `test_componente_procesada_fuertemente_conexa` | con NetworkX: el grafo de los CSV es fuertemente conexo y tiene tantos nodos como la componente más grande de la red cruda |
| `test_cargar_grafo_completo_y_rapido` | carga en < 2 s, todos los nodos y aristas, velocidades entre 5 y 130 km/h |

---

## Lugares a más de 500 m

`experimentos/r1_lugares.py` se ejecutó con el catálogo de 46 lugares (2026-11-03). La
verificación contra `ox.distance.nearest_nodes` dio el mismo nodo en los 46. Distancia al nodo
más cercano: mediana 75.0 m, mínimo 6.4 m, máximo 1 178.0 m. Siete lugares quedan a más de
500 m (`resultados/r1_lugares_lejanos.csv`):

| id | Lugar | Categoría | Nodo | Distancia al nodo (m) |
|---|---|---|---|---|
| BBR | Reserva Natural Barbas Bremen | atractivo | 2734445328 | 1 178.0 |
| COC | Valle de Cocora | atractivo | 1543526033 | 934.0 |
| FES | Finca Hotel La Esperanza | finca | 10149145145 | 800.7 |
| PBL | Peñas Blancas | atractivo | 4612341644 | 758.8 |
| GRA | Finca Cafetera La Granada | finca | 7623496803 | 741.7 |
| CMB | Combia Finca Hotel | finca | 6387018054 | 710.0 |
| REC | RECUCA - Recorrido de la Cultura Cafetera | atractivo | 6334517962 | 596.7 |

**Tratamiento.** Los siete son reservas, miradores o fincas rurales a las que se llega por un
camino privado, carreteable destapado o sendero que OSM no clasifica como vía para carro
(`network_type="drive"` deja fuera `track` y `path`). Las coordenadas son las del lugar (ver
`docs/notas_catalogo.md`), así que no se corrigen: cada lugar se **conserva asociado a su nodo
más cercano** y el tiempo de una ruta hacia él es el tiempo hasta ese nodo. El último tramo no
modelado es como mucho 1.2 km; a 30 km/h serían unos 2.4 min, poco frente a los tiempos entre
lugares de `resultados/matriz_tiempos.csv` (mediana 43.9 min, máximo 156.4 min).

**Cambio de código (método largo).** Para la sustentación, `asociar_lugares` ahora llama a
`nodo_mas_cercano(x, y, ids, xs, ys, traza=None)`, la búsqueda lineal con bucle explícito y la
distancia euclidiana calculada paso a paso (`dx`, `dy`, `d2`). `parsear_maxspeed` ya no usa
expresiones regulares: parte el texto carácter por carácter y lee el número con `leer_numero`.
`asignar_pesos` se escribió con bucles visibles y pasos numerados. Las firmas y los resultados
no cambiaron: se compararon la versión anterior y la nueva sobre las 20 157 aristas de la red
cruda (0 diferencias en `speed_kph`, `travel_time` y `velocidad_imputada`) y sobre los 46
lugares (mismo nodo y distancia). Ejemplo a mano en `docs/paso_a_paso_R1.md`; prueba nueva
`test_nodo_mas_cercano_y_leer_numero_metodo_largo`.
