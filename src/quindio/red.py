"""R1 - Modelo de la red vial: pesos de las aristas, ubicación de lugares y carga del grafo procesado.

Las funciones algorítmicas (parsear_maxspeed, asignar_pesos, nodo_mas_cercano, asociar_lugares)
están escritas por el "método largo": bucles visibles y pasos numerados, para poder explicarlas
paso a paso. Ejemplo resuelto a mano: docs/paso_a_paso_R1.md (y `python -m quindio.red`).
"""
import csv
import math

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

DIGITOS = "0123456789"


def leer_numero(texto):
    """Convierte un texto como "30", "12.5" o "12,5" en número. Devuelve None si no es un número.

    Idea: recorrer el texto carácter por carácter separando la parte entera de la decimal.

    Pseudocódigo:
        1. parte_entera <- "", parte_decimal <- "", vio_separador <- falso
        2. para cada carácter c del texto:
             si c es dígito: agregarlo a la parte entera (o a la decimal si ya vio el separador)
             si c es "." o ",": si ya había un separador -> no es número; si no, marcarlo
             cualquier otro carácter -> no es número
        3. si no hay parte entera, o hay separador sin decimales -> no es número
        4. devolver float(parte_entera "." parte_decimal)

    Complejidad: O(m) en tiempo para un texto de m caracteres; O(m) en memoria.
    """
    # Paso 1: acumuladores vacíos
    parte_entera = ""
    parte_decimal = ""
    vio_separador = False
    # Paso 2: recorrer carácter por carácter
    for caracter in texto:
        if caracter in DIGITOS:
            if vio_separador:
                parte_decimal = parte_decimal + caracter
            else:
                parte_entera = parte_entera + caracter
        elif caracter == "." or caracter == ",":
            if vio_separador:
                return None  # dos separadores: "1.2.3" no es un número
            vio_separador = True
        else:
            return None  # letra u otro símbolo
    # Paso 3: validar que quedó un número completo
    if parte_entera == "":
        return None
    if vio_separador and parte_decimal == "":
        return None
    # Paso 4: armar el número
    if vio_separador:
        return float(parte_entera + "." + parte_decimal)
    return float(parte_entera)


def parsear_maxspeed(valor):
    """Convierte el atributo maxspeed de OSM a km/h. Devuelve None si no se puede leer.

    Acepta: "30", "30 km/h", "20 mph", "40|60" o "40;60" (varios carriles: media),
    y listas ["60", "30"] (tramos fusionados al simplificar el grafo: media de los válidos).

    Pseudocódigo:
        1. si valor es una lista: parsear cada elemento y devolver la media de los válidos
           (None si ninguno es válido)
        2. si valor no es texto (None o NaN): devolver None
        3. partir el texto en pedazos separados por "|" o ";"
        4. para cada pedazo:
             4a. quitar espacios y pasar a minúsculas
             4b. si termina en "mph", "km/h", "kmh" o "kph": quitar la unidad y anotar el factor
             4c. leer el número (leer_numero); si no es número -> devolver None
             4d. guardar número * factor
        5. devolver la media de los números guardados

    Complejidad: O(m) en tiempo y memoria para un texto de m caracteres.
    """
    # Paso 1: lista de valores -> media de los que se pueden leer
    if isinstance(valor, list):
        suma = 0
        cantidad = 0
        for elemento in valor:
            velocidad = parsear_maxspeed(elemento)
            if velocidad is not None:
                suma = suma + velocidad
                cantidad = cantidad + 1
        if cantidad == 0:
            return None
        return suma / cantidad

    # Paso 2: None o NaN (el tramo no tiene velocidad en OSM)
    if not isinstance(valor, str):
        return None

    # Paso 3: partir por "|" o ";" recorriendo el texto
    pedazos = []
    pedazo_actual = ""
    for caracter in valor:
        if caracter == "|" or caracter == ";":
            pedazos.append(pedazo_actual)
            pedazo_actual = ""
        else:
            pedazo_actual = pedazo_actual + caracter
    pedazos.append(pedazo_actual)

    # Paso 4: leer cada pedazo
    velocidades = []
    for pedazo in pedazos:
        # Paso 4a: limpiar
        texto = pedazo.strip().lower()
        # Paso 4b: quitar la unidad (si la hay)
        factor = 1.0
        if texto.endswith("mph"):
            factor = MPH_A_KMH
            texto = texto[:-3]
        elif texto.endswith("km/h"):
            texto = texto[:-4]
        elif texto.endswith("kmh") or texto.endswith("kph"):
            texto = texto[:-3]
        texto = texto.strip()
        # Paso 4c: leer el número
        numero = leer_numero(texto)
        if numero is None:
            return None  # p. ej. "CO:urban", "signals", "walk": no numérico
        # Paso 4d: guardar en km/h
        if factor == 1.0:
            velocidades.append(numero)
        else:
            velocidades.append(numero * factor)

    # Paso 5: media de los pedazos
    suma = 0
    for velocidad in velocidades:
        suma = suma + velocidad
    return suma / len(velocidades)


