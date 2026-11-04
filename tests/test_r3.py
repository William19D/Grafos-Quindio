"""Pruebas del R3 (ver specs/R3.md)."""
import random

from quindio.config import SEMILLA
from quindio.envolvente import (area_km2, envolvente_scipy, orientacion, preparar_puntos,
                                quickhull, quitar_colineales)


def test_cuadrado_con_interiores_y_colineales_resuelto_a_mano():
    puntos = [(2, 0), (1, 1), (4, 4), (0, 3), (4, 2), (0, 0), (2, 3), (1, 4), (4, 0), (0, 4)]
    assert quickhull(puntos) == [(0, 0), (4, 0), (4, 4), (0, 4)]


def test_puntos_repetidos():
    assert preparar_puntos([0.4, 0.2, 10.6], [0.1, -0.3, 2.5]) == [(0, 0), (11, 2)]
    base = [(0, 0), (5, 0), (5, 5), (0, 5), (2, 2)]
    con_repetidos = base + [(0, 0), (5, 5), (2, 2), (0, 5)]
    assert quickhull(con_repetidos) == quickhull(base) == [(0, 0), (5, 0), (5, 5), (0, 5)]


def test_casos_degenerados():
    assert quickhull([(0, 0), (1, 1), (2, 2), (3, 3)]) == [(0, 0), (3, 3)]
    assert quickhull([(3, 3), (0, 0), (2, 2)]) == [(0, 0), (3, 3)]
    assert quickhull([(7, 7)]) == [(7, 7)]
    assert quickhull([(7, 7), (7, 7)]) == [(7, 7)]
    assert quickhull([]) == []


def test_igual_que_scipy_en_puntos_aleatorios():
    rng = random.Random(SEMILLA)
    # Rango grande (pocos colineales) y rango pequeño (muchos puntos alineados y repetidos).
    for tamano, rango in [(50, 1000), (500, 100_000), (5000, 100_000), (300, 10), (2000, 30), (40, 4), (200, 6)]:
        puntos = []
        for _ in range(tamano):
            puntos.append((rng.randint(0, rango), rng.randint(0, rango)))
        puntos = preparar_puntos([p[0] for p in puntos], [p[1] for p in puntos])
        assert quickhull(puntos) == envolvente_scipy(puntos)


def test_orden_antihorario_y_sin_colineales():
    rng = random.Random(SEMILLA + 1)
    puntos = [(rng.randint(0, 50), rng.randint(0, 50)) for _ in range(1000)]
    poligono = quickhull(puntos)
    h = len(poligono)
    assert h >= 3
    for i in range(h):
        assert orientacion(poligono[i], poligono[(i + 1) % h], poligono[(i + 2) % h]) > 0
    assert quitar_colineales(poligono) == poligono


def test_area_zapato():
    assert area_km2([(0, 0), (1000, 0), (1000, 1000), (0, 1000)]) == 1.0
    assert area_km2([(0, 0), (2000, 0), (0, 1000)]) == 1.0


def test_empate_en_el_punto_mas_lejano():
    # Tres puntos empatados a la máxima distancia de AB, con el del medio primero en la
    # lista: el del medio está alineado sobre el lado superior y no debe ser vértice.
    puntos = [(0, 0), (10, 0), (5, 5), (2, 5), (8, 5), (4, 2)]
    assert quickhull(puntos) == [(0, 0), (10, 0), (8, 5), (2, 5)]
