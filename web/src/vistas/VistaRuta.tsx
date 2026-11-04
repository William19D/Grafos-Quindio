// Vista 1 - Ruta más rápida entre dos lugares (Dijkstra con cola de prioridad, R2).
import { useEffect, useState } from 'react'
import { CircleMarker, Polyline, Tooltip } from 'react-leaflet'
import { pedirRuta, type Lugar, type Ruta } from '../api'
import { Aviso } from '../componentes/Aviso'
import { Cifra, CifraPrincipal, Cifras } from '../componentes/Cifras'
import { ConMapa } from '../componentes/ConMapa'
import { Mapa } from '../componentes/Mapa'
import { SelectorLugar } from '../componentes/SelectorLugar'
import { COLOR } from '../colores'
import { numero } from '../formato'

export function VistaRuta({ lugares }: { lugares: Lugar[] }) {
  const [origen, setOrigen] = useState('ARM')
  const [destino, setDestino] = useState('COC')
  const [ruta, setRuta] = useState<Ruta | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  async function calcular() {
    setCargando(true)
    setError('')
    try {
      setRuta(await pedirRuta(origen, destino))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setCargando(false)
    }
  }

  // Al abrir la vista se muestra una ruta de ejemplo (Armenia -> Valle de Cocora).
  useEffect(() => {
    calcular()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Se derivan al renderizar: no hace falta guardarlos en otro estado
  const mismoLugar = origen === destino
  const desactualizada = ruta !== null && (ruta.origen.id !== origen || ruta.destino.id !== destino)

  const intercambiar = () => {
    setOrigen(destino)
    setDestino(origen)
  }

  const panel = (
    <>
      <div>
        <h1 className="text-2xl font-semibold">Ruta más rápida</h1>
        <p className="mt-1 text-tinta-2">Dijkstra con cola de prioridad sobre la red vial, calculado en el servidor en este momento.</p>
      </div>

      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault()
          calcular()
        }}
      >
        <SelectorLugar etiqueta="Origen" lugares={lugares} valor={origen} alCambiar={setOrigen} />
        <SelectorLugar etiqueta="Destino" lugares={lugares} valor={destino} alCambiar={setDestino} />
        <div className="flex flex-wrap gap-2">
          <button type="submit" disabled={cargando || mismoLugar} aria-describedby="estado-ruta" className="boton-primario">
            {cargando ? 'Calculando…' : 'Calcular ruta'}
          </button>
          <button type="button" onClick={intercambiar} className="boton-secundario">
            Invertir sentido
          </button>
        </div>
        <p id="estado-ruta" aria-live="polite" className="text-sm font-medium text-negativo empty:hidden">
          {mismoLugar ? 'El origen y el destino son el mismo lugar: elige otro destino.' : ''}
        </p>
      </form>

      {error ? <Aviso tipo="error">{error}</Aviso> : null}
      {desactualizada && !mismoLugar ? <Aviso tipo="nota">Cambiaste el origen o el destino: la ruta de abajo es la anterior. Pulsa “Calcular ruta”.</Aviso> : null}

      {ruta ? (
        <div className="space-y-4" aria-live="polite">
          <CifraPrincipal etiqueta={`${ruta.origen.nombre} → ${ruta.destino.nombre}`} valor={numero(ruta.tiempo_min, 1)} unidad="min">
            Dijkstra fijó el destino después de explorar {numero(ruta.nodos_explorados)} de {numero(ruta.nodos_grafo)} nodos (
            {numero((100 * ruta.nodos_explorados) / ruta.nodos_grafo, 1)} %).
          </CifraPrincipal>
          <Cifras>
            <Cifra etiqueta="Distancia" valor={numero(ruta.distancia_km, 1)} unidad="km" />
            <Cifra etiqueta="Nodos explorados" valor={numero(ruta.nodos_explorados)} />
            <Cifra etiqueta="Nodos de la ruta" valor={numero(ruta.nodos_ruta)} />
            <Cifra etiqueta="Cómputo" valor={numero(ruta.ms, 1)} unidad="ms" />
          </Cifras>
          <p className="text-[13px] text-tinta-3">
            El tiempo supone la velocidad máxima de cada vía (o la imputada por tipo de vía en R1). Los ms cuentan solo el algoritmo, no la red.
          </p>
        </div>
      ) : null}
    </>
  )

  const inicio = ruta?.polilinea[0]
  const fin = ruta?.polilinea[ruta.polilinea.length - 1]
  return (
    <ConMapa panel={panel}>
      <Mapa etiqueta="Mapa de la ruta" limites={ruta && ruta.polilinea.length > 1 ? ruta.polilinea : undefined}>
        {ruta ? (
          <>
            {/* Borde blanco debajo de la línea para que se lea sobre cualquier fondo */}
            <Polyline positions={ruta.polilinea} pathOptions={{ color: '#ffffff', weight: 9, opacity: 0.9 }} />
            <Polyline positions={ruta.polilinea} pathOptions={{ color: COLOR.cereza, weight: 5 }} />
            {inicio ? (
              <CircleMarker center={inicio} radius={8} pathOptions={{ color: '#fff', weight: 2, fillColor: COLOR.tinta, fillOpacity: 1 }}>
                {/* Etiquetas fijas: en el teléfono no hay "pasar el ratón", y el color solo no dice cuál es cuál */}
                <Tooltip permanent direction="auto">Origen: {ruta.origen.nombre}</Tooltip>
              </CircleMarker>
            ) : null}
            {fin ? (
              <CircleMarker center={fin} radius={8} pathOptions={{ color: '#fff', weight: 2, fillColor: COLOR.cereza, fillOpacity: 1 }}>
                <Tooltip permanent direction="auto">Destino: {ruta.destino.nombre}</Tooltip>
              </CircleMarker>
            ) : null}
          </>
        ) : null}
      </Mapa>
    </ConMapa>
  )
}
