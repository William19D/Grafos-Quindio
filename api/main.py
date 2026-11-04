"""R5 - API de la aplicación demostrativa (FastAPI).

Solo USA los algoritmos propios del proyecto (Dijkstra de R2, QuickHull de R3, Held-Karp y vecino
más cercano de R4); aquí no se reimplementa ninguno. Ver specs/R5.md.

Correr (desde la raíz del repositorio):
    .venv/Scripts/python.exe -m uvicorn api.main:app --port 8000
Si existe web/dist (npm run build dentro de web/), la aplicación completa queda en http://localhost:8000
"""
import csv
import math
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))  # para poder importar el paquete quindio

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.gzip import GZipMiddleware  # noqa: E402
from pyproj import Transformer  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import json  # noqa: E402

from quindio.config import CRS_UTM, FIGURAS, GEOMETRIAS, LUGARES_NODOS, NODOS, RESULTADOS  # noqa: E402
from quindio.dijkstra import dijkstra_cola  # noqa: E402
from quindio.envolvente import area_km2, preparar_puntos, quickhull  # noqa: E402
from quindio.red import cargar_grafo  # noqa: E402
from quindio.tsp import held_karp, leer_matriz, submatriz, vecino_mas_cercano  # noqa: E402

LIMITE_JORNADA_H = 11
MIN_ATRACTIVOS = 6
MAX_ATRACTIVOS = 8
WEB_DIST = RAIZ / "web" / "dist"
A_GRADOS = Transformer.from_crs(CRS_UTM, "EPSG:4326", always_xy=True)  # UTM 18N -> lat/lon

# Todo lo que se carga una sola vez al iniciar el servidor.
estado = {}


# ---------------------------------------------------------------------------------------------
# Carga de datos (una vez)
# ---------------------------------------------------------------------------------------------

def numero_o_nada(texto):
    """'90' -> 90, '' -> None."""
    if texto == "":
        return None
    return int(float(texto))