def tipo_via(highway):
    """Tipo de vía de una arista; si la simplificación dejó una lista, se toma el primero (como OSMnx)."""
    if isinstance(highway, list):
        return highway[0]
    return highway


def asignar_pesos(G, traza=None):
    """Agrega a cada arista speed_kph, travel_time (s) y velocidad_imputada. Modifica G.

    Idea: dos pasadas por las aristas. En la primera se lee la velocidad de OSM y se agrupan las
    velocidades conocidas por tipo de vía; con eso se calcula una velocidad de reemplazo por tipo.
    En la segunda se asigna a cada arista su velocidad (leída o de reemplazo) y su tiempo.

    Pseudocódigo:
        1. para cada arista (u, v): leer maxspeed (parsear_maxspeed) y, si se pudo leer,
           agregarla a la lista de velocidades conocidas de su tipo de vía
        2. para cada tipo de vía:
             si tiene velocidades conocidas: reemplazo <- media de esas velocidades
             si no: reemplazo <- VELOCIDAD_POR_TIPO[tipo] (o 30 km/h si el tipo no está)
        3. para cada arista:
             velocidad <- la leída en el paso 1, o el reemplazo de su tipo si no se pudo leer
             travel_time <- length / (velocidad / 3.6)          (metros / (m/s) = segundos)
        4. devolver un resumen por tipo de vía

    Complejidad: O(E) en tiempo (dos recorridos de las E aristas, más O(T log T) para ordenar el
    resumen de T tipos de vía, T << E) y O(E) en memoria.
    traza: lista opcional; si no es None se le agregan textos con cada decisión (para la demo).
    """
    # Paso 1: primera pasada, velocidades conocidas por tipo de vía
    conocidas = {}  # tipo -> lista de velocidades leídas
    for u, v, datos in G.edges(data=True):
        tipo = tipo_via(datos.get("highway"))
        velocidad_leida = parsear_maxspeed(datos.get("maxspeed"))
        datos["_vel"] = velocidad_leida
        if tipo not in conocidas:
            conocidas[tipo] = []
        if velocidad_leida is not None:
            conocidas[tipo].append(velocidad_leida)
        if traza is not None:
            traza.append(f"Paso 1: arista {u}->{v} tipo={tipo} maxspeed={datos.get('maxspeed')!r} "
                         f"-> leída={velocidad_leida}")

    # Paso 2: velocidad de reemplazo por tipo de vía
    reemplazo = {}
    fuente = {}
    for tipo in conocidas:
        lista = conocidas[tipo]
        if len(lista) > 0:
            suma = 0
            for velocidad in lista:
                suma = suma + velocidad
            reemplazo[tipo] = suma / len(lista)
            fuente[tipo] = "media maxspeed del tipo"
        elif tipo in VELOCIDAD_POR_TIPO:
            reemplazo[tipo] = VELOCIDAD_POR_TIPO[tipo]
            fuente[tipo] = "tabla normativa"
        else:
            reemplazo[tipo] = VELOCIDAD_DEFECTO
            fuente[tipo] = "tabla normativa"
        if traza is not None:
            traza.append(f"Paso 2: tipo={tipo} conocidas={lista} -> reemplazo={reemplazo[tipo]} "
                         f"({fuente[tipo]})")

    # Paso 3: segunda pasada, velocidad y tiempo de cada arista
    total = {}
    for u, v, datos in G.edges(data=True):
        tipo = tipo_via(datos.get("highway"))
        velocidad_leida = datos.pop("_vel")
        if velocidad_leida is None:
            datos["velocidad_imputada"] = True
            datos["speed_kph"] = reemplazo[tipo]
        else:
            datos["velocidad_imputada"] = False
            datos["speed_kph"] = velocidad_leida
        velocidad_m_s = datos["speed_kph"] / 3.6
        datos["travel_time"] = datos["length"] / velocidad_m_s  # m / (m/s) = s
        if tipo not in total:
            total[tipo] = 0
        total[tipo] = total[tipo] + 1
        if traza is not None:
            traza.append(f"Paso 3: arista {u}->{v} {datos['length']} m a {datos['speed_kph']} km/h "
                         f"-> {datos['travel_time']:.2f} s")

    # Paso 4: resumen por tipo, ordenado de mayor a menor cantidad de aristas solo para
    # presentarlo. Ordenamiento por inserción a mano (pocos tipos de vía, ~11).
    tipos_ordenados = []
    for tipo in total:
        posicion = len(tipos_ordenados)
        while posicion > 0 and total[tipos_ordenados[posicion - 1]] < total[tipo]:
            posicion = posicion - 1
        tipos_ordenados.insert(posicion, tipo)
    resumen = []
    for tipo in tipos_ordenados:
        resumen.append({"tipo_via": tipo, "aristas": total[tipo], "con_maxspeed": len(conocidas[tipo]),
                        "velocidad_imputada_kmh": round(reemplazo[tipo], 2), "fuente": fuente[tipo]})
    return resumen


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


