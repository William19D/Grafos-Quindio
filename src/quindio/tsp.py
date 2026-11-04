"""R4 - Ruta óptima de recorrido: problema del viajero (TSP) asimétrico, "método largo".

Representación común: una matriz cuadrada d (lista de listas) de tamaño (k+1)×(k+1). El índice 0
es el lugar de partida y 1..k son los lugares que hay que visitar. d[i][j] es el tiempo para ir
de i a j (puede ser distinto de d[j][i]: la matriz es asimétrica).
Un recorrido es [0, a1, a2, ..., ak, 0]. Todas las funciones devuelven (costo, recorrido).

Algoritmos propios:
    permutaciones_heap: generador de permutaciones (algoritmo de Heap).
    fuerza_bruta:       prueba las k! órdenes posibles.               O(k·k!)
    held_karp:          programación dinámica sobre subconjuntos.     O(k²·2^k)
    vecino_mas_cercano: heurística voraz.                             O(k²)
    itinerario / ajustar_a_jornada: el itinerario de un día con Held-Karp.

Referencias:
    M. Held y R. M. Karp, "A dynamic programming approach to sequencing problems", Journal of the
    SIAM 10(1), pp. 196-210, 1962.
    R. Bellman, "Dynamic programming treatment of the travelling salesman problem", Journal of
    the ACM 9(1), pp. 61-63, 1962.
    B. R. Heap, "Permutations by interchanges", The Computer Journal 6(3), pp. 293-294, 1963;
    R. Sedgewick, "Permutation generation methods", ACM Computing Surveys 9(2), pp. 137-164, 1977.
    D. Rosenkrantz, R. Stearns y P. Lewis, "An analysis of several heuristics for the traveling
    salesman problem", SIAM Journal on Computing 6(3), pp. 563-581, 1977 (vecino más cercano).

Ejemplo resuelto a mano: docs/paso_a_paso_R4.md (y `python -m quindio.tsp`).
"""
import csv
import math

from .config import CATALOGO, MATRIZ_TIEMPOS


# ---------------------------------------------------------------------------------------------
# Lectura de datos (no forma parte de lo que se mide)
# ---------------------------------------------------------------------------------------------

def leer_matriz(ruta=MATRIZ_TIEMPOS):
    """Lee la matriz de tiempos de R2. Devuelve (ids, matriz) con matriz[a][b] en segundos."""
    with open(ruta, encoding="utf-8") as archivo:
        lector = csv.reader(archivo)
        encabezado = next(lector)
        ids = encabezado[1:]
        matriz = {}
        for fila in lector:
            origen = fila[0]
            matriz[origen] = {}
            for posicion in range(len(ids)):
                matriz[origen][ids[posicion]] = float(fila[posicion + 1])
    return ids, matriz


def leer_catalogo(ruta=CATALOGO):
    """Lee el catálogo. Devuelve {id: {"nombre", "categoria", "duracion_min"}} (duración None si no tiene)."""
    catalogo = {}
    with open(ruta, encoding="utf-8") as archivo:
        for fila in csv.DictReader(archivo):
            duracion = None
            if fila["duracion_visita_min"] != "":
                duracion = int(float(fila["duracion_visita_min"]))
            catalogo[fila["id"]] = {"nombre": fila["nombre"], "categoria": fila["categoria"],
                                    "duracion_min": duracion}
    return catalogo


def submatriz(matriz, lugares):
    """Arma la matriz d (lista de listas) para los lugares dados; lugares[0] es la partida. O(k²)."""
    d = []
    for origen in lugares:
        fila = []
        for destino in lugares:
            fila.append(matriz[origen][destino])
        d.append(fila)
    return d


def costo_recorrido(d, recorrido):
    """Suma d[recorrido[t]][recorrido[t+1]] para todos los tramos. O(k)."""
    total = 0
    for t in range(len(recorrido) - 1):
        total = total + d[recorrido[t]][recorrido[t + 1]]
    return total


def _conjunto_texto(mascara, k):
    """Convierte una máscara de bits en texto, p. ej. 0b101 -> "{1,3}" (solo para la traza)."""
    elementos = []
    for lugar in range(1, k + 1):
        if mascara & (1 << (lugar - 1)):
            elementos.append(str(lugar))
    return "{" + ",".join(elementos) + "}"


