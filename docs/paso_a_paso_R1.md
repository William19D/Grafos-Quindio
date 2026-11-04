# R1 paso a paso: asociar lugares y calcular pesos

Ejemplos pequeños resueltos a mano. Se reproducen con:

```
cd /c/temp/Grafos-Quindio
PYTHONIOENCODING=utf-8 PYTHONPATH=src .venv/Scripts/python.exe -m quindio.red
```

## 1. Nodo más cercano a un lugar (`red.nodo_mas_cercano`)

Coordenadas ya proyectadas a metros (UTM). En el proyecto real la proyección la hace pyproj
(`red.a_utm`); aquí se usan números redondos para hacer las cuentas a mano.

Nodos de la red:

| Nodo | x (m) | y (m) |
|---|---|---|
| A | 0 | 0 |
| B | 300 | 0 |
| C | 100 | 200 |
| D | 400 | 400 |

Lugar P = (120, 160).

**Pseudocódigo** (el mismo que el docstring de la función):

1. `mejor_nodo <- ninguno`, `mejor_d2 <- infinito`
2. para cada nodo i: `dx <- x_i - x`, `dy <- y_i - y`, `d2 <- dx² + dy²`;
   si `d2 < mejor_d2`, el nodo i pasa a ser el mejor
3. devolver el mejor nodo y `raíz(mejor_d2)`

Se compara `d2` (la distancia al cuadrado) y no la distancia, porque la raíz cuadrada es
creciente: si `d2_a < d2_b` entonces `d_a < d_b`. Así la raíz se saca una sola vez.

**Traza** (una fila por vuelta del bucle):

| Vuelta | Nodo | dx | dy | d2 = dx² + dy² | ¿d2 < mejor_d2? | mejor_nodo | mejor_d2 |
|---|---|---|---|---|---|---|---|
| inicio | — | — | — | — | — | ninguno | ∞ |
| 1 | A | 0 − 120 = −120 | 0 − 160 = −160 | 14 400 + 25 600 = 40 000 | sí (40 000 < ∞) | A | 40 000 |
| 2 | B | 300 − 120 = 180 | 0 − 160 = −160 | 32 400 + 25 600 = 58 000 | no | A | 40 000 |
| 3 | C | 100 − 120 = −20 | 200 − 160 = 40 | 400 + 1 600 = 2 000 | sí | C | 2 000 |
| 4 | D | 400 − 120 = 280 | 400 − 160 = 240 | 78 400 + 57 600 = 136 000 | no | C | 2 000 |

Resultado: nodo **C**, distancia `raíz(2 000) = 44.7 m`. Como 44.7 ≤ 500, el lugar **no** se
marca como lejano (`lejano_500m = False`).

**Invariante**: al terminar la vuelta i, `mejor_nodo` es el más cercano entre los i primeros
nodos. Al terminar las V vueltas es el más cercano de todos. **Costo**: V vueltas con trabajo
constante, Θ(V) por lugar; para L lugares Θ(L·V) (46 × 8 792 ≈ 404 000 vueltas en el proyecto).

`asociar_lugares` repite esto para cada lugar del catálogo y agrega las columnas `nodo`,
`dist_nodo_m` (redondeada a 0.1 m) y `lejano_500m`.

## 2. Velocidad y tiempo de cada arista (`red.asignar_pesos`)

Red de ejemplo (5 aristas):

| Arista | Tipo de vía | Longitud (m) | maxspeed en OSM |
|---|---|---|---|
| 1→2 | secondary | 1 000 | "50" |
| 2→3 | residential | 360 | "20" |
| 3→4 | residential | 360 | "40 km/h" |
| 4→1 | residential | 1 000 | (no tiene) |
| 4→5 | primary_link | 900 | (no tiene) |

### Paso 1: leer `maxspeed` (`parsear_maxspeed`) y agrupar por tipo

`parsear_maxspeed("40 km/h")`: se parte por `|` o `;` (queda un solo pedazo), se pasa a
minúsculas, termina en `km/h` → se quita la unidad → `"40"` → `leer_numero` recorre `4`, `0`
(dígitos de la parte entera) → 40.0. Con `"20 mph"` el factor sería 1.609344 → 32.19 km/h.

| Arista | Velocidad leída (km/h) | Lista de conocidas del tipo, después de esta arista |
|---|---|---|
| 1→2 | 50 | secondary: [50] |
| 2→3 | 20 | residential: [20] |
| 3→4 | 40 | residential: [20, 40] |
| 4→1 | ninguna | residential: [20, 40] |
| 4→5 | ninguna | primary_link: [] |

### Paso 2: velocidad de reemplazo por tipo

| Tipo | Conocidas | Regla | Reemplazo (km/h) |
|---|---|---|---|
| secondary | [50] | media | 50 |
| residential | [20, 40] | media = (20 + 40) / 2 | 30 |
| primary_link | [] | tabla `VELOCIDAD_POR_TIPO` (normativa) | 40 |

### Paso 3: tiempo = longitud / (velocidad / 3.6)

Se divide entre 3.6 para pasar de km/h a m/s; metros ÷ (m/s) = segundos.

| Arista | Velocidad usada | ¿Imputada? | Cuenta | Tiempo (s) |
|---|---|---|---|---|
| 1→2 | 50 | no | 1 000 / (50 / 3.6) = 1 000 / 13.89 | 72.0 |
| 2→3 | 20 | no | 360 / (20 / 3.6) = 360 / 5.56 | 64.8 |
| 3→4 | 40 | no | 360 / (40 / 3.6) = 360 / 11.11 | 32.4 |
| 4→1 | 30 | sí (media residential) | 1 000 / (30 / 3.6) = 1 000 / 8.33 | 120.0 |
| 4→5 | 40 | sí (tabla) | 900 / (40 / 3.6) = 900 / 11.11 | 81.0 |

**Costo**: dos recorridos de las E aristas → O(E) en tiempo y memoria (en la red real
E = 20 157).
