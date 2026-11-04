"""R1.5 (complemento): exporta la forma real de cada tramo de vía para dibujar rutas en el mapa.

OSMnx simplifica la red: cada arista u->v va de una intersección a otra y la forma de la vía
(curvas intermedias) queda en el atributo `geometry` (LineString con puntos lon, lat orientados
de u a v). aristas.csv solo guarda distancia y tiempo, así que sin este archivo la app une los
nodos con líneas rectas. Igual que en aristas.csv, de las aristas paralelas u->v se toma la de
menor tiempo, que es la que usa Dijkstra. Las aristas sin `geometry` ya son rectas entre u y v.

Salida: data/processed/geometria_aristas.json  {"u,v": [[lat, lon], ...]}
"""
import json

import osmnx as ox

from quindio.config import GEOMETRIAS, GRAFO_SCC


def main():
    G = ox.load_graphml(GRAFO_SCC)
    mejor_tiempo = {}
    geometrias = {}
    for u, v, datos in G.edges(data=True):
        clave = f"{u},{v}"
        if clave in mejor_tiempo and datos["travel_time"] >= mejor_tiempo[clave]:
            continue
        mejor_tiempo[clave] = datos["travel_time"]
        if "geometry" in datos:
            puntos = []
            for lon, lat in datos["geometry"].coords:
                puntos.append([round(lat, 6), round(lon, 6)])
            geometrias[clave] = puntos
        else:
            geometrias.pop(clave, None)  # la paralela más rápida es recta
    GEOMETRIAS.write_text(json.dumps(geometrias, separators=(",", ":")), encoding="utf-8")
    print(f"{len(geometrias)} tramos con forma de {len(mejor_tiempo)} aristas -> {GEOMETRIAS}")


if __name__ == "__main__":
    main()
