# R2 paso a paso: Dijkstra en un grafo pequeño

Se reproduce con:

```
cd /c/temp/Grafos-Quindio
PYTHONIOENCODING=utf-8 PYTHONPATH=src .venv/Scripts/python.exe -m quindio.dijkstra
PYTHONIOENCODING=utf-8 PYTHONPATH=src .venv/Scripts/python.exe -m quindio.estructuras
```

## El grafo

Grafo dirigido de 6 nodos; el peso es el tiempo (en minutos, para que las cuentas sean fáciles).
Es el mismo grafo de `tests/test_r2.py`.

| Arista | Peso | Arista | Peso |
|---|---|---|---|
| A → B | 4 | C → E | 10 |
| A → C | 2 | D → E | 2 |
| C → B | 1 | D → F | 6 |
| B → D | 5 | E → F | 2 |
| C → D | 8 | F → A | 3 |

Pregunta: ¿tiempo mínimo y ruta de **A** a **F**?

## Idea y pseudocódigo

Dijkstra mantiene una distancia tentativa `d[v]` para cada nodo. En cada paso toma el nodo
**no explorado** con menor `d`, lo marca como **explorado** (su distancia ya es definitiva) y
**relaja** sus aristas: si `d[u] + peso(u, v) < d[v]`, entonces `d[v]` baja y `pred[v] = u`.

1. `d[v] = ∞` y `pred[v] = ninguno` para todo v; `d[origen] = 0`.
2. Repetir: elegir el no explorado u de menor d (versión lineal: recorriendo todos; versión con
   cola: `extraer_minimo` del montículo). Si u es el destino, parar. Relajar las aristas de u.
3. Reconstruir la ruta caminando hacia atrás por `pred` desde el destino.

## Versión lineal: tabla de estado por iteración

En cada iteración se recorren **todos** los nodos no explorados para ver cuál tiene la menor d
(columna "candidatos"). En negrita, el valor que cambió por una relajación.

| Iter. | Candidatos (no explorados con d finita) | Elegido | Relajaciones | d[A] | d[B] | d[C] | d[D] | d[E] | d[F] |
|---|---|---|---|---|---|---|---|---|---|
| 0 | — | — | inicialización | 0 | ∞ | ∞ | ∞ | ∞ | ∞ |
| 1 | A(0) | A | A→B: ∞→4; A→C: ∞→2 | 0 | **4** | **2** | ∞ | ∞ | ∞ |
| 2 | B(4), C(2) | C | C→B: 4→3; C→D: ∞→10; C→E: ∞→12 | 0 | **3** | 2 | **10** | **12** | ∞ |
| 3 | B(3), D(10), E(12) | B | B→D: 10→8 | 0 | 3 | 2 | **8** | 12 | ∞ |
| 4 | D(8), E(12) | D | D→E: 12→10; D→F: ∞→14 | 0 | 3 | 2 | 8 | **10** | **14** |
| 5 | E(10), F(14) | E | E→F: 14→12 | 0 | 3 | 2 | 8 | 10 | **12** |
| 6 | F(12) | F = destino → **parar** | — | 0 | 3 | 2 | 8 | 10 | 12 |

Predecesores al final: `pred[C] = A`, `pred[B] = C`, `pred[D] = B`, `pred[E] = D`, `pred[F] = E`.

**Reconstrucción de la ruta**: F → pred E → pred D → pred B → pred C → pred A (origen). Al revés:
**A – C – B – D – E – F**, tiempo **12** = 2 + 1 + 5 + 2 + 2. Nodos explorados: **6**.

Observaciones para la sustentación:

- La arista directa A→B (4) no se usa: por C se llega en 2 + 1 = 3.
- En la iteración 2, C→D deja d[D] = 10, pero en la 3 el camino por B lo baja a 8. Por eso no se
  puede dar por definitivo un nodo apenas se descubre, solo cuando es el mínimo.
- Si la pregunta fuera A → B, el algoritmo pararía en la iteración 3 con 3 nodos explorados
  (A, C, B) y no tocaría D, E ni F.

## Versión con cola de prioridad (montículo propio, inserción perezosa)

La cola guarda pares (d, nodo). Cuando una distancia mejora, **no** se busca el par viejo: se
inserta uno nuevo. El viejo queda en la cola y, cuando sale, el nodo ya está explorado: es
**obsoleto** y se descarta sin contarlo. El contenido de la cola se muestra tal como queda en
el arreglo del montículo (`datos[0]` es siempre el mínimo).

