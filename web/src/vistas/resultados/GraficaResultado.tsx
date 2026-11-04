// Una gráfica interactiva (Recharts) construida a partir de una tabla de resultados.
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts'
import type { Tabla } from '../../api'
import { COLOR } from '../../colores'
import { numero } from '../../formato'

export type Serie = {
  columna: string
  nombre: string
  color: string
  discontinua?: boolean
  valor?: string // solo en dispersión con grupo: el valor de la columna `grupo` de esta serie
}

export type DefinicionGrafica = {
  requerimiento: string
  archivo: string
  titulo: string
  tipo: 'linea' | 'barras' | 'dispersion'
  x: string
  xEtiqueta: string
  yEtiqueta: string
  series: Serie[]
  logY?: boolean
  grupo?: string
  lectura?: (tablas: Tabla[]) => string
}

type Fila = Record<string, string | number | null>

// Convierte las filas (listas) en objetos {columna: valor}; las celdas vacías quedan en null.
function aObjetos(tabla: Tabla): Fila[] {
  return tabla.filas.map((fila) => {
    const objeto: Fila = {}
    tabla.columnas.forEach((columna, i) => {
      objeto[columna] = fila[i] === '' ? null : fila[i]
    })
    return objeto
  })
}

const EJE = { fontSize: 12, fill: COLOR.tinta3 }
// Enteros sin decimales (k = 5, no 5,0); solo lleva un decimal lo que no es entero (0,1 ms)
const formatoEje = (v: number) => numero(v, Number.isInteger(v) ? 0 : 1)
const formatoTooltip = (v: unknown) => (typeof v === 'number' ? numero(v, Math.abs(v) < 10 ? 3 : 1) : String(v))

export function GraficaResultado({ definicion: g, tablas }: { definicion: DefinicionGrafica; tablas: Tabla[] }) {
  const tabla = tablas.find((t) => t.archivo === g.archivo)
  if (!tabla) {
    return <p className="rounded-md border border-dashed border-control p-4 text-sm text-tinta-3">Falta {g.archivo} en resultados/.</p>
  }
  const filas = aObjetos(tabla)
  // Escala logarítmica: de la potencia de 10 por debajo del mínimo a la de encima del máximo,
  // con una marca en cada potencia de 10 (1, 10, 100, ...).
  let marcasLog: number[] | undefined
  if (g.logY) {
    const valores = filas.flatMap((f) => g.series.map((s) => f[s.columna])).filter((v): v is number => typeof v === 'number' && v > 0)
    const desde = Math.floor(Math.log10(Math.min(...valores)))
    const hasta = Math.ceil(Math.log10(Math.max(...valores)))
    marcasLog = []
    for (let p = desde; p <= hasta; p++) marcasLog.push(10 ** p)
  }
  const ejeY = (
    <YAxis
      scale={g.logY ? 'log' : 'auto'}
      domain={marcasLog ? [marcasLog[0], marcasLog[marcasLog.length - 1]] : [0, 'auto']}
      ticks={marcasLog}
      tick={EJE}
      tickFormatter={formatoEje}
      axisLine={false}
      tickLine={false}
      width={56}
    />
  )
  const rejilla = <CartesianGrid vertical={false} stroke={COLOR.regla} />
  const ayuda = <Tooltip formatter={formatoTooltip} contentStyle={{ border: `1px solid ${COLOR.borde}`, borderRadius: 6, fontSize: 13 }} />

  let grafica
  if (g.tipo === 'linea') {
    grafica = (
      <LineChart data={filas} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
        {rejilla}
        {/* 'auto' + sin decimales: marcas redondas (4, 6, 8…; 10.000, 20.000…), no 5.305, 11.305… */}
        <XAxis dataKey={g.x} type="number" domain={['auto', 'auto']} allowDecimals={false} tick={EJE} tickFormatter={formatoEje} stroke={COLOR.borde} />
        {ejeY}
        {ayuda}
        {g.series.map((s) => (
          <Line key={s.columna} dataKey={s.columna} name={s.nombre} stroke={s.color} strokeWidth={2} strokeDasharray={s.discontinua ? '6 4' : undefined} dot={{ r: 3 }} connectNulls={false} isAnimationActive={false} />
        ))}
      </LineChart>
    )
  } else if (g.tipo === 'barras') {
    grafica = (
      <BarChart data={filas} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
        {rejilla}
        <XAxis dataKey={g.x} tick={EJE} stroke={COLOR.borde} interval={0} />
        {ejeY}
        {ayuda}
        {g.series.map((s) => (
          <Bar key={s.columna} dataKey={s.columna} name={s.nombre} fill={s.color} isAnimationActive={false} />
        ))}
      </BarChart>
    )
  } else {
    // Dispersión: una nube de puntos por cada valor de la columna `grupo`
    grafica = (
      <ScatterChart margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
        {rejilla}
        <XAxis dataKey={g.x} type="number" name={g.xEtiqueta} domain={['auto', 'auto']} allowDecimals={false} tick={EJE} tickFormatter={formatoEje} stroke={COLOR.borde} />
        {ejeY}
        {ayuda}
        {g.series.map((s) => (
          <Scatter
            key={s.valor}
            name={s.nombre}
            data={filas.filter((f) => f[g.grupo!] === s.valor).map((f) => ({ [g.x]: f[g.x], [s.columna]: f[s.columna] }))}
            dataKey={s.columna}
            fill={s.color}
            isAnimationActive={false}
          />
        ))}
      </ScatterChart>
    )
  }

  return (
    <figure className="rounded-md border border-borde bg-superficie p-4">
      <figcaption>
        <span className="block font-semibold [font-stretch:88%]">{g.titulo}</span>
        {/* Leyenda: cada muestra es la misma marca de la gráfica */}
        {g.series.length > 1 ? (
          <span className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-[13px] text-tinta-2">
            {g.series.map((s) => (
              <span key={s.nombre} className="flex items-center gap-1.5">
                {g.tipo === 'linea' ? (
                  <svg width="20" height="8" aria-hidden="true"><line x1="0" y1="4" x2="20" y2="4" stroke={s.color} strokeWidth="2" strokeDasharray={s.discontinua ? '5 3' : undefined} /></svg>
                ) : (
                  <span className={`inline-block size-2.5 ${g.tipo === 'dispersion' ? 'rounded-full' : ''}`} style={{ background: s.color }} aria-hidden="true" />
                )}
                {s.nombre}
              </span>
            ))}
          </span>
        ) : null}
      </figcaption>
      <div className="mt-3 h-64" role="img" aria-label={`${g.titulo}. Eje x: ${g.xEtiqueta}; eje y: ${g.yEtiqueta}. Los datos están en la tabla ${g.archivo}.`}>
        <ResponsiveContainer width="100%" height="100%">
          {grafica}
        </ResponsiveContainer>
      </div>
      <p className="mt-1 flex justify-between gap-4 text-[12px] text-tinta-3">
        <span>x: {g.xEtiqueta}</span>
        <span>y: {g.yEtiqueta}</span>
      </p>
      {g.lectura ? <p className="mt-2 text-sm text-tinta-2">{g.lectura(tablas)}</p> : null}
    </figure>
  )
}
