"""R2 - Mide las dos versiones de Dijkstra con pares de lugares del catálogo.

Pares (semilla config.SEMILLA = 2026):
  - 10 pares "cercanos": ambos lugares del mismo municipio (nodos distintos), elegidos al azar
    entre todos los pares ordenados del mismo municipio. Se miden con las dos versiones.
  - 15 pares al azar entre lugares de municipios distintos. Solo con la versión con cola.
Primero se verifica cada par (lineal = cola = NetworkX) y después se mide (5 repeticiones, mediana).

Salidas: resultados/r2_dijkstra.csv, r2_verificacion.csv, r2_cociente.csv, r2_cociente_pares.csv.
"""
import math
import random
import statistics

import networkx as nx
import pandas as pd

from quindio.config import ARISTAS, LUGARES_NODOS, RESULTADOS, SEMILLA
from quindio.dijkstra import dijkstra_cola, dijkstra_lineal
from quindio.medicion import guardar_maquina, medir, medir_con_limite
from quindio.red import cargar_grafo

N_CERCANOS = 10
N_LEJANOS = 15
TOLERANCIA_S = 1e-6


def elegir_pares(lugares):
    """Devuelve (cercanos, otros): listas de pares (id_origen, id_destino)."""
    filas = lugares.to_dict("records")
    mismo_municipio, distinto_municipio = [], []
    for a in filas:
        for b in filas:
            if a["id"] == b["id"] or a["nodo"] == b["nodo"]:
                continue
            if a["municipio"] == b["municipio"]:
                mismo_municipio.append((a["id"], b["id"]))
            else:
                distinto_municipio.append((a["id"], b["id"]))
    rnd = random.Random(SEMILLA)
    return rnd.sample(mismo_municipio, N_CERCANOS), rnd.sample(distinto_municipio, N_LEJANOS)


def main():
    guardar_maquina()
    adj, _ = cargar_grafo()
    lugares = pd.read_csv(LUGARES_NODOS)
    nodo_de = dict(zip(lugares["id"], lugares["nodo"]))
    municipio_de = dict(zip(lugares["id"], lugares["municipio"]))
    cercanos, otros = elegir_pares(lugares)
    pares = [(o, d, "cercano") for o, d in cercanos] + [(o, d, "otro") for o, d in otros]

    # --- 1. Verificación (antes de medir): cola = lineal = NetworkX
    aristas = pd.read_csv(ARISTAS)
    G = nx.MultiDiGraph()
    G.add_weighted_edges_from(zip(aristas["u"], aristas["v"], aristas["tiempo_s"]), weight="tiempo_s")
    verificacion = []
    for o, d, tipo in pares:
        t_cola, ruta, _ = dijkstra_cola(adj, nodo_de[o], nodo_de[d])
        t_nx = nx.dijkstra_path_length(G, nodo_de[o], nodo_de[d], weight="tiempo_s")
        t_lin = dijkstra_lineal(adj, nodo_de[o], nodo_de[d])[0] if tipo == "cercano" else math.nan
        ok = abs(t_cola - t_nx) < TOLERANCIA_S and (tipo != "cercano" or abs(t_lin - t_cola) < TOLERANCIA_S)
        verificacion.append({"origen": o, "destino": d, "tipo_par": tipo, "tiempo_cola_s": round(t_cola, 4),
                             "tiempo_lineal_s": round(t_lin, 4), "tiempo_networkx_s": round(t_nx, 4),
                             "dif_max_s": max(abs(t_cola - t_nx), 0 if math.isnan(t_lin) else abs(t_lin - t_cola)),
                             "coincide": ok})
        assert ok, f"{o}->{d}: cola={t_cola} lineal={t_lin} networkx={t_nx}"
    pd.DataFrame(verificacion).to_csv(RESULTADOS / "r2_verificacion.csv", index=False)
    print(f"Verificación OK en {len(pares)} pares")

    # --- 2. Medición (solo el algoritmo; 5 repeticiones, mediana)
    filas = []
    for o, d, tipo in pares:
        no, nd = nodo_de[o], nodo_de[d]
        versiones = [("cola_prioridad", dijkstra_cola)]
        if tipo == "cercano":
            versiones.append(("lineal", dijkstra_lineal))
        for nombre, funcion in versiones:
            if nombre == "lineal":
                ms, res = medir_con_limite(funcion, adj, no, nd)  # límite de 5 min
            else:
                ms, res = medir(funcion, adj, no, nd)
            fila = {"origen": o, "destino": d, "version": nombre,
                    "tiempo_viaje_s": None, "nodos_explorados": None, "tiempo_ms": None,
                    "nodo_origen": no, "nodo_destino": nd, "nodos_ruta": None, "tipo_par": tipo,
                    "municipio_origen": municipio_de[o], "municipio_destino": municipio_de[d],
                    "completada": ms is not None}
            if ms is not None:
                tiempo, ruta, explorados = res
                fila.update(tiempo_viaje_s=round(tiempo, 2), nodos_explorados=explorados,
                            tiempo_ms=round(ms, 3), nodos_ruta=len(ruta))
            filas.append(fila)
            print(f"{o}->{d} {nombre:15s} {fila['tiempo_viaje_s']} s  explorados={fila['nodos_explorados']}  "
                  f"{fila['tiempo_ms']} ms", flush=True)
    tabla = pd.DataFrame(filas)
    tabla.to_csv(RESULTADOS / "r2_dijkstra.csv", index=False)

    # --- 3. Cociente lineal / cola en los pares medidos con ambas
    lin = tabla[tabla["version"] == "lineal"].set_index(["origen", "destino"])
    cola = tabla[tabla["version"] == "cola_prioridad"].set_index(["origen", "destino"])
    comunes = lin.index[lin["completada"]]
    pares_cociente = pd.DataFrame({
        "origen": [i[0] for i in comunes], "destino": [i[1] for i in comunes],
        "nodos_explorados": [lin.loc[i, "nodos_explorados"] for i in comunes],
        "tiempo_lineal_ms": [lin.loc[i, "tiempo_ms"] for i in comunes],
        "tiempo_cola_ms": [cola.loc[i, "tiempo_ms"] for i in comunes]})
    pares_cociente["cociente"] = (pares_cociente["tiempo_lineal_ms"] / pares_cociente["tiempo_cola_ms"]).round(2)
    pares_cociente.to_csv(RESULTADOS / "r2_cociente_pares.csv", index=False)
    c = pares_cociente["cociente"].tolist()
    resumen = pd.DataFrame([{"mediana": round(statistics.median(c), 2), "minimo": min(c), "maximo": max(c),
                             "pares": len(c), "pares_no_completados": int((~lin["completada"]).sum())}])
    resumen.to_csv(RESULTADOS / "r2_cociente.csv", index=False)
    print(pares_cociente.to_string(index=False))
    print(resumen.to_string(index=False))


if __name__ == "__main__":
    main()
