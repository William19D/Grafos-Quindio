"""R1.3 - Tiempo de ox.truncate.largest_component(G, strongly=True) en redes crecientes.

Descarga (si no existen) las redes de radio 2, 5, 10 y 20 km alrededor de la plaza de Bolívar
de Armenia y usa la red completa del departamento ya descargada. Solo se mide la función
(la lectura del GraphML queda por fuera). Salida: resultados/r1_scc_tiempos.csv
"""
import csv

import networkx as nx
import osmnx as ox

from quindio.config import GRAFO_RAW, PLAZA_BOLIVAR_ARMENIA, RAW, RESULTADOS
from quindio.descarga import con_reintentos
from quindio.medicion import guardar_maquina, medir

RADIOS_KM = [2, 5, 10, 20]


def componente_osmnx(G):
    """Lo que se pide medir: la función completa de OSMnx (Tarjan + copia del subgrafo)."""
    return ox.truncate.largest_component(G, strongly=True)


def solo_tarjan(G):
    """Solo el algoritmo de componentes de NetworkX, sin copiar el subgrafo."""
    return max(nx.strongly_connected_components(G), key=len)


def cargar_redes():
    """Generador: carga una red a la vez para que en memoria solo esté la red que se mide
    (con todas cargadas, el recolector de basura de Python recorre más objetos y el tiempo
    de las últimas redes sale inflado)."""
    for r in RADIOS_KM:
        ruta = RAW / f"armenia_r{r}km.graphml"
        if not ruta.exists():
            print(f"Descargando radio {r} km ...")
            G = con_reintentos(ox.graph_from_point, PLAZA_BOLIVAR_ARMENIA, dist=r * 1000, network_type="drive")
            ox.save_graphml(G, ruta)
        yield f"Radio de {r} km", ox.load_graphml(ruta)
    yield "Departamento completo", ox.load_graphml(GRAFO_RAW)


def main():
    guardar_maquina()
    filas = []
    for nombre, G in cargar_redes():
        V, E = G.number_of_nodes(), G.number_of_edges()
        t_total, C = medir(componente_osmnx, G)
        t_tarjan, nodos_cc = medir(solo_tarjan, G)
        # verificación: la componente devuelta es fuertemente conexa y coincide con la de Tarjan
        assert nx.is_strongly_connected(C) and set(C.nodes) == nodos_cc
        fila = {"red": nombre, "V": V, "E": E, "V_mas_E": V + E,
                "tiempo_ms": round(t_total, 3), "tiempo_tarjan_ms": round(t_tarjan, 3),
                "nodos_scc": C.number_of_nodes(), "aristas_scc": C.number_of_edges()}
        print(fila)
        filas.append(fila)
        del G, C
    with open(RESULTADOS / "r1_scc_tiempos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)


if __name__ == "__main__":
    main()
