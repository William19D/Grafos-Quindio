"""Pruebas del R4 (ver specs/R4.md)."""
import importlib.util
import itertools
import random

import pytest

from quindio.config import RAIZ, SEMILLA
from quindio.tsp import (ajustar_a_jornada, costo_recorrido, fuerza_bruta, held_karp,
                         leer_catalogo, leer_matriz, permutaciones_heap, vecino_mas_cercano)

# Matriz del ejemplo a mano (docs/paso_a_paso_R4.md). Fila = desde, columna = hacia.
D_MANO = [[0, 2, 9, 10],
          [1, 0, 6, 4],
          [15, 7, 0, 8],
          [6, 3, 12, 0]]


def _matriz_aleatoria(n, rnd):
    d = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i != j:
                d[i][j] = rnd.uniform(1, 100)  # asimétrica: d[i][j] y d[j][i] independientes
    return d


def _es_recorrido_valido(recorrido, n):
    return (recorrido[0] == 0 and recorrido[-1] == 0 and len(recorrido) == n + 1
            and sorted(recorrido[1:-1]) == list(range(1, n)))


def test_ejemplo_a_mano():
    assert fuerza_bruta(D_MANO) == (21, [0, 2, 3, 1, 0])
    assert held_karp(D_MANO) == (21, [0, 2, 3, 1, 0])
    # la voraz se va primero al más cercano (1) y termina pagando 2 -> 0 = 15
    assert vecino_mas_cercano(D_MANO) == (33, [0, 1, 3, 2, 0])


def test_permutaciones_heap():
    vistas = [tuple(p) for p in permutaciones_heap([1, 2, 3, 4, 5])]
    assert len(vistas) == 120
    assert set(vistas) == set(itertools.permutations([1, 2, 3, 4, 5]))


@pytest.mark.parametrize("n", range(1, 9))  # k = n - 1 = 0..7 lugares a visitar
def test_held_karp_igual_fuerza_bruta(n):
    rnd = random.Random(SEMILLA + n)
    for _ in range(5):
        d = _matriz_aleatoria(n, rnd)
        costo_fb, rec_fb = fuerza_bruta(d)
        costo_hk, rec_hk = held_karp(d)
        assert costo_hk == pytest.approx(costo_fb)
        assert _es_recorrido_valido(rec_hk, n) and _es_recorrido_valido(rec_fb, n)
        assert costo_recorrido(d, rec_hk) == pytest.approx(costo_hk)
        assert costo_recorrido(d, rec_fb) == pytest.approx(costo_fb)


def test_vecino_mas_cercano_valido():
    rnd = random.Random(SEMILLA)
    for n in range(1, 10):
        d = _matriz_aleatoria(n, rnd)
        costo, recorrido = vecino_mas_cercano(d)
        assert _es_recorrido_valido(recorrido, n)
        assert costo == pytest.approx(costo_recorrido(d, recorrido))
        assert costo >= held_karp(d)[0] - 1e-9


def test_itinerario_cabe_en_11_horas():
    # el mismo conjunto que usa el experimento (se carga el script por su ruta)
    especificacion = importlib.util.spec_from_file_location(
        "r4_itinerario", RAIZ / "experimentos" / "r4_itinerario.py")
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    ATRACTIVOS, PARTIDA = modulo.ATRACTIVOS, modulo.PARTIDA
    _ids, matriz = leer_matriz()
    catalogo = leer_catalogo()
    duraciones = {}
    for lugar in ATRACTIVOS:
        duraciones[lugar] = catalogo[lugar]["duracion_min"]
    final, _quitados = ajustar_a_jornada(PARTIDA, ATRACTIVOS, matriz, duraciones, limite_h=11)
    assert final["cabe"] and final["jornada_h"] <= 11
    filas = final["filas"]
    assert filas[-1]["orden"] == "Regreso" and filas[-1]["lugar"] == PARTIDA
    desplaz = sum(f["desplazamiento_desde_anterior_min"] for f in filas)
    visitas = sum(f["visita_min"] for f in filas[:-1])
    assert desplaz == pytest.approx(final["total_desplazamientos_min"], abs=0.01)
    assert visitas == pytest.approx(final["total_visitas_min"])
    assert filas[-1]["tiempo_acumulado_h"] == pytest.approx(final["jornada_h"], abs=0.01)


def test_traza_no_cambia_resultado():
    for funcion in (fuerza_bruta, held_karp, vecino_mas_cercano):
        pasos = []
        assert funcion(D_MANO, traza=pasos) == funcion(D_MANO)
        assert len(pasos) > 0
