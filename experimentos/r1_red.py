"""R1.1, R1.2 y R1.5 - Pesos, componente fuertemente conexa y grafo procesado.

Lee la red cruda (data/raw/quindio_drive.graphml, descargada el 2026-11-03), asigna velocidad y
tiempo a cada arista, se queda con la componente fuertemente conexa más grande y guarda:
  data/processed/grafo_scc.graphml, nodos.csv, aristas.csv, descarga.json
  resultados/r1_tamano.csv, r1_velocidades.csv, r1_memoria.json
"""
import csv
import json
import shutil
import sys
import time

import networkx as nx
import osmnx as ox

from quindio.config import ARISTAS, GRAFO_RAW, GRAFO_SCC, NODOS, PROCESADO, RAW, RESULTADOS
from quindio.red import a_utm, asignar_pesos, cargar_grafo, estimar_memoria


def escribir_csv(ruta, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)


def tamano_python(adj):
    """Bytes reales del dict de listas de tuplas en CPython (contando cada objeto una vez)."""
    total = sys.getsizeof(adj)
    for u, vecinos in adj.items():
        total += sys.getsizeof(u) + sys.getsizeof(vecinos)
        for t in vecinos:
            total += sys.getsizeof(t) + sum(sys.getsizeof(x) for x in t)
    return total


def matriz_python_medida(V, muestra=1000):
    """Mide una matriz muestra x muestra (listas de listas con None) y escala a V x V."""
    m = [[None] * muestra for _ in range(muestra)]
    b = sys.getsizeof(m) + sum(sys.getsizeof(f) for f in m)
    return b * (V / muestra) ** 2


def main():
    PROCESADO.mkdir(parents=True, exist_ok=True)
    G = ox.load_graphml(GRAFO_RAW)

    # R1.2 pesos (sobre la red completa, para tener más tramos con maxspeed al imputar)
    resumen = asignar_pesos(G)
    escribir_csv(RESULTADOS / "r1_velocidades.csv", resumen)

    # R1.3 componente fuertemente conexa
    C = ox.truncate.largest_component(G, strongly=True)
    assert nx.is_strongly_connected(C)
    ox.save_graphml(C, GRAFO_SCC)
    escribir_csv(RESULTADOS / "r1_tamano.csv", [
        {"red": "Red descargada", "nodos": G.number_of_nodes(), "aristas": G.number_of_edges()},
        {"red": "Componente fuertemente conexa", "nodos": C.number_of_nodes(), "aristas": C.number_of_edges()},
    ])

    # R1.5 nodos.csv
    ids = list(C.nodes)
    lats = [C.nodes[n]["y"] for n in ids]
    lons = [C.nodes[n]["x"] for n in ids]
    xs, ys = a_utm(lats, lons)
    escribir_csv(NODOS, [{"osmid": n, "lat": la, "lon": lo, "x_utm": round(x, 3), "y_utm": round(y, 3)}
                         for n, la, lo, x, y in zip(ids, lats, lons, xs, ys)])

    # aristas.csv: de las aristas paralelas u->v se conserva la de menor tiempo
    mejor = {}
    for u, v, d in C.edges(data=True):
        if (u, v) not in mejor or d["travel_time"] < mejor[(u, v)]["tiempo_s"]:
            mejor[(u, v)] = {"u": u, "v": v, "distancia_m": round(d["length"], 3),
                             "tiempo_s": round(d["travel_time"], 4), "velocidad_kmh": round(d["speed_kph"], 2)}
    escribir_csv(ARISTAS, list(mejor.values()))
    shutil.copy(RAW / "descarga.json", PROCESADO / "descarga.json")

    # R1.1 memoria: estimación con V y E reales + medición del dict que usa el proyecto
    t0 = time.perf_counter()
    adj, _ = cargar_grafo()
    t_carga = time.perf_counter() - t0
    memoria = {
        "supuestos": {
            "matriz_bajo_nivel": "V*V celdas de 8 B (tiempo float32 + distancia float32)",
            "listas_bajo_nivel": "E entradas de 12 B (vecino int32 + tiempo float32 + distancia float32) + V punteros de 8 B",
            "matriz_python": "V listas de V punteros de 8 B + 56 B de cabecera por lista (sin contar los float de las celdas con arista)",
            "listas_python_medido": "dict {nodo: [(vecino, tiempo, distancia), ...]} medido con sys.getsizeof",
            "MB": "10^6 bytes",
        },
        "red_descargada": estimar_memoria(G.number_of_nodes(), G.number_of_edges()),
        "componente": estimar_memoria(C.number_of_nodes(), C.number_of_edges()),
        "aristas_sin_paralelas": len(mejor),
        "aristas_paralelas_descartadas": C.number_of_edges() - len(mejor),
        "listas_python_medido_mb": tamano_python(adj) / 1e6,
        "matriz_python_medida_escalada_mb": matriz_python_medida(C.number_of_nodes()) / 1e6,
        "tiempo_cargar_grafo_s": round(t_carga, 3),
    }
    (RESULTADOS / "r1_memoria.json").write_text(json.dumps(memoria, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(memoria, indent=2, ensure_ascii=False))
    for r in resumen:
        print(r)


if __name__ == "__main__":
    main()