def _texto_lista(lista):
    """[0, 2, 3, 1, 0] -> "0-2-3-1-0" (solo para la traza)."""
    partes = []
    for x in lista:
        partes.append(str(x))
    return "-".join(partes)


# ---------------------------------------------------------------------------------------------
# Generador de permutaciones (algoritmo de Heap)
# ---------------------------------------------------------------------------------------------

def permutaciones_heap(elementos):
    """Genera todas las permutaciones de `elementos` con el algoritmo de Heap (versión iterativa).

    Idea: cada permutación nueva se obtiene de la anterior con UN solo intercambio. Un contador
    c[i] por posición recuerda cuántos intercambios lleva la posición i; cuando c[i] llega a i,
    se reinicia y se pasa a la posición siguiente (como un odómetro).
    OJO: entrega SIEMPRE la misma lista, modificada; quien la use debe copiarla para guardarla.

    Pseudocódigo (Heap 1963; Sedgewick 1977, secc. 2):
        1. A <- copia de elementos; c[0..n-1] <- 0; entregar A
        2. i <- 1
        3. mientras i < n:
             3a. si c[i] < i:
                   si i es par: intercambiar A[0] y A[i]
                   si i es impar: intercambiar A[c[i]] y A[i]
                   entregar A; c[i] <- c[i] + 1; i <- 1
             3b. si no: c[i] <- 0; i <- i + 1

    Complejidad: n! permutaciones con O(1) intercambios amortizados cada una -> O(n!) tiempo,
    O(n) memoria (la lista A y los contadores c).
    """
    # Paso 1: la primera permutación es la lista tal cual
    n = len(elementos)
    arreglo = list(elementos)
    contador = [0] * n
    yield arreglo
    # Paso 2
    i = 1
    # Paso 3
    while i < n:
        if contador[i] < i:
            # Paso 3a: un intercambio produce la permutación siguiente
            if i % 2 == 0:
                otra = 0
            else:
                otra = contador[i]
            temporal = arreglo[otra]
            arreglo[otra] = arreglo[i]
            arreglo[i] = temporal
            yield arreglo
            contador[i] = contador[i] + 1
            i = 1
        else:
            # Paso 3b: esta posición ya dio todas sus vueltas; reiniciarla y pasar a la siguiente
            contador[i] = 0
            i = i + 1


# ---------------------------------------------------------------------------------------------
# Solución exacta 1: fuerza bruta
# ---------------------------------------------------------------------------------------------

def fuerza_bruta(d, traza=None):
    """TSP exacto probando todos los órdenes posibles de los lugares 1..k.

    Idea: el recorrido siempre empieza y termina en 0, así que basta probar las k! permutaciones
    de 1..k, calcular el costo de cada una y quedarse con la menor.

    Pseudocódigo:
        1. si k = 0: devolver (0, [0, 0])
        2. lugares <- [1, 2, ..., k]; mejor_costo <- ∞
        3. para cada permutación P de lugares (permutaciones_heap):
             3a. costo <- d(0, P[0]) + Σ d(P[t], P[t+1]) + d(P[k-1], 0)
             3b. si costo < mejor_costo: mejor_costo <- costo; mejor_orden <- copia de P
        4. devolver (mejor_costo, [0] + mejor_orden + [0])

    Complejidad: k! permutaciones × O(k) para sumar cada una = O(k·k!) tiempo; O(k) memoria
    (solo la permutación actual y la mejor). Fuente: Cormen, Leiserson, Rivest y Stein,
    "Introduction to Algorithms", 3.ª ed., MIT Press, 2009, secc. 34.5.4 (el TSP) y
    Sedgewick 1977 para el generador.
    """
    n = len(d)
    k = n - 1
    # Paso 1: sin lugares que visitar
    if k == 0:
        return 0, [0, 0]
    # Paso 2
    lugares = []
    for lugar in range(1, n):
        lugares.append(lugar)
    mejor_costo = math.inf
    mejor_orden = None
    numero = 0
    # Paso 3: recorrer todas las permutaciones
    for orden in permutaciones_heap(lugares):
        numero = numero + 1
        # Paso 3a: costo del recorrido 0 -> orden[0] -> ... -> orden[k-1] -> 0
        costo = d[0][orden[0]]
        for t in range(k - 1):
            costo = costo + d[orden[t]][orden[t + 1]]
        costo = costo + d[orden[k - 1]][0]
        # Paso 3b: ¿es el mejor hasta ahora?
        mejora = costo < mejor_costo
        if mejora:
            mejor_costo = costo
            mejor_orden = list(orden)  # copia: el generador reutiliza la misma lista
        if traza is not None:
            texto = f"permutación {numero}: 0-" + _texto_lista(orden) + f"-0 cuesta {costo}"
            if mejora:
                texto = texto + "  <- nuevo mejor"
            traza.append(texto)
    # Paso 4: armar el recorrido completo
    recorrido = [0]
    for lugar in mejor_orden:
        recorrido.append(lugar)
    recorrido.append(0)
    return mejor_costo, recorrido


