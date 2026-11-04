"""R3 - Envolvente convexa de los nodos de la red vial con QuickHull (divide y vencerás).

Todas las coordenadas son enteras (metros UTM 18N redondeados), así que los giros se
deciden con aritmética entera exacta: no hay errores de redondeo.
"""


def preparar_puntos(xs, ys):
    """Redondea cada coordenada al entero más cercano y elimina los puntos repetidos.

    Idea: el enunciado pide trabajar con coordenadas enteras en metros. Al redondear, dos
    nodos muy cercanos (menos de 1 m) pueden caer en el mismo punto; se deja solo el primero.

    Pseudocódigo:
        1. vistos <- conjunto vacío; resultado <- lista vacía
        2. para i = 0 .. n-1:
        3.     p <- (redondear(xs[i]), redondear(ys[i]))
        4.     si p no está en vistos: agregar p a vistos y a resultado
        5. devolver resultado

    Complejidad: O(n) tiempo esperado (búsqueda en conjunto hash O(1) promedio) y O(n) memoria.
    """
    # Paso 1: estructuras vacías.
    vistos = set()
    resultado = []
    # Paso 2: recorrer todos los puntos de entrada.
    for i in range(len(xs)):
        # Paso 3: redondear al entero más cercano.
        x_entero = int(round(xs[i]))
        y_entero = int(round(ys[i]))
        punto = (x_entero, y_entero)
        # Paso 4: guardar solo la primera aparición.
        if punto not in vistos:
            vistos.add(punto)
            resultado.append(punto)
    # Paso 5
    return resultado


def orientacion(a, b, c):
    """Producto cruz (b - a) x (c - a) con enteros.

    > 0 : c está a la IZQUIERDA del segmento dirigido a -> b (giro antihorario).
    < 0 : c está a la DERECHA (giro horario).
    = 0 : a, b y c están alineados.

    Su valor absoluto es el doble del área del triángulo abc = |ab| * distancia(c, recta ab).
    Python usa enteros de tamaño ilimitado; en C o Java se usarían enteros de 64 bits
    (coordenadas UTM ~10^6 dan productos ~10^12, lejos del máximo 9.2 * 10^18).
    Complejidad: O(1).
    """
    dx1 = b[0] - a[0]
    dy1 = b[1] - a[1]
    dx2 = c[0] - a[0]
    dy2 = c[1] - a[1]
    return dx1 * dy2 - dy1 * dx2


def proyeccion(p, q, x):
    """Producto punto (q - p) · (x - p): crece a medida que x avanza de p hacia q. O(1)."""
    return (q[0] - p[0]) * (x[0] - p[0]) + (q[1] - p[1]) * (x[1] - p[1])


