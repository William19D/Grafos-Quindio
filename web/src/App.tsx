// Armazón de la aplicación: barra superior con las cuatro vistas y la vista elegida.
// La vista elegida vive en la dirección (#ruta, #itinerario, ...) para poder enlazarla.
import { lazy, Suspense, useEffect, useState } from 'react'
import { pedirLugares, type Lugar } from './api'
import { Marca } from './componentes/Marca'
import { Aviso } from './componentes/Aviso'
import { VistaRuta } from './vistas/VistaRuta'
import { VistaEnvolvente } from './vistas/VistaEnvolvente'
import { VistaItinerario } from './vistas/VistaItinerario'

// Recharts pesa: la vista de resultados se descarga solo cuando se abre.
const VistaResultados = lazy(() => import('./vistas/VistaResultados'))

const VISTAS = [
  { id: 'ruta', nombre: 'Ruta' },
  { id: 'envolvente', nombre: 'Envolvente' },
  { id: 'itinerario', nombre: 'Itinerario' },
  { id: 'resultados', nombre: 'Resultados' },
] as const
type IdVista = (typeof VISTAS)[number]['id']

function vistaDeLaDireccion(): IdVista {
  const pedida = window.location.hash.slice(1)
  const encontrada = VISTAS.find((v) => v.id === pedida)
  return encontrada ? encontrada.id : 'ruta'
}

export default function App() {
  const [vista, setVista] = useState<IdVista>(vistaDeLaDireccion)
  const [lugares, setLugares] = useState<Lugar[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    // Al cambiar de vista se vuelve arriba: si no, la vista nueva se abre en la posición de
    // desplazamiento de la anterior (en el teléfono, a mitad de página).
    const alCambiar = () => {
      setVista(vistaDeLaDireccion())
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', alCambiar)
    return () => window.removeEventListener('hashchange', alCambiar)
  }, [])

  // Los lugares se piden una sola vez y los usan todas las vistas.
  useEffect(() => {
    pedirLugares().then(setLugares).catch((e: Error) => setError(e.message))
  }, [])

  return (
    <>
      <a href="#contenido" className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-2 focus:z-[2000] focus:bg-superficie focus:px-3 focus:py-2">
        Saltar al contenido
      </a>
      <header className="sticky top-0 z-[1100] border-b border-borde bg-superficie">
        <div className="flex flex-wrap items-center gap-x-8 px-4 lg:px-6">
          <a href="#ruta" className="flex h-12 items-center gap-2.5 no-underline sm:h-14">
            <Marca />
            <span className="leading-tight">
              <span className="block font-semibold [font-stretch:88%]">Rutas del Paisaje Cultural Cafetero</span>
              <span className="hidden text-[13px] text-tinta-3 sm:block">Red vial del Quindío · OpenStreetMap</span>
            </span>
          </a>
          <nav aria-label="Vistas" className="-mx-4 w-[calc(100%+2rem)] overflow-x-auto px-4 sm:mx-0 sm:w-auto sm:px-0">
            <ul className="flex gap-1">
              {VISTAS.map((v) => (
                <li key={v.id}>
                  <a
                    href={`#${v.id}`}
                    aria-current={vista === v.id ? 'page' : undefined}
                    className="flex h-12 items-center border-b-2 border-transparent px-3 text-tinta-2 transition-colors hover:text-tinta aria-[current=page]:border-cereza aria-[current=page]:font-semibold aria-[current=page]:text-tinta sm:h-14"
                  >
                    {v.nombre}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </header>

      <main id="contenido">
        {error ? (
          <div className="p-6">
            <Aviso tipo="error">No se pudieron cargar los lugares: {error}. ¿Está corriendo el backend en el puerto 8000?</Aviso>
          </div>
        ) : !lugares ? (
          <p className="p-6 text-tinta-3">Cargando lugares…</p>
        ) : vista === 'ruta' ? (
          <VistaRuta lugares={lugares} />
        ) : vista === 'envolvente' ? (
          <VistaEnvolvente lugares={lugares} />
        ) : vista === 'itinerario' ? (
          <VistaItinerario lugares={lugares} />
        ) : (
          <Suspense fallback={<p className="p-6 text-tinta-3">Cargando resultados…</p>}>
            <VistaResultados />
          </Suspense>
        )}
      </main>
    </>
  )
}
