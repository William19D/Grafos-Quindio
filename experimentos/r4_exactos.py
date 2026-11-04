"""R4 punto 1 - Soluciones exactas: fuerza bruta y Held-Karp para k = 5..12.

Partida: Armenia (ARM). Los k lugares se eligen al azar entre TODO el catálogo (todas las
categorías, sin ARM) con random.Random(SEMILLA + k). Cada método se mide con medir_con_limite
(5 repeticiones, mediana, límite de 5 min); al primer "no completada" ese método deja de subir k.
Antes de guardar se verifica que ambos den el mismo costo óptimo y que el recorrido cueste eso.

Además (fuera de lo medido): memoria de Held-Karp con tracemalloc para k = 5..16 y tiempos de
Held-Karp para k = 13..16, para ver mejor la forma O(k²·2^k).

Salidas: resultados/r4_exactos.csv, resultados/r4_memoria.csv, resultados/r4_held_karp_extendido.csv
Uso: PYTHONPATH=src .venv/Scripts/python.exe experimentos/r4_exactos.py   (tarda ~10 min)
"""
import csv
import random
import tracemalloc

from quindio.config import RESULTADOS, SEMILLA
from quindio.medicion import guardar_maquina, medir, medir_con_limite
from quindio.tsp import costo_recorrido, fuerza_bruta, held_karp, leer_matriz, submatriz

PARTIDA = "ARM"
KS = range(5, 13)
KS_EXTRA = range(13, 17)


def instancia(k, ids, matriz):
    """Lugares al azar (semilla SEMILLA + k) y su matriz d con ARM en la posición 0."""
    candidatos = [i for i in ids if i != PARTIDA]
    lugares = random.Random(SEMILLA + k).sample(candidatos, k)
    return lugares, submatriz(matriz, [PARTIDA] + lugares)


def escribir_csv(ruta, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


def texto_recorrido(lugares, recorrido):
    nombres = [PARTIDA] + lugares
    return " -> ".join(nombres[i] for i in recorrido)


def main():
    guardar_maquina()
    ids, matriz = leer_matriz()
    filas = []
    sigue = {"fuerza_bruta": True, "held_karp": True}
    for k in KS:
        lugares, d = instancia(k, ids, matriz)
        fila = {"k": k, "semilla": SEMILLA + k, "lugares": " ".join(lugares)}
        resultados = {}
        for nombre, funcion in (("fuerza_bruta", fuerza_bruta), ("held_karp", held_karp)):
            if not sigue[nombre]:
                fila[f"tiempo_{nombre}_ms"] = ""
                fila[f"costo_{nombre}_s"] = ""
                fila[f"estado_{nombre}"] = "no ejecutada (un k menor no completó)"
                continue
            tiempo_ms, res = medir_con_limite(funcion, d)
            if tiempo_ms is None:
                sigue[nombre] = False
                fila[f"tiempo_{nombre}_ms"] = ""
                fila[f"costo_{nombre}_s"] = ""
                fila[f"estado_{nombre}"] = "no completada"
                print(f"k={k:2d} {nombre}: no completada (> 5 min)", flush=True)
                continue
            costo, recorrido = res
            # verificación: el recorrido es válido y cuesta lo reportado
            assert sorted(recorrido[1:-1]) == list(range(1, k + 1)) and recorrido[0] == recorrido[-1] == 0
            assert abs(costo_recorrido(d, recorrido) - costo) < 1e-6
            resultados[nombre] = res
            fila[f"tiempo_{nombre}_ms"] = round(tiempo_ms, 3)
            fila[f"costo_{nombre}_s"] = round(costo, 2)
            fila[f"estado_{nombre}"] = "completada" + (" (1 repetición, > 1 min)" if tiempo_ms > 60_000 else "")
            print(f"k={k:2d} {nombre}: {tiempo_ms:12.3f} ms  costo {costo:.2f} s", flush=True)
        if len(resultados) == 2:  # verificación cruzada: el mismo óptimo
            assert abs(resultados["fuerza_bruta"][0] - resultados["held_karp"][0]) < 1e-6
            fila["mismo_costo"] = "sí"
        else:
            fila["mismo_costo"] = "solo Held-Karp"
        mejor = resultados.get("held_karp") or resultados.get("fuerza_bruta")
        fila["recorrido_optimo"] = texto_recorrido(lugares, mejor[1]) if mejor else ""
        filas.append(fila)
        escribir_csv(RESULTADOS / "r4_exactos.csv", filas)  # se guarda en cada k por si se corta

    # Memoria de Held-Karp: tamaño de la tabla y pico medido con tracemalloc (no se mide tiempo aquí)
    memoria = []
    for k in list(KS) + list(KS_EXTRA):
        _lugares, d = instancia(k, ids, matriz)
        tracemalloc.start()
        held_karp(d)
        _actual, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        entradas = 2 * k * 2 ** k  # tablas C y padre, 2^k filas × k columnas cada una
        memoria.append({"k": k, "entradas_tablas": entradas, "bytes_estimados_8B": entradas * 8,
                        "pico_tracemalloc_bytes": pico, "pico_tracemalloc_mb": round(pico / 2**20, 3)})
        print(f"memoria k={k:2d}: {entradas} entradas, pico {pico / 2**20:.3f} MB", flush=True)
    escribir_csv(RESULTADOS / "r4_memoria.csv", memoria)

    # Held-Karp más allá de 12 (solo para ver la curva; fuerza bruta ya no completó antes)
    extra = []
    for k in KS_EXTRA:
        _lugares, d = instancia(k, ids, matriz)
        tiempo_ms, (costo, recorrido) = medir(held_karp, d)
        assert abs(costo_recorrido(d, recorrido) - costo) < 1e-6
        extra.append({"k": k, "semilla": SEMILLA + k, "tiempo_held_karp_ms": round(tiempo_ms, 3),
                      "costo_held_karp_s": round(costo, 2)})
        print(f"extra k={k:2d} held_karp: {tiempo_ms:.3f} ms", flush=True)
    escribir_csv(RESULTADOS / "r4_held_karp_extendido.csv", extra)


if __name__ == "__main__":
    main()