def quickhull(puntos, traza=None):
    """Envolvente convexa por QuickHull (divide y vencerás), sin recursión.

    Idea: los puntos extremos A (menor x) y B (mayor x) siempre son vértices. La recta AB
    divide los puntos en dos lados. Para cada lado se busca el punto C más lejano a la recta:
    C también es vértice, y todos los puntos dentro del triángulo A-C-B ya no pueden ser
    vértices, así que se DESCARTAN. Quedan dos subproblemas más pequeños (puntos fuera de AC
    y puntos fuera de CB) que se resuelven igual. En la red vial casi todos los nodos están
    en los cascos urbanos, lejos del borde, y se descartan en los primeros niveles.

    Convención: una tarea (P, Q, candidatos) significa "el lado P -> Q de la envolvente
    provisional tiene a su DERECHA estos candidatos". Como la envolvente se recorre en sentido
    antihorario, el interior queda a la izquierda de cada lado y lo que falta, a la derecha.

    Pseudocódigo:
        1. si no hay puntos, devolver []
        2. A <- punto con menor (x, y); B <- punto con mayor (x, y)
           si A = B (todos iguales), devolver [A]
        3. abajo  <- puntos a la derecha de A -> B   (orientacion(A, B, p) < 0)
           arriba <- puntos a la izquierda de A -> B (orientacion(A, B, p) > 0)
           (los alineados con AB están sobre el segmento AB: no son vértices)
        4. pila <- [(B, A, arriba), (A, B, abajo)]; envolvente <- []
        5. mientras la pila no esté vacía:
               (P, Q, candidatos) <- sacar de la pila
        6.     si candidatos está vacío: P -> Q es un lado definitivo; agregar P a envolvente
        7.     si no: C <- candidato más lejano de la recta PQ (mayor orientacion(Q, P, x));
                   en empate, el más cercano a P (menor proyeccion(P, Q, x))
        8.         fuera_PC <- candidatos a la derecha de P -> C
                   fuera_CQ <- candidatos a la derecha de C -> Q
                   (el resto está dentro del triángulo P-C-Q o sobre sus lados: se descarta)
        9.         apilar (C, Q, fuera_CQ) y luego (P, C, fuera_PC)
                   (se apila al revés para que P -> C se procese primero y salga en orden)
       10. devolver envolvente (antihoraria, empieza en A)

    Recurrencia: T(n) = T(n1) + T(n2) + O(n), con n1 + n2 <= n - 1.
    Tiempo: O(n log n) en promedio / cuando se reparte bien; O(n * h) en general y O(n^2) en
    el peor caso (h = vértices de la envolvente). Memoria: O(n) (cada punto vive en una sola
    lista de candidatos por nivel; la pila tiene a lo sumo O(h) tareas).
    Fuente: Barber, Dobkin y Huhdanpaa, "The Quickhull algorithm for convex hulls",
    ACM TOMS 22(4), 1996; Preparata y Shamos, "Computational Geometry: An Introduction",
    Springer, 1985, cap. 3 (técnicas QuickHull).

    traza: si es una lista, se le agrega un diccionario por paso (para la demostración).
    """
    # Paso 1: sin puntos no hay envolvente.
    if len(puntos) == 0:
        return []

    # Paso 2: extremos A (menor x; en empate, menor y) y B (mayor x; en empate, mayor y).
    punto_a = puntos[0]
    punto_b = puntos[0]
    for p in puntos:
        if p[0] < punto_a[0] or (p[0] == punto_a[0] and p[1] < punto_a[1]):
            punto_a = p
        if p[0] > punto_b[0] or (p[0] == punto_b[0] and p[1] > punto_b[1]):
            punto_b = p
    if punto_a == punto_b:
        return [punto_a]

    # Paso 3: dividir todos los puntos según el lado de la recta A -> B.
    abajo = []
    arriba = []
    alineados_ab = 0
    for p in puntos:
        giro = orientacion(punto_a, punto_b, p)
        if giro < 0:
            abajo.append(p)
        elif giro > 0:
            arriba.append(p)
        else:
            alineados_ab = alineados_ab + 1
    if traza is not None:
        traza.append({"paso": "division_inicial", "A": punto_a, "B": punto_b,
                      "abajo": list(abajo), "arriba": list(arriba),
                      "descartados": alineados_ab - 2})

    # Paso 4: pila explícita de tareas (P, Q, candidatos, nivel). Se usa pila en vez de
    # recursión porque en el peor caso la profundidad puede ser O(n) y Python limita la
    # recursión a unos 1000 niveles.
    pila = []
    pila.append((punto_b, punto_a, arriba, 1))
    pila.append((punto_a, punto_b, abajo, 1))
    envolvente = []

    # Paso 5: procesar tareas hasta vaciar la pila.
    while len(pila) > 0:
        tarea = pila.pop()
        punto_p = tarea[0]
        punto_q = tarea[1]
        candidatos = tarea[2]
        nivel = tarea[3]

        # Paso 6: nadie a la derecha de P -> Q: el lado es definitivo y P es vértice.
        if len(candidatos) == 0:
            envolvente.append(punto_p)
            if traza is not None:
                traza.append({"paso": "lado_definitivo", "P": punto_p, "Q": punto_q,
                              "nivel": nivel})
            continue

        # Paso 7: buscar el candidato más lejano de la recta PQ. orientacion(Q, P, x) es
        # positivo para los candidatos (están a la izquierda de Q -> P) y vale
        # |PQ| * distancia, así que el mayor valor es el más lejano (|PQ| es fijo aquí).
        # Empate: si varios están a la misma distancia (sobre una recta paralela a PQ), se
        # toma el más cercano a P (menor proyección sobre P -> Q). Así C es el extremo de ese
        # lado y no uno del medio, que estaría alineado y no sería vértice.
        punto_c = candidatos[0]
        mayor_distancia = orientacion(punto_q, punto_p, punto_c)
        menor_proyeccion = proyeccion(punto_p, punto_q, punto_c)
        for x in candidatos:
            distancia = orientacion(punto_q, punto_p, x)
            if distancia > mayor_distancia:
                mayor_distancia = distancia
                menor_proyeccion = proyeccion(punto_p, punto_q, x)
                punto_c = x
            elif distancia == mayor_distancia:
                proyeccion_x = proyeccion(punto_p, punto_q, x)
                if proyeccion_x < menor_proyeccion:
                    menor_proyeccion = proyeccion_x
                    punto_c = x

        # Paso 8: repartir los candidatos. Un punto no puede estar fuera de los dos lados a
        # la vez porque C es el más lejano; los demás quedan dentro del triángulo P-C-Q.
        fuera_pc = []
        fuera_cq = []
        descartados = 0
        for x in candidatos:
            if orientacion(punto_c, punto_p, x) > 0:      # a la derecha de P -> C
                fuera_pc.append(x)
            elif orientacion(punto_q, punto_c, x) > 0:    # a la derecha de C -> Q
                fuera_cq.append(x)
            else:
                descartados = descartados + 1
        # C se contó como descartado (está sobre los dos lados), pero es vértice.
        descartados = descartados - 1
        if traza is not None:
            traza.append({"paso": "dividir", "P": punto_p, "Q": punto_q, "nivel": nivel,
                          "candidatos": len(candidatos), "C": punto_c,
                          "fuera_PC": list(fuera_pc), "fuera_CQ": list(fuera_cq),
                          "descartados": descartados})

        # Paso 9: apilar los dos subproblemas (el último en entrar sale primero).
        pila.append((punto_c, punto_q, fuera_cq, nivel + 1))
        pila.append((punto_p, punto_c, fuera_pc, nivel + 1))

    # Paso 10
    return envolvente