def nodo_mas_cercano(x, y, ids, xs, ys, traza=None):
    """Búsqueda lineal del nodo más cercano al punto (x, y) en metros (UTM).

    ids, xs, ys: listas paralelas con el id y las coordenadas de cada nodo.
    Devuelve (id_del_nodo_mas_cercano, distancia_en_metros).

    Idea: revisar TODOS los nodos y recordar el de menor distancia. Se compara el cuadrado de la
    distancia (dx² + dy²) porque la raíz es creciente: si a² < b² entonces a < b; así la raíz se
    calcula una sola vez, al final.

    Pseudocódigo:
        1. mejor_nodo <- ninguno, mejor_d2 <- infinito
        2. para i = 0, 1, ..., V-1:
             2a. dx <- xs[i] - x ;  dy <- ys[i] - y
             2b. d2 <- dx*dx + dy*dy
             2c. si d2 < mejor_d2: mejor_nodo <- ids[i], mejor_d2 <- d2
        3. devolver mejor_nodo, raíz(mejor_d2)

    Invariante: al terminar la vuelta i, mejor_nodo es el más cercano entre los nodos 0..i.
    Complejidad: Θ(V) en tiempo (una comparación por nodo) y O(1) de memoria extra.
    """
    # Paso 1: todavía no hay candidato
    mejor_nodo = None
    mejor_d2 = math.inf
    # Paso 2: recorrer todos los nodos
    for i in range(len(ids)):
        # Paso 2a: diferencias en x y en y
        dx = xs[i] - x
        dy = ys[i] - y
        # Paso 2b: distancia al cuadrado
        d2 = dx * dx + dy * dy
        # Paso 2c: ¿es mejor que el mejor visto hasta ahora?
        if d2 < mejor_d2:
            if traza is not None:
                traza.append(f"nodo {ids[i]}: d = {math.sqrt(d2):.1f} m < mejor anterior -> nuevo mejor")
            mejor_nodo = ids[i]
            mejor_d2 = d2
        elif traza is not None:
            traza.append(f"nodo {ids[i]}: d = {math.sqrt(d2):.1f} m, no mejora")
    # Paso 3: una sola raíz cuadrada al final
    return mejor_nodo, math.sqrt(mejor_d2)


