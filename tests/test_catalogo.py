"""Pruebas del catálogo de lugares (specs/catalogo.md)."""
import csv
import math

from quindio.config import CATALOGO, PLAZA_BOLIVAR_ARMENIA

COLUMNAS = ["id", "nombre", "municipio", "categoria", "lat", "lon",
            "duracion_visita_min", "fuente_duracion", "fuente_coordenadas"]
MINIMOS = {"cabecera": 12, "atractivo": 15, "finca": 8, "acopio": 5}
MUNICIPIOS = {"Armenia", "Buenavista", "Calarcá", "Circasia", "Córdoba", "Filandia", "Génova",
              "La Tebaida", "Montenegro", "Pijao", "Quimbaya", "Salento"}


def leer():
    with open(CATALOGO, encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        return lector.fieldnames, list(lector)


def distancia_km(lat1, lon1, lat2, lon2):
    """Semiverseno (haversine) sobre una esfera de 6371 km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def test_distancia_caso_a_mano():
    # 1 grado de latitud = 2*pi*6371/360 = 111.19 km
    assert abs(distancia_km(4.0, -75.0, 5.0, -75.0) - 111.19) < 0.01


def test_columnas():
    columnas, _ = leer()
    assert columnas == COLUMNAS


def test_minimos_por_categoria():
    _, filas = leer()
    assert len(filas) >= 40
    assert {f["categoria"] for f in filas} <= set(MINIMOS)
    for cat, minimo in MINIMOS.items():
        assert sum(f["categoria"] == cat for f in filas) >= minimo, cat


def test_ids_unicos_y_armenia():
    _, filas = leer()
    ids = [f["id"] for f in filas]
    assert len(ids) == len(set(ids))
    assert all(i.isupper() and i.replace("_", "").isalnum() for i in ids)
    arm = next(f for f in filas if f["id"] == "ARM")
    assert arm["categoria"] == "cabecera"
    assert (float(arm["lat"]), float(arm["lon"])) == PLAZA_BOLIVAR_ARMENIA


def test_una_cabecera_por_municipio():
    _, filas = leer()
    cabeceras = [f["municipio"] for f in filas if f["categoria"] == "cabecera"]
    assert sorted(cabeceras) == sorted(MUNICIPIOS)
    assert {f["municipio"] for f in filas} <= MUNICIPIOS


def test_dentro_del_rectangulo_del_quindio():
    _, filas = leer()
    for f in filas:
        assert 4.05 <= float(f["lat"]) <= 4.75 and -75.95 <= float(f["lon"]) <= -75.35, f["id"]


def test_duraciones_y_fuentes():
    _, filas = leer()
    for f in filas:
        assert f["fuente_coordenadas"].strip(), f["id"]
        if f["categoria"] == "atractivo":
            assert int(f["duracion_visita_min"]) > 0, f["id"]
            assert f["fuente_duracion"].strip(), f["id"]
        else:
            assert f["duracion_visita_min"] == "" and f["fuente_duracion"] == "", f["id"]


def test_cerca_de_su_cabecera():
    _, filas = leer()
    cab = {f["municipio"]: (float(f["lat"]), float(f["lon"])) for f in filas if f["categoria"] == "cabecera"}
    for f in filas:
        lat, lon = cab[f["municipio"]]
        assert distancia_km(float(f["lat"]), float(f["lon"]), lat, lon) < 20, f["id"]