def quitar_colineales(poligono):
    """Quita los vértices alineados con su anterior y su siguiente (no cuentan como vértices).

    Pseudocódigo:
        1. para cada vértice v del polígono (cerrado):
        2.     si orientacion(anterior, v, siguiente) != 0, conservar v
    Complejidad: O(h). En un polígono convexo una sola pasada basta.
    """
    h = len(poligono)
    if h < 3:
        return list(poligono)
    resultado = []
    for i in range(h):
        anterior = poligono[i - 1]
        actual = poligono[i]
        siguiente = poligono[(i + 1) % h]
        if orientacion(anterior, actual, siguiente) != 0:
            resultado.append(actual)
    return resultado


def empezar_en_menor(poligono):
    """Rota el polígono para que empiece en el punto de menor (x, y), igual que quickhull."""
    if len(poligono) == 0:
        return []
    indice_menor = 0
    for i in range(1, len(poligono)):
        if poligono[i] < poligono[indice_menor]:
            indice_menor = i
    return list(poligono[indice_menor:]) + list(poligono[:indice_menor])


def envolvente_scipy(puntos):
    """Envolvente con scipy.spatial.ConvexHull (Qhull), SOLO para verificar.

    En 2D Qhull entrega los vértices en orden antihorario. Se quitan los colineales (Qhull
    normalmente no los incluye, pero se limpia por si acaso) y se rota para empezar en el
    mismo punto que quickhull, así las dos listas se comparan con ==.
    """
    import numpy as np
    from scipy.spatial import ConvexHull

    arreglo = np.array(puntos, dtype=float)
    casco = ConvexHull(arreglo)
    poligono = []
    for indice in casco.vertices:
        poligono.append(puntos[int(indice)])
    return empezar_en_menor(quitar_colineales(poligono))


def area_km2(poligono):
    """Área del polígono con la fórmula del zapato (Gauss), en km².

    Pseudocódigo:
        1. suma <- 0
        2. para i = 0 .. h-1: suma <- suma + x_i * y_(i+1) - x_(i+1) * y_i  (índices módulo h)
        3. área = |suma| / 2  (m²)  ->  / 10^6 (km²)
    Complejidad: O(h). La suma es positiva si el polígono está en orden antihorario.
    """
    h = len(poligono)
    suma = 0
    for i in range(h):
        x_actual, y_actual = poligono[i]
        x_siguiente, y_siguiente = poligono[(i + 1) % h]
        suma = suma + x_actual * y_siguiente - x_siguiente * y_actual
    return abs(suma) / 2 / 1_000_000


def _mostrar(p):
    return f"({p[0]},{p[1]})"


def _mostrar_lista(lista):
    textos = []
    for p in lista:
        textos.append(_mostrar(p))
    return "[" + ", ".join(textos) + "]"


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")  # tildes correctas en la consola de Windows
    # Ejemplo pequeño resuelto a mano (ver docs/paso_a_paso_R3.md).
    ejemplo = [(0, 0), (4, 0), (2, 0), (6, 1), (7, 4), (5, 6), (2, 5), (0, 3),
               (3, 2), (4, 4), (1, 1), (5, 2), (2, 3), (4, 0)]
    print("Puntos de entrada:", _mostrar_lista(ejemplo))
    limpios = preparar_puntos([p[0] for p in ejemplo], [p[1] for p in ejemplo])
    print(f"Tras quitar repetidos: {len(limpios)} puntos")
    pasos = []
    resultado = quickhull(limpios, traza=pasos)
    for numero, paso in enumerate(pasos, start=1):
        if paso["paso"] == "division_inicial":
            print(f"{numero}. División inicial: A={_mostrar(paso['A'])}, B={_mostrar(paso['B'])}")
            print(f"   abajo (derecha de A->B): {_mostrar_lista(paso['abajo'])}")
            print(f"   arriba (izquierda de A->B): {_mostrar_lista(paso['arriba'])}")
            print(f"   alineados con AB descartados: {paso['descartados']}")
        elif paso["paso"] == "dividir":
            print(f"{numero}. [nivel {paso['nivel']}] lado {_mostrar(paso['P'])}->{_mostrar(paso['Q'])}"
                  f" con {paso['candidatos']} candidatos: más lejano C={_mostrar(paso['C'])}")
            print(f"   fuera de P->C: {_mostrar_lista(paso['fuera_PC'])}; "
                  f"fuera de C->Q: {_mostrar_lista(paso['fuera_CQ'])}; descartados: {paso['descartados']}")
        else:
            print(f"{numero}. [nivel {paso['nivel']}] lado {_mostrar(paso['P'])}->{_mostrar(paso['Q'])}"
                  f" sin candidatos: es definitivo, vértice {_mostrar(paso['P'])}")
    print("Envolvente (antihoraria):", _mostrar_lista(resultado))
    print(f"Área: {area_km2(resultado) * 1_000_000:.1f} m²")
    print("Igual a SciPy:", resultado == envolvente_scipy(limpios))
