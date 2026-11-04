import type { ReactNode } from 'react'

// Una franja dividida con varias cifras (etiqueta arriba, valor abajo).
// Uso: <Cifras><Cifra etiqueta="Distancia" valor="21,3" unidad="km" /> ...</Cifras>
export function Cifras({ children }: { children: ReactNode }) {
  // Truco de las líneas divisorias: el fondo de la rejilla es del color del borde y el espacio
  // de 1px entre celdas (gap-px) deja verlo.
  return <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-md border border-borde bg-borde">{children}</dl>
}

export function Cifra({ etiqueta, valor, unidad }: { etiqueta: string; valor: string; unidad?: string }) {
  return (
    <div className="bg-superficie px-3 py-2.5">
      <dt className="text-[13px] text-tinta-3">{etiqueta}</dt>
      <dd className="cifra text-lg font-medium">
        {valor}
        {unidad ? <span className="ml-1 text-sm font-normal text-tinta-3">{unidad}</span> : null}
      </dd>
    </div>
  )
}

// La cifra que responde la pregunta de la vista: más grande que las demás.
export function CifraPrincipal({ etiqueta, valor, unidad, children }: { etiqueta: string; valor: string; unidad: string; children?: ReactNode }) {
  return (
    <div>
      <p className="text-sm text-tinta-2">{etiqueta}</p>
      <p className="cifra text-[34px] font-semibold leading-tight">
        {valor}
        <span className="ml-1.5 text-lg font-normal text-tinta-3">{unidad}</span>
      </p>
      {children ? <p className="mt-1 text-sm text-tinta-2">{children}</p> : null}
    </div>
  )
}