def leer_lugares():
    """Lee data/processed/lugares_nodos.csv (catálogo + nodo asociado en R1)."""
    lugares = []
    with open(LUGARES_NODOS, encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            lugares.append({
                "id": fila["id"], "nombre": fila["nombre"], "categoria": fila["categoria"],
                "municipio": fila["municipio"], "lat": float(fila["lat"]), "lon": float(fila["lon"]),
                "nodo": int(fila["nodo"]), "dist_nodo_m": float(fila["dist_nodo_m"]),
                "duracion_visita_min": numero_o_nada(fila["duracion_visita_min"]),
            })
    return lugares


def leer_puntos_utm():
    """Coordenadas UTM de los nodos, redondeadas a enteros y sin repetidos (como en R3)."""
    xs, ys = [], []
    with open(NODOS, encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            xs.append(float(fila["x_utm"]))
            ys.append(float(fila["y_utm"]))
    return preparar_puntos(xs, ys)


def cargar_todo():
    adj, coords = cargar_grafo()
    estado["adj"] = adj
    estado["coords"] = coords
    estado["lugares"] = leer_lugares()
    estado["lugar"] = {lugar["id"]: lugar for lugar in estado["lugares"]}
    _ids, estado["matriz"] = leer_matriz()
    estado["puntos_utm"] = leer_puntos_utm()
    # Forma real de cada tramo ("u,v" -> [[lat, lon], ...]); sin ella la ruta se dibuja recta
    # entre intersecciones. La genera experimentos/r1_geometrias.py.
    estado["geometrias"] = {}
    if GEOMETRIAS.exists():
        estado["geometrias"] = json.loads(GEOMETRIAS.read_text(encoding="utf-8"))
    estado["rutas_guardadas"] = {}  # (nodo_a, nodo_b) -> resultado de ruta_entre_nodos


@asynccontextmanager
async def al_iniciar(_app):
    cargar_todo()
    yield


app = FastAPI(title="Rutas del Paisaje Cultural Cafetero", lifespan=al_iniciar)
app.add_middleware(GZipMiddleware, minimum_size=1000)  # el árbol de exploración pesa ~1,7 MB sin comprimir


# ---------------------------------------------------------------------------------------------
# Ayudas
# ---------------------------------------------------------------------------------------------

def buscar_lugar(identificador):
    if identificador not in estado["lugar"]:
        raise HTTPException(status_code=404, detail=f"No existe el lugar '{identificador}'")
    return estado["lugar"][identificador]


def distancia_de_ruta(adj, ruta):
    """Suma la distancia (m) de las aristas de la ruta. Si hubiera aristas paralelas u->v se toma
    la de menor tiempo, que es la que usó Dijkstra."""
    total_m = 0.0
    for posicion in range(len(ruta) - 1):
        u = ruta[posicion]
        v = ruta[posicion + 1]
        mejor_tiempo = math.inf
        distancia_elegida = 0.0
        for vecino, tiempo, distancia in adj[u]:
            if vecino == v and tiempo < mejor_tiempo:
                mejor_tiempo = tiempo
                distancia_elegida = distancia
        total_m = total_m + distancia_elegida
    return total_m


def ruta_entre_nodos(nodo_origen, nodo_destino):
    """Dijkstra con cola de prioridad (R2) + distancia y polilínea. Mide solo el algoritmo."""
    adj = estado["adj"]
    inicio = time.perf_counter()
    tiempo_s, ruta, explorados = dijkstra_cola(adj, nodo_origen, nodo_destino)
    ms = (time.perf_counter() - inicio) * 1000
    return {"tiempo_s": tiempo_s, "distancia_km": distancia_de_ruta(adj, ruta) / 1000,
            "nodos_explorados": explorados, "nodos_ruta": len(ruta), "ms": ms,
            "polilinea": polilinea_de_ruta(ruta)}


def polilinea_de_ruta(ruta):
    """Puntos [lat, lon] para dibujar la ruta siguiendo la vía: por cada tramo u->v se agregan
    los puntos intermedios de su forma real y luego el nodo v (si el tramo es recto, solo v)."""
    if not ruta:
        return []
    lat, lon = estado["coords"][ruta[0]]
    polilinea = [[lat, lon]]
    for posicion in range(len(ruta) - 1):
        clave = f"{ruta[posicion]},{ruta[posicion + 1]}"
        if clave in estado["geometrias"]:
            puntos = estado["geometrias"][clave]
            # el primero y el último de la forma son u y v; se usan las coordenadas exactas del nodo
            for indice in range(1, len(puntos) - 1):
                polilinea.append(puntos[indice])
        lat, lon = estado["coords"][ruta[posicion + 1]]
        polilinea.append([lat, lon])
    return polilinea


def ruta_guardada(nodo_origen, nodo_destino):
    """Igual que ruta_entre_nodos, pero recuerda cada par ya calculado (para los tramos)."""
    clave = (nodo_origen, nodo_destino)
    if clave not in estado["rutas_guardadas"]:
        estado["rutas_guardadas"][clave] = ruta_entre_nodos(nodo_origen, nodo_destino)
    return estado["rutas_guardadas"][clave]


def tabla_del_dia(lugares, recorrido):
    """Arma la tabla del anexo para un recorrido [0, a1, ..., ak, 0] sobre `lugares`.

    Pseudocódigo (mismo cálculo que tsp.itinerario):
        1. acumulado <- 0
        2. para cada tramo (anterior -> actual) del recorrido:
             desplazamiento <- matriz[anterior][actual] / 60
             si es el último tramo: fila "Regreso", acumulado += desplazamiento
             si no: acumulado += desplazamiento + visita del lugar actual
        3. jornada = acumulado / 60 horas; cabe si jornada <= 11
    """
    matriz = estado["matriz"]
    filas = []
    tramos = []
    orden = [lugares[0]]
    acumulado_min = 0.0
    total_desplazamientos_min = 0.0
    total_visitas_min = 0
    ultima = len(recorrido) - 1
    for posicion in range(1, len(recorrido)):
        anterior = lugares[recorrido[posicion - 1]]
        actual = lugares[recorrido[posicion]]
        desplazamiento_min = matriz[anterior][actual] / 60
        total_desplazamientos_min = total_desplazamientos_min + desplazamiento_min
        if posicion == ultima:
            etiqueta = "Regreso"
            visita = None
            acumulado_min = acumulado_min + desplazamiento_min
        else:
            etiqueta = posicion
            visita = estado["lugar"][actual]["duracion_visita_min"]
            total_visitas_min = total_visitas_min + visita
            acumulado_min = acumulado_min + desplazamiento_min + visita
        filas.append({"orden": etiqueta, "lugar": actual, "nombre": estado["lugar"][actual]["nombre"],
                      "desplazamiento_desde_anterior_min": round(desplazamiento_min, 1),
                      "visita_min": visita, "tiempo_acumulado_h": round(acumulado_min / 60, 2)})
        tramo = ruta_guardada(estado["lugar"][anterior]["nodo"], estado["lugar"][actual]["nodo"])
        tramos.append({"desde": anterior, "hasta": actual, "tiempo_min": round(desplazamiento_min, 1),
                       "polilinea": tramo["polilinea"]})
        orden.append(actual)
    jornada_h = acumulado_min / 60
    return {"orden": orden, "filas": filas, "tramos": tramos,
            "total_desplazamientos_min": round(total_desplazamientos_min, 1),
            "total_visitas_min": total_visitas_min, "jornada_h": jornada_h,
            "limite_h": LIMITE_JORNADA_H, "cabe": jornada_h <= LIMITE_JORNADA_H}


def requerimiento_de(archivo):
    """'r2_dijkstra.csv' -> 'R2'; 'catalogo_verificacion.csv' -> 'Catálogo'."""
    if archivo.startswith("catalogo"):
        return "Catálogo"
    return archivo.split("_")[0].upper()


TITULOS = {
    "catalogo_verificacion.csv": "Verificación del catálogo de lugares",
    "r1_tamano.csv": "Tamaño de la red",
    "r1_velocidades.csv": "Velocidades por tipo de vía",
    "r1_lugares_lejanos.csv": "Lugares a más de 500 m de la red",
    "r1_scc_tiempos.csv": "Componente fuertemente conexa: tiempos",
    "r2_dijkstra.csv": "Dijkstra: lineal contra cola de prioridad",
    "r2_cociente.csv": "Cociente lineal / cola: resumen",
    "r2_cociente_pares.csv": "Cociente lineal / cola por par",
    "r2_verificacion.csv": "Verificación de Dijkstra contra NetworkX",
    "r3_envolvente.csv": "QuickHull propio contra SciPy",
    "r3_niveles.csv": "QuickHull: puntos descartados por nivel",
    "r4_exactos.csv": "Fuerza bruta contra Held-Karp",
    "r4_held_karp_extendido.csv": "Held-Karp con k grande",
    "r4_calidad.csv": "Vecino más cercano: brecha con el óptimo",
    "r4_calidad_detalle.csv": "Brecha por instancia",
    "r4_memoria.csv": "Held-Karp: memoria",
    "r4_itinerario.csv": "Itinerario de un día",
}


def tamano_png(ruta):
    """Ancho y alto en píxeles de un PNG: están en los bytes 16 a 24 del archivo (bloque IHDR).
    La página los usa para reservar el espacio de la imagen antes de que cargue."""
    with open(ruta, "rb") as archivo:
        cabecera = archivo.read(24)
    return int.from_bytes(cabecera[16:20], "big"), int.from_bytes(cabecera[20:24], "big")


def convertir(texto):
    """Convierte el texto de una celda en número cuando se puede."""
    try:
        numero = float(texto)
    except ValueError:
        return texto
    if not math.isfinite(numero):
        return texto  # "inf" o "nan" no son válidos en JSON: se dejan como texto
    if numero.is_integer() and "." not in texto:
        return int(numero)
    return numero


# ---------------------------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------------------------

@app.get("/api/lugares")
def lugares():
    return estado["lugares"]


@app.get("/api/ruta")
def ruta(origen: str, destino: str):
    lugar_o = buscar_lugar(origen)
    lugar_d = buscar_lugar(destino)
    resultado = ruta_entre_nodos(lugar_o["nodo"], lugar_d["nodo"])
    resultado["tiempo_min"] = resultado["tiempo_s"] / 60
    resultado["nodos_grafo"] = len(estado["adj"])
    resultado["origen"] = {"id": origen, "nombre": lugar_o["nombre"]}
    resultado["destino"] = {"id": destino, "nombre": lugar_d["nombre"]}
    return resultado


def tramo_dibujable(u, v):
    """Puntos [lat, lon] del tramo u->v siguiendo la vía (5 decimales ≈ 1 m, para aligerar)."""
    clave = f"{u},{v}"
    if clave in estado["geometrias"]:
        puntos = estado["geometrias"][clave]
    else:
        puntos = [estado["coords"][u], estado["coords"][v]]
    tramo = []
    for lat, lon in puntos:
        tramo.append([round(lat, 5), round(lon, 5)])
    return tramo


@app.get("/api/arbol")
def arbol(origen: str, destino: str):
    """Árbol de exploración de Dijkstra (cola de prioridad) de origen a destino, en el orden en
    que cada nodo salió de la cola: tramo predecesor -> nodo y su distancia definitiva."""
    lugar_o = buscar_lugar(origen)
    lugar_d = buscar_lugar(destino)
    pasos = []
    tiempo_s, ruta_nodos, explorados = dijkstra_cola(estado["adj"], lugar_o["nodo"], lugar_d["nodo"], arbol=pasos)
    tramos = []
    tiempos_s = []
    for predecesor, nodo, distancia in pasos:
        if predecesor is None:
            continue  # el origen no tiene tramo de llegada
        tramos.append(tramo_dibujable(predecesor, nodo))
        tiempos_s.append(round(distancia, 1))
    return {"origen": {"id": origen, "nombre": lugar_o["nombre"]},
            "destino": {"id": destino, "nombre": lugar_d["nombre"]},
            "tiempo_s": tiempo_s, "nodos_explorados": explorados, "nodos_grafo": len(estado["adj"]),
            "tramos": tramos, "tiempos_s": tiempos_s, "ruta": polilinea_de_ruta(ruta_nodos)}


@app.get("/api/envolvente")
def envolvente():
    puntos = estado["puntos_utm"]
    inicio = time.perf_counter()
    poligono = quickhull(puntos)
    ms = (time.perf_counter() - inicio) * 1000
    # Pasar cada vértice (x, y) de metros UTM a (lat, lon).
    vertices = []
    for x, y in poligono:
        lon, lat = A_GRADOS.transform(x, y)
        vertices.append({"lat": lat, "lon": lon, "x_utm": x, "y_utm": y})
    return {"vertices": vertices, "n_vertices": len(poligono), "n_puntos": len(puntos),
            "area_km2": round(area_km2(poligono), 2), "ms": ms}


class PedidoItinerario(BaseModel):
    partida: str = "ARM"
    atractivos: list[str]


def validar_itinerario(pedido):
    """Devuelve una lista de errores en español (vacía si el pedido es válido)."""
    errores = []
    cantidad = len(pedido.atractivos)
    if cantidad < MIN_ATRACTIVOS or cantidad > MAX_ATRACTIVOS:
        errores.append(f"Elige entre {MIN_ATRACTIVOS} y {MAX_ATRACTIVOS} atractivos (llegaron {cantidad}).")
    if len(set(pedido.atractivos)) != cantidad:
        errores.append("Hay atractivos repetidos.")
    if pedido.partida not in estado["lugar"]:
        errores.append(f"No existe la partida '{pedido.partida}'.")
    if pedido.partida in pedido.atractivos:
        errores.append("La partida no puede estar también entre los atractivos.")
    for identificador in pedido.atractivos:
        if identificador not in estado["lugar"]:
            errores.append(f"No existe el lugar '{identificador}'.")
        elif estado["lugar"][identificador]["duracion_visita_min"] is None:
            errores.append(f"'{identificador}' no es un atractivo con duración de visita.")
    return errores


@app.post("/api/itinerario")
def itinerario_del_dia(pedido: PedidoItinerario):
    errores = validar_itinerario(pedido)
    if errores:
        raise HTTPException(status_code=422, detail=errores)
    lugares = [pedido.partida] + list(pedido.atractivos)
    d = submatriz(estado["matriz"], lugares)

    inicio = time.perf_counter()
    _costo_hk, recorrido_hk = held_karp(d)
    ms_hk = (time.perf_counter() - inicio) * 1000

    inicio = time.perf_counter()
    _costo_voraz, recorrido_voraz = vecino_mas_cercano(d)
    ms_voraz = (time.perf_counter() - inicio) * 1000

    hk = tabla_del_dia(lugares, recorrido_hk)
    hk["ms"] = ms_hk
    voraz = tabla_del_dia(lugares, recorrido_voraz)
    voraz["ms"] = ms_voraz
    diferencia = voraz["total_desplazamientos_min"] - hk["total_desplazamientos_min"]
    return {"partida": pedido.partida, "held_karp": hk, "voraz": voraz,
            "diferencia_min": round(diferencia, 1),
            "diferencia_pct": round(100 * diferencia / hk["total_desplazamientos_min"], 2)}


@app.get("/api/resultados")
def resultados():
    tablas = []
    for ruta_csv in sorted(RESULTADOS.glob("*.csv")):
        if ruta_csv.name == "matriz_tiempos.csv":
            continue  # matriz 46 x 46: no es una tabla de resultados para leer en pantalla
        with open(ruta_csv, encoding="utf-8") as archivo:
            lector = csv.reader(archivo)
            columnas = next(lector)
            filas = []
            for fila in lector:
                filas.append([convertir(celda) for celda in fila])
        tablas.append({"archivo": ruta_csv.name, "requerimiento": requerimiento_de(ruta_csv.name),
                       "titulo": TITULOS.get(ruta_csv.name, ruta_csv.stem), "columnas": columnas,
                       "filas": filas})
    figuras = []
    for ruta_png in sorted(FIGURAS.glob("*.png")):
        ancho, alto = tamano_png(ruta_png)
        figuras.append({"archivo": ruta_png.name, "requerimiento": requerimiento_de(ruta_png.name),
                        "url": "/figuras/" + ruta_png.name, "ancho": ancho, "alto": alto})
    return {"tablas": tablas, "figuras": figuras}


# ---------------------------------------------------------------------------------------------
# Archivos estáticos (al final, para que no tapen las rutas /api)
# ---------------------------------------------------------------------------------------------

app.mount("/figuras", StaticFiles(directory=FIGURAS), name="figuras")
if WEB_DIST.exists():
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
