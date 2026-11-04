"""R3.2 - Tiempo de QuickHull propio vs scipy.spatial.ConvexHull.

Conjuntos: nodos de la componente (data/processed/nodos.csv) y puntos enteros al azar en el
cuadrado [0, 100 000]² m con semilla config.SEMILLA (1 000, 10 000 y 50 000 puntos).
Cada conjunto se verifica (mismos vértices) antes de medir. Solo se mide el algoritmo.
Salidas: resultados/r3_envolvente.csv, resultados/r3_niveles.csv, resultados/envolvente.json,
resultados/r3_scipy_costo_fijo.json
"""
import csv
import json
import random
from datetime import date

import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import ConvexHull

from quindio.config import CRS_UTM, NODOS, RESULTADOS, SEMILLA
from quindio.envolvente import area_km2, envolvente_scipy, preparar_puntos, quickhull
from quindio.medicion import guardar_maquina, medir

LADO_CUADRADO_M = 100_000
TAMANOS = [1_000, 10_000, 50_000]


def cargar_nodos():
    df = pd.read_csv(NODOS)
    if "x_utm" not in df.columns:
        a_utm = Transformer.from_crs("EPSG:4326", CRS_UTM, always_xy=True)
        df["x_utm"], df["y_utm"] = a_utm.transform(df["lon"].to_numpy(), df["lat"].to_numpy())
    return df


def puntos_cuadrado(n, rng):
    xs, ys = [], []
    for _ in range(n):
        xs.append(rng.randint(0, LADO_CUADRADO_M))
        ys.append(rng.randint(0, LADO_CUADRADO_M))
    return preparar_puntos(xs, ys)


def scipy_convexhull(arreglo):
    """Lo que se mide de SciPy: solo la construcción de ConvexHull."""
    return ConvexHull(arreglo)


def descartes_por_nivel(nombre, puntos):
    """Con la traza (fuera de la medición) cuenta cuántos candidatos entran a cada nivel de
    QuickHull y cuántos se descartan ahí."""
    traza = []
    quickhull(puntos, traza=traza)
    niveles = {}
    for paso in traza:
        if paso["paso"] == "dividir":
            fila = niveles.setdefault(paso["nivel"], [0, 0])
            fila[0] += paso["candidatos"]
            fila[1] += paso["descartados"]
    filas = []
    for nivel in sorted(niveles):
        entran, descartados = niveles[nivel]
        filas.append({"conjunto": nombre, "n": len(puntos), "nivel": nivel,
                      "candidatos": entran, "descartados": descartados})
    return filas


def main():
    guardar_maquina()
    df = cargar_nodos()
    red = preparar_puntos(df["x_utm"].to_numpy(), df["y_utm"].to_numpy())
    print(f"Nodos: {len(df)}; puntos distintos tras redondear: {len(red)}")

    rng = random.Random(SEMILLA)
    conjuntos = [("Nodos de la red", red)]
    for n in TAMANOS:
        nombre = "Cuadrado, " + f"{n:,}".replace(",", " ") + " puntos"
        conjuntos.append((nombre, puntos_cuadrado(n, rng)))

    filas, niveles = [], []
    for nombre, puntos in conjuntos:
        propio = quickhull(puntos)
        assert propio == envolvente_scipy(puntos), f"{nombre}: la envolvente no coincide con SciPy"
        arreglo = np.array(puntos, dtype=float)  # conversión fuera de la medición
        t_propio, _ = medir(quickhull, puntos)
        t_scipy, _ = medir(scipy_convexhull, arreglo)
        filas.append({"conjunto": nombre, "n": len(puntos), "vertices": len(propio),
                      "tiempo_propio_ms": round(t_propio, 3), "tiempo_scipy_ms": round(t_scipy, 3),
                      "cociente": round(t_propio / t_scipy, 1)})
        niveles += descartes_por_nivel(nombre, puntos)
        print(filas[-1])

    # Costo fijo de llamar a SciPy (validar el arreglo, preparar Qhull, armar el objeto de
    # salida): ConvexHull con solo 4 puntos. Ayuda a explicar el cociente con n pequeño.
    t_fijo, _ = medir(scipy_convexhull, np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float))
    (RESULTADOS / "r3_scipy_costo_fijo.json").write_text(
        json.dumps({"puntos": 4, "tiempo_scipy_ms": round(t_fijo, 3)}, indent=2), encoding="utf-8")
    print(f"ConvexHull con 4 puntos: {t_fijo:.3f} ms")

    with open(RESULTADOS / "r3_envolvente.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    with open(RESULTADOS / "r3_niveles.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(niveles[0]))
        w.writeheader()
        w.writerows(niveles)

    # Envolvente de la red para el mapa de la aplicación.
    poligono = quickhull(red)
    osmid_de = {}
    for osmid, x, y in zip(df["osmid"], df["x_utm"], df["y_utm"]):
        osmid_de.setdefault((int(round(x)), int(round(y))), int(osmid))
    a_grados = Transformer.from_crs(CRS_UTM, "EPSG:4326", always_xy=True)
    vertices = []
    for x, y in poligono:
        lon, lat = a_grados.transform(x, y)
        vertices.append({"osmid": osmid_de[(x, y)], "lat": round(lat, 7), "lon": round(lon, 7),
                         "x_utm": x, "y_utm": y})
    salida = {
        "descripcion": "Envolvente convexa de los nodos de la componente fuertemente conexa "
                       "(QuickHull propio, verificado con scipy.spatial.ConvexHull)",
        "orden": "antihorario",
        "crs_utm": CRS_UTM,
        "n_puntos": len(red),
        "n_vertices": len(poligono),
        "area_km2": round(area_km2(poligono), 2),
        "fecha": date.today().isoformat(),
        "vertices": vertices,
    }
    (RESULTADOS / "envolvente.json").write_text(json.dumps(salida, indent=2, ensure_ascii=False),
                                                 encoding="utf-8")
    print(f"Envolvente de la red: {len(poligono)} vértices, {salida['area_km2']} km²")


if __name__ == "__main__":
    main()
