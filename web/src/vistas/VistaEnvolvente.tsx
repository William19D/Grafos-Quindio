// Vista 2 - Envolvente convexa de la red vial (QuickHull propio, R3) y lugares por categoría.
import { useEffect, useMemo, useState } from 'react'
import { CircleMarker, Polygon, Tooltip } from 'react-leaflet'
import { pedirEnvolvente, type Envolvente, type Lugar } from '../api'
import { Aviso } from '../componentes/Aviso'
import { Cifra, CifraPrincipal, Cifras } from '../componentes/Cifras'
import { ConMapa } from '../componentes/ConMapa'
import { Mapa } from '../componentes/Mapa'
import { COLOR, ESTILO_CATEGORIA } from '../colores'
import { NOMBRE_CATEGORIA, numero } from '../formato'

const CATEGORIAS = ['cabecera', 'atractivo', 'finca', 'acopio']

export function VistaEnvolvente({ lugares }: { lugares: Lugar[] }) {
  const [envolvente, setEnvolvente] = useState<Envolvente | null>(null)
  const [error, setError] = useState('')
  const [visibles, setVisibles] = useState<string[]>(CATEGORIAS)

  useEffect(() => {
    pedirEnvolvente().then(setEnvolvente).catch((e: Error) => setError(e.message))
  }, [])

  const alternar = (categoria: string) =>
    setVisibles((actuales) => (actuales.includes(categoria) ? actuales.filter((c) => c !== categoria) : [...actuales, categoria]))

  // useMemo: la misma lista mientras no cambie la envolvente, para no reencuadrar el mapa al filtrar
  const vertices = useMemo<[number, number][]>(() => (envolvente ? envolvente.vertices.map((v) => [v.lat, v.lon]) : []), [envolvente])

  const panel = (
    <>
      <div>
        <h1 className="text-2xl font-semibold">Envolvente convexa</h1>
        <p className="mt-1 text-tinta-2">El polígono convexo más pequeño que contiene todos los nodos de la red, con QuickHull (divide y vencerás).</p>
      </div>

      {error ? <Aviso tipo="error">No se pudo calcular la envolvente: {error}</Aviso> : null}

      {envolvente ? (
        <div className="space-y-4">
          <CifraPrincipal etiqueta="Área de la envolvente" valor={numero(envolvente.area_km2, 1)} unidad="km²">
            Mide la extensión de la red, no el límite político: el departamento mide ≈ 1.845 km².
          </CifraPrincipal>
          <Cifras>
            <Cifra etiqueta="Vértices" valor={numero(envolvente.n_vertices)} />
            <Cifra etiqueta="Puntos (nodos)" valor={numero(envolvente.n_puntos)} />
            <Cifra etiqueta="Cómputo QuickHull" valor={numero(envolvente.ms, 1)} unidad="ms" />
            <Cifra etiqueta="Coordenadas" valor="UTM 18N" />
          </Cifras>
        </div>
      ) : !error ? (
        <p className="text-tinta-3">Calculando la envolvente…</p>
      ) : null}

      <fieldset>
        <legend className="mb-2 text-sm font-medium">Lugares del catálogo por categoría</legend>
        <ul className="divide-y divide-regla rounded-md border border-borde">
          {CATEGORIAS.map((categoria) => {
            const cantidad = lugares.filter((l) => l.categoria === categoria).length
            const estilo = ESTILO_CATEGORIA[categoria]
            return (
              <li key={categoria}>
                <label className="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-hundido">
                  <input type="checkbox" checked={visibles.includes(categoria)} onChange={() => alternar(categoria)} className="size-4" />
                  <svg width="14" height="14" aria-hidden="true">
                    <circle cx="7" cy="7" r={estilo.radio - 1} fill={estilo.color} stroke="#fff" strokeWidth="1.5" />
                  </svg>
                  <span className="flex-1">{NOMBRE_CATEGORIA[categoria]}</span>
                  <span className="cifra text-tinta-3">{cantidad}</span>
                </label>
              </li>
            )
          })}
        </ul>
      </fieldset>

      {envolvente ? (
        <details className="text-sm">
          <summary className="cursor-pointer font-medium">Vértices en orden antihorario</summary>
          <table className="mt-2 w-full">
            <thead className="text-left text-[13px] text-tinta-3">
              <tr>
                <th className="py-1 font-normal">#</th>
                <th className="py-1 text-right font-normal">x (m)</th>
                <th className="py-1 text-right font-normal">y (m)</th>
              </tr>
            </thead>
            <tbody>
              {envolvente.vertices.map((v, i) => (
                <tr key={i} className="border-t border-regla">
                  <td className="py-1">{i + 1}</td>
                  <td className="py-1 text-right">{numero(v.x_utm)}</td>
                  <td className="py-1 text-right">{numero(v.y_utm)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      ) : null}
    </>
  )

  return (
    <ConMapa panel={panel}>
      <Mapa etiqueta="Mapa de la envolvente convexa" limites={vertices.length > 0 ? vertices : undefined}>
        {vertices.length > 0 ? (
          <Polygon positions={vertices} pathOptions={{ color: COLOR.primario, weight: 2.5, fillColor: COLOR.primario, fillOpacity: 0.06 }} />
        ) : null}
        {vertices.map((v, i) => (
          <CircleMarker key={i} center={v} radius={3.5} pathOptions={{ color: COLOR.primario, weight: 2, fillColor: '#fff', fillOpacity: 1 }}>
            <Tooltip>Vértice {i + 1}</Tooltip>
          </CircleMarker>
        ))}
        {lugares
          .filter((l) => visibles.includes(l.categoria))
          .map((l) => {
            const estilo = ESTILO_CATEGORIA[l.categoria]
            return (
              <CircleMarker key={l.id} center={[l.lat, l.lon]} radius={estilo.radio} pathOptions={{ color: '#fff', weight: 1.5, fillColor: estilo.color, fillOpacity: 1 }}>
                <Tooltip>
                  <strong>{l.nombre}</strong>
                  <br />
                  {NOMBRE_CATEGORIA[l.categoria]} · {l.municipio}
                </Tooltip>
              </CircleMarker>
            )
          })}
      </Mapa>
    </ConMapa>
  )
}
