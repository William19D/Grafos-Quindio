// La jornada de cada recorrido dibujada sobre un mismo eje de horas, con el límite de 11 h.
// Cada visita es un bloque lleno; cada desplazamiento, una línea delgada entre bloques.
import type { Recorrido } from '../../api'
import { COLOR } from '../../colores'
import { horasMinutos, numero } from '../../formato'

export function BarraJornada({ heldKarp, voraz }: { heldKarp: Recorrido; voraz: Recorrido }) {
  const limite = heldKarp.limite_h
  // El eje llega a la hora entera siguiente a la jornada más larga (mínimo 12 h)
  const escalaH = Math.max(12, Math.ceil(Math.max(heldKarp.jornada_h, voraz.jornada_h)))
  const porcentaje = (horas: number) => `${(100 * horas) / escalaH}%`
  const horas = Array.from({ length: escalaH + 1 }, (_, h) => h)

  return (
    <figure className="rounded-md border border-borde bg-superficie p-4">
      <figcaption className="mb-3 font-semibold [font-stretch:88%]">La jornada contra el límite de {limite} h</figcaption>
      <div className="grid grid-cols-[88px_1fr] items-center gap-x-3 gap-y-2 sm:grid-cols-[150px_1fr]">
        <Carril nombre="Held-Karp" color={COLOR.cereza} recorrido={heldKarp} escalaH={escalaH} limite={limite} />
        <Carril nombre="Vecino más cercano" color={COLOR.azul} recorrido={voraz} escalaH={escalaH} limite={limite} />
        {/* Eje de horas */}
        <span />
        <div className="relative h-5 text-[12px] text-tinta-3" aria-hidden="true">
          {/* Marcas cada 2 h y en el límite; se omiten las que quedarían pegadas al límite */}
          {horas.map((h) =>
            h === limite || (h % 2 === 0 && Math.abs(h - limite) > 1) ? (
              <span key={h} className="cifra absolute -translate-x-1/2" style={{ left: porcentaje(h) }}>
                {h} h
              </span>
            ) : null,
          )}
        </div>
      </div>
      <p className="mt-2 text-[13px] text-tinta-3">Bloques: visitas (con el código del lugar). Líneas: desplazamientos. La franja rosada queda fuera de la jornada de {limite} h.</p>
    </figure>
  )
}

type PropsCarril = { nombre: string; color: string; recorrido: Recorrido; escalaH: number; limite: number }

function Carril({ nombre, color, recorrido, escalaH, limite }: PropsCarril) {
  const ancho = (minutos: number) => `${(100 * minutos) / 60 / escalaH}%`
  return (
    <>
      <span className="text-sm leading-tight">{nombre}</span>
      <div
        role="img"
        aria-label={`${nombre}: jornada de ${horasMinutos(recorrido.jornada_h)}, límite ${limite} h. Orden: ${recorrido.orden.join(', ')}.`}
        className="relative h-9 overflow-hidden rounded-sm bg-hundido"
      >
        {/* Lo que pasa de 11 h */}
        <div className="absolute inset-y-0 right-0 bg-negativo-palido" style={{ left: `${(100 * limite) / escalaH}%` }} />
        <div className="absolute inset-y-0 w-px bg-negativo" style={{ left: `${(100 * limite) / escalaH}%` }} />
        <div className="relative flex h-full items-center">
          {recorrido.filas.map((fila, i) => (
            <div key={i} className="contents">
              <div className="h-[3px] shrink-0" style={{ width: ancho(fila.desplazamiento_desde_anterior_min), background: color }} title={`Viaje a ${fila.nombre}: ${numero(fila.desplazamiento_desde_anterior_min, 1)} min`} />
              {fila.visita_min !== null ? (
                <div
                  className="flex h-7 shrink-0 items-center justify-center overflow-hidden border-x border-white text-[11px] font-semibold text-white"
                  style={{ width: ancho(fila.visita_min), background: color }}
                  title={`${fila.nombre}: ${fila.visita_min} min de visita`}
                >
                  {/* El código solo cabe en bloques de 1 h o más y con la barra ancha (no en el teléfono) */}
                  {fila.visita_min >= 60 ? <span className="hidden sm:inline">{fila.lugar}</span> : null}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
