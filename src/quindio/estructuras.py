"""Estructuras de datos propias de apoyo para los algoritmos.

MonticuloMinimo: montículo binario mínimo (cola de prioridad) guardado en un arreglo.
Referencia: Cormen, Leiserson, Rivest y Stein, "Introduction to Algorithms", 3.ª ed., MIT Press,
2009, cap. 6 (Heapsort), secciones 6.1-6.5 (montículos y colas de prioridad).
"""


class MonticuloMinimo:
    """Cola de prioridad con montículo binario mínimo.

    Se guarda en una lista `datos` de pares (prioridad, elemento). Para la posición i:
        padre(i) = (i - 1) // 2      hijo izquierdo = 2*i + 1      hijo derecho = 2*i + 2
    Propiedad del montículo: la prioridad de cada padre es <= la de sus hijos, así que el
    mínimo siempre está en datos[0].

    Costo (Cormen et al. 2009, secc. 6.5): la altura de un montículo de n elementos es
    floor(log2 n) (secc. 6.1). subir y bajar recorren a lo sumo un camino de la raíz a una hoja,
    por eso insertar y extraer_minimo cuestan O(log n). Memoria: O(n).
    """

    def __init__(self):
        self.datos = []

    def __len__(self):
        return len(self.datos)

    def esta_vacio(self):
        return len(self.datos) == 0

    def insertar(self, prioridad, elemento):
        """Agrega (prioridad, elemento). O(log n).

        Pseudocódigo:
            1. poner el par nuevo al final del arreglo (primera hoja libre)
            2. subirlo mientras sea menor que su padre
        """
        # Paso 1: al final
        self.datos.append((prioridad, elemento))
        # Paso 2: restaurar la propiedad hacia arriba
        self.subir(len(self.datos) - 1)

    def extraer_minimo(self):
        """Saca y devuelve el par (prioridad, elemento) de menor prioridad. O(log n).

        Pseudocódigo:
            1. si está vacío: error
            2. guardar la raíz (es el mínimo)
            3. sacar el último elemento; si quedan elementos, ponerlo en la raíz
            4. bajarlo mientras sea mayor que alguno de sus hijos
            5. devolver la raíz guardada
        """
        # Paso 1: no hay nada que extraer
        if len(self.datos) == 0:
            raise IndexError("extraer_minimo de un montículo vacío")
        # Paso 2: el mínimo está en la raíz
        minimo = self.datos[0]
        # Paso 3: el último pasa a la raíz
        ultimo = self.datos.pop()
        if len(self.datos) > 0:
            self.datos[0] = ultimo
            # Paso 4: restaurar la propiedad hacia abajo
            self.bajar(0)
        # Paso 5
        return minimo

    def subir(self, i):
        """Sube el elemento de la posición i hasta que su padre no sea mayor. O(log n).

        Pseudocódigo:
            1. mientras i no sea la raíz:
                 1a. padre <- (i - 1) // 2
                 1b. si prioridad(i) < prioridad(padre): intercambiar y seguir desde el padre
                 1c. si no: terminar (ya cumple la propiedad)
        """
        # Paso 1
        while i > 0:
            # Paso 1a: posición del padre
            padre = (i - 1) // 2
            # Paso 1b: ¿el hijo es menor que el padre?
            if self.datos[i][0] < self.datos[padre][0]:
                temporal = self.datos[i]
                self.datos[i] = self.datos[padre]
                self.datos[padre] = temporal
                i = padre
            else:
                # Paso 1c: ya está en su lugar
                break

    def bajar(self, i):
        """Baja el elemento de la posición i hasta que no sea mayor que sus hijos. O(log n).

        Pseudocódigo:
            1. repetir:
                 1a. izquierdo <- 2i + 1, derecho <- 2i + 2, menor <- i
                 1b. si el izquierdo existe y es menor que datos[menor]: menor <- izquierdo
                 1c. si el derecho existe y es menor que datos[menor]: menor <- derecho
                 1d. si menor == i: terminar (ya es menor o igual que sus hijos)
                 1e. intercambiar i con menor y seguir desde menor
        """
        cantidad = len(self.datos)
        # Paso 1
        while True:
            # Paso 1a: hijos de i
            izquierdo = 2 * i + 1
            derecho = 2 * i + 2
            menor = i
            # Paso 1b
            if izquierdo < cantidad and self.datos[izquierdo][0] < self.datos[menor][0]:
                menor = izquierdo
            # Paso 1c
            if derecho < cantidad and self.datos[derecho][0] < self.datos[menor][0]:
                menor = derecho
            # Paso 1d
            if menor == i:
                break
            # Paso 1e
            temporal = self.datos[i]
            self.datos[i] = self.datos[menor]
            self.datos[menor] = temporal
            i = menor


if __name__ == "__main__":
    # Demostración: insertar 5, 3, 8, 1 y extraer todo (sale en orden 1, 3, 5, 8).
    m = MonticuloMinimo()
    for p in [5, 3, 8, 1]:
        m.insertar(p, f"x{p}")
        print(f"insertar {p}: arreglo = {[par[0] for par in m.datos]}")
    while not m.esta_vacio():
        p, e = m.extraer_minimo()
        print(f"extraer_minimo -> {p} ({e}); arreglo = {[par[0] for par in m.datos]}")
