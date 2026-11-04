// Tabla del itinerario con el formato del anexo: orden, lugar, desplazamiento, visita, acumulado.
import type { Recorrido } from '../../api'
import { numero } from '../../formato'

export function TablaDia({ titulo, color, recorrido }: { titulo: string; color: string; recorrido: Recorrido }) {
  return (
    <div className="rounded-md border border-borde bg-superficie">
      <h3 className="flex items-center gap-2 border-b border-borde px-4 py-2.5 font-semibold">
        <span className="inline-block size-2.5 rounded-full" style={{ background: color }} aria-hidden="true" />
        Orden de visita · {titulo}
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[520px] text-sm">
          <thead className="text-[13px] text-tinta-3">
            <tr>
              <th scope="col" className="px-4 py-2 text-left font-normal">Orden</th>
              <th scope="col" className="py-2 text-left font-normal">Lugar</th>
              <th scope="col" className="py-2 pl-3 text-right font-normal">Desplazamiento (min)</th>
              <th scope="col" className="py-2 pl-3 text-right font-normal">Visita (min)</th>
              <th scope="col" className="px-4 py-2 text-right font-normal">Acumulado (h)</th>
            </tr>
          </thead>
          <tbody>
            {recorrido.filas.map((fila) => (
              <tr key={String(fila.orden)} className="border-t border-regla">
                <td className="px-4 py-2 text-tinta-2">{fila.orden}</td>
                <td className="py-2">{fila.nombre}</td>
                <td className="py-2 pl-3 text-right">{numero(fila.desplazamiento_desde_anterior_min, 1)}</td>
                <td className="py-2 pl-3 text-right">{fila.visita_min === null ? <span className="text-tinta-3">—</span> : fila.visita_min}</td>
                <td className={`px-4 py-2 text-right ${fila.tiempo_acumulado_h > recorrido.limite_h ? 'font-semibold text-negativo' : ''}`}>
                  {numero(fila.tiempo_acumulado_h, 2)}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot className="border-t-2 border-borde font-semibold">
            <tr>
              <td className="px-4 py-2" colSpan={2}>Total</td>
              <td className="py-2 pl-3 text-right">{numero(recorrido.total_desplazamientos_min, 1)}</td>
              <td className="py-2 pl-3 text-right">{recorrido.total_visitas_min}</td>
              <td className="px-4 py-2 text-right">{numero(recorrido.jornada_h, 2)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}
