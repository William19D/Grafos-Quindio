import type { ReactNode } from 'react'

// Disposición de las vistas de mapa: panel de trabajo a la izquierda (arriba en el teléfono)
// y el mapa ocupando el resto de la pantalla.
export function ConMapa({ panel, children }: { panel: ReactNode; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)] lg:h-[calc(100dvh-57px)] lg:grid-cols-[400px_minmax(0,1fr)]">
      <section className="space-y-6 border-borde bg-superficie p-4 lg:overflow-y-auto lg:border-r lg:p-6">{panel}</section>
      <div className="h-[60dvh] lg:h-full">{children}</div>
    </div>
  )
}
