"""Pruebas del R5 - API de la aplicación demostrativa (ver specs/R5.md)."""
import json

import pytest
from fastapi.testclient import TestClient

from api.main import app, estado
from quindio.config import RESULTADOS
from quindio.dijkstra import dijkstra_cola
from quindio.tsp import itinerario

SIETE = ["MOQ", "FUN", "JBQ", "CLC", "CIL", "CRS", "ACR"]


@pytest.fixture(scope="module")
def cliente():
    with TestClient(app) as c:  # "with" ejecuta la carga de datos del inicio
        yield c


def test_lugares(cliente):
    r = cliente.get("/api/lugares")
    assert r.status_code == 200
    lugares = r.json()
    assert len(lugares) == 46
    assert any(lugar["id"] == "ARM" for lugar in lugares)


def test_ruta_coincide_con_dijkstra_directo(cliente):
    r = cliente.get("/api/ruta", params={"origen": "ARM", "destino": "SAL"})
    assert r.status_code == 200
    ruta = r.json()
    nodo_o = estado["lugar"]["ARM"]["nodo"]
    nodo_d = estado["lugar"]["SAL"]["nodo"]
    tiempo, camino, explorados = dijkstra_cola(estado["adj"], nodo_o, nodo_d)
    assert ruta["tiempo_s"] == pytest.approx(tiempo)
    assert ruta["nodos_explorados"] == explorados
    assert ruta["nodos_ruta"] == len(camino)
    assert ruta["polilinea"][0] == list(estado["coords"][nodo_o])
    assert ruta["polilinea"][-1] == list(estado["coords"][nodo_d])
    assert ruta["tiempo_s"] == pytest.approx(estado["matriz"]["ARM"]["SAL"], abs=0.01)
    assert ruta["distancia_km"] > 0


def test_ruta_id_inexistente(cliente):
    assert cliente.get("/api/ruta", params={"origen": "ARM", "destino": "XXX"}).status_code == 404


def test_envolvente_igual_a_r3(cliente):
    r = cliente.get("/api/envolvente")
    assert r.status_code == 200
    env = r.json()
    guardada = json.loads((RESULTADOS / "envolvente.json").read_text(encoding="utf-8"))
    assert env["n_vertices"] == guardada["n_vertices"]
    assert env["area_km2"] == pytest.approx(guardada["area_km2"], abs=0.01)


@pytest.mark.parametrize("atractivos", [SIETE[:5], SIETE + ["PVI", "MMQ"], SIETE[:6] + ["OCA"],
                                        SIETE[:5] + ["MOQ"]])
def test_itinerario_invalido_422(cliente, atractivos):
    # 5 atractivos, 9 atractivos, una finca sin duración y un repetido
    r = cliente.post("/api/itinerario", json={"partida": "ARM", "atractivos": atractivos})
    assert r.status_code == 422


def test_itinerario_held_karp_no_peor_que_voraz(cliente):
    r = cliente.post("/api/itinerario", json={"partida": "ARM", "atractivos": SIETE})
    assert r.status_code == 200
    res = r.json()
    hk, voraz = res["held_karp"], res["voraz"]
    assert hk["total_desplazamientos_min"] <= voraz["total_desplazamientos_min"] + 1e-9
    assert res["diferencia_min"] >= 0
    for recorrido in (hk, voraz):
        assert recorrido["orden"][0] == "ARM" and recorrido["orden"][-1] == "ARM"
        assert sorted(recorrido["orden"][1:-1]) == sorted(SIETE)
        assert len(recorrido["tramos"]) == 8
    # La tabla de Held-Karp es la misma que arma tsp.itinerario()
    duraciones = {i: estado["lugar"][i]["duracion_visita_min"] for i in SIETE}
    esperado = itinerario("ARM", SIETE, estado["matriz"], duraciones)
    assert hk["orden"] == esperado["orden"]
    assert hk["jornada_h"] == pytest.approx(esperado["jornada_h"])


def test_resultados_y_figuras(cliente):
    r = cliente.get("/api/resultados")
    assert r.status_code == 200
    datos = r.json()
    requerimientos = {t["requerimiento"] for t in datos["tablas"]}
    assert {"R1", "R2", "R3", "R4"} <= requerimientos
    assert len(datos["figuras"]) >= 1
    assert cliente.get(datos["figuras"][0]["url"]).status_code == 200
