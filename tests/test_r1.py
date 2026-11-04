"""Pruebas del R1 (ver specs/R1.md)."""
import random
import time

import networkx as nx
import osmnx as ox
import pandas as pd
import pytest
from pyproj import Transformer

from quindio.config import ARISTAS, CRS_UTM, GRAFO_RAW, NODOS, PLAZA_BOLIVAR_ARMENIA, SEMILLA
from quindio.red import a_utm, asignar_pesos, asociar_lugares, cargar_grafo, estimar_memoria, parsear_maxspeed

UTM_A_GRADOS = Transformer.from_crs(CRS_UTM, "EPSG:4326", always_xy=True)


def test_parsear_maxspeed_casos_a_mano():
    assert parsear_maxspeed("30") == 30
    assert parsear_maxspeed("30 km/h") == 30
    assert parsear_maxspeed("20 mph") == pytest.approx(32.18688)
    assert parsear_maxspeed("40|60") == 50
    assert parsear_maxspeed("40;60") == 50
    assert parsear_maxspeed(["60", "30"]) == 45
    assert parsear_maxspeed(["60", "signals"]) == 60
    assert parsear_maxspeed(None) is None
    assert parsear_maxspeed(float("nan")) is None
    assert parsear_maxspeed("CO:urban") is None
    assert parsear_maxspeed(["walk"]) is None


@pytest.mark.skipif(not GRAFO_RAW.exists(), reason="falta la red cruda")
def test_parseo_igual_que_osmnx_en_la_red_real():
    """Comparación con la limpieza interna de OSMnx (solo para verificar)."""
    from osmnx.routing import _clean_maxspeed, _collapse_multiple_maxspeed_values
    G = ox.load_graphml(GRAFO_RAW)
    revisadas = 0
    for _, _, d in G.edges(data=True):
        if "maxspeed" in d:
            ref = _collapse_multiple_maxspeed_values(d["maxspeed"], agg=lambda s: sum(s) / len(s))
            ref = _clean_maxspeed(ref) if isinstance(ref, str) else ref
            assert parsear_maxspeed(d["maxspeed"]) == pytest.approx(ref)
            revisadas += 1
    assert revisadas > 1000


def test_asignar_pesos_imputacion_y_tiempo():
    G = nx.MultiDiGraph()
    G.add_edge(1, 2, length=1000.0, highway="secondary", maxspeed="50")
    G.add_edge(2, 3, length=360.0, highway="residential", maxspeed="20")
    G.add_edge(3, 4, length=360.0, highway="residential", maxspeed="40")
    G.add_edge(4, 1, length=1000.0, highway="residential")              # media de residential = 30
    G.add_edge(4, 5, length=900.0, highway=["primary_link", "trunk"])  # sin datos -> tabla (40)
    G.add_edge(5, 4, length=900.0, highway="ladder")                   # tipo desconocido -> 30
    asignar_pesos(G)
    e = {(u, v): d for u, v, d in G.edges(data=True)}
    assert e[(1, 2)]["travel_time"] == pytest.approx(1000 / (50 / 3.6))   # 72 s
    assert e[(2, 3)]["travel_time"] == pytest.approx(64.8)                # 360 m a 20 km/h
    assert e[(4, 1)]["speed_kph"] == 30 and e[(4, 1)]["velocidad_imputada"]
    assert e[(4, 1)]["travel_time"] == pytest.approx(120)
    assert e[(4, 5)]["speed_kph"] == 40
    assert e[(5, 4)]["speed_kph"] == 30
    assert not e[(1, 2)]["velocidad_imputada"]


def test_estimar_memoria_caso_pequeno():
    m = estimar_memoria(2, 1)
    assert m["matriz_bajo_nivel_mb"] * 1e6 == pytest.approx(32)
    assert m["listas_bajo_nivel_mb"] * 1e6 == pytest.approx(28)


def _cuadricula(x0, y0, n=5, paso=100.0):
    filas, k = [], 0
    for i in range(n):
        for j in range(n):
            filas.append({"osmid": k, "x_utm": x0 + i * paso, "y_utm": y0 + j * paso})
            k += 1
    return pd.DataFrame(filas)


def _lugar(x, y, nombre):
    lon, lat = UTM_A_GRADOS.transform(x, y)
    return {"id": nombre, "nombre": nombre, "categoria": "prueba", "lat": lat, "lon": lon}


