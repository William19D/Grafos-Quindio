"""R1.4 - Asocia cada lugar del catálogo al nodo más cercano de la componente (UTM 18N).

Entrada: data/catalogo.csv (id,nombre,...,categoria,lat,lon) y data/processed/nodos.csv.
Salida: data/processed/lugares_nodos.csv y resultados/r1_lugares_lejanos.csv (lugares a > 500 m).
"""
import networkx as nx
import osmnx as ox
import pandas as pd

from quindio.config import CATALOGO, CRS_UTM, LUGARES_NODOS, NODOS, RESULTADOS
from quindio.red import a_utm, asociar_lugares


def main():
    catalogo = pd.read_csv(CATALOGO)
    nodos = pd.read_csv(NODOS)
    res = asociar_lugares(catalogo, nodos)

    # verificación contra OSMnx (solo para comprobar): mismo nodo para cada lugar
    Gp = nx.MultiDiGraph(crs=CRS_UTM)
    Gp.add_nodes_from((n, {"x": x, "y": y}) for n, x, y in zip(nodos["osmid"], nodos["x_utm"], nodos["y_utm"]))
    X, Y = a_utm(catalogo["lat"].tolist(), catalogo["lon"].tolist())
    assert list(ox.distance.nearest_nodes(Gp, X, Y)) == res["nodo"].tolist()

    primeras = ["id", "nombre", "categoria", "lat", "lon", "nodo", "dist_nodo_m", "lejano_500m"]
    res = res[primeras + [c for c in res.columns if c not in primeras]]
    res.to_csv(LUGARES_NODOS, index=False)

    lejanos = res[res["lejano_500m"]][["id", "nombre", "categoria", "lat", "lon", "nodo", "dist_nodo_m"]]
    lejanos.sort_values("dist_nodo_m", ascending=False).to_csv(RESULTADOS / "r1_lugares_lejanos.csv", index=False)
    print(f"{len(res)} lugares asociados; {len(lejanos)} a más de 500 m de su nodo")
    print(res["dist_nodo_m"].describe())
    print(lejanos.to_string(index=False))


if __name__ == "__main__":
    main()
