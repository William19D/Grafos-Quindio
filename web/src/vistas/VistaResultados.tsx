// Vista 4 - Tablas y gráficas de R1 a R4, leídas de los CSV de resultados/ (vía /api/resultados).
import { useEffect, useState } from 'react'
import { pedirResultados, type Resultados, type Tabla } from '../api'
import { Aviso } from '../componentes/Aviso'
import { GraficaResultado, type DefinicionGrafica } from './resultados/GraficaResultado'
import { TablaResultado } from './resultados/TablaResultado'
import { COLOR } from '../colores'
import { numero } from '../formato'

const REQUERIMIENTOS = [
  { id: 'R1', titulo: 'R1 — Modelo de la red vial' },
  { id: 'R2', titulo: 'R2 — Caminos mínimos con Dijkstra' },
  { id: 'R3', titulo: 'R3 — Envolvente convexa' },
  { id: 'R4', titulo: 'R4 — Ruta óptima de recorrido (TSP)' },
  { id: 'Catálogo', titulo: 'Catálogo de lugares' },
]

// Valor numérico de una celda (columna, fila) de una tabla; se usa en las frases de lectura
function celda(tabla: Tabla | undefined, columna: string, fila = 0): number {
  if (!tabla) return NaN
  return Number(tabla.filas[fila]?.[tabla.columnas.indexOf(columna)])
}

const GRAFICAS: DefinicionGrafica[] = [
  {
    requerimiento: 'R1',
    archivo: 'r1_scc_tiempos.csv',
    titulo: 'Tiempo de obtener la componente fuertemente conexa',
    tipo: 'linea',
    x: 'V_mas_E',
    xEtiqueta: 'V + E',
    yEtiqueta: 'ms',
    series: [
      { columna: 'tiempo_ms', nombre: 'largest_component (Tarjan + copia)', color: COLOR.cereza },
      { columna: 'tiempo_tarjan_ms', nombre: 'Solo Tarjan', color: COLOR.azul, discontinua: true },
    ],
    lectura: () => 'Las dos curvas crecen casi en línea recta con V + E, como predice O(V + E).',
  },
  {
    requerimiento: 'R2',
    archivo: 'r2_dijkstra.csv',
    titulo: 'Tiempo de Dijkstra contra nodos explorados',
    tipo: 'dispersion',
    x: 'nodos_explorados',
    xEtiqueta: 'Nodos explorados',
    yEtiqueta: 'ms (escala logarítmica)',
    logY: true,
    grupo: 'version',
    series: [
      { valor: 'cola_prioridad', columna: 'tiempo_ms', nombre: 'Cola de prioridad', color: COLOR.cereza },
      { valor: 'lineal', columna: 'tiempo_ms', nombre: 'Lineal', color: COLOR.azul },
    ],
    lectura: (tablas) => {
      const cociente = tablas.find((t) => t.archivo === 'r2_cociente.csv')
      return `Mediana del cociente lineal / cola: ${numero(celda(cociente, 'mediana'), 1)} veces más lenta la versión lineal.`
    },
  },
  {
    requerimiento: 'R3',
    archivo: 'r3_envolvente.csv',
    titulo: 'QuickHull propio contra SciPy (Qhull)',
    tipo: 'barras',
    x: 'conjunto',
    xEtiqueta: 'Conjunto de puntos',
    yEtiqueta: 'ms',
    series: [
      { columna: 'tiempo_propio_ms', nombre: 'QuickHull propio (Python)', color: COLOR.cereza },
      { columna: 'tiempo_scipy_ms', nombre: 'SciPy (Qhull, en C)', color: COLOR.azul },
    ],
    lectura: () => 'Los dos dan los mismos vértices; Qhull está escrito en C, por eso es más rápido.',
  },
  {
    requerimiento: 'R4',
    archivo: 'r4_exactos.csv',
    titulo: 'Fuerza bruta contra Held-Karp',
    tipo: 'linea',
    x: 'k',
    xEtiqueta: 'k (lugares a visitar)',
    yEtiqueta: 'ms (escala logarítmica)',
    logY: true,
    series: [
      { columna: 'tiempo_held_karp_ms', nombre: 'Held-Karp O(k²·2ᵏ)', color: COLOR.cereza },
      { columna: 'tiempo_fuerza_bruta_ms', nombre: 'Fuerza bruta O(k·k!)', color: COLOR.azul, discontinua: true },
    ],
    lectura: () => 'Con k = 12 la fuerza bruta no terminó en 5 minutos; Held-Karp tardó menos de un segundo.',
  },
  {
    requerimiento: 'R4',
    archivo: 'r4_calidad.csv',
    titulo: 'Brecha de la voraz con el óptimo',
    tipo: 'barras',
    x: 'k',
    xEtiqueta: 'k (lugares a visitar)',
    yEtiqueta: '% sobre el óptimo',
    series: [
      { columna: 'brecha_promedio_pct', nombre: 'Promedio', color: COLOR.cereza },
      { columna: 'brecha_maxima_pct', nombre: 'Máxima', color: COLOR.azul },
    ],
    lectura: (tablas) => {
      const calidad = tablas.find((t) => t.archivo === 'r4_calidad.csv')
      if (!calidad) return ''
      const promedios = calidad.filas.map((_, f) => celda(calidad, 'brecha_promedio_pct', f))
      const maximas = calidad.filas.map((_, f) => celda(calidad, 'brecha_maxima_pct', f))
      return `En promedio la voraz queda entre ${numero(Math.min(...promedios), 1)} % y ${numero(Math.max(...promedios), 1)} % por encima del óptimo; la peor instancia medida, ${numero(Math.max(...maximas), 1)} %.`
    },
  },
  {
    requerimiento: 'R4',
    archivo: 'r4_held_karp_extendido.csv',
    titulo: 'Held-Karp con k de 13 a 16',
    tipo: 'linea',
    x: 'k',
    xEtiqueta: 'k (lugares a visitar)',
    yEtiqueta: 'ms',
    series: [{ columna: 'tiempo_held_karp_ms', nombre: 'Held-Karp', color: COLOR.cereza }],
    lectura: () => 'Cada lugar más multiplica el tiempo por algo más de 2, como dice el factor 2ᵏ.',
  },
]

