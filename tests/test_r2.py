"""Pruebas del R2 (ver specs/R2.md)."""
import heapq
import math
import random

import networkx as nx
import pytest

from quindio.config import SEMILLA
from quindio.dijkstra import dijkstra_cola, dijkstra_lineal
from quindio.estructuras import MonticuloMinimo

# Grafo del ejemplo a mano (docs/paso_a_paso_R2.md). adj[u] = [(v, tiempo, distancia)]
ARISTAS_MANO = [("A", "B", 4), ("A", "C", 2), ("C", "B", 1), ("B", "D", 5), ("C", "D", 8),
                ("C", "E", 10), ("D", "E", 2), ("D", "F", 6), ("E", "F", 2), ("F", "A", 3)]


def _adj(aristas, nodos=()):
    adj = {n: [] for n in nodos}
    for u, v, w in aristas:
        adj.setdefault(u, []).append((v, w, 0.0))
        adj.setdefault(v, [])
    return adj


def _grafo_aleatorio(n=300, m=1500):
    rnd = random.Random(SEMILLA)
    aristas = [(rnd.randrange(n), rnd.randrange(n), rnd.uniform(1, 100)) for _ in range(m)]
    # pesos reales: sin empates, así ambas versiones exploran exactamente los mismos nodos
    aristas = [(u, v, w) for u, v, w in aristas if u != v]
    return _adj(aristas, range(n)), aristas, rnd


VERSIONES = [dijkstra_lineal, dijkstra_cola]


@pytest.mark.parametrize("dijkstra", VERSIONES)
def test_grafo_a_mano(dijkstra):
    adj = _adj(ARISTAS_MANO)
    assert dijkstra(adj, "A", "F") == (12, ["A", "C", "B", "D", "E", "F"], 6)
    assert dijkstra(adj, "A", "B") == (3, ["A", "C", "B"], 3)  # explora A, C y B
    assert dijkstra(adj, "D", "D") == (0, ["D"], 1)


def test_uno_a_todos_a_mano():
    distancias, predecesores, explorados = dijkstra_cola(_adj(ARISTAS_MANO), "A")
    assert distancias == {"A": 0, "B": 3, "C": 2, "D": 8, "E": 10, "F": 12}
    assert predecesores["F"] == "E" and predecesores["B"] == "C"
    assert explorados == 6


@pytest.mark.parametrize("dijkstra", VERSIONES)
def test_inalcanzable(dijkstra):
    adj = _adj([(1, 2, 5), (2, 3, 1), (4, 1, 1)])  # al nodo 4 no llega nadie
    tiempo, ruta, explorados = dijkstra(adj, 1, 4)
    assert tiempo == math.inf and ruta == [] and explorados == 3


def test_traza_no_cambia_resultado():
    adj = _adj(ARISTAS_MANO)
    pasos = []
    assert dijkstra_cola(adj, "A", "F", traza=pasos) == dijkstra_cola(adj, "A", "F")
    assert len(pasos) > 6
    pasos = []
    assert dijkstra_lineal(adj, "A", "F", traza=pasos) == dijkstra_lineal(adj, "A", "F")
    assert len(pasos) > 6


def test_lineal_igual_a_cola_y_a_networkx_en_grafo_aleatorio():
    adj, aristas, rnd = _grafo_aleatorio()
    G = nx.MultiDiGraph()
    G.add_nodes_from(adj)
    G.add_weighted_edges_from(aristas)
    pesos = {}
    for u, v, w in aristas:  # peso mínimo entre aristas paralelas, para validar la ruta
        pesos[(u, v)] = min(w, pesos.get((u, v), math.inf))
    alcanzados = 0
    for _ in range(30):
        o, d = rnd.randrange(300), rnd.randrange(300)
        t_lin, ruta_lin, exp_lin = dijkstra_lineal(adj, o, d)
        t_cola, ruta_cola, exp_cola = dijkstra_cola(adj, o, d)
        assert t_lin == t_cola and exp_lin == exp_cola
        if nx.has_path(G, o, d):
            alcanzados += 1
            assert t_cola == pytest.approx(nx.dijkstra_path_length(G, o, d))
            assert ruta_cola[0] == o and ruta_cola[-1] == d
            assert sum(pesos[(ruta_cola[i], ruta_cola[i + 1])] for i in range(len(ruta_cola) - 1)) == pytest.approx(t_cola)
        else:
            assert t_cola == math.inf
    assert alcanzados >= 20
    o = 0
    distancias, _, _ = dijkstra_cola(adj, o)
    esperadas = nx.single_source_dijkstra_path_length(G, o)
    alcanzadas = {v: t for v, t in distancias.items() if t < math.inf}
    assert alcanzadas.keys() == esperadas.keys()
    assert all(alcanzadas[v] == pytest.approx(esperadas[v]) for v in esperadas)


def test_monticulo_igual_que_heapq():
    rnd = random.Random(SEMILLA)
    m, h = MonticuloMinimo(), []
    salida_m, salida_h = [], []
    for k in range(200):
        p = rnd.randint(0, 50)
        m.insertar(p, k)
        heapq.heappush(h, p)
        if k % 3 == 0:  # extracciones intercaladas
            salida_m.append(m.extraer_minimo()[0])
            salida_h.append(heapq.heappop(h))
    while not m.esta_vacio():
        salida_m.append(m.extraer_minimo()[0])
        salida_h.append(heapq.heappop(h))
    assert salida_m == salida_h and len(h) == 0
    with pytest.raises(IndexError):
        m.extraer_minimo()


def test_arbol_de_exploracion_en_orden_y_sin_cambiar_resultado():
    """El árbol anota cada nodo explorado una vez, en orden de distancia, con su predecesor."""
    adj = _adj(ARISTAS_MANO)
    arbol = []
    assert dijkstra_cola(adj, "A", "F", arbol=arbol) == dijkstra_cola(adj, "A", "F")
    tiempo, ruta, explorados = dijkstra_cola(adj, "A", "F")
    assert len(arbol) == explorados
    assert arbol[0] == (None, "A", 0)
    assert arbol[-1][1] == "F" and arbol[-1][2] == tiempo
    distancias = [d for _, _, d in arbol]
    assert distancias == sorted(distancias)  # sale en orden no decreciente (invariante)
    vistos = {"A"}
    for pred, nodo, _ in arbol[1:]:
        assert pred in vistos  # el padre ya estaba fijado: es un árbol que crece desde el origen
        vistos.add(nodo)
