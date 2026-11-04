"""R1 - Modelo de la red vial: pesos de las aristas, ubicación de lugares y carga del grafo procesado."""
import csv
import math
import re

from pyproj import Transformer

from .config import ARISTAS, CRS_UTM, NODOS

MPH_A_KMH = 1.609344

# Velocidad (km/h) por tipo de vía para los tipos que no tienen NINGÚN tramo con maxspeed en OSM.
# Valores dentro de los límites de la Ley 769 de 2002 (arts. 106 y 107, modificados por la
# Ley 1239 de 2008): zonas residenciales 30 km/h, vías urbanas máx. 80 km/h (50 km/h tras la
# Ley 2251 de 2022), carreteras máx. 120 km/h. Ver docs/notas_R1.md.
VELOCIDAD_POR_TIPO = {
    "trunk": 80, "trunk_link": 50,
    "primary": 60, "primary_link": 40,
    "secondary": 50, "secondary_link": 40,
    "tertiary": 40, "tertiary_link": 30,
    "unclassified": 30, "residential": 30, "road": 30,
    "living_street": 20, "service": 20,
}
VELOCIDAD_DEFECTO = 30  # tipo desconocido: se trata como vía residencial


def parsear_maxspeed(valor):
    """Convierte el atributo maxspeed de OSM a km/h. Devuelve None si no se puede leer.

    Acepta: "30", "30 km/h", "20 mph", "40|60" o "40;60" (varios carriles: media),
    y listas ["60", "30"] (tramos fusionados al simplificar el grafo: media de los válidos).
    """
    if isinstance(valor, list):
        vals = [v for v in (parsear_maxspeed(x) for x in valor) if v is not None]
        return sum(vals) / len(vals) if vals else None
    if not isinstance(valor, str):
        return None  # None o NaN: el tramo no tiene velocidad en OSM
    vals = []
    for parte in re.split(r"[|;]", valor):
        m = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*(km/h|kmh|kph|mph)?\s*", parte.lower())
        if m is None:
            return None  # p. ej. "CO:urban", "signals", "walk": no numérico
        v = float(m.group(1).replace(",", "."))
        vals.append(v * MPH_A_KMH if m.group(2) == "mph" else v)
    return sum(vals) / len(vals)


def tipo_via(highway):
    """Tipo de vía de una arista; si la simplificación dejó una lista, se toma el primero (como OSMnx)."""
    return highway[0] if isinstance(highway, list) else highway


def asignar_pesos(G):
    """Agrega a cada arista speed_kph, travel_time (s) y velocidad_imputada. Modifica G.

    1) maxspeed de OSM si se puede leer; 2) si no, la media de los tramos del mismo tipo de vía
    con maxspeed; 3) si ningún tramo del tipo la tiene, VELOCIDAD_POR_TIPO.
    Devuelve un resumen por tipo de vía (lista de dicts).
    """
    conocidas = {}  # tipo -> lista de velocidades leídas
    for _, _, d in G.edges(data=True):
        v = parsear_maxspeed(d.get("maxspeed"))
        d["_vel"] = v
        conocidas.setdefault(tipo_via(d.get("highway")), [])
        if v is not None:
            conocidas[tipo_via(d.get("highway"))].append(v)

    media, fuente = {}, {}
    for tipo, vals in conocidas.items():
        if vals:
            media[tipo], fuente[tipo] = sum(vals) / len(vals), "media maxspeed del tipo"
        else:
            media[tipo], fuente[tipo] = VELOCIDAD_POR_TIPO.get(tipo, VELOCIDAD_DEFECTO), "tabla normativa"

    total = {}
    for _, _, d in G.edges(data=True):
        tipo = tipo_via(d.get("highway"))
        v = d.pop("_vel")
        d["velocidad_imputada"] = v is None
        d["speed_kph"] = media[tipo] if v is None else v
        d["travel_time"] = d["length"] / (d["speed_kph"] / 3.6)  # m / (m/s) = s
        total[tipo] = total.get(tipo, 0) + 1

    return [{"tipo_via": t, "aristas": total[t], "con_maxspeed": len(conocidas[t]),
             "velocidad_imputada_kmh": round(media[t], 2), "fuente": fuente[t]}
            for t in sorted(total, key=total.get, reverse=True)]


def estimar_memoria(V, E):
    """MB (10^6 bytes) de la red como matriz y como listas de adyacencia (modelo de bajo nivel
    y matriz como listas de listas en Python). Supuestos en specs/R1.md."""
    return {
        "V": V, "E": E,
        "matriz_bajo_nivel_mb": V * V * 8 / 1e6,          # celda = tiempo float32 + distancia float32
        "listas_bajo_nivel_mb": (E * 12 + V * 8) / 1e6,   # entrada = vecino int32 + 2 float32; V punteros
        "matriz_python_mb": (V * (56 + 8 * V)) / 1e6,      # V listas de V punteros de 8 B (sin contar los floats)
    }


_A_UTM = Transformer.from_crs("EPSG:4326", CRS_UTM, always_xy=True)


def a_utm(lat, lon):
    """(lat, lon) en grados -> (x, y) en metros, UTM zona 18N. Acepta escalares o listas."""
    return _A_UTM.transform(lon, lat)


def asociar_lugares(catalogo_df, nodos):
    """Asocia cada lugar al nodo más cercano en línea recta (distancia euclidiana en UTM 18N).

    catalogo_df: columnas lat, lon (+ las que tenga). nodos: DataFrame con osmid, x_utm, y_utm.
    Búsqueda lineal: O(L * V) para L lugares. Devuelve una copia con nodo, dist_nodo_m, lejano_500m.
    """
    ids = nodos["osmid"].tolist()
    xs = nodos["x_utm"].tolist()
    ys = nodos["y_utm"].tolist()
    px, py = a_utm(catalogo_df["lat"].tolist(), catalogo_df["lon"].tolist())
    elegidos, distancias = [], []
    for x, y in zip(px, py):
        mejor, mejor_d2 = None, math.inf
        for i in range(len(ids)):
            d2 = (xs[i] - x) ** 2 + (ys[i] - y) ** 2  # se compara el cuadrado: evita la raíz
            if d2 < mejor_d2:
                mejor, mejor_d2 = ids[i], d2
        elegidos.append(mejor)
        distancias.append(math.sqrt(mejor_d2))
    res = catalogo_df.copy()
    res["nodo"] = elegidos
    res["dist_nodo_m"] = [round(d, 1) for d in distancias]
    res["lejano_500m"] = res["dist_nodo_m"] > 500
    return res


def cargar_grafo(ruta_nodos=NODOS, ruta_aristas=ARISTAS):
    """Lee el grafo procesado. Devuelve (adj, coords):
    adj[u] = lista de (v, tiempo_s, distancia_m); coords[u] = (lat, lon)."""
    adj, coords = {}, {}
    with open(ruta_nodos, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            n = int(fila["osmid"])
            coords[n] = (float(fila["lat"]), float(fila["lon"]))
            adj[n] = []
    with open(ruta_aristas, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            adj[int(fila["u"])].append((int(fila["v"]), float(fila["tiempo_s"]), float(fila["distancia_m"])))
    return adj, coords
