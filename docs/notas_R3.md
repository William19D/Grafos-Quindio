# Notas R3 — Envolvente convexa de la red vial

Código: `src/quindio/envolvente.py` (algoritmo y utilidades), `experimentos/r3_envolvente.py`
(verificación, mediciones y `envolvente.json`), `experimentos/r3_figuras.py` (figuras a partir de
los archivos de resultados). Especificación: `specs/R3.md`. Pruebas: `tests/test_r3.py`.
Explicación de un ejemplo pequeño, iteración por iteración: `docs/paso_a_paso_R3.md`.

Datos: nodos de la componente fuertemente conexa (`data/processed/nodos.csv`, 8 792 nodos, con
coordenadas UTM 18N, EPSG:32618, calculadas en R1). Máquina en `resultados/maquina.json`
(Intel Core i5-12450H, 31.6 GB RAM, Windows 11, Python 3.11; SciPy 1.17.1, NumPy).

Cómo reproducir (desde la raíz del repositorio):

```
PYTHONPATH=src .venv/Scripts/python.exe experimentos/r3_envolvente.py
PYTHONPATH=src .venv/Scripts/python.exe experimentos/r3_figuras.py
PYTHONPATH=src .venv/Scripts/python.exe -m quindio.envolvente      # traza del ejemplo pequeño
.venv/Scripts/python.exe -m pytest -q tests/test_r3.py
```

---

## 1. El problema

La envolvente convexa de un conjunto de puntos es el menor polígono convexo que los contiene.
Tomando los nodos de la red como puntos del plano, da una aproximación de la extensión de la
red vial del departamento.

**Preparación de coordenadas** (`preparar_puntos`). Las coordenadas UTM (metros) se redondean
al entero más cercano y se eliminan los puntos repetidos (se conserva la primera aparición). En
la red, los 8 792 nodos dan **8 792 puntos distintos** (ningún par de nodos cae en el mismo metro
cuadrado). Costo: O(n) tiempo esperado (conjunto hash) y O(n) memoria.

