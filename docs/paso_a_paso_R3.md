# R3 paso a paso — QuickHull sobre un ejemplo pequeño

Código: `src/quindio/envolvente.py`. Para ver esta misma traza en consola:

```
cd C:\temp\Grafos-Quindio
set PYTHONPATH=src
.venv\Scripts\python.exe -m quindio.envolvente
```

## 1. Datos

14 puntos enteros (metros). `(4,0)` aparece dos veces y `(2,0)` está sobre el lado inferior.

```
(0,0) (4,0) (2,0) (6,1) (7,4) (5,6) (2,5) (0,3) (3,2) (4,4) (1,1) (5,2) (2,3) (4,0)
```

`preparar_puntos` redondea (ya son enteros) y quita el `(4,0)` repetido → **13 puntos**.

```
 y
 6 |                 (5,6)
 5 |    (2,5)
 4 |                (4,4)        (7,4)
 3 | (0,3)  (2,3)
 2 |          (3,2)   (5,2)
 1 |    (1,1)                (6,1)
 0 | (0,0)  (2,0)   (4,0)
   +----------------------------------- x
     0   1   2   3   4   5   6   7
```

## 2. Herramienta: el giro con enteros

`orientacion(a, b, c) = (bx-ax)(cy-ay) - (by-ay)(cx-ax)`

- `> 0`: c está a la izquierda de a→b; `< 0`: a la derecha; `0`: alineados.
- Su valor es `|ab| × distancia(c, recta ab)`: con `|ab|` fijo, sirve para comparar distancias
  sin raíces cuadradas ni divisiones (todo exacto con enteros).

## 3. Paso 2 y 3 — extremos y división inicial

- A = menor (x, y) = **(0,0)**; B = mayor (x, y) = **(7,4)**. Ambos son vértices seguros.
- Para cada punto p: `orientacion(A, B, p) = 7·py − 4·px`.

| Punto | 7y − 4x | Lado |
|---|---|---|
| (4,0) | −16 | abajo (derecha de A→B) |
| (2,0) | −8 | abajo |
| (6,1) | −17 | abajo |
| (5,2) | −6 | abajo |
| (5,6) | 22 | arriba (izquierda de A→B) |
| (2,5) | 27 | arriba |
| (0,3) | 21 | arriba |
| (3,2) | 2 | arriba |
| (4,4) | 12 | arriba |
| (1,1) | 3 | arriba |
| (2,3) | 13 | arriba |

Pila inicial (el tope es la última fila): `(B→A, arriba)`, `(A→B, abajo)`.

## 4. Iteraciones de la pila

En cada tarea (P, Q, candidatos) los candidatos están a la derecha de P→Q. La "distancia" es
`orientacion(Q, P, x)`; C es el mayor. Luego cada candidato va a *fuera de P→C*, *fuera de C→Q*
o se descarta (dentro del triángulo P-C-Q o sobre sus lados).

| It. | Nivel | Lado P→Q | Candidatos (distancia) | C | Fuera P→C | Fuera C→Q | Descartados |
|---|---|---|---|---|---|---|---|
| 1 | 1 | (0,0)→(7,4) | (4,0)=16, (2,0)=8, (6,1)=**17**, (5,2)=6 | (6,1) | (4,0), (2,0) | — | (5,2) |
| 2 | 2 | (0,0)→(6,1) | (4,0)=**4**, (2,0)=2 | (4,0) | — | — | (2,0) (alineado en el lado (0,0)–(4,0)) |
| 3 | 3 | (0,0)→(4,0) | ninguno | | | | lado definitivo: vértice **(0,0)** |
| 4 | 3 | (4,0)→(6,1) | ninguno | | | | lado definitivo: vértice **(4,0)** |
| 5 | 2 | (6,1)→(7,4) | ninguno | | | | lado definitivo: vértice **(6,1)** |
| 6 | 1 | (7,4)→(0,0) | (5,6)=22, (2,5)=**27**, (0,3)=21, (3,2)=2, (4,4)=12, (1,1)=3, (2,3)=13 | (2,5) | (5,6) | (0,3) | (3,2), (4,4), (1,1), (2,3) |
| 7 | 2 | (7,4)→(2,5) | (5,6) | (5,6) | — | — | — |
| 8 | 3 | (7,4)→(5,6) | ninguno | | | | lado definitivo: vértice **(7,4)** |
| 9 | 3 | (5,6)→(2,5) | ninguno | | | | lado definitivo: vértice **(5,6)** |
| 10 | 2 | (2,5)→(0,0) | (0,3) | (0,3) | — | — | — |
| 11 | 3 | (2,5)→(0,3) | ninguno | | | | lado definitivo: vértice **(2,5)** |
| 12 | 3 | (0,3)→(0,0) | ninguno | | | | lado definitivo: vértice **(0,3)** |

