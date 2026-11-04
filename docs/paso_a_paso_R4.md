# R4 paso a paso: el viajero (TSP) asimétrico en una matriz pequeña

Se reproduce con:

```
cd /c/temp/Grafos-Quindio
PYTHONIOENCODING=utf-8 PYTHONPATH=src .venv/Scripts/python.exe -m quindio.tsp
```

## La matriz

Partida = lugar **0**; hay que visitar **1, 2 y 3** (k = 3) y volver a 0. Los tiempos están en
minutos para que las cuentas sean fáciles. Fila = desde, columna = hacia. Es **asimétrica**:
por ejemplo d(0,2) = 9 pero d(2,0) = 15. Es la misma matriz de `tests/test_r4.py`.

| desde \ hacia | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **0** | 0 | 2 | 9 | 10 |
| **1** | 1 | 0 | 6 | 4 |
| **2** | 15 | 7 | 0 | 8 |
| **3** | 6 | 3 | 12 | 0 |

Pregunta: ¿en qué orden visitar 1, 2 y 3 para que el tiempo total (con el regreso) sea mínimo?

---

## 1. Generador de permutaciones (algoritmo de Heap)

La fuerza bruta necesita todas las órdenes de [1, 2, 3]. No se usa `itertools`: se escribe el
algoritmo de Heap (B. R. Heap, 1963), que pasa de una permutación a la siguiente con **un
solo intercambio**. Un contador `c[i]` por posición funciona como un odómetro.

Pseudocódigo (versión iterativa):

1. `A ← elementos`, `c[0..n-1] ← 0`, entregar A.
2. `i ← 1`.
3. Mientras `i < n`:
   - 3a. Si `c[i] < i`: si i es par, intercambiar `A[0]` y `A[i]`; si es impar, intercambiar
     `A[c[i]]` y `A[i]`. Entregar A. `c[i] ← c[i] + 1`; `i ← 1`.
   - 3b. Si no: `c[i] ← 0`; `i ← i + 1`.

| Paso | i | c antes | Intercambio | A entregado |
|---|---|---|---|---|
| inicio | – | [0,0,0] | – | [1, 2, 3] |
| 1 | 1 (impar) | c[1]=0 < 1 | A[c[1]]=A[0] ↔ A[1] | [2, 1, 3] |
| 2 | 1 | c[1]=1, no < 1 → c[1]=0, i=2 | – | – |
| 3 | 2 (par) | c[2]=0 < 2 | A[0] ↔ A[2] | [3, 1, 2] |
| 4 | 1 (impar) | c[1]=0 < 1 | A[0] ↔ A[1] | [1, 3, 2] |
| 5 | 1 → 2 | c[1]=1 → reinicio, i=2; c[2]=1 < 2 | A[0] ↔ A[2] | [2, 3, 1] |
| 6 | 1 (impar) | c[1]=0 < 1 | A[0] ↔ A[1] | [3, 2, 1] |
| fin | 1 → 2 → 3 | c[1]=1 → 0; c[2]=2 → 0; i = 3 = n | – | termina |

Salen las 3! = 6 permutaciones, cada una una sola vez.

---

## 2. Fuerza bruta

Para cada permutación P se calcula `d(0,P[0]) + d(P[0],P[1]) + d(P[1],P[2]) + d(P[2],0)` y se
guarda la menor (con `<` estricto: en un empate se queda la primera que apareció).

| # | Recorrido | Cuenta | Costo | ¿Mejor? |
|---|---|---|---|---|
| 1 | 0-1-2-3-0 | 2 + 6 + 8 + 6 | 22 | sí (primero) |
| 2 | 0-2-1-3-0 | 9 + 7 + 4 + 6 | 26 | no |
| 3 | 0-3-1-2-0 | 10 + 3 + 6 + 15 | 34 | no |
| 4 | 0-1-3-2-0 | 2 + 4 + 12 + 15 | 33 | no |
| 5 | 0-2-3-1-0 | 9 + 8 + 3 + 1 | **21** | **sí** |
| 6 | 0-3-2-1-0 | 10 + 12 + 7 + 1 | 30 | no |

**Óptimo: 21 con 0 → 2 → 3 → 1 → 0.** Trabajo: k! = 6 permutaciones × k + 1 = 4 sumas.
Con k = 12 serían 479 001 600 permutaciones: por eso la fuerza bruta deja de ser práctica.

---

## 3. Held-Karp (programación dinámica)

**Subestructura óptima.** Si el mejor camino que sale de 0, visita todo S y termina en j pasa
justo antes por i, entonces el tramo de 0 a i (visitando S \ {j}) también tiene que ser el mejor
posible: si hubiera uno más corto, se cambiaría y el camino a j mejoraría, contradicción.

**Recurrencia.** C(S, j) = tiempo mínimo de salir de 0, visitar exactamente S y terminar en j:

- Caso base: C({j}, j) = d(0, j)
- C(S, j) = min sobre i ∈ S \ {j} de [ C(S \ {j}, i) + d(i, j) ]
- Respuesta: min sobre j de [ C({1,2,3}, j) + d(j, 0) ]

