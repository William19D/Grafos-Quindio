// Mapa base del Quindío (react-leaflet). Las vistas le ponen encima sus capas como hijos.
import { useEffect, type ReactNode } from 'react'
import { MapContainer, TileLayer, useMap } from 'react-leaflet'
import type { LatLngBoundsExpression } from 'leaflet'

const CENTRO_QUINDIO: [number, number] = [4.46, -75.68]

// Ajusta el encuadre cuando cambian los límites (p. ej. al calcular otra ruta).
function Encuadre({ limites }: { limites?: LatLngBoundsExpression }) {
  const mapa = useMap()
  useEffect(() => {
    if (limites) mapa.fitBounds(limites, { padding: [32, 32] })
  }, [mapa, limites])
  return null
}

// En una pantalla táctil el dedo arrastra la página, no el mapa (con dos dedos se acerca y aleja).
const PANTALLA_TACTIL = window.matchMedia('(pointer: coarse)').matches

type Props = {
  limites?: LatLngBoundsExpression
  etiqueta: string
  // true cuando el mapa está en medio de una página que se desplaza (itinerario): la rueda del
  // ratón y el dedo deben mover la página y no quedar atrapados en el mapa.
  dentroDePagina?: boolean
  children: ReactNode
}

export function Mapa({ limites, etiqueta, dentroDePagina = false, children }: Props) {
  return (
    <div role="region" aria-label={etiqueta} className="h-full w-full">
      <MapContainer
        center={CENTRO_QUINDIO}
        zoom={10}
        scrollWheelZoom={!dentroDePagina}
        dragging={!(dentroDePagina && PANTALLA_TACTIL)}
        className="h-full w-full"
      >
        {/* Teselas de OpenStreetMap; en index.css se les baja la saturación para que la ruta resalte */}
        <TileLayer
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">colaboradores de OpenStreetMap</a>'
          maxZoom={19}
        />
        <Encuadre limites={limites} />
        {children}
      </MapContainer>
    </div>
  )
}
