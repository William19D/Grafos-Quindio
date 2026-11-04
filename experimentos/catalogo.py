"""Catálogo de lugares: verificación geográfica y figura.

Lee data/catalogo.csv y comprueba, para cada lugar:
  1. que cae dentro del polígono del Quindío (OSM, ox.geocode_to_gdf);
  2. en qué municipio cae según los polígonos municipales de OSM;
  3. su distancia en línea recta (km) a la cabecera de su municipio.
Escribe resultados/catalogo_verificacion.csv y dibuja resultados/figuras/catalogo.png
a partir del CSV del catálogo.

Uso: PYTHONPATH=src .venv/Scripts/python.exe experimentos/catalogo.py
"""
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import osmnx as ox
import pandas as pd
from shapely.geometry import Point

from quindio.config import CATALOGO, FIGURAS, LUGAR, RESULTADOS

COLORES = {"cabecera": "#d62728", "atractivo": "#1f77b4", "finca": "#2ca02c", "acopio": "#8c564b"}
MARCAS = {"cabecera": "s", "atractivo": "o", "finca": "^", "acopio": "D"}


def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia en km sobre una esfera de radio 6371 km (fórmula del semiverseno)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def poligonos_municipios(municipios):
    """Polígono de cada municipio según Nominatim/OSM (osmnx respeta 1 petición/s y usa caché)."""
    polis = {}
    for m in municipios:
        try:
            gdf = ox.geocode_to_gdf(f"{m}, Quindío, Colombia")
            geom = gdf.geometry.iloc[0]
            if geom.geom_type in ("Polygon", "MultiPolygon"):
                polis[m] = geom
        except Exception as e:  # noqa: BLE001 - si Nominatim no lo encuentra se usa solo la distancia
            print(f"sin polígono para {m}: {e}")
    return polis


def verificar(cat):
    ox.settings.use_cache = True
    depto = ox.geocode_to_gdf(LUGAR).geometry.iloc[0]
    polis = poligonos_municipios(sorted(cat["municipio"].unique()))
    cabeceras = cat[cat["categoria"] == "cabecera"].set_index("municipio")

    filas = []
    for _, l in cat.iterrows():
        p = Point(l["lon"], l["lat"])
        en_osm = [m for m, g in polis.items() if g.contains(p)]
        cab = cabeceras.loc[l["municipio"]]
        filas.append({
            "id": l["id"],
            "municipio": l["municipio"],
            "dentro_quindio": depto.contains(p),
            "municipio_osm": ";".join(en_osm),
            "municipio_coincide": l["municipio"] in en_osm if l["municipio"] in polis else None,
            "dist_cabecera_km": round(haversine_km(l["lat"], l["lon"], cab["lat"], cab["lon"]), 2),
        })
    return pd.DataFrame(filas), depto


def figura(cat, depto):
    fig, ax = plt.subplots(figsize=(8, 10))
    x, y = depto.exterior.xy if depto.geom_type == "Polygon" else max(depto.geoms, key=lambda g: g.area).exterior.xy
    ax.fill(x, y, color="#f2efe6", edgecolor="#555", linewidth=1)
    for c, g in cat.groupby("categoria"):
        ax.scatter(g["lon"], g["lat"], c=COLORES[c], marker=MARCAS[c], s=45, edgecolor="k",
                   linewidth=0.4, label=f"{c} ({len(g)})", zorder=3)
    for _, l in cat.iterrows():
        ax.annotate(l["id"], (l["lon"], l["lat"]), fontsize=6, xytext=(3, 3), textcoords="offset points")
    ax.set_title(f"Catálogo de lugares del Quindío ({len(cat)} lugares)")
    ax.set_xlabel("Longitud (°)")
    ax.set_ylabel("Latitud (°)")
    ax.set_aspect("equal")
    ax.legend(loc="lower left")
    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURAS / "catalogo.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def main():
    cat = pd.read_csv(CATALOGO)
    ver, depto = verificar(cat)
    ver.to_csv(RESULTADOS / "catalogo_verificacion.csv", index=False)
    print(cat["categoria"].value_counts().to_string())
    print(ver.to_string(index=False))
    print("fuera del Quindío:", ver.loc[~ver["dentro_quindio"], "id"].tolist())
    print("municipio distinto en OSM:", ver.loc[ver["municipio_coincide"] == False, "id"].tolist())  # noqa: E712
    print("máx. distancia a la cabecera (km):", ver["dist_cabecera_km"].max())
    figura(cat, depto)


if __name__ == "__main__":
    main()