# ---------------------------------------------------------------------------------------------
# Solución exacta 2: Held-Karp (programación dinámica)
# ---------------------------------------------------------------------------------------------

def held_karp(d, traza=None):
    """TSP exacto con programación dinámica sobre subconjuntos (Held y Karp 1962; Bellman 1962).

    Idea: C(S, j) = costo mínimo de salir de 0, visitar exactamente los lugares de S y terminar
    en j (j ∈ S). Un recorrido óptimo que termina en j, quitando j, es un recorrido óptimo para
    S \\ {j} que termina en algún i (subestructura óptima), por eso:
        caso base:   C({j}, j) = d(0, j)
        recurrencia: C(S, j)   = min_{i ∈ S\\{j}} [ C(S\\{j}, i) + d(i, j) ]
        respuesta:   min_{j} [ C(N, j) + d(j, 0) ],  N = {1..k}
    S se guarda como máscara de bits: el bit j-1 está en 1 si el lugar j pertenece a S. La tabla
    es una lista indexada por máscara: C[mascara][j-1]. padre[mascara][j-1] guarda el i que dio
    el mínimo, para reconstruir el recorrido al final.

    Pseudocódigo:
        1. si k = 0: devolver (0, [0, 0])
        2. crear C y padre de 2^k filas × k columnas, llenas de ∞ / -1
        3. caso base: para cada j, C[{j}][j] <- d(0, j), padre <- 0
        4. para cada máscara de 1 a 2^k - 1 (orden creciente: los subconjuntos van primero)
           con 2 o más lugares, y para cada j en la máscara:
             4a. sin_j <- máscara sin el bit de j
             4b. C[máscara][j] <- min sobre i en sin_j de C[sin_j][i] + d(i, j); padre <- ese i
        5. cerrar el ciclo: costo <- min_j C[N][j] + d(j, 0); último <- ese j
        6. reconstruir: desde (N, último) seguir padre quitando cada lugar de la máscara hasta
           llegar a 0; invertir la lista y agregar 0 al principio y al final

    Complejidad: hay k·2^k pares (S, j) y cada uno revisa hasta k valores de i: O(k²·2^k)
    tiempo. Memoria: las dos tablas de 2^k × k entradas: O(k·2^k).
    Fuente: Held y Karp 1962, secc. 2; Cormen et al. 2009, cap. 15 (programación dinámica).
    """
    n = len(d)
    k = n - 1
    # Paso 1
    if k == 0:
        return 0, [0, 0]
    total_mascaras = 1 << k  # 2^k subconjuntos
    # Paso 2: tablas de 2^k filas y k columnas (columna j-1 = "termina en el lugar j")
    C = []
    padre = []
    for mascara in range(total_mascaras):
        C.append([math.inf] * k)
        padre.append([-1] * k)
    # Paso 3: caso base, subconjuntos de un solo lugar
    for j in range(1, k + 1):
        mascara_j = 1 << (j - 1)
        C[mascara_j][j - 1] = d[0][j]
        padre[mascara_j][j - 1] = 0
        if traza is not None:
            traza.append(f"caso base: C({{{j}}}, {j}) = d(0,{j}) = {d[0][j]}")
    # Paso 4: llenar la tabla en orden creciente de máscara
    for mascara in range(1, total_mascaras):
        if mascara & (mascara - 1) == 0:
            continue  # un solo bit: ya es caso base
        for j in range(1, k + 1):
            bit_j = 1 << (j - 1)
            if mascara & bit_j == 0:
                continue  # j no está en S
            # Paso 4a: S sin j
            sin_j = mascara ^ bit_j
            # Paso 4b: probar cada i de S \ {j} como penúltimo lugar
            mejor = math.inf
            mejor_i = -1
            candidatos_texto = []
            for i in range(1, k + 1):
                bit_i = 1 << (i - 1)
                if sin_j & bit_i == 0:
                    continue
                candidato = C[sin_j][i - 1] + d[i][j]
                if traza is not None:
                    candidatos_texto.append(
                        f"C({_conjunto_texto(sin_j, k)},{i})+d({i},{j}) = {C[sin_j][i - 1]}+{d[i][j]} = {candidato}")
                if candidato < mejor:
                    mejor = candidato
                    mejor_i = i
            C[mascara][j - 1] = mejor
            padre[mascara][j - 1] = mejor_i
            if traza is not None:
                traza.append(f"C({_conjunto_texto(mascara, k)}, {j}) = min[ " + " ; ".join(candidatos_texto)
                             + f" ] = {mejor}  (penúltimo = {mejor_i})")
    # Paso 5: cerrar el ciclo volviendo a 0
    completa = total_mascaras - 1
    mejor_costo = math.inf
    ultimo = -1
    for j in range(1, k + 1):
        costo = C[completa][j - 1] + d[j][0]
        if traza is not None:
            traza.append(f"cierre: C({_conjunto_texto(completa, k)},{j}) + d({j},0) = "
                         f"{C[completa][j - 1]}+{d[j][0]} = {costo}")
        if costo < mejor_costo:
            mejor_costo = costo
            ultimo = j
    # Paso 6: reconstruir el recorrido hacia atrás con la tabla padre
    al_reves = []
    mascara = completa
    actual = ultimo
    while actual != 0:
        al_reves.append(actual)
        anterior = padre[mascara][actual - 1]
        mascara = mascara ^ (1 << (actual - 1))  # quitar el lugar actual del conjunto
        actual = anterior
    recorrido = [0]
    posicion = len(al_reves) - 1
    while posicion >= 0:
        recorrido.append(al_reves[posicion])
        posicion = posicion - 1
    recorrido.append(0)
    if traza is not None:
        traza.append(f"óptimo = {mejor_costo}, recorrido = " + _texto_lista(recorrido))
    return mejor_costo, recorrido


