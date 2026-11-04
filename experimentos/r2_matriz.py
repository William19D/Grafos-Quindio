"""R2 - Matriz de tiempos entre todos los lugares del catálogo (incluida Armenia).

Se ejecuta dijkstra_cola SIN destino (uno a todos) una vez desde cada lugar y se toma el tiempo
hasta el nodo de cada uno de los demás lugares. Se verifica contra NetworkX antes de guardar y
se mide el tiempo total de construcción (5 repeticiones, mediana).

Salidas: resultados/matriz_tiempos.csv (primera fila y primera columna = ids; celda (i, j) =
segundos de i a j) y resultados/r2_matriz_resumen.json (tiempo de construcción y asimetría).
"""
import csv
import json

import networkx as nx
import pandas as pd

from quindio.config import ARISTAS, LUGARES_NODOS, MATRIZ_TIEMPOS, RESULTADOS
from quindio.dijkstra import dijkstra_cola
from quindio.medicion import guardar_maquina, medir
from quindio.red import cargar_grafo


def construir_matriz(adj, ids, nodos):
    """matriz[i][j] = segundos del lugar ids[i] al lugar ids[j]. Un Dijkstra uno-a-todos por fila."""
    matriz = []
    for i in range(len(ids)):
        distancias, _predecesores, _explorados = dijkstra_cola(adj, nodos[i])
        fila = []
        for j in range(len(ids)):
            fila.append(distancias[nodos[j]])
        matriz.append(fila)
    return matriz


def main():
    guardar_maquina()
    adj, _ = cargar_grafo()
    lugares = pd.read_csv(LUGARES_NODOS)
    ids = lugares["id"].tolist()
    nodos = lugares["nodo"].tolist()

    ms, matriz = medir(construir_matriz, adj, ids, nodos)

    # Verificación contra NetworkX (solo para comprobar)
    aristas = pd.read_csv(ARISTAS)
    G = nx.MultiDiGraph()
    G.add_weighted_edges_from(zip(aristas["u"], aristas["v"], aristas["tiempo_s"]), weight="tiempo_s")
    dif_max_nx = 0.0
    for i, origen in enumerate(nodos):
        ref = nx.single_source_dijkstra_path_length(G, origen, weight="tiempo_s")
        for j, destino in enumerate(nodos):
            dif_max_nx = max(dif_max_nx, abs(matriz[i][j] - ref[destino]))
    assert dif_max_nx < 1e-6, dif_max_nx

    with open(MATRIZ_TIEMPOS, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id"] + ids)
        for i, id_i in enumerate(ids):
            w.writerow([id_i] + [round(t, 2) for t in matriz[i]])

    # Asimetría |t_ij - t_ji|
    peor = (0.0, None, None)
    suma, cuenta, relativa_max = 0.0, 0, 0.0
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            dif = abs(matriz[i][j] - matriz[j][i])
            suma, cuenta = suma + dif, cuenta + 1
            if matriz[i][j] > 0:
                relativa_max = max(relativa_max, dif / max(matriz[i][j], matriz[j][i]))
            if dif > peor[0]:
                peor = (dif, ids[i], ids[j])
    i, j = ids.index(peor[1]), ids.index(peor[2])
    resumen = {
        "lugares": len(ids),
        "dijkstras_uno_a_todos": len(ids),
        "tiempo_construccion_ms": round(ms, 1),
        "tiempo_por_fila_ms": round(ms / len(ids), 2),
        "asimetria_max_s": round(peor[0], 2),
        "par_asimetria_max": f"{peor[1]} <-> {peor[2]}",
        "t_ida_s": round(matriz[i][j], 2),
        "t_vuelta_s": round(matriz[j][i], 2),
        "asimetria_media_s": round(suma / cuenta, 2),
        "asimetria_relativa_max": round(relativa_max, 4),
        "pares_distintos": cuenta,
        "tiempo_max_s": round(max(max(f) for f in matriz), 2),
        "dif_max_vs_networkx_s": dif_max_nx,
    }
    (RESULTADOS / "r2_matriz_resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False),
                                                      encoding="utf-8")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