**Aritmética entera** (`orientacion(a, b, c)`). El giro se decide con el producto cruz
`(b−a)×(c−a)` (Cormen et al., *Introduction to Algorithms*, 3.ª ed., MIT Press, 2009, sec. 33.1,
"Line-segment properties"): positivo = giro a la izquierda, negativo = derecha, cero = alineados.
Con enteros el resultado es exacto (no hay errores de redondeo que hagan dudar si tres puntos están
alineados). En Python los `int` tienen precisión ilimitada ("Integers have unlimited precision",
documentación de Python, *Built-in Types*, sección *Numeric Types*,
https://docs.python.org/3/library/stdtypes.html), así que no hay desbordamiento. En un lenguaje
con enteros de tamaño fijo (C, Java) se usarían enteros de 64 bits: las coordenadas UTM son del
orden de 10⁶ m y las diferencias de 10⁵ m, así que los productos son del orden de 10¹⁰–10¹², muy por
debajo del máximo de 64 bits (≈ 9.2·10¹⁸), mientras que 32 bits (≈ 2.1·10⁹) sí desbordarían.

**Alineados**: los puntos que quedan sobre un lado del polígono no son vértices. El algoritmo
solo conserva puntos *estrictamente* a un lado de cada segmento (giro ≠ 0), y en caso de empate
en el punto más lejano elige el extremo del lado (ver sección 3).

## 2. Elección del algoritmo: QuickHull (divide y vencerás)

Se eligió **QuickHull** en lugar de la mezcla de Preparata-Hong por la distribución de los puntos
de la red:

- **Pocos vértices en la envolvente** (h ≪ n): la red tiene 14 vértices para 8 792 puntos.
- **Puntos concentrados en los cascos urbanos** (Armenia, Calarcá, Montenegro, La Tebaida,
  Quimbaya, Circasia, etc.; ver `resultados/figuras/r3_envolvente.png`), lejos del borde de la
  envolvente. QuickHull descarta en cada paso todos los puntos dentro del triángulo formado por un
  lado y el punto más lejano, así que la mayoría de los nodos se elimina en el primer nivel.
  **Medido** (`resultados/r3_niveles.csv`): de los 8 790 candidatos del primer nivel se descartan
  8 246 (**93.8 %**); al segundo nivel llegan 542 y al tercero 22.
- Es más simple de explicar y programar que la mezcla de dos envolventes (Preparata-Hong), que
  necesita encontrar las tangentes superior e inferior de dos polígonos y siempre divide hasta
  llegar a conjuntos de tamaño constante, aunque casi todos los puntos sean interiores.

Fuentes: C. B. Barber, D. P. Dobkin y H. Huhdanpaa, "The Quickhull algorithm for convex hulls",
*ACM Transactions on Mathematical Software* 22(4):469–483, 1996; F. P. Preparata y M. I. Shamos,
*Computational Geometry: An Introduction*, Springer, 1985, cap. 3 (técnicas QuickHull y
algoritmos de divide y vencerás en el plano).

### Algoritmo (`quickhull(puntos, traza=None)`)

1. A ← punto de menor (x, y); B ← punto de mayor (x, y). Ambos son vértices.
2. Dividir los puntos: *abajo* (a la derecha de A→B) y *arriba* (a la izquierda). Los alineados con
   AB están sobre el segmento AB y se descartan.
3. Para cada lado P→Q con su conjunto de candidatos (puntos a su derecha):
   - si no hay candidatos, P→Q es un lado de la envolvente;
   - si no, C ← el candidato más lejano de la recta PQ (C es vértice);
   - candidatos a la derecha de P→C → subproblema (P, C); a la derecha de C→Q → subproblema (C, Q);
     los que están dentro del triángulo P-C-Q (o sobre sus lados) se descartan.
4. Los vértices salen en orden antihorario empezando en A.

En lugar de recursión se usa una **pila explícita** de tareas (P, Q, candidatos, nivel): en el peor
caso la profundidad es O(n) y Python limita la recursión a ~1000 llamadas. Se apila primero
(C, Q) y luego (P, C) para que P→C se resuelva antes y los vértices salgan en orden.

### Complejidad

- **Recurrencia**: T(n) = T(n₁) + T(n₂) + O(n), con n₁ + n₂ ≤ n − 1 (el O(n) es buscar el punto
  más lejano y repartir los candidatos) (Preparata y Shamos 1985, cap. 3; Barber et al. 1996).
- **Tiempo**: si cada división reparte de forma balanceada (n₁, n₂ ≤ c·n con c < 1), la
  recurrencia da **O(n log n)**, que es el caso promedio; con divisiones muy desbalanceadas
  (n₁ = n − 2, n₂ = 0 en cada paso, por ejemplo puntos sobre una parábola o una circunferencia
  en posiciones desfavorables) da T(n) = T(n−1) + O(n) = **O(n²)** en el peor caso. Como cada nivel
  de la pila recorre a lo sumo n puntos y cada tarea produce un vértice, también vale la cota
  O(n·h) (Barber et al. 1996 la describen como sensible a la salida).
- **Cota inferior**: cualquier algoritmo de envolvente basado en comparaciones necesita
  Ω(n log n) en el peor caso (Preparata y Shamos 1985, cap. 3, reducción desde ordenamiento;
  Cormen et al. 2009, sec. 33.3) y Ω(n log h) en función de la salida (D. G. Kirkpatrick y
  R. Seidel, "The ultimate planar convex hull algorithm?", *SIAM J. Computing* 15(1), 1986).
- **Memoria**: O(n). Cada punto vivo está en una sola lista de candidatos y la pila guarda a lo
  sumo una tarea pendiente por nivel más una (las listas de todas las tareas de la pila suman ≤ n
  puntos). La salida ocupa O(h).
- Funciones auxiliares: `orientacion` y `proyeccion` O(1); `preparar_puntos` O(n);
  `quitar_colineales` y `area_km2` O(h).

### Correctitud (argumento)

Invariante de cada tarea (P, Q, S): P y Q son vértices de la envolvente, consecutivos en el polígono
provisional recorrido en sentido antihorario, y S contiene todos los puntos de la entrada que están
estrictamente a la derecha de P→Q (fuera del polígono provisional).

1. *Inicio*: A y B son vértices porque son extremos en el orden lexicográfico (x, y): ninguno se
   puede escribir como combinación convexa de otros puntos. Los puntos con giro 0 respecto de AB
   están entre A y B (A y B son los extremos en x), así que quedan sobre el segmento y no son
   vértices. *Abajo* y *arriba* cumplen el invariante para A→B y B→A.
2. *C es vértice*: la recta paralela a PQ que pasa por C deja a todos los puntos de S del mismo lado
   (C es el más lejano), así que es una recta de apoyo. Si varios puntos están sobre esa recta, se
   toma el más cercano a P (menor producto punto con P→Q), que es un extremo del segmento que
   forman y por lo tanto vértice; los del medio quedan alineados y se descartan en la tarea
   siguiente (prueba `test_empate_en_el_punto_mas_lejano`; sin este desempate la prueba fallaba).
3. *Descartar es seguro*: un punto de S que no está a la derecha de P→C ni de C→Q está dentro del
   triángulo P-C-Q o sobre sus lados; es combinación convexa de P, C y Q, así que no es vértice.
   Ningún punto puede estar a la derecha de P→C y de C→Q a la vez, porque estaría más lejos de PQ que C.
4. *Mantenimiento*: las tareas (P, C, S₁) y (C, Q, S₂) cumplen el invariante.
5. *Terminación*: cada tarea con candidatos saca al menos a C de S, así que |S| baja
   estrictamente y la pila se vacía.
6. *Resultado*: cuando una tarea no tiene candidatos, ningún punto está a la derecha de P→Q, así
   que P→Q es un lado de la envolvente. El orden de la pila (primero P→C, después C→Q) recorre los
   lados de A a B por abajo y de B a A por arriba: **orden antihorario**, sin alineados.

## 3. Verificación

- `tests/test_r3.py` (7 pruebas, en verde): cuadrado con 2 puntos interiores y 4 alineados sobre los
  lados (resultado a mano `[(0,0),(4,0),(4,4),(0,4)]`); puntos repetidos; casos degenerados (todos
  alineados → los dos extremos, un punto, vacío); comparación con SciPy en 7 conjuntos aleatorios
  con semilla 2026 (incluye rangos de 4×4 a 30×30 con muchos repetidos, alineados y empates);
  orden antihorario (todos los giros consecutivos > 0); área por la fórmula del zapato; empate en
  el punto más lejano.
- **Comparación con SciPy** (`envolvente_scipy`): `scipy.spatial.ConvexHull` devuelve en 2D los
  vértices en orden antihorario. Qhull trabaja con punto flotante y, según su tolerancia, podría
  incluir u omitir puntos casi alineados; por eso a la salida de SciPy se le aplica
  `quitar_colineales` (elimina v si `orientacion(anterior, v, siguiente) == 0`) y se rota para
  empezar en el mismo punto. La salida propia **no** se limpia: ya debe venir sin alineados, y la
  prueba lo exige (comparación con `==` de listas, mismo conjunto y mismo orden). En una prueba
  adicional de 2 992 conjuntos pequeños al azar con muchos alineados, las dos coincidieron en todos.
- Antes de medir, el experimento verifica cada conjunto (`assert propio == envolvente_scipy(...)`):
  los 4 conjuntos coinciden. Con todos los puntos alineados, Qhull lanza `QhullError` (no hay
  envolvente 2D); el algoritmo propio devuelve los dos extremos, y ese caso se prueba a mano.

## 4. Experimento

Protocolo: solo se mide el algoritmo (la lectura del CSV, el redondeo y la conversión a arreglo de
NumPy quedan fuera), 5 repeticiones y mediana con `quindio.medicion.medir`, tiempos en
milisegundos, semilla `config.SEMILLA = 2026` (`random.Random(2026)`), puntos enteros uniformes en
el cuadrado [0, 100 000]² m. El tiempo de SciPy mide solo `ConvexHull(arreglo)`. Ninguna ejecución
se acercó al límite de 5 minutos. *n* = puntos tras redondear y quitar repetidos (en los
cuadrados no salió ningún repetido).

### Tabla 1 — Tiempos (`resultados/r3_envolvente.csv`, tiempos en ms)

| Conjunto de puntos | n | Vértices de la envolvente | Tiempo propio (ms) | Tiempo SciPy (ms) | Cociente (propio/SciPy) |
|---|---|---|---|---|---|
| Nodos de la red | 8 792 | 14 | 19.031 | 3.586 | 5.3 |
| Cuadrado, 1 000 puntos | 1 000 | 21 | 4.470 | 2.555 | 1.7 |
| Cuadrado, 10 000 puntos | 10 000 | 26 | 27.635 | 4.227 | 6.5 |
| Cuadrado, 50 000 puntos | 50 000 | 29 | 133.388 | 14.310 | 9.3 |

Costo fijo de una llamada a `ConvexHull` con solo 4 puntos (`resultados/r3_scipy_costo_fijo.json`):
**2.021 ms**.

Variabilidad: el experimento se ejecutó cuatro veces el mismo día con otros procesos activos en la
máquina (las tres primeras con una versión previa sin el desempate de la sección 2, de costo
equivalente); las medianas cambiaron hasta ~50 % entre ejecuciones (por ejemplo, propio con la red entre
17.7 y 29.1 ms; propio con 50 000 puntos entre 125 y 229 ms), pero el orden de los conjuntos y que
el cociente crece con n se mantuvieron en todas. La tabla es la última ejecución, la del código final.

### Tabla 2 — Descartes por nivel de QuickHull (`resultados/r3_niveles.csv`)

| Conjunto | n | Candidatos nivel 1 | Descartados nivel 1 | % | Candidatos nivel 2 | Candidatos nivel ≥ 3 | Total de candidatos procesados / n |
|---|---|---|---|---|---|---|---|
| Nodos de la red | 8 792 | 8 790 | 8 246 | 93.8 % | 542 | 24 | 1.06 |
| Cuadrado, 1 000 | 1 000 | 998 | 555 | 55.6 % | 441 | 61 | 1.50 |
| Cuadrado, 10 000 | 10 000 | 9 998 | 7 262 | 72.6 % | 2 734 | 201 | 1.29 |
| Cuadrado, 50 000 | 50 000 | 49 998 | 41 743 | 83.5 % | 8 253 | 490 | 1.17 |

(Nivel 1 = las dos tareas A→B y B→A; además, la división inicial recorre los n puntos una vez.)

**Discusión de la tabla 2.** Coincide con la justificación de la sección 2: en la red, por estar los
nodos agrupados en los cascos urbanos lejos del borde, el primer triángulo de cada lado ya elimina el
93.8 % de los puntos, más que en los puntos uniformes del cuadrado. En total QuickHull procesa solo
≈ 1.06·n candidatos en la red y entre 1.17·n y 1.50·n en el cuadrado, más la pasada inicial: el
trabajo real se parece mucho más a O(n) que a O(n log n), porque los conjuntos se reducen de forma
geométrica y la profundidad es de apenas 4 a 6 niveles. La cota O(n log n) promedio es una cota
superior; el peor caso O(n²) requiere que casi todos los puntos estén en la envolvente, lo que no
pasa ni en la red (h = 14) ni en el cuadrado.

**Vértices en el cuadrado.** Para n puntos uniformes en un cuadrado, el número esperado de vértices
crece como (8/3)·ln n más una constante (A. Rényi y R. Sulanke, "Über die konvexe Hülle von n
zufällig gewählten Punkten", *Z. Wahrscheinlichkeitstheorie* 2, 1963). (8/3)·ln n da 18.4, 24.6 y
28.9 para 1 000, 10 000 y 50 000; se midieron 21, 26 y 29: crecen igual de lento (logarítmico), con
una diferencia casi constante. Es la situación favorable para QuickHull (h ≪ n).

### Gráfica — `resultados/figuras/r3_tiempos.png`

Barras del tiempo propio y del de SciPy por conjunto (escala logarítmica, ms), con el cociente
anotado. Se genera leyendo `resultados/r3_envolvente.csv`.

**Discusión de la tabla 1 y la gráfica.**

*Crecimiento con n (propio).* De 10 000 a 50 000 puntos (×5) el tiempo propio pasa de 27.6 a
133.4 ms (×4.8): crecimiento prácticamente lineal, como predice la tabla 2 (≈ 2.1–2.5·n
evaluaciones de puntos en total). El costo por punto es estable, ≈ 2.2–2.8 µs en la red y en los
cuadrados de 10 000 y 50 000; con 1 000 puntos sube a 4.5 µs porque la proporción de candidatos
procesados es mayor (1.50·n) y pesan los costos fijos. La red (8 792 puntos) es más barata que el
cuadrado de 10 000 no solo por tener menos puntos sino porque descarta más en el primer nivel. Coincide
con la teoría para h ≪ n.

*Por qué SciPy es más rápido.* `scipy.spatial.ConvexHull` no implementa el algoritmo en Python: es
un envoltorio en Cython (módulo `scipy/spatial/_qhull`, compilado como
`_qhull.cp311-win_amd64.pyd` en el paquete instalado) sobre la biblioteca **Qhull** escrita en
**C** (C. B. Barber, The Geometry Center; el paquete incluye `qhull_src/COPYING_QHULL.txt`,
"Qhull, Copyright (c) 1993-2020"; documentación de SciPy: "Convex hulls in N dimensions" usando
Qhull, http://www.qhull.org/). Qhull implementa precisamente **Quickhull** (Barber, Dobkin y
Huhdanpaa 1996), así que los dos programas tienen la misma complejidad; la diferencia es de
constante: Python interpreta cada operación (despacho de bytecode, enteros y tuplas como objetos en
memoria dinámica, listas de punteros), mientras que Qhull trabaja con arreglos contiguos de `double`
en código compilado. En cambio Qhull hace más trabajo por vértice (está hecho para N dimensiones:
construye facetas, vecinos, ecuaciones de hiperplanos y controla errores de punto flotante), lo
que no importa aquí porque h es pequeño.

*Por qué el cociente varía con n.* El cociente sube de 1.7 (1 000 puntos) a 6.5 (10 000) y 9.3
(50 000). Cada llamada a SciPy tiene un costo fijo de ≈ 2 ms (medido con 4 puntos: 2.021 ms):
validar y copiar el arreglo, inicializar Qhull (memoria, opciones; SciPy siempre agrega la opción
"Qt") y construir los arreglos de salida (`vertices`, `simplices`, `neighbors`, `equations`). Con
1 000 puntos ese costo fijo es casi todo el tiempo de SciPy (2.6 ms en total), así que el cociente
es pequeño. Al crecer n domina la parte proporcional a n y el cociente se acerca a la relación
entre el costo por punto en Python y en C: descontando el costo fijo, SciPy gasta ≈ 0.25 µs por
punto con 50 000 puntos frente a ≈ 2.7 µs del código propio (≈ 10×). Se espera que con n aún mayor
el cociente se estabilice alrededor de ese valor, porque ambos crecen igual (casi linealmente).

*Por qué el cociente varía con la distribución.* Con la red el cociente (5.3) es algo menor que con
el cuadrado de tamaño parecido (6.5 con 10 000): la red favorece más al algoritmo propio (descarta
el 93.8 % en el primer nivel y procesa solo 1.06·n candidatos, frente a 1.29·n), mientras que el
tiempo de Qhull depende menos de cuántos puntos se descartan pronto (su costo fijo y su lectura del
arreglo son iguales). Parte de la diferencia también entra dentro de la variabilidad entre
ejecuciones descrita arriba.

## 5. Envolvente de la red (para el mapa y la extensión)

`resultados/envolvente.json` guarda los **14 vértices** en orden antihorario con su `osmid` (un
nodo de la red que cae en ese punto), lat/lon (EPSG:4326, para dibujar en la aplicación) y UTM
entero (EPSG:32618), además de `n_puntos = 8 792` y el área.

- **Área de la envolvente: 1 631.5 km²** (fórmula del zapato sobre los vértices UTM:
  área = |Σ (xᵢ·yᵢ₊₁ − xᵢ₊₁·yᵢ)| / 2, O(h); la suma es positiva porque el orden es antihorario).
  Es una aproximación de la extensión de la red: el departamento del Quindío mide ≈ 1 845 km², pero
  la red de vías para carros casi no llega a la zona montañosa del oriente (cordillera Central), por eso
  la envolvente, aun siendo convexa, cubre menos que el departamento y deja por fuera esa zona.
- Figura `resultados/figuras/r3_envolvente.png`: los 8 792 nodos y el polígono (generada leyendo
  `data/processed/nodos.csv` y `resultados/envolvente.json`). Se ven los cascos urbanos como
  manchas densas, todos lejos del borde, lo que explica el 93.8 % de descartes en el primer nivel.

## 6. Archivos de resultados

| Archivo | Contenido |
|---|---|
| `resultados/r3_envolvente.csv` | Tabla 1: `conjunto,n,vertices,tiempo_propio_ms,tiempo_scipy_ms,cociente` |
| `resultados/r3_niveles.csv` | Tabla 2: `conjunto,n,nivel,candidatos,descartados` |
| `resultados/r3_scipy_costo_fijo.json` | Tiempo de `ConvexHull` con 4 puntos (costo fijo) |
| `resultados/envolvente.json` | Vértices de la envolvente de la red (lat/lon, UTM, osmid), área |
| `resultados/figuras/r3_envolvente.png` | Nodos + envolvente |
| `resultados/figuras/r3_tiempos.png` | Tiempos propio vs SciPy |