def asociar_lugares(catalogo_df, nodos, traza=None):
    """Asocia cada lugar al nodo más cercano en línea recta (distancia euclidiana en UTM 18N).

    catalogo_df: columnas lat, lon (+ las que tenga). nodos: DataFrame con osmid, x_utm, y_utm.
    Devuelve una copia con nodo, dist_nodo_m, lejano_500m.

    Pseudocódigo:
        1. pasar las columnas de los nodos a listas (ids, xs, ys)
        2. proyectar (lat, lon) de cada lugar a metros UTM 18N (pyproj)
        3. para cada lugar: (nodo, distancia) <- nodo_mas_cercano(x, y, ids, xs, ys)
        4. agregar las columnas nodo, dist_nodo_m (redondeada a 0.1 m) y lejano_500m (> 500 m)

    Complejidad: Θ(L · V) en tiempo para L lugares y V nodos; Θ(V + L) en memoria.
    """
    # Paso 1: columnas de los nodos como listas
    ids = nodos["osmid"].tolist()
    xs = nodos["x_utm"].tolist()
    ys = nodos["y_utm"].tolist()
    # Paso 2: lugares en metros
    lugares_x, lugares_y = a_utm(catalogo_df["lat"].tolist(), catalogo_df["lon"].tolist())
    # Paso 3: búsqueda lineal para cada lugar
    elegidos = []
    distancias = []
    marcas_lejano = []
    for k in range(len(lugares_x)):
        if traza is not None:
            traza.append(f"--- lugar {k} en ({lugares_x[k]:.1f}, {lugares_y[k]:.1f})")
        nodo, distancia = nodo_mas_cercano(lugares_x[k], lugares_y[k], ids, xs, ys, traza)
        distancia_redondeada = round(distancia, 1)
        elegidos.append(nodo)
        distancias.append(distancia_redondeada)
        marcas_lejano.append(distancia_redondeada > 500)
    # Paso 4: columnas nuevas
    resultado = catalogo_df.copy()
    resultado["nodo"] = elegidos
    resultado["dist_nodo_m"] = distancias
    resultado["lejano_500m"] = marcas_lejano
    return resultado


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


if __name__ == "__main__":
    # Demostración con ejemplos pequeños resueltos a mano (docs/paso_a_paso_R1.md).
    import networkx as nx

    print("=== 1. Nodo más cercano (coordenadas en metros) ===")
    ids_demo = ["A", "B", "C", "D"]
    xs_demo = [0.0, 300.0, 100.0, 400.0]
    ys_demo = [0.0, 0.0, 200.0, 400.0]
    pasos = []
    nodo, d = nodo_mas_cercano(120.0, 160.0, ids_demo, xs_demo, ys_demo, traza=pasos)
    for p in pasos:
        print("  " + p)
    print(f"  Resultado: nodo {nodo} a {d:.1f} m (esperado C a 44.7 m)")

    print("\n=== 2. Pesos de las aristas ===")
    G = nx.MultiDiGraph()
    G.add_edge(1, 2, length=1000.0, highway="secondary", maxspeed="50")
    G.add_edge(2, 3, length=360.0, highway="residential", maxspeed="20")
    G.add_edge(3, 4, length=360.0, highway="residential", maxspeed="40 km/h")
    G.add_edge(4, 1, length=1000.0, highway="residential")
    G.add_edge(4, 5, length=900.0, highway="primary_link")
    pasos = []
    asignar_pesos(G, traza=pasos)
    for p in pasos:
        print("  " + p)
