// Una tabla de resultados (un CSV) plegable. Números a la derecha con dígitos del mismo ancho.
import type { Tabla } from '../../api'

const formato = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 3 })

export function TablaResultado({ tabla }: { tabla: Tabla }) {
  return (
    <details className="group rounded-md border border-borde bg-superficie">
      <summary className="flex cursor-pointer items-baseline justify-between gap-4 px-4 py-2.5 hover:bg-hundido">
        <span className="font-medium">{tabla.titulo}</span>
        <span className="shrink-0 text-[13px] text-tinta-3">
          {tabla.archivo} · {tabla.filas.length} filas
        </span>
      </summary>
      <div className="max-h-[420px] overflow-auto border-t border-borde">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-superficie text-[13px] text-tinta-3">
            <tr>
              {tabla.columnas.map((columna, i) => (
                <th key={columna} scope="col" className={`whitespace-nowrap px-3 py-2 font-normal ${typeof tabla.filas[0]?.[i] === 'number' ? 'text-right' : 'text-left'}`}>
                  {columna.replaceAll('_', ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {tabla.filas.map((fila, f) => (
              <tr key={f} className="border-t border-regla">
                {fila.map((valor, c) =>
                  typeof valor === 'number' ? (
                    <td key={c} className="whitespace-nowrap px-3 py-1.5 text-right">{formato.format(valor)}</td>
                  ) : (
                    <td key={c} className="px-3 py-1.5">{valor === '' ? <span className="text-tinta-3">—</span> : valor}</td>
                  ),
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}
