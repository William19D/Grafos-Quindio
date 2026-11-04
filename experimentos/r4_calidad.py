"""R4 puntos 3 y 5 - Calidad de la heurística voraz (vecino más cercano) frente al óptimo.

Para k = 5, 8, 10, 12 se generan 5 instancias por k: partida ARM y k lugares al azar de todo el
catálogo (sin ARM) con random.Random(SEMILLA + 100*k + i), i = 0..4.
brecha % = (costo voraz - costo óptimo Held-Karp) / costo óptimo × 100.
También se mide (5 repeticiones, mediana) el tiempo de cada método en cada instancia.

Punto 5: de esas instancias reales se toma la de menor k con mayor brecha como ejemplo de que la
voraz no encuentra el óptimo; se guarda con los dos recorridos y la traza de la voraz.

Salidas: resultados/r4_calidad.csv, r4_calidad_detalle.csv, r4_voraz_vs_optimo.json
Uso: PYTHONPATH=src .venv/Scripts/python.exe experimentos/r4_calidad.py
"""
import csv
import json
import random
import statistics

from quindio.config import RESULTADOS, SEMILLA
from quindio.medicion import guardar_maquina, medir
from quindio.tsp import costo_recorrido, held_karp, leer_catalogo, leer_matriz, submatriz, vecino_mas_cercano

PARTIDA = "ARM"
KS = [5, 8, 10, 12]
INSTANCIAS = 5


def escribir_csv(ruta, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)


def main():
    guardar_maquina()
    ids, matriz = leer_matriz()
    catalogo = leer_catalogo()
    candidatos = [i for i in ids if i != PARTIDA]
    detalle, resumen, casos = [], [], []
    for k in KS:
        brechas = []
        for i in range(INSTANCIAS):
            semilla = SEMILLA + 100 * k + i
            lugares = random.Random(semilla).sample(candidatos, k)
            nombres = [PARTIDA] + lugares
            d = submatriz(matriz, nombres)
            t_hk, (optimo, rec_hk) = medir(held_karp, d)
            t_nn, (voraz, rec_nn) = medir(vecino_mas_cercano, d)
            # verificación antes de usar los números
            assert abs(costo_recorrido(d, rec_hk) - optimo) < 1e-6
            assert abs(costo_recorrido(d, rec_nn) - voraz) < 1e-6
            assert voraz >= optimo - 1e-6
            brecha = (voraz - optimo) / optimo * 100
            brechas.append(brecha)
            detalle.append({"k": k, "instancia": i, "semilla": semilla, "lugares": " ".join(lugares),
                            "costo_optimo_s": round(optimo, 2), "costo_voraz_s": round(voraz, 2),
                            "brecha_pct": round(brecha, 3),
                            "tiempo_held_karp_ms": round(t_hk, 4), "tiempo_voraz_ms": round(t_nn, 4),
                            "recorrido_optimo": " -> ".join(nombres[j] for j in rec_hk),
                            "recorrido_voraz": " -> ".join(nombres[j] for j in rec_nn)})
            casos.append((k, brecha, nombres, d, optimo, rec_hk, voraz, rec_nn, semilla))
            print(f"k={k:2d} inst {i}: óptimo {optimo:8.1f} s, voraz {voraz:8.1f} s, brecha {brecha:6.2f} %", flush=True)
        resumen.append({"k": k, "instancias": INSTANCIAS,
                        "brecha_promedio_pct": round(statistics.mean(brechas), 2),
                        "brecha_maxima_pct": round(max(brechas), 2),
                        "brecha_minima_pct": round(min(brechas), 2),
                        "instancias_con_optimo": sum(1 for b in brechas if b < 1e-9)})
    escribir_csv(RESULTADOS / "r4_calidad_detalle.csv", detalle)
    escribir_csv(RESULTADOS / "r4_calidad.csv", resumen)

    # Punto 5: ejemplo real donde la voraz falla (menor k; dentro de ese k, la mayor brecha)
    con_brecha = [c for c in casos if c[1] > 1e-9]
    k_min = min(c[0] for c in con_brecha)
    k, brecha, nombres, d, optimo, rec_hk, voraz, rec_nn, semilla = max(
        (c for c in con_brecha if c[0] == k_min), key=lambda c: c[1])
    traza = []
    vecino_mas_cercano(d, traza)
    primer_desvio = next(p for p in range(len(rec_nn)) if rec_nn[p] != rec_hk[p])
    def tramos(rec):
        return [{"desde": nombres[rec[t]], "hacia": nombres[rec[t + 1]],
                 "tiempo_min": round(d[rec[t]][rec[t + 1]] / 60, 1)} for t in range(len(rec) - 1)]
    ejemplo = {
        "k": k, "semilla": semilla, "partida": PARTIDA,
        "lugares": {n: catalogo[n]["nombre"] for n in nombres},
        "indices": {str(j): nombres[j] for j in range(len(nombres))},
        "optimo_held_karp": {"recorrido": [nombres[j] for j in rec_hk], "costo_s": round(optimo, 2),
                             "costo_min": round(optimo / 60, 1), "tramos": tramos(rec_hk)},
        "vecino_mas_cercano": {"recorrido": [nombres[j] for j in rec_nn], "costo_s": round(voraz, 2),
                               "costo_min": round(voraz / 60, 1), "tramos": tramos(rec_nn), "traza": traza},
        "brecha_pct": round(brecha, 2),
        "primer_desvio": {"posicion": primer_desvio, "voraz_elige": nombres[rec_nn[primer_desvio]],
                          "optimo_elige": nombres[rec_hk[primer_desvio]],
                          "desde": nombres[rec_nn[primer_desvio - 1]]},
    }
    (RESULTADOS / "r4_voraz_vs_optimo.json").write_text(json.dumps(ejemplo, indent=2, ensure_ascii=False),
                                                        encoding="utf-8")
    print(json.dumps(ejemplo, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
