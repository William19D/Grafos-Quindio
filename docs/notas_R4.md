# Notas R4 — Ruta óptima de recorrido (TSP asimétrico)

Archivos: `src/quindio/tsp.py`, `experimentos/r4_exactos.py`, `experimentos/r4_calidad.py`,
`experimentos/r4_itinerario.py`, `experimentos/r4_figuras.py`, `specs/R4.md`, `tests/test_r4.py`.
Ejemplo a mano para la sustentación: `docs/paso_a_paso_R4.md` (y `python -m quindio.tsp`).

Máquina (`resultados/maquina.json`): Intel Core i5-12450H (12 núcleos lógicos), 31.6 GB de RAM,
Windows 11 (build 26200), Python 3.11. Semilla base: `config.SEMILLA = 2026`. Mediciones:
5 repeticiones, mediana, milisegundos, solo el algoritmo (la matriz ya está en memoria; sin
lectura de archivos ni impresión; `traza=None`). Límite de 5 min por método y k con
`medicion.medir_con_limite` (proceso aparte; si no termina se marca «no completada»). Si una
ejecución pasa de 1 min se mide una sola vez (protocolo 6.3).

---

## 1. El problema

Entrada: la matriz de tiempos mínimos de R2 (`resultados/matriz_tiempos.csv`, 46 × 46, en
segundos). Es **asimétrica**: d(i, j) ≠ d(j, i) en general (vías de un sentido, velocidades
distintas por sentido). Como cada celda es un camino mínimo en la red, cumple la desigualdad
triangular d(i, j) ≤ d(i, m) + d(m, j).

Problema: salir de un lugar (Armenia, `ARM`), visitar k lugares más, cada uno una vez, y regresar,
minimizando el tiempo total de desplazamiento. Es el problema del viajero asimétrico (ATSP),
NP-difícil (Garey y Johnson, *Computers and Intractability*, W. H. Freeman, 1979, problema ND22;
Cormen, Leiserson, Rivest y Stein, *Introduction to Algorithms*, 3.ª ed., MIT Press, 2009,
secc. 34.5.4).

Representación en el código: una matriz pequeña `d` (lista de listas) de (k+1) × (k+1) con la
partida en el índice 0 (`tsp.submatriz`). Un recorrido es `[0, a1, ..., ak, 0]` y todas las
funciones devuelven `(costo, recorrido)`.

## 2. Algoritmos (implementación propia, "método largo")

Ninguno usa librerías que resuelvan el problema: ni `itertools`, ni NetworkX, ni NumPy. Todo con
bucles explícitos, variables con nombre en español, docstring con pseudocódigo numerado y
comentarios `# Paso n` que corresponden a ese pseudocódigo.

### 2.1 Generador de permutaciones: algoritmo de Heap (`permutaciones_heap`)

En vez de `itertools.permutations` se escribió el algoritmo de Heap en versión iterativa (B. R.
Heap, "Permutations by interchanges", *The Computer Journal* 6(3), 293-294, 1963; R. Sedgewick,
"Permutation generation methods", *ACM Computing Surveys* 9(2), 137-164, 1977, secc. 2). Cada
permutación sale de la anterior con **un solo intercambio**, guiado por un contador por posición
que funciona como odómetro. Tiempo O(n!) (O(1) amortizado por permutación), memoria O(n).
Entrega siempre la misma lista modificada: la fuerza bruta la copia solo cuando encuentra una mejor.

### 2.2 Fuerza bruta (`fuerza_bruta`)

1. Si k = 0, devolver (0, [0, 0]).
2. Para cada permutación P de 1..k: costo = d(0, P[0]) + Σ d(P[t], P[t+1]) + d(P[k−1], 0).
3. Guardar la de menor costo (`<` estricto: en empate se queda la primera).

**Complejidad**: k! permutaciones × O(k) para sumar cada una → **O(k · k!)** tiempo; **O(k)**
memoria (permutación actual, la mejor y los contadores de Heap). Fuente: Cormen et al. 2009,
secc. 34.5.4 y Sedgewick 1977. Solo se permutan los k lugares (la partida está fija), por eso son
k! y no (k+1)!.

