"""R2 - Caminos mínimos con Dijkstra (implementación propia, "método largo").

Grafo: adj[u] = lista de (v, tiempo_s, distancia_m), como lo devuelve red.cargar_grafo().
El peso que se minimiza es tiempo_s (segundos), que siempre es > 0.

Dos versiones:
    dijkstra_lineal: elige el mínimo recorriendo todos los nodos no explorados. O(V²).
    dijkstra_cola:   elige el mínimo con un montículo binario propio (MonticuloMinimo). O((V+E) log V).

Referencias:
    E. W. Dijkstra, "A note on two problems in connexion with graphs", Numerische Mathematik 1,
    pp. 269-271, 1959.
    Cormen, Leiserson, Rivest y Stein, "Introduction to Algorithms", 3.ª ed., MIT Press, 2009,
    secc. 24.3 (Dijkstra's algorithm) y cap. 6 (montículos).

Ejemplo resuelto a mano: docs/paso_a_paso_R2.md (y `python -m quindio.dijkstra`).
"""
import math

from .estructuras import MonticuloMinimo


def reconstruir_ruta(predecesor, origen, destino):
    """Arma la ruta origen -> destino siguiendo los predecesores hacia atrás.

    Pseudocódigo:
        1. actual <- destino; ruta_al_reves <- []
        2. mientras actual no sea "ninguno":
             agregar actual a ruta_al_reves; si actual == origen, terminar
             actual <- predecesor[actual]
        3. invertir ruta_al_reves recorriéndola desde el final

    Complejidad: O(k) para una ruta de k nodos.
    """
    # Paso 1
    ruta_al_reves = []
    actual = destino
    # Paso 2: caminar hacia atrás hasta el origen
    while actual is not None:
        ruta_al_reves.append(actual)
        if actual == origen:
            break
        actual = predecesor[actual]
    # Paso 3: dar vuelta la lista
    ruta = []
    posicion = len(ruta_al_reves) - 1
    while posicion >= 0:
        ruta.append(ruta_al_reves[posicion])
        posicion = posicion - 1
    return ruta


def dijkstra_lineal(adj, origen, destino, traza=None):
    """Dijkstra con arreglo de distancias y búsqueda lineal del mínimo.

    Devuelve (tiempo_s, ruta, nodos_explorados). Si el destino no se alcanza: (inf, [], explorados).

    Idea: se mantiene una distancia tentativa para cada nodo. En cada paso se elige, entre los
    nodos NO explorados, el de menor distancia (recorriéndolos todos), se marca como explorado
    (su distancia ya es definitiva) y se relajan sus aristas de salida.

    Pseudocódigo:
        1. para cada nodo v: distancia[v] <- inf, predecesor[v] <- ninguno, explorado[v] <- falso
           distancia[origen] <- 0
        2. repetir:
             2a. recorrer TODOS los nodos y elegir u = el no explorado con menor distancia
             2b. si no hay ninguno con distancia finita: terminar (lo que falta es inalcanzable)
             2c. explorado[u] <- verdadero; contar u como explorado
             2d. si u == destino: terminar (su distancia ya es definitiva)
             2e. para cada arista (u, v, tiempo):
                   si distancia[u] + tiempo < distancia[v]:          (relajación)
                       distancia[v] <- distancia[u] + tiempo; predecesor[v] <- u
        3. reconstruir la ruta con los predecesores y devolver

    Complejidad: el paso 2 se repite a lo sumo V veces y cada búsqueda 2a recorre V nodos:
    O(V²). Las relajaciones suman O(E) en total (cada arista una vez). Total O(V² + E) = O(V²).
    Memoria: O(V) (tres diccionarios de V entradas). Cormen et al. 2009, secc. 24.3.
    """
    # Paso 1: inicialización
    distancia = {}
    predecesor = {}
    explorado = {}
    for nodo in adj:
        distancia[nodo] = math.inf
        predecesor[nodo] = None
        explorado[nodo] = False
    distancia[origen] = 0
    nodos_explorados = 0

    # Paso 2: repetir hasta sacar el destino o quedarse sin nodos alcanzables
    while True:
        # Paso 2a: búsqueda lineal del mínimo entre los no explorados
        nodo_minimo = None
        distancia_minima = math.inf
        for nodo in adj:
            if not explorado[nodo]:
                if distancia[nodo] < distancia_minima:
                    nodo_minimo = nodo
                    distancia_minima = distancia[nodo]

        # Paso 2b: no queda ningún nodo alcanzable sin explorar
        if nodo_minimo is None:
            if traza is not None:
                traza.append("No quedan nodos con distancia finita: el destino es inalcanzable")
            break

        # Paso 2c: su distancia queda fija
        explorado[nodo_minimo] = True
        nodos_explorados = nodos_explorados + 1
        if traza is not None:
            traza.append(f"Exploro {nodo_minimo} (distancia definitiva {distancia_minima})")

        # Paso 2d: si es el destino, parar
        if nodo_minimo == destino:
            break

        # Paso 2e: relajar las aristas que salen del nodo
        for vecino, tiempo, _distancia_m in adj[nodo_minimo]:
            if explorado[vecino]:
                continue  # ya es definitivo: no puede mejorar
            candidata = distancia_minima + tiempo
            if candidata < distancia[vecino]:
                if traza is not None:
                    traza.append(f"   relajo {nodo_minimo}->{vecino}: {distancia[vecino]} -> {candidata}")
                distancia[vecino] = candidata
                predecesor[vecino] = nodo_minimo

    # Paso 3: resultado
    if not explorado[destino]:
        return math.inf, [], nodos_explorados
    return distancia[destino], reconstruir_ruta(predecesor, origen, destino), nodos_explorados