| Paso | Sale de la cola | ¿Qué se hace? | Inserciones | Cola después (arreglo del montículo) |
|---|---|---|---|---|
| 0 | — | inicialización | (0, A) | [(0, A)] |
| 1 | (0, A) | explora A (1) | (4, B), (2, C) | [(2, C), (4, B)] |
| 2 | (2, C) | explora C (2) | (3, B), (10, D), (12, E) | [(3, B), (4, B), (10, D), (12, E)] |
| 3 | (3, B) | explora B (3) | (8, D) | [(4, B), (8, D), (10, D), (12, E)] |
| 4 | (4, B) | **obsoleta** (B ya explorado): descartar | — | [(8, D), (12, E), (10, D)] |
| 5 | (8, D) | explora D (4) | (10, E), (14, F) | [(10, D), (12, E), (10, E), (14, F)] |
| 6 | (10, D) | **obsoleta**: descartar | — | [(10, E), (12, E), (14, F)] |
| 7 | (10, E) | explora E (5) | (12, F) | [(12, E), (14, F), (12, F)] |
| 8 | (12, E) | **obsoleta**: descartar | — | [(12, F), (14, F)] |
| 9 | (12, F) | explora F (6) = destino → **parar** | — | [(14, F)] |

Mismo resultado: tiempo 12, ruta A – C – B – D – E – F, 6 nodos explorados (las 3 entradas
obsoletas no cuentan). La entrada (14, F) se queda en la cola sin usarse.

### Cómo trabaja el montículo (paso 2 de la tabla)

Antes de las inserciones del paso 2 la cola es [(4, B)] (acaba de salir (2, C)).

1. `insertar(3, B)`: se pone al final → [(4, B), (3, B)]. **subir(1)**: padre = (1 − 1) // 2 = 0;
   3 < 4 → intercambiar → [(3, B), (4, B)].
2. `insertar(10, D)`: al final → [(3, B), (4, B), (10, D)]. subir(2): padre 0; 10 < 3 no → queda.
3. `insertar(12, E)`: al final, posición 3. subir(3): padre = 1; 12 < 4 no → queda.
   Resultado [(3, B), (4, B), (10, D), (12, E)].

Y `extraer_minimo` del paso 3: se guarda la raíz (3, B); el último (12, E) pasa a la raíz →
[(12, E), (4, B), (10, D)]; **bajar(0)**: hijos en 1 (4) y 2 (10), el menor es 4 < 12 →
intercambiar → [(4, B), (12, E), (10, D)]; en la posición 1 no hay hijos (3 y 4 no existen) →
fin. Luego se inserta (8, D): al final, posición 3, padre 1 (12): 8 < 12 → sube →
[(4, B), (8, D), (10, D), (12, E)]; padre 0 (4): 8 < 4 no → fin.

Cada `subir` o `bajar` recorre a lo sumo la altura del árbol, ⌊log₂ n⌋ niveles: por eso
insertar y extraer cuestan O(log n) (Cormen et al. 2009, secc. 6.1 y 6.5).

## Uno a todos (para la matriz de tiempos)

`dijkstra_cola(adj, "A")` sin destino no para en F: sigue hasta vaciar la cola y devuelve
d = {A: 0, B: 3, C: 2, D: 8, E: 10, F: 12}. La matriz de tiempos se arma corriendo esto una vez
desde cada lugar y leyendo la distancia a los nodos de los demás lugares.

## Por qué es correcto (resumen para exponer)

- **Invariante**: cada vez que un nodo u se marca explorado, `d[u]` es el tiempo mínimo real
  δ(origen, u) (Cormen et al. 2009, teorema 24.6).
- **Por qué vale**: si existiera un camino más corto hasta u, tendría que salir del conjunto de
  explorados por alguna arista hacia un nodo y no explorado; con pesos **no negativos** el
  tramo de y a u no resta, así que d[y] ≤ longitud de ese camino < d[u], y el algoritmo habría
  elegido a y antes que a u. Contradicción.
- **Parar al sacar el destino**: por el invariante, en ese momento su distancia ya es la
  definitiva; seguir no la puede cambiar.
- **Pesos negativos**: si un peso fuera negativo, el argumento anterior falla (un camino
  podría "abaratarse" después de pasar por y). Aquí los pesos son tiempos de viaje > 0.