**Máscaras.** S se guarda como un número binario: bit 0 = lugar 1, bit 1 = lugar 2, bit 2 =
lugar 3. Así {1,3} = 101₂ = 5. La tabla es una lista `C[mascara][j-1]`. Se llena en orden
creciente de máscara; un subconjunto siempre tiene máscara menor que el conjunto que lo
contiene, así que cuando se necesita `C[S \ {j}]` ya está calculado.

Pseudocódigo:

1. Si k = 0, devolver (0, [0, 0]).
2. Crear `C` y `padre` de 2^k = 8 filas × k = 3 columnas (∞ / -1).
3. Caso base: `C[{j}][j] = d(0, j)`, `padre = 0`.
4. Para cada máscara con 2 o más lugares y cada j dentro: 4a. `sin_j = máscara sin j`;
   4b. probar cada i de `sin_j`, quedarse con el menor `C[sin_j][i] + d(i, j)` y guardar ese i en `padre`.
5. Cerrar el ciclo: el menor `C[N][j] + d(j, 0)`.
6. Reconstruir con `padre` hacia atrás.

### Llenado de la tabla (orden de la traza)

| Máscara | S | j | Candidatos (i: C(S\{j}, i) + d(i, j)) | C(S, j) | padre |
|---|---|---|---|---|---|
| 001 | {1} | 1 | caso base d(0,1) | 2 | 0 |
| 010 | {2} | 2 | caso base d(0,2) | 9 | 0 |
| 100 | {3} | 3 | caso base d(0,3) | 10 | 0 |
| 011 | {1,2} | 1 | i=2: 9 + 7 = 16 | 16 | 2 |
| 011 | {1,2} | 2 | i=1: 2 + 6 = 8 | 8 | 1 |
| 101 | {1,3} | 1 | i=3: 10 + 3 = 13 | 13 | 3 |
| 101 | {1,3} | 3 | i=1: 2 + 4 = 6 | 6 | 1 |
| 110 | {2,3} | 2 | i=3: 10 + 12 = 22 | 22 | 3 |
| 110 | {2,3} | 3 | i=2: 9 + 8 = 17 | 17 | 2 |
| 111 | {1,2,3} | 1 | i=2: 22 + 7 = 29 ; i=3: 17 + 3 = **20** | 20 | 3 |
| 111 | {1,2,3} | 2 | i=1: 13 + 6 = 19 ; i=3: 6 + 12 = **18** | 18 | 3 |
| 111 | {1,2,3} | 3 | i=1: 16 + 4 = 20 ; i=2: 8 + 8 = **16** | 16 | 2 |

### Cierre del ciclo

| j | C({1,2,3}, j) + d(j, 0) | Total |
|---|---|---|
| 1 | 20 + 1 | **21** ← mínimo |
| 2 | 18 + 15 | 33 |
| 3 | 16 + 6 | 22 |

### Reconstrucción (paso 6)

| Máscara actual | Lugar actual | padre[máscara][lugar] | Máscara sin el lugar |
|---|---|---|---|
| 111 | 1 | 3 | 110 |
| 110 | 3 | 2 | 010 |
| 010 | 2 | 0 (fin) | 000 |

Lista al revés: [1, 3, 2] → invertida: [2, 3, 1] → **recorrido 0-2-3-1-0, costo 21**, igual que
la fuerza bruta. Trabajo: k·2^k = 24 casillas, cada una con a lo sumo k candidatos → O(k²·2^k).

---

## 4. Heurística voraz: vecino más cercano

Desde el lugar actual se va al **no visitado más cercano**; al final se regresa a 0.

| Paso | Desde | Opciones (lugar: tiempo) | Elige | Acumulado |
|---|---|---|---|---|
| 1 | 0 | 1: **2**, 2: 9, 3: 10 | 1 | 2 |
| 2 | 1 | 2: 6, 3: **4** | 3 | 6 |
| 3 | 3 | 2: **12** | 2 | 18 |
| regreso | 2 | 0: 15 | 0 | **33** |

**Voraz: 33 con 0-1-3-2-0. Óptimo: 21 con 0-2-3-1-0** (la voraz es 57 % peor).

¿Por qué falla? En el paso 1 ir a 1 parece lo mejor (2 min), pero esa decisión deja al lugar 2
para el final, y desde 2 regresar a 0 cuesta 15. La decisión local no mira **el costo de
regresar** ni cómo quedan los lugares restantes. El óptimo empieza por el tramo "caro" 0 → 2
(9 min) y a cambio termina con 1 → 0 (1 min).

En cambio en **Dijkstra** la elección voraz sí es segura: con pesos no negativos, el nodo no
explorado de menor distancia ya no puede mejorar por ningún otro camino (cualquier otro pasa por
un nodo con distancia mayor o igual y solo suma), así que su distancia es definitiva
(propiedad de elección voraz + subestructura óptima, Cormen et al. 2009, teorema 24.6). En el
TSP no existe una propiedad así: el valor de una decisión depende de todas las que vienen
después, y el problema es NP-difícil.

---

## 5. Ajuste del itinerario a 11 h (idea)

`ajustar_a_jornada` repite: si la jornada (visitas + desplazamientos con el orden óptimo) pasa de
11 h, prueba quitar cada atractivo, recalcula el óptimo con Held-Karp y quita el que más acorta
el día. Con los datos reales (`experimentos/r4_itinerario.py`): 7 atractivos → 12,26 h (no cabe);
sin el Jardín Botánico → 9,53 h (cabe).