def dijkstra_cola(adj, origen, destino=None, traza=None, arbol=None):
    """Dijkstra con cola de prioridad (montículo binario propio) e inserción perezosa.

    Con destino: devuelve (tiempo_s, ruta, nodos_explorados); (inf, [], explorados) si no se alcanza.
    Sin destino (uno a todos): devuelve (distancias, predecesores, nodos_explorados), donde
    distancias[v] es el tiempo mínimo de origen a v (inf si no se alcanza).

    arbol: lista opcional. Si no es None, cada vez que un nodo se explora (paso 2c) se agrega
    (predecesor, nodo, distancia_definitiva) en el orden en que salió de la cola. Esas parejas
    predecesor -> nodo forman el árbol de caminos mínimos que Dijkstra va construyendo; la app lo
    anima para mostrar cómo avanza la búsqueda. Como traza, se deja en None al medir.

    Idea: igual que la versión lineal, pero el nodo no explorado de menor distancia se obtiene
    del montículo. "Inserción perezosa": en vez de disminuir la prioridad de un nodo que ya está
    en la cola, se inserta una entrada nueva (distancia, nodo). Así un nodo puede estar varias
    veces en la cola; cuando sale una entrada de un nodo ya explorado, es obsoleta y se descarta.

    Pseudocódigo:
        1. para cada nodo v: distancia[v] <- inf, predecesor[v] <- ninguno, explorado[v] <- falso
           distancia[origen] <- 0; insertar (0, origen) en la cola
        2. mientras la cola no esté vacía:
             2a. (d, u) <- extraer_minimo()
             2b. si u ya está explorado: es una entrada obsoleta, descartarla y seguir
             2c. explorado[u] <- verdadero; contar u como explorado (solo esta primera vez)
             2d. si u == destino: terminar
             2e. para cada arista (u, v, tiempo):
                   si d + tiempo < distancia[v]:                       (relajación)
                       distancia[v] <- d + tiempo; predecesor[v] <- u
                       insertar (distancia[v], v) en la cola
        3. con destino: reconstruir la ruta; sin destino: devolver todas las distancias

    Complejidad: cada relajación exitosa inserta una entrada, así que hay a lo sumo E + 1
    inserciones y E + 1 extracciones, cada una O(log E) = O(log V) (porque E <= V², log E <= 2 log V).
    Total O((V + E) log V). Memoria: O(V + E) (diccionarios de V entradas y hasta E entradas en
    la cola). Cormen et al. 2009, secc. 24.3 (análisis con montículo binario).
    """
    # Paso 1: inicialización
    distancia = {}
    predecesor = {}
    explorado = {}
    for nodo in adj:
        distancia[nodo] = math.inf
        predecesor[nodo] = None
        explorado[nodo] = False
    distancia[origen] = 0
    nodos_explorados = 0
    cola = MonticuloMinimo()
    cola.insertar(0, origen)

    # Paso 2: procesar la cola
    while not cola.esta_vacio():
        # Paso 2a: entrada de menor distancia
        distancia_extraida, nodo = cola.extraer_minimo()

        # Paso 2b: descartar entradas obsoletas
        if explorado[nodo]:
            if traza is not None:
                traza.append(f"   descarto entrada obsoleta ({distancia_extraida}, {nodo})")
            continue

        # Paso 2c: primera vez que sale -> explorado
        explorado[nodo] = True
        nodos_explorados = nodos_explorados + 1
        if traza is not None:
            traza.append(f"Exploro {nodo} (distancia definitiva {distancia_extraida})")
        if arbol is not None:
            arbol.append((predecesor[nodo], nodo, distancia_extraida))

        # Paso 2d: llegamos al destino
        if nodo == destino:
            break

        # Paso 2e: relajar aristas de salida
        for vecino, tiempo, _distancia_m in adj[nodo]:
            candidata = distancia_extraida + tiempo
            if candidata < distancia[vecino]:
                if traza is not None:
                    traza.append(f"   relajo {nodo}->{vecino}: {distancia[vecino]} -> {candidata}; "
                                 f"inserto ({candidata}, {vecino})")
                distancia[vecino] = candidata
                predecesor[vecino] = nodo
                cola.insertar(candidata, vecino)

    # Paso 3: resultado
    if destino is None:
        return distancia, predecesor, nodos_explorados
    if not explorado[destino]:
        return math.inf, [], nodos_explorados
    return distancia[destino], reconstruir_ruta(predecesor, origen, destino), nodos_explorados


if __name__ == "__main__":
    # Ejemplo pequeño resuelto a mano (docs/paso_a_paso_R2.md): de A a F.
    aristas = [("A", "B", 4), ("A", "C", 2), ("C", "B", 1), ("B", "D", 5), ("C", "D", 8),
               ("C", "E", 10), ("D", "E", 2), ("D", "F", 6), ("E", "F", 2), ("F", "A", 3)]
    adj_demo = {}
    for u, v, w in aristas:
        if u not in adj_demo:
            adj_demo[u] = []
        if v not in adj_demo:
            adj_demo[v] = []
        adj_demo[u].append((v, w, 0.0))

    for nombre, funcion in (("LINEAL", dijkstra_lineal), ("COLA DE PRIORIDAD", dijkstra_cola)):
        pasos = []
        tiempo, ruta, explorados = funcion(adj_demo, "A", "F", traza=pasos)
        print(f"=== Dijkstra {nombre}: de A a F ===")
        for p in pasos:
            print(p)
        print(f"Tiempo = {tiempo}, ruta = {'-'.join(ruta)}, nodos explorados = {explorados}\n")
