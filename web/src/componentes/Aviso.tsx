import type { ReactNode } from 'react'

// Mensaje dentro del bloque que falló o que necesita atención (no un aviso de pantalla completa).
const ESTILOS = {
  error: 'border-negativo/30 bg-negativo-palido text-negativo',
  nota: 'border-borde bg-hundido text-tinta-2',
}

export function Aviso({ tipo, children }: { tipo: keyof typeof ESTILOS; children: ReactNode }) {
  return (
    <p role={tipo === 'error' ? 'alert' : undefined} className={`rounded-md border px-3 py-2 text-sm ${ESTILOS[tipo]}`}>
      {children}
    </p>
  )
}
