// Vista 3 - Itinerario de un día: Held-Karp (óptimo) contra vecino más cercano (voraz), R4.
import { useEffect, useMemo, useState } from 'react'
import { divIcon } from 'leaflet'
import { Marker, Polyline, Tooltip } from 'react-leaflet'
import { pedirItinerario, type Itinerario, type Lugar } from '../api'
import { Aviso } from '../componentes/Aviso'
import { Mapa } from '../componentes/Mapa'
import { SelectorLugar } from '../componentes/SelectorLugar'
import { BarraJornada } from './itinerario/BarraJornada'
import { ResumenAlgoritmo } from './itinerario/ResumenAlgoritmo'
import { TablaDia } from './itinerario/TablaDia'
import { COLOR } from '../colores'
import { horasMinutos, numero } from '../formato'

const MINIMO = 6
const MAXIMO = 8
// La misma selección del experimento de R4 (resultados/r4_itinerario.json)
const SELECCION_INICIAL = ['MOQ', 'FUN', 'JBQ', 'CLC', 'CIL', 'CRS', 'ACR']

export function VistaItinerario({ lugares }: { lugares: Lugar[] }) {
  const [partida, setPartida] = useState('ARM')
  const [elegidos, setElegidos] = useState<string[]>(SELECCION_INICIAL)
  const [resultado, setResultado] = useState<Itinerario | null>(null)
  const [pedidoDelResultado, setPedidoDelResultado] = useState('')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')
  const [verHeldKarp, setVerHeldKarp] = useState(true)
  const [verVoraz, setVerVoraz] = useState(true)

  const porId = new Map(lugares.map((l) => [l.id, l]))
  const atractivos = lugares.filter((l) => l.duracion_visita_min !== null && l.id !== partida)

  // Validación (se deriva en cada render, no se guarda en otro estado)
  const cantidad = elegidos.length
  const esValido = cantidad >= MINIMO && cantidad <= MAXIMO
  let mensaje = ''
  if (cantidad < MINIMO) mensaje = `Elige ${MINIMO - cantidad} más: el mínimo es ${MINIMO}.`
  else if (cantidad > MAXIMO) mensaje = `Quita ${cantidad - MAXIMO}: el máximo es ${MAXIMO}.`
  let visitasMin = 0
  for (const id of elegidos) visitasMin += porId.get(id)?.duracion_visita_min ?? 0

  const pedidoActual = partida + ':' + [...elegidos].sort().join(',')
  const resultadoDesactualizado = resultado !== null && pedidoActual !== pedidoDelResultado

  async function armar() {
    if (!esValido) return
    setCargando(true)
    setError('')
    try {
      setResultado(await pedirItinerario(partida, elegidos))
      setPedidoDelResultado(pedidoActual)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setCargando(false)
    }
  }

  // Al abrir la vista se arma el itinerario de la selección de R4.
  useEffect(() => {
    armar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function alternar(id: string) {
    setElegidos((actuales) => (actuales.includes(id) ? actuales.filter((x) => x !== id) : [...actuales, id]))
  }

  function cambiarPartida(id: string) {
    setPartida(id)
    setElegidos((actuales) => actuales.filter((x) => x !== id)) // la partida no puede ser un atractivo
  }

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] lg:h-[calc(100dvh-57px)] lg:grid-cols-[380px_minmax(0,1fr)]">
      {/* Panel de selección */}
      <section className="space-y-5 border-borde bg-superficie p-4 lg:scroll-pb-20 lg:overflow-y-auto lg:border-r lg:p-6 lg:pb-0">
        <div>
          <h1 className="text-2xl font-semibold">Itinerario de un día</h1>
          <p className="mt-1 text-tinta-2">Salir, visitar los atractivos y volver en 11 horas como máximo. Orden óptimo con Held-Karp frente a la voraz.</p>
        </div>

        <form
          className="space-y-5"
          onSubmit={(e) => {
            e.preventDefault()
            armar()
          }}
        >
          <SelectorLugar etiqueta="Partida y regreso" lugares={lugares} valor={partida} alCambiar={cambiarPartida} />

          <fieldset>
            <legend className="text-sm font-medium">Atractivos (de {MINIMO} a {MAXIMO})</legend>
            <p id="estado-seleccion" aria-live="polite" className={`mt-1 text-sm ${esValido ? 'text-tinta-2' : 'font-medium text-negativo'}`}>
              {esValido ? `${cantidad} elegidos · ${horasMinutos(visitasMin / 60)} de visitas` : mensaje}
            </p>
            <ul className="mt-2 divide-y divide-regla rounded-md border border-borde">
              {atractivos.map((l) => (
                <li key={l.id}>
                  <label className="flex cursor-pointer items-center gap-3 px-3 py-2 hover:bg-hundido has-[:checked]:bg-hundido">
                    <input type="checkbox" checked={elegidos.includes(l.id)} onChange={() => alternar(l.id)} className="size-4 shrink-0" />
                    <span className="min-w-0 flex-1 leading-snug">
                      <span className="block">{l.nombre}</span>
                      <span className="block text-[13px] text-tinta-3">{l.municipio}</span>
                    </span>
                    <span className="cifra shrink-0 text-sm text-tinta-2">{l.duracion_visita_min} min</span>
                  </label>
                </li>
              ))}
            </ul>
          </fieldset>

          {/* El botón queda pegado abajo: la lista es larga y no hay que bajar hasta el final para usarlo */}
          <div className="sticky bottom-0 -mx-4 border-t border-borde bg-superficie px-4 py-3 lg:-mx-6 lg:px-6 lg:py-4">
            <button type="submit" disabled={!esValido || cargando} aria-describedby="estado-seleccion" className="boton-primario w-full">
              {cargando ? 'Calculando…' : 'Armar itinerario'}
            </button>
          </div>
        </form>
      </section>

      {/* Resultado */}
      <section aria-label="Resultado del itinerario" className="space-y-5 p-4 lg:overflow-y-auto lg:p-6">
        {error ? <Aviso tipo="error">{error}</Aviso> : null}
        {resultadoDesactualizado ? <Aviso tipo="nota">La selección cambió: el resultado de abajo es el de la selección anterior. Pulsa “Armar itinerario”.</Aviso> : null}
        {!resultado ? (
          !error ? <p className="text-tinta-3">Calculando el itinerario…</p> : null
        ) : (
          <>
            <div className="grid gap-px overflow-hidden rounded-md border border-borde bg-borde md:grid-cols-2">
              <ResumenAlgoritmo nombre="Held-Karp" detalle="programación dinámica, óptimo" color={COLOR.cereza} recorrido={resultado.held_karp} />
              <ResumenAlgoritmo nombre="Vecino más cercano" detalle="heurística voraz" color={COLOR.azul} recorrido={resultado.voraz} trazo="discontinuo" />
            </div>
            <p className="text-tinta-2">
              {resultado.diferencia_min === 0
                ? 'La voraz encontró el mismo tiempo de desplazamiento que el óptimo para esta selección.'
                : `La voraz pasa ${numero(resultado.diferencia_min, 1)} min más en la carretera que Held-Karp (${numero(resultado.diferencia_pct, 1)} % más de desplazamiento). Las visitas suman lo mismo en los dos.`}
            </p>

            <BarraJornada heldKarp={resultado.held_karp} voraz={resultado.voraz} />

            <div className="overflow-hidden rounded-md border border-borde bg-superficie">
              <div className="flex flex-wrap items-center gap-x-5 gap-y-1 border-b border-borde px-4 py-2.5 text-sm">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={verHeldKarp} onChange={(e) => setVerHeldKarp(e.target.checked)} className="size-4" />
                  <svg width="28" height="8" aria-hidden="true"><line x1="0" y1="4" x2="28" y2="4" stroke={COLOR.cereza} strokeWidth="5" /></svg>
                  Held-Karp
                </label>
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={verVoraz} onChange={(e) => setVerVoraz(e.target.checked)} className="size-4" />
                  <svg width="28" height="8" aria-hidden="true"><line x1="0" y1="4" x2="28" y2="4" stroke={COLOR.azul} strokeWidth="3" strokeDasharray="7 5" /></svg>
                  Vecino más cercano
                </label>
                <span className="text-tinta-3">Los números son el orden de Held-Karp.</span>
              </div>
              <div className="h-[440px]">
                <MapaItinerario resultado={resultado} porId={porId} verHeldKarp={verHeldKarp} verVoraz={verVoraz} />
              </div>
            </div>

            <div className="grid grid-cols-[minmax(0,1fr)] gap-5 xl:grid-cols-2">
              <TablaDia titulo="Held-Karp" color={COLOR.cereza} recorrido={resultado.held_karp} />
              <TablaDia titulo="Vecino más cercano" color={COLOR.azul} recorrido={resultado.voraz} />
            </div>
          </>
        )}
      </section>
    </div>
  )
}