# ---------------------------------------------------------------------------------------------
# Heurística voraz: vecino más cercano
# ---------------------------------------------------------------------------------------------

def vecino_mas_cercano(d, traza=None):
    """Heurística voraz: desde el lugar actual, ir siempre al lugar no visitado más cercano.

    Idea: es lo que haría un turista sin mapa completo: "¿qué me queda más cerca ahora?".
    Al visitar todos, regresa al punto de partida. No garantiza el óptimo: la decisión local no
    mira cuánto costará regresar ni cómo quedan los lugares restantes.

    Pseudocódigo:
        1. visitado[0] <- verdadero; actual <- 0; recorrido <- [0]; costo <- 0
        2. repetir k veces:
             2a. buscar entre los no visitados el j con menor d(actual, j)
             2b. marcarlo, sumarlo al costo, agregarlo al recorrido; actual <- j
        3. regresar: costo <- costo + d(actual, 0); agregar 0

    Complejidad: k pasos y cada uno revisa hasta k candidatos: O(k²) tiempo, O(k) memoria.
    Fuente: Rosenkrantz, Stearns y Lewis 1977 (la heurística y su análisis).
    """
    n = len(d)
    k = n - 1
    # Paso 1
    visitado = [False] * n
    visitado[0] = True
    actual = 0
    recorrido = [0]
    costo = 0
    # Paso 2
    for paso in range(1, k + 1):
        # Paso 2a: búsqueda lineal del no visitado más cercano
        mas_cercano = -1
        menor_tiempo = math.inf
        for candidato in range(1, n):
            if visitado[candidato]:
                continue
            if d[actual][candidato] < menor_tiempo:
                menor_tiempo = d[actual][candidato]
                mas_cercano = candidato
        if traza is not None:
            opciones = []
            for candidato in range(1, n):
                if not visitado[candidato]:
                    opciones.append(f"{candidato}:{d[actual][candidato]}")
            traza.append(f"paso {paso}: desde {actual}, opciones [" + ", ".join(opciones)
                         + f"] -> voy a {mas_cercano} (+{menor_tiempo})")
        # Paso 2b: moverse
        visitado[mas_cercano] = True
        costo = costo + menor_tiempo
        recorrido.append(mas_cercano)
        actual = mas_cercano
    # Paso 3: volver al punto de partida
    costo = costo + d[actual][0]
    recorrido.append(0)
    if traza is not None:
        traza.append(f"regreso: {actual} -> 0 (+{d[actual][0]}); total = {costo}")
    return costo, recorrido