def test_asociar_lugares_cuadricula_a_mano():
    x0, y0 = a_utm(*PLAZA_BOLIVAR_ARMENIA)
    nodos = _cuadricula(x0, y0)  # osmid = 5*i + j en el punto (x0 + 100 i, y0 + 100 j)
    cat = pd.DataFrame([_lugar(x0 + 130, y0 + 40, "a"),      # más cerca de (1, 0): 50 m
                        _lugar(x0 + 400, y0 + 400, "b"),     # encima del nodo (4, 4)
                        _lugar(x0 - 600, y0 + 200, "c")])    # lejos: 600 m del nodo (0, 2)
    r = asociar_lugares(cat, nodos)
    assert r["nodo"].tolist() == [5, 24, 2]
    assert r["dist_nodo_m"].tolist() == pytest.approx([50, 0, 600], abs=0.2)
    assert r["lejano_500m"].tolist() == [False, False, True]


def test_asociar_lugares_igual_que_nearest_nodes():
    rnd = random.Random(SEMILLA)
    lat0, lon0 = PLAZA_BOLIVAR_ARMENIA
    Gp = nx.MultiDiGraph(crs=CRS_UTM)  # grafo ya proyectado a UTM 18N
    for k in range(300):
        x, y = a_utm(lat0 + rnd.uniform(-0.05, 0.05), lon0 + rnd.uniform(-0.05, 0.05))
        Gp.add_node(k, x=x, y=y)
    nodos = pd.DataFrame({"osmid": list(Gp.nodes),
                          "x_utm": [Gp.nodes[n]["x"] for n in Gp.nodes],
                          "y_utm": [Gp.nodes[n]["y"] for n in Gp.nodes]})
    cat = pd.DataFrame({"lat": [lat0 + rnd.uniform(-0.06, 0.06) for _ in range(40)],
                        "lon": [lon0 + rnd.uniform(-0.06, 0.06) for _ in range(40)]})
    r = asociar_lugares(cat, nodos)
    X, Y = a_utm(cat["lat"].tolist(), cat["lon"].tolist())
    esperado, dist = ox.distance.nearest_nodes(Gp, X, Y, return_dist=True)
    assert r["nodo"].tolist() == list(esperado)
    assert r["dist_nodo_m"].tolist() == pytest.approx(list(dist), abs=0.1)


procesado = pytest.mark.skipif(not (NODOS.exists() and ARISTAS.exists()), reason="falta correr r1_red.py")


@procesado
def test_componente_procesada_fuertemente_conexa():
    nodos = pd.read_csv(NODOS)
    aristas = pd.read_csv(ARISTAS)
    D = nx.DiGraph()
    D.add_nodes_from(nodos["osmid"])
    D.add_edges_from(zip(aristas["u"], aristas["v"]))
    assert nx.is_strongly_connected(D)
    assert (aristas["tiempo_s"] > 0).all()
    if GRAFO_RAW.exists():  # es la componente MÁS GRANDE de la red cruda
        G = ox.load_graphml(GRAFO_RAW)
        assert len(D) == len(max(nx.strongly_connected_components(G), key=len))


@procesado
def test_cargar_grafo_completo_y_rapido():
    t0 = time.perf_counter()
    adj, coords = cargar_grafo()
    assert time.perf_counter() - t0 < 2
    assert len(adj) == len(coords) == len(pd.read_csv(NODOS))
    assert sum(len(l) for l in adj.values()) == len(pd.read_csv(ARISTAS))
    u = next(iter(adj))
    v, t, d = adj[u][0]
    assert v in adj and t > 0 and d > 0
    # tiempo = distancia / velocidad con velocidades razonables (km/h)
    assert all(5 <= dd / tt * 3.6 <= 130 for l in adj.values() for _, tt, dd in l)


def test_nodo_mas_cercano_y_leer_numero_metodo_largo():
    """Ejemplo de docs/paso_a_paso_R1.md: el punto (120, 160) queda a 44.7 m del nodo C."""
    from quindio.red import leer_numero, nodo_mas_cercano
    pasos = []
    nodo, d = nodo_mas_cercano(120.0, 160.0, ["A", "B", "C", "D"], [0.0, 300.0, 100.0, 400.0],
                               [0.0, 0.0, 200.0, 400.0], traza=pasos)
    assert nodo == "C" and d == pytest.approx(44.72, abs=0.01)
    assert len(pasos) == 4  # una línea de traza por nodo revisado
    assert leer_numero("12,5") == 12.5 and leer_numero("40") == 40
    assert leer_numero("5.") is None and leer_numero("1.2.3") is None and leer_numero("") is None
