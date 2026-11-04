// Panel para ver cómo explora Dijkstra: reproducir, pausar, mover la barra y elegir la velocidad.
import type { Arbol } from '../../api'
import { TONOS_ARBOL } from '../../colores'
import { numero } from '../../formato'

const VELOCIDADES = [
  { etiqueta: 'Lenta', segundos: 25 },
  { etiqueta: 'Normal', segundos: 10 },
  { etiqueta: 'Rápida', segundos: 4 },
]

type Props = {
  arbol: Arbol
  paso: number
  reproduciendo: boolean
  segundos: number
  alternar: () => void
  reiniciar: () => void
  saltarA: (paso: number) => void
  cambiarVelocidad: (segundos: number) => void
}

export function ControlesArbol({ arbol, paso, reproduciendo, segundos, alternar, reiniciar, saltarA, cambiarVelocidad }: Props) {
  const total = arbol.tramos.length
  // paso tramos dibujados = paso + 1 nodos explorados (el origen no tiene tramo)
  const explorados = paso + 1
  const frenteMin = paso > 0 ? arbol.tiempos_s[paso - 1] / 60 : 0
  const terminado = paso >= total

  return (
    <div className="space-y-3 rounded-md border border-borde p-3">
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" onClick={alternar} className="boton-primario">
          {reproduciendo ? 'Pausar' : terminado ? 'Repetir' : paso > 0 ? 'Continuar' : 'Reproducir'}
        </button>
        <button type="button" onClick={reiniciar} className="boton-secundario" disabled={paso === 0}>
          Reiniciar
        </button>
        <label className="ml-auto flex items-center gap-2 text-sm text-tinta-2">
          Velocidad
          <select
            value={segundos}
            onChange={(e) => cambiarVelocidad(Number(e.target.value))}
            className="h-10 rounded-md border border-control bg-superficie px-2 text-tinta"
          >
            {VELOCIDADES.map((v) => (
              <option key={v.segundos} value={v.segundos}>
                {v.etiqueta}
              </option>
            ))}
          </select>
        </label>
      </div>

      <input
        type="range"
        min={0}
        max={total}
        value={paso}
        onChange={(e) => saltarA(Number(e.target.value))}
        aria-label="Paso de la exploración"
        className="w-full accent-[var(--color-primario)]"
      />

      <p className="cifra text-sm" aria-live="off">
        <span className="font-medium">{numero(explorados)}</span> de {numero(arbol.nodos_explorados)} nodos explorados · frente de
        búsqueda a <span className="font-medium">{numero(frenteMin, 1)} min</span> del origen
      </p>
      {terminado ? (
        <p className="text-sm font-medium text-cereza">Dijkstra sacó el destino de la cola: su tiempo ya es definitivo y la búsqueda se detiene.</p>
      ) : null}

      {/* Leyenda de colores: tiempo desde el origen */}
      <div>
        <div className="flex h-2 overflow-hidden rounded-sm" aria-hidden="true">
          {TONOS_ARBOL.map((color) => (
            <span key={color} className="flex-1" style={{ background: color }} />
          ))}
        </div>
        <div className="mt-1 flex justify-between text-[13px] text-tinta-3">
          <span>cerca del origen</span>
          <span>{numero(arbol.tiempo_s / 60, 1)} min (destino)</span>
        </div>
      </div>

      <p className="text-[13px] text-tinta-3">
        Cada línea une un nodo con su predecesor: el nodo desde el que Dijkstra lo alcanzó por el camino más corto. Los nodos salen de la cola
        en orden de tiempo creciente, por eso la búsqueda crece como una mancha alrededor del origen hasta tocar el destino; al final, el
        camino de predecesores del destino es la ruta.
      </p>
    </div>
  )
}