# ---------------------------------------------------------------------------------------------
# Itinerario de un día
# ---------------------------------------------------------------------------------------------

def itinerario(partida, atractivos, matriz, duraciones, limite_h=11, nombres=None):
    """Ordena los atractivos con Held-Karp y arma la tabla del día (formato del anexo).

    partida: id del lugar de salida y regreso. atractivos: lista de ids. matriz: matriz[a][b] en
    segundos (leer_matriz). duraciones: {id: minutos de visita}. nombres: {id: nombre} opcional.

    Devuelve un diccionario con:
        orden: ids en el orden de visita, empezando y terminando en la partida
        filas: [{orden, lugar, nombre, desplazamiento_desde_anterior_min, visita_min,
                 tiempo_acumulado_h}, ...] con la fila final orden = "Regreso"
        total_visitas_min, total_desplazamientos_min, jornada_h, limite_h, cabe
    """
    # Paso 1: matriz pequeña con la partida en la posición 0
    lugares = [partida]
    for lugar in atractivos:
        lugares.append(lugar)
    d = submatriz(matriz, lugares)
    # Paso 2: orden óptimo de visita
    _costo_s, recorrido = held_karp(d)
    # Paso 3: recorrer el orden acumulando desplazamientos y visitas
    filas = []
    orden_ids = [partida]
    acumulado_min = 0.0
    total_desplazamientos_min = 0.0
    total_visitas_min = 0
    ultima_posicion = len(recorrido) - 1
    for posicion in range(1, len(recorrido)):
        anterior = lugares[recorrido[posicion - 1]]
        actual = lugares[recorrido[posicion]]
        desplazamiento_min = matriz[anterior][actual] / 60
        total_desplazamientos_min = total_desplazamientos_min + desplazamiento_min
        if posicion == ultima_posicion:
            etiqueta = "Regreso"
            visita = "—"
            acumulado_min = acumulado_min + desplazamiento_min
        else:
            etiqueta = posicion
            visita = duraciones[actual]
            total_visitas_min = total_visitas_min + visita
            acumulado_min = acumulado_min + desplazamiento_min + visita
        nombre = actual
        if nombres is not None:
            nombre = nombres[actual]
        filas.append({"orden": etiqueta, "lugar": actual, "nombre": nombre,
                      "desplazamiento_desde_anterior_min": desplazamiento_min,
                      "visita_min": visita, "tiempo_acumulado_h": acumulado_min / 60})
        orden_ids.append(actual)
    jornada_h = acumulado_min / 60
    return {"orden": orden_ids, "filas": filas, "total_visitas_min": total_visitas_min,
            "total_desplazamientos_min": total_desplazamientos_min, "jornada_h": jornada_h,
            "limite_h": limite_h, "cabe": jornada_h <= limite_h}