type PropsMapa = {
  resultado: Itinerario
  porId: Map<string, Lugar>
  verHeldKarp: boolean
  verVoraz: boolean
}

function MapaItinerario({ resultado, porId, verHeldKarp, verVoraz }: PropsMapa) {
  const hk = resultado.held_karp
  // useMemo: el encuadre solo cambia con un resultado nuevo, no al ocultar una capa
  const todos = useMemo(() => hk.tramos.flatMap((t) => t.polilinea), [hk])
  const visitas = hk.orden.slice(1, -1)
  const ordenVoraz = resultado.voraz.orden
  const partida = porId.get(resultado.partida)
  return (
    <Mapa etiqueta="Mapa de los dos recorridos" dentroDePagina limites={todos.length > 1 ? todos : undefined}>
      {/* Held-Karp abajo y más grueso; la voraz encima, discontinua: así se ven las dos donde coinciden */}
      {verHeldKarp ? hk.tramos.map((t, i) => <Polyline key={`hk${i}`} positions={t.polilinea} pathOptions={{ color: COLOR.cereza, weight: 6, opacity: 0.85 }} />) : null}
      {verVoraz
        ? resultado.voraz.tramos.map((t, i) => <Polyline key={`vz${i}`} positions={t.polilinea} pathOptions={{ color: COLOR.azul, weight: 3, dashArray: '8 6' }} />)
        : null}
      {partida ? (
        <Marker position={[partida.lat, partida.lon]} icon={divIcon({ className: '', html: '<span class="marca-orden partida">S</span>', iconSize: [24, 24] })}>
          <Tooltip>Salida y regreso: {partida.nombre}</Tooltip>
        </Marker>
      ) : null}
      {visitas.map((id, i) => {
        const lugar = porId.get(id)
        if (!lugar) return null
        return (
          <Marker key={id} position={[lugar.lat, lugar.lon]} icon={divIcon({ className: '', html: `<span class="marca-orden">${i + 1}</span>`, iconSize: [24, 24] })}>
            <Tooltip>
              <strong>{lugar.nombre}</strong>
              <br />
              Held-Karp: parada {i + 1} · voraz: parada {ordenVoraz.indexOf(id)}
            </Tooltip>
          </Marker>
        )
      })}
    </Mapa>
  )
}
