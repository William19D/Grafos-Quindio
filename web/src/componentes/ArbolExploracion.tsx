// Capa del mapa con el árbol de exploración de Dijkstra hasta el paso `paso`.
// Cada tramo une un nodo explorado con su predecesor (el nodo desde el que se alcanzó por el
// camino más corto). Se colorea por la distancia definitiva del nodo: cerca del origen en verde,
// lejos en tostado, así se ve el "frente" de búsqueda creciendo en orden de tiempo.
//
// Son ~8 500 tramos: en vez de un <Polyline> de React por tramo se usa Leaflet directamente,
// con el renderizador Canvas y una sola polilínea múltiple por franja de color.
import { useEffect, useRef } from 'react'
import L from 'leaflet'
import { useMap } from 'react-leaflet'
import type { Punto } from '../api'
import { TONOS_ARBOL } from '../colores'


type Props = {
  tramos: Punto[][]
  tiempos: number[] // distancia definitiva (s) del nodo al final de cada tramo
  tiempoTotal: number // tiempo hasta el destino (s), para repartir en franjas
  paso: number // cuántos tramos dibujar (0..tramos.length)
}

function franjaDe(tiempo: number, tiempoTotal: number) {
  const fraccion = tiempoTotal > 0 ? tiempo / tiempoTotal : 0
  const indice = Math.floor(fraccion * TONOS_ARBOL.length)
  return Math.min(indice, TONOS_ARBOL.length - 1)
}

export function ArbolExploracion({ tramos, tiempos, tiempoTotal, paso }: Props) {
  const mapa = useMap()
  const capas = useRef<L.Polyline[]>([])
  const porFranja = useRef<Punto[][][]>([])
  const dibujados = useRef(0)

  // Crear una polilínea por franja al montar; quitarlas al desmontar
  useEffect(() => {
    const lienzo = L.canvas({ padding: 0.5 })
    capas.current = TONOS_ARBOL.map((color) =>
      L.polyline([], { renderer: lienzo, color, weight: 1.6, opacity: 0.85, interactive: false }).addTo(mapa),
    )
    porFranja.current = TONOS_ARBOL.map(() => [])
    dibujados.current = 0
    return () => {
      capas.current.forEach((capa) => capa.remove())
      capas.current = []
    }
  }, [mapa, tramos])

  // Al avanzar se agregan solo los tramos nuevos; al retroceder se reconstruye desde cero
  useEffect(() => {
    if (paso < dibujados.current) {
      porFranja.current = TONOS_ARBOL.map(() => [])
      dibujados.current = 0
    }
    const tocadas = new Set<number>()
    for (let i = dibujados.current; i < paso; i++) {
      const franja = franjaDe(tiempos[i], tiempoTotal)
      porFranja.current[franja].push(tramos[i])
      tocadas.add(franja)
    }
    if (dibujados.current === 0) {
      // reconstrucción: todas las franjas
      TONOS_ARBOL.forEach((_, franja) => tocadas.add(franja))
    }
    dibujados.current = paso
    tocadas.forEach((franja) => capas.current[franja]?.setLatLngs(porFranja.current[franja]))
  }, [paso, tramos, tiempos, tiempoTotal])

  return null
}