### 2.3 Held-Karp (`held_karp`)

**Subestructura óptima.** Sea C(S, j) el tiempo mínimo de un camino que sale de 0, visita
exactamente los lugares de S ⊆ N = {1..k} y termina en j ∈ S. Si en el camino óptimo el lugar
anterior a j es i, el tramo de 0 a i visita S \ {j} y debe ser óptimo para (S \ {j}, i): si
hubiera uno más corto, se reemplaza y el camino hasta j bajaría, contradicción. Además el costo
del resto (d(i, j)) solo depende de i y j, no del orden en que se visitó S \ {j}: por eso basta
guardar el par (conjunto, último lugar).

**Recurrencia** (M. Held y R. M. Karp, "A dynamic programming approach to sequencing problems",
*Journal of the SIAM* 10(1), 196-210, 1962; R. Bellman, "Dynamic programming treatment of the
travelling salesman problem", *Journal of the ACM* 9(1), 61-63, 1962):

- Caso base: C({j}, j) = d(0, j)
- C(S, j) = min_{i ∈ S \ {j}} [ C(S \ {j}, i) + d(i, j) ]
- Respuesta: min_{j ∈ N} [ C(N, j) + d(j, 0) ]

**Implementación.** S es una máscara de bits (bit j−1 = lugar j). Las tablas `C[mascara][j-1]` y
`padre[mascara][j-1]` son **listas indexadas por máscara** (no diccionarios de tuplas). Se llenan
en orden creciente de máscara: S \ {j} siempre es un número menor que S, así que ya está
calculado. `padre` guarda el i del mínimo y permite **reconstruir el recorrido** (no solo el
costo) caminando hacia atrás desde (N, último).

Pseudocódigo: (1) caso k = 0; (2) crear tablas de 2^k × k; (3) caso base; (4) para cada máscara
de 2 o más bits y cada j de la máscara, probar cada i de S \ {j}; (5) cerrar el ciclo; (6)
reconstruir con `padre` e invertir.

**Complejidad**: k·2^k pares (S, j), cada uno revisa hasta k valores de i → **O(k² · 2^k)**
tiempo. Contando exacto, las combinaciones válidas (S, j, i) con i ≠ j en S son
Σ_s C(k, s)·s·(s−1) = k(k−1)·2^(k−2). Memoria: dos tablas de 2^k × k → **O(k · 2^k)**
(Held y Karp 1962; Cormen et al. 2009, cap. 15).

**Memoria estimada según el tamaño de la tabla** (`resultados/r4_memoria.csv`; pico real con
`tracemalloc`, medido aparte del tiempo):

| k | Entradas (2 tablas × 2^k × k) | Estimado a 8 B/entrada | Pico medido (MiB) |
|---|---|---|---|
| 5 | 320 | 2.5 KB | 0.005 |
| 8 | 4 096 | 32 KB | 0.080 |
| 10 | 20 480 | 160 KB | 0.394 |
| 12 | 98 304 | 768 KB | 1.807 |
| 14 | 458 752 | 3.5 MB | 8.129 |
| 16 | 2 097 152 | 16 MB | 36.069 |

El pico real es ≈ 2.3 veces el estimado a 8 bytes, y la razón se explica entrada por entrada: en
Python cada casilla de una lista es un puntero de 8 B; además cada fila es una lista con ~56 B de
encabezado (2 × 2^k filas), y los costos calculados de C son objetos `float` nuevos de 24 B
(hay k·2^(k−1) casillas válidas; los enteros pequeños de `padre` y el `inf` inicial son objetos
compartidos y no suman). Para k = 16: 16.8 millones de bytes de punteros + 7.3 millones de
encabezados + 12.6 millones de floats ≈ 36.7 millones de bytes, frente a 37.8 millones medidos
(36.1 MiB). Lo importante:
el pico se **duplica (algo más) por cada lugar extra**, como dice O(k·2^k).

### 2.4 Heurística voraz: vecino más cercano (`vecino_mas_cercano`)

Elegida por el grupo: desde el lugar actual ir al **no visitado más cercano** y, al terminar,
regresar a la partida. Justificación: es lo que haría un turista con el mapa ("¿qué me queda más
cerca ahora?"), es muy simple de explicar y de implementar con dos bucles, y cuesta **O(k²)**
tiempo (k pasos × hasta k candidatos con búsqueda lineal) y **O(k)** memoria (D. Rosenkrantz,
R. Stearns y P. Lewis, "An analysis of several heuristics for the traveling salesman problem",
*SIAM Journal on Computing* 6(3), 563-581, 1977). Esos autores muestran que, aun con desigualdad
triangular, su resultado puede ser hasta Θ(log k) veces el óptimo: no hay garantía de calidad
constante.

### 2.5 Itinerario (`itinerario`, `ajustar_a_jornada`)

`itinerario(partida, atractivos, matriz, duraciones)` ordena con Held-Karp y arma las filas del
anexo (orden, lugar, desplazamiento desde el anterior, visita, tiempo acumulado) con la fila final
«Regreso» y los totales; la app lo puede reutilizar. `ajustar_a_jornada` quita atractivos
mientras la jornada pase de 11 h con este **criterio explícito**: se prueba quitar cada uno,
se recalcula el óptimo con Held-Karp y se quita el que **más acorta la jornada** (su visita + el
desvío que se ahorra). Así se quitan los menos atractivos posibles. Costo por ronda: k
ejecuciones de Held-Karp, O(k³·2^k); con k ≤ 8 es instantáneo.

## 3. Correctitud

- **Fuerza bruta**: examina todas las permutaciones de 1..k (el algoritmo de Heap genera cada
  una exactamente una vez, Sedgewick 1977, secc. 2), así que la mínima está entre ellas.
- **Held-Karp**: por inducción sobre |S|. Para |S| = 1 el caso base es el único camino posible.
  Si C es correcto para todos los conjuntos de tamaño s − 1, la recurrencia prueba todos los
  penúltimos i posibles para un conjunto de tamaño s, y por la subestructura óptima uno de ellos
  es el del camino óptimo. El cierre agrega el regreso desde cada último j posible.
- **Vecino más cercano**: siempre devuelve una permutación válida (cada paso marca un lugar no
  visitado y hay exactamente k pasos), pero no necesariamente óptima (sección 6.4).

## 4. Verificación

| Prueba (`tests/test_r4.py`) | Qué comprueba |
|---|---|
| `test_ejemplo_a_mano` | matriz asimétrica 4 × 4 resuelta a mano: fuerza bruta y Held-Karp dan 21 con 0-2-3-1-0; la voraz da 33 con 0-1-3-2-0 |
| `test_permutaciones_heap` | el generador da las 120 permutaciones de 5 elementos, iguales a `itertools.permutations` (solo en la prueba) |
| `test_held_karp_igual_fuerza_bruta[1..8]` | matrices aleatorias asimétricas (semilla 2026 + n, k = 0..7, 5 por tamaño): mismo costo; ambos recorridos válidos y cuestan lo reportado |
| `test_vecino_mas_cercano_valido` | permutación válida, costo = suma del recorrido, costo ≥ óptimo |
| `test_itinerario_cabe_en_11_horas` | con la matriz real, el itinerario ajustado dura ≤ 11 h, termina en «Regreso» a ARM y los totales coinciden con la suma de las filas |
| `test_traza_no_cambia_resultado` | el parámetro `traza` no altera el resultado |

Resultado: `.venv/Scripts/python.exe -m pytest -q tests/test_r4.py` → 13 pruebas en verde.

En los experimentos, antes de guardar cada número, se verifica que el recorrido sea una
permutación válida, que su suma sea el costo reportado y que **fuerza bruta y Held-Karp den el
mismo óptimo** en todos los k que la fuerza bruta resolvió (k = 5..11: coinciden siempre, columna
`mismo_costo`). En la calidad se verifica además voraz ≥ óptimo.

## 5. Elección de las instancias

- Exactos (punto 1): partida ARM; para cada k, `random.Random(2026 + k).sample(...)` sobre los 45
  lugares del catálogo distintos de ARM (las 4 categorías: cabecera, atractivo, finca, acopio).
  Una instancia por k (lugares en la columna `lugares` del CSV).
- Calidad (punto 3): k = 5, 8, 10, 12 y 5 instancias por k con `random.Random(2026 + 100·k + i)`,
  i = 0..4 (semillas 2526-2530, 2826-2830, 3026-3030, 3226-3230; columna `semilla`).

## 6. Resultados

### 6.1 Soluciones exactas (`resultados/r4_exactos.csv`)

| k | Tiempo fuerza bruta (ms) | Tiempo Held-Karp (ms) | Óptimo (min) | ¿Mismo costo? |
|---|---|---|---|---|
| 5 | 0.138 | 0.248 | 151.1 | sí |
| 6 | 0.913 | 0.350 | 161.3 | sí |
| 7 | 7.505 | 0.908 | 311.4 | sí |
| 8 | 62.051 | 2.313 | 325.1 | sí |
| 9 | 656.317 | 6.055 | 345.3 | sí |
| 10 | 6 638.790 | 13.938 | 291.3 | sí |
| 11 | 84 030.081 (1 repetición, > 1 min) | 36.491 | 320.9 | sí |
| 12 | no completada (> 5 min) | 81.215 | 376.7 | solo Held-Karp |

Mayor k resuelto: **fuerza bruta k = 11**; **Held-Karp k = 12** (todos los pedidos; como extra,
`r4_held_karp_extendido.csv`: k = 13 → 185.9 ms, 14 → 440.0 ms, 15 → 1 001.1 ms,
16 → 2 224.3 ms).

Gráfica: `resultados/figuras/r4_tiempo_vs_k.png` (k en x, ms en y, escala logarítmica).

**Discusión.** Lo medido coincide con la teoría. Para la fuerza bruta, el cociente entre k y
k − 1 debería ser k·k!/((k−1)·(k−1)!) = k²/(k−1): 8.2, 9.1, 10.1, 11.1, 12.1 para k = 7..11; se
midió 8.2, 8.3, 10.6, 10.1 y 12.7. Dicho de otra forma, el tiempo por unidad de trabajo
tiempo/(k·k!) se mantiene casi constante, entre 183 y 230 ns. Con ese ritmo, k = 12 necesitaría
≈ 84 s × 12²/11 ≈ 1 100 s ≈ 18 min, muy por encima del límite: por eso «no completada», como se
esperaba. Para Held-Karp el cociente teórico entre k y k − 1 es ≈ 2(k/(k−1))² ≈ 2.3-2.7 y se
midió 2.2-2.6 desde k = 7 (también en la extensión hasta 16); tiempo/(k(k−1)·2^(k−2)) ≈ 570-680 ns,
estable. La única desviación es k = 5 (0.248 ms, 1 550 ns por unidad): con tan poco trabajo pesa
el costo fijo (crear las tablas, llamar la función); en `r4_calidad_detalle.csv` las instancias
de k = 5 tardan 0.14 ms. En la gráfica la fuerza bruta es una curva que se empina (factorial) y
Held-Karp una recta de pendiente casi fija en escala log (exponencial 2^k con un factor
polinomial). Para k = 5 la fuerza bruta es incluso más rápida (120 permutaciones contra la
preparación de las tablas), pero desde k = 6 Held-Karp gana y en k = 11 es ≈ 2 300 veces más rápido.

### 6.2 Calidad de la heurística (`resultados/r4_calidad.csv`; detalle en `r4_calidad_detalle.csv`)

| k | Instancias | Brecha promedio (%) | Brecha máxima (%) | Brecha mínima (%) | Tiempo voraz (ms, mediana) | Tiempo Held-Karp (ms, mediana) |
|---|---|---|---|---|---|---|
| 5 | 5 | 3.09 | 5.38 | 0.74 | 0.006 | 0.144 |
| 8 | 5 | 8.51 | 14.53 | 0.01 | 0.010 | 2.521 |
| 10 | 5 | 6.40 | 9.84 | 2.44 | 0.014 | 16.449 |
| 12 | 5 | 10.74 | 16.94 | 4.98 | 0.019 | 90.101 |

brecha % = (voraz − óptimo Held-Karp) / óptimo × 100.

**Discusión.** En ninguna de las 20 instancias la voraz encontró el óptimo (la más cercana:
0.007 % en k = 8, instancia 2). La brecha tiende a crecer con k (promedio 3 % → 11 %; máxima
5 % → 17 %): con más lugares hay más decisiones locales que pueden salir mal y el regreso final
suele ser largo. No es monótona (k = 10 promedia menos que k = 8) porque con solo 5 instancias por
k la variación entre instancias es grande. Es coherente con la teoría: no hay garantía constante
(Rosenkrantz et al. 1977), pero en la práctica con desigualdad triangular queda a pocas decenas de
por ciento. A cambio la voraz es miles de veces más rápida (0.019 ms contra 90 ms en k = 12) y su
tiempo crece casi lineal en el rango medido (O(k²) con k pequeño, dominado por el costo fijo).

### 6.3 Itinerario de un día (lugar de partida: Plaza de Bolívar de Armenia, `ARM`)

**Conjunto elegido (7 atractivos)**: Museo del Oro Quimbaya (MOQ, 90 min), Parque de los
Fundadores (FUN, 90), Jardín Botánico del Quindío (JBQ, 150), Cementerio Libre de Circasia (CLC,
90), Mirador Colina Iluminada de Filandia (CIL, 45), Calle Real de Salento (CRS, 90) y Mirador Alto
de la Cruz (ACR, 45). Por qué: es una ruta de patrimonio cultural y miradores por el eje
Armenia - Calarcá - Circasia - Filandia - Salento, todo a menos de 1 h de Armenia; no se
incluyen los parques temáticos de jornada completa (Parque del Café, PANACA: 6 h cada uno), que
llenarían el día solos. Las visitas suman 600 min = 10 h, así que el día solo cabe si los
desplazamientos duran menos de 1 h: el ejercicio es interesante porque el primer intento falla
**por los desplazamientos**, no por las visitas.

**Primer intento (7 atractivos, orden de Held-Karp)**: ARM → JBQ → ACR → CRS → CIL → CLC → MOQ →
FUN → ARM: 600 min de visitas + 135.4 min de desplazamientos = **12.26 h > 11 h: no cabe**.

**Ajuste** (`ajustar_a_jornada`, criterio de la sección 2.5): quitando cada uno la jornada
quedaría en MOQ 10.76 h, FUN 10.76, **JBQ 9.53**, CLC 10.74, CIL 10.89, CRS 10.76, ACR 11.50.
Se quita el **Jardín Botánico (JBQ)**: es la visita más larga (150 min) y además está en Calarcá,
al otro lado de Armenia respecto al resto de la ruta (quitarlo ahorra 13.7 min de viaje). Aquí el
criterio coincide con "quitar el de mayor duración". Se recalcula el orden con Held-Karp:

`resultados/r4_itinerario.csv`:

| Orden | Lugar | Desplazamiento desde el anterior (min) | Visita (min) | Tiempo acumulado (h) |
|---|---|---|---|---|
| 1 | Cementerio Libre de Circasia (CLC) | 21.8 | 90 | 1.86 |
| 2 | Mirador Colina Iluminada de Filandia (CIL) | 26.9 | 45 | 3.06 |
| 3 | Mirador Alto de la Cruz (ACR) | 33.7 | 45 | 4.37 |
| 4 | Calle Real de Salento (CRS) | 0.3 | 90 | 5.88 |
| 5 | Museo del Oro Quimbaya (MOQ) | 29.5 | 90 | 7.87 |
| 6 | Parque de los Fundadores (FUN) | 5.6 | 90 | 9.46 |
| Regreso | Plaza de Bolívar de Armenia (ARM) | 3.8 | — | 9.53 |

Totales: visitas **450 min (7.5 h)**; desplazamientos **121.7 min (2.03 h)**; jornada
**9.53 h ≤ 11 h** (`resultados/r4_itinerario.json` guarda también el primer intento y las rondas).

**Discusión.** Held-Karp arma un circuito sin ir y volver: sube por Circasia y Filandia, pasa a
Salento y baja a Armenia terminando en los dos atractivos urbanos, cerca del punto de partida.
Los desplazamientos son ~21 % de la jornada. El tramo de 0.3 min (mirador → Calle Real de
Salento) es real: ambos están en el casco urbano de Salento. El orden óptimo no visita primero
lo más cercano a Armenia (FUN está a ~5 min), sino que lo deja para el final para no pagar un
regreso largo, la misma idea del punto 6.4.

### 6.4 Voraz frente a óptimo (`resultados/r4_voraz_vs_optimo.json`)

Ejemplo con datos reales: k = 5, semilla 2530, lugares Hotel Decameron Panaca (DPA), Plaza de
Bolívar de Salento (SAL), Trilladora Europa (TEU), Parque de la Vida (PVI) y RECUCA (REC).

| Método | Recorrido | Tramos (min) | Total |
|---|---|---|---|
| Óptimo (Held-Karp) | ARM → TEU → REC → DPA → SAL → PVI → ARM | 5.2 + 21.7 + 64.8 + 75.6 + 34.8 + 4.6 | **206.5 min** |
| Vecino más cercano | ARM → PVI → TEU → REC → SAL → DPA → ARM | 4.9 + 7.7 + 21.7 + 63.4 + 76.2 + 43.6 | **217.6 min** (+5.38 %) |

La voraz sale al Parque de la Vida porque está a 4.9 min (TEU está a 5.2 min). Esa ganancia de
0.3 min la paga al final: el último lugar que le queda es DPA, en el extremo occidental
(Quimbaya), y regresar de allí a Armenia cuesta 43.6 min. El óptimo deja el Parque de la Vida
para el final (4.6 min de regreso). Ejemplo a mano aún más claro (paso a paso, sección 4): voraz
33 frente a óptimo 21.

**Por qué en Dijkstra la elección voraz sí es óptima y aquí no.** En Dijkstra, con pesos no
negativos, el nodo no explorado de menor distancia tentativa ya tiene su distancia definitiva:
cualquier otro camino hacia él tendría que salir del conjunto explorado por un nodo con
distancia mayor o igual y solo puede sumar (propiedad de elección voraz + subestructura óptima;
Cormen et al. 2009, teorema 24.6). La decisión de hoy nunca se arrepiente. En el TSP la decisión
local "ir al más cercano" no tiene en cuenta el costo de regresar ni cómo quedan agrupados los
lugares restantes: el valor de cada paso depende de todos los pasos siguientes. No existe una
propiedad de elección voraz y el problema es NP-difícil, por lo que, salvo que P = NP, ningún
algoritmo polinomial (voraz o no) puede garantizar el óptimo.

## 7. Supuestos y limitaciones

- Los tiempos son los de la matriz de R2 (red sin tráfico, velocidades por tipo de vía); el
  itinerario no considera horarios de apertura ni tiempos de parqueo.
- Una sola instancia por k en los exactos: los tiempos dependen poco de la instancia (fuerza
  bruta siempre hace k! permutaciones; Held-Karp siempre llena las mismas casillas).
- La fuerza bruta de k = 11 se midió una sola vez (> 1 min, protocolo 6.3).
- Las mediciones son de Python puro; un lenguaje compilado sería decenas de veces más rápido,
  pero el crecimiento (k·k! frente a k²·2^k) sería el mismo.
- La memoria de Held-Karp se midió con `tracemalloc` en una ejecución aparte (tracemalloc
  ralentiza el código y por eso no se mezcla con la medición de tiempo).