def ajustar_a_jornada(partida, atractivos, matriz, duraciones, limite_h=11, nombres=None, traza=None):
    """Si el itinerario no cabe en `limite_h` horas, quita atractivos uno a uno y recalcula.

    Criterio: en cada ronda se prueba quitar cada atractivo (recalculando el óptimo con
    Held-Karp) y se quita el que MÁS acorta la jornada (su visita + el desvío que se ahorra).
    Así se quitan los menos atractivos posibles. Empate: el primero de la lista.

    Pseudocódigo:
        1. actuales <- atractivos; resultado <- itinerario(actuales)
        2. mientras no quepa y queden atractivos:
             2a. para cada atractivo a: prueba <- itinerario(actuales sin a)
             2b. elegir el a cuya prueba tenga la menor jornada; quitarlo; resultado <- prueba
        3. devolver (resultado, lista de quitados con el motivo)

    Complejidad: cada ronda hace k ejecuciones de Held-Karp: O(k · k²·2^k) por ronda.
    """
    # Paso 1
    actuales = list(atractivos)
    resultado = itinerario(partida, actuales, matriz, duraciones, limite_h, nombres)
    if traza is not None:
        traza.append(f"intento con {len(actuales)} atractivos: {resultado['jornada_h']:.2f} h "
                     f"(límite {limite_h} h) -> {'cabe' if resultado['cabe'] else 'no cabe'}")
    quitados = []
    # Paso 2
    while not resultado["cabe"] and len(actuales) > 0:
        mejor_lugar = None
        mejor_prueba = None
        mejor_resto = None
        # Paso 2a: probar quitar cada uno
        for candidato in actuales:
            resto = []
            for lugar in actuales:
                if lugar != candidato:
                    resto.append(lugar)
            prueba = itinerario(partida, resto, matriz, duraciones, limite_h, nombres)
            if traza is not None:
                traza.append(f"   sin {candidato}: {prueba['jornada_h']:.2f} h")
            # Paso 2b: quedarse con la que más acorta la jornada
            if mejor_prueba is None or prueba["jornada_h"] < mejor_prueba["jornada_h"]:
                mejor_lugar = candidato
                mejor_prueba = prueba
                mejor_resto = resto
        ahorro_h = resultado["jornada_h"] - mejor_prueba["jornada_h"]
        ahorro_desplazamiento_min = (resultado["total_desplazamientos_min"]
                                     - mejor_prueba["total_desplazamientos_min"])
        quitados.append({"lugar": mejor_lugar, "visita_min": duraciones[mejor_lugar],
                         "jornada_antes_h": resultado["jornada_h"],
                         "jornada_despues_h": mejor_prueba["jornada_h"],
                         "ahorro_h": ahorro_h,
                         "ahorro_desplazamiento_min": ahorro_desplazamiento_min})
        if traza is not None:
            traza.append(f"quito {mejor_lugar} (visita {duraciones[mejor_lugar]} min, ahorra "
                         f"{ahorro_desplazamiento_min:.1f} min de desplazamiento): "
                         f"{mejor_prueba['jornada_h']:.2f} h")
        actuales = mejor_resto
        resultado = mejor_prueba
    # Paso 3
    return resultado, quitados


if __name__ == "__main__":
    # Ejemplo pequeño resuelto a mano (docs/paso_a_paso_R4.md): partida 0 y lugares 1, 2, 3.
    D = [[0, 2, 9, 10],
         [1, 0, 6, 4],
         [15, 7, 0, 8],
         [6, 3, 12, 0]]
    print("Matriz d (fila = desde, columna = hacia):")
    for fila_d in D:
        print("   ", fila_d)

    print("\n=== Generador de Heap sobre [1, 2, 3] ===")
    for p in permutaciones_heap([1, 2, 3]):
        print("   ", p)

    for titulo, funcion in (("FUERZA BRUTA", fuerza_bruta), ("HELD-KARP", held_karp),
                            ("VECINO MÁS CERCANO", vecino_mas_cercano)):
        pasos = []
        costo_demo, recorrido_demo = funcion(D, traza=pasos)
        print(f"\n=== {titulo} ===")
        for linea in pasos:
            print(linea)
        print(f"Resultado: costo = {costo_demo}, recorrido = {_texto_lista(recorrido_demo)}")