const DESCRIPCION_FIGURA: Record<string, string> = {
  'catalogo.png': 'Mapa de los lugares del catálogo por categoría',
  'r1_scc.png': 'Tiempo de obtener la componente fuertemente conexa contra V + E',
  'r2_tiempo_vs_nodos.png': 'Tiempo de Dijkstra contra nodos explorados, versión lineal y con cola de prioridad',
  'r3_envolvente.png': 'Envolvente convexa sobre los nodos de la red',
  'r3_tiempos.png': 'Tiempo de QuickHull propio y de SciPy contra el número de puntos',
  'r4_tiempo_vs_k.png': 'Tiempo de fuerza bruta y de Held-Karp contra k',
}

export default function VistaResultados() {
  const [datos, setDatos] = useState<Resultados | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    pedirResultados().then(setDatos).catch((e: Error) => setError(e.message))
  }, [])

  return (
    <div className="mx-auto max-w-[1240px] px-4 py-6 lg:px-6">
      <h1 className="text-2xl font-semibold">Resultados de los experimentos</h1>
      <p className="mt-1 max-w-[70ch] text-tinta-2">
        Las mismas tablas y gráficas del documento técnico, leídas de los archivos de <code className="text-[14px]">resultados/</code>. Tiempos en milisegundos: mediana de 5 repeticiones.
      </p>
      <nav aria-label="Requerimientos" className="mt-4 flex flex-wrap gap-2">
        {REQUERIMIENTOS.map((r) => (
          <a key={r.id} href={`#seccion-${r.id}`} // Sin cambiar el #: el # de la dirección elige la vista (Ruta, Itinerario, ...)
            onClick={(e) => {
              e.preventDefault()
              document.getElementById(`seccion-${r.id}`)?.scrollIntoView()
            }} className="rounded-md border border-control bg-superficie px-3 py-1.5 text-sm hover:bg-hundido">
            {r.id}
          </a>
        ))}
      </nav>

      {error ? <div className="mt-6"><Aviso tipo="error">No se pudieron leer los resultados: {error}</Aviso></div> : null}
      {!datos && !error ? <p className="mt-6 text-tinta-3">Leyendo resultados…</p> : null}

      {datos
        ? REQUERIMIENTOS.map((req) => {
            const graficas = GRAFICAS.filter((g) => g.requerimiento === req.id)
            const figuras = datos.figuras.filter((f) => f.requerimiento === req.id)
            const tablas = datos.tablas.filter((t) => t.requerimiento === req.id)
            return (
              <section key={req.id} id={`seccion-${req.id}`} className="mt-12 scroll-mt-20">
                <h2 className="border-b border-borde pb-2 text-xl font-semibold">{req.titulo}</h2>

                {/* Gráficas interactivas y figuras del documento en una sola rejilla; si quedan en
                    número impar, la última ocupa las dos columnas para no dejar un hueco. */}
                <div className="mt-4 grid gap-4 lg:grid-cols-2 lg:[&>*:last-child:nth-child(odd)]:col-span-2">
                  {graficas.map((g) => (
                    <GraficaResultado key={g.archivo} definicion={g} tablas={datos.tablas} />
                  ))}
                  {figuras.map((f) => (
                    <figure key={f.archivo} className="rounded-md border border-borde bg-superficie p-3">
                      <img src={f.url} alt={DESCRIPCION_FIGURA[f.archivo] ?? f.archivo} width={f.ancho} height={f.alto} loading="lazy" className="mx-auto h-auto max-h-[520px] w-auto max-w-full" />
                      <figcaption className="mt-2 text-[13px] text-tinta-3">
                        {DESCRIPCION_FIGURA[f.archivo] ?? f.archivo} · figura del documento ({f.archivo})
                      </figcaption>
                    </figure>
                  ))}
                </div>

                <div className="mt-4 space-y-2">
                  {tablas.map((t) => (
                    <TablaResultado key={t.archivo} tabla={t} />
                  ))}
                </div>
              </section>
            )
          })
        : null}
    </div>
  )
}