Cálculos de la iteración 1 (cómo se reparten los candidatos):

- Fuera de P→C con P=(0,0), C=(6,1): `orientacion(C, P, x) = x − 6y > 0`.
  (4,0): 4 ✔; (2,0): 2 ✔; (5,2): −7 ✘.
- Fuera de C→Q con Q=(7,4): `orientacion(Q, C, x) = 3x − y − 17 > 0`. (5,2): −4 ✘ → descartado.

Cálculos de la iteración 6:

- Fuera de P→C con P=(7,4), C=(2,5): `x + 5y − 27 > 0`. Solo (5,6): 8 ✔.
- Fuera de C→Q con Q=(0,0): `orientacion(Q, C, x) = 2y − 5x > 0`. Solo (0,3): 6 ✔.
- Los otros 4 están dentro del triángulo (7,4)-(2,5)-(0,0): se descartan sin volver a mirarlos.

Lo que muestra el ejemplo: en el primer nivel ya se descartan 5 de los 11 candidatos; en la red
del Quindío se descarta el 93.8 % en el primer nivel (ver `resultados/r3_niveles.csv`).

## 5. Resultado

Los vértices salen en el orden en que se cierran los lados (iteraciones 3, 4, 5, 8, 9, 11, 12):

```
(0,0) → (4,0) → (6,1) → (7,4) → (5,6) → (2,5) → (0,3)    (antihorario, 7 vértices)
```

`(2,0)` no es vértice: está alineado sobre el lado (0,0)–(4,0). SciPy da los mismos 7 vértices.

## 6. Área con la fórmula del zapato

| i | (x_i, y_i) | (x_i+1, y_i+1) | x_i·y_i+1 − x_i+1·y_i |
|---|---|---|---|
| 1 | (0,0) | (4,0) | 0 |
| 2 | (4,0) | (6,1) | 4 |
| 3 | (6,1) | (7,4) | 17 |
| 4 | (7,4) | (5,6) | 22 |
| 5 | (5,6) | (2,5) | 13 |
| 6 | (2,5) | (0,3) | 6 |
| 7 | (0,3) | (0,0) | 0 |
| | | **Suma** | **62** |

Área = 62 / 2 = **31 m²** (la suma es positiva porque el orden es antihorario).

## 7. Caso de empate (por qué se desempata por proyección)

Puntos `(0,0),(10,0),(5,5),(2,5),(8,5),(4,2)`. En el lado (10,0)→(0,0) los tres puntos de
arriba están a la misma distancia (y = 5). Si se tomara el primero de la lista, (5,5), saldría
como vértice aunque está alineado entre (2,5) y (8,5). Por eso, en empate se elige el más
cercano a P = (10,0) según `proyeccion(P, Q, x)`: C = (8,5). En la siguiente tarea (8,5)→(0,0)
el más lejano es (2,5) y (5,5) queda alineado sobre el lado (8,5)–(2,5) y se descarta.
Resultado: `(0,0),(10,0),(8,5),(2,5)` (prueba `test_empate_en_el_punto_mas_lejano`).
