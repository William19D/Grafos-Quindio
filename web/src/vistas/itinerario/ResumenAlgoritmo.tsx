// Resumen de un recorrido: jornada total, si cabe en 11 h, desplazamientos, visitas y ms.
import type { Recorrido } from '../../api'
import { horasMinutos, numero } from '../../formato'

type Props = {
  nombre: string
  detalle: string
  color: string
  recorrido: Recorrido
  trazo?: 'continuo' | 'discontinuo'
}

export function ResumenAlgoritmo({ nombre, detalle, color, recorrido, trazo = 'continuo' }: Props) {
  const exceso = recorrido.jornada_h - recorrido.limite_h
  return (
    <div className="bg-superficie p-4">
      <h2 className="flex items-center gap-2 text-lg font-semibold">
        <svg width="24" height="8" aria-hidden="true">
          <line x1="0" y1="4" x2="24" y2="4" stroke={color} strokeWidth="4" strokeDasharray={trazo === 'discontinuo' ? '6 4' : undefined} />
        </svg>
        {nombre}
        <span className="text-sm font-normal text-tinta-3">{detalle}</span>
      </h2>
      <div className="mt-2 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <p className="cifra text-[30px] font-semibold leading-tight">{horasMinutos(recorrido.jornada_h)}</p>
        {recorrido.cabe ? (
          <span className="rounded-full bg-positivo-palido px-2.5 py-0.5 text-sm font-medium text-positivo">Cabe en 11 h</span>
        ) : (
          <span className="rounded-full bg-negativo-palido px-2.5 py-0.5 text-sm font-medium text-negativo">No cabe: {horasMinutos(exceso)} de más</span>
        )}
      </div>
      {/* flex-wrap y no 3 columnas fijas: en el teléfono "Desplazamientos" no cabe en un tercio */}
      <dl className="mt-3 flex flex-wrap gap-x-6 gap-y-2 text-sm">
        <div>
          <dt className="text-tinta-3">Desplazamientos</dt>
          <dd className="cifra font-medium">{numero(recorrido.total_desplazamientos_min, 1)} min</dd>
        </div>
        <div>
          <dt className="text-tinta-3">Visitas</dt>
          <dd className="cifra font-medium">{numero(recorrido.total_visitas_min)} min</dd>
        </div>
        <div>
          <dt className="text-tinta-3">Cómputo</dt>
          <dd className="cifra font-medium">{numero(recorrido.ms, 2)} ms</dd>
        </div>
      </dl>
    </div>
  )
}
