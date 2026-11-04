// Selector de lugar con búsqueda (patrón "combobox" de WAI-ARIA).
// Se escribe para filtrar por nombre, municipio o código; flechas para moverse, Enter para elegir,
// Escape para cerrar.
import { useEffect, useId, useState } from 'react'
import type { Lugar } from '../api'
import { NOMBRE_CATEGORIA, normalizar } from '../formato'

type Props = {
  etiqueta: string
  lugares: Lugar[]
  valor: string // id del lugar elegido
  alCambiar: (id: string) => void
}

export function SelectorLugar({ etiqueta, lugares, valor, alCambiar }: Props) {
  const id = useId()
  const elegido = lugares.find((l) => l.id === valor)
  const [texto, setTexto] = useState<string | null>(null) // null = no se está escribiendo
  const [abierto, setAbierto] = useState(false)
  const [activo, setActivo] = useState(0)

  // Opciones filtradas (se calculan en cada render: son solo 46 lugares)
  // Cada palabra escrita debe aparecer, en cualquier orden: "bolivar arm" encuentra
  // "Plaza de Bolívar de Armenia" aunque falte el "de".
  const palabras = normalizar(texto ?? '').split(' ').filter(Boolean)
  const opciones = lugares.filter((l) => {
    const donde = normalizar(`${l.nombre} ${l.municipio} ${l.id}`)
    return palabras.every((p) => donde.includes(p))
  })

  // Con el teclado, la opción activa siempre a la vista dentro de la lista (que tiene su propio scroll)
  const idActiva = abierto && opciones[activo] ? `${id}-${opciones[activo].id}` : undefined
  useEffect(() => {
    if (idActiva) document.getElementById(idActiva)?.scrollIntoView({ block: 'nearest' })
  }, [idActiva])

  function elegir(lugar: Lugar) {
    alCambiar(lugar.id)
    setTexto(null)
    setAbierto(false)
  }

  function alPresionarTecla(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      // Si la lista estaba cerrada, la primera flecha solo la abre (sin saltarse la primera opción)
      if (!abierto) setAbierto(true)
      else setActivo((a) => Math.min(a + 1, opciones.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActivo((a) => Math.max(a - 1, 0))
    } else if (e.key === 'Enter' && abierto && opciones[activo]) {
      e.preventDefault()
      elegir(opciones[activo])
    } else if (e.key === 'Escape') {
      setTexto(null)
      setAbierto(false)
    }
  }

  return (
    <div className="relative">
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium">
        {etiqueta}
      </label>
      <input
        id={id}
        role="combobox"
        aria-expanded={abierto}
        aria-controls={`${id}-lista`}
        aria-autocomplete="list"
        aria-activedescendant={idActiva}
        autoComplete="off"
        spellCheck={false}
        value={texto ?? elegido?.nombre ?? ''}
        placeholder="Escribe un lugar o municipio…"
        onChange={(e) => {
          setTexto(e.target.value)
          setActivo(0)
          setAbierto(true)
        }}
        onFocus={(e) => e.target.select()}
        onClick={(e) => {
          // Si el campo ya tenía el foco (p. ej. justo después de elegir), al hacer clic también se
          // selecciona el nombre, para escribir encima y no en medio de él.
          if (texto === null) e.currentTarget.select()
          setAbierto(true)
        }}
        onBlur={() => {
          setTexto(null)
          setAbierto(false)
        }}
        onKeyDown={alPresionarTecla}
        className="h-10 w-full rounded-md border border-control bg-superficie px-3 placeholder:text-tinta-3"
      />
      {elegido && texto === null ? (
        <p className="mt-1 text-[13px] text-tinta-3">
          {elegido.municipio} · {NOMBRE_CATEGORIA[elegido.categoria]} · {elegido.id}
        </p>
      ) : null}
      {abierto ? (
        <ul
          id={`${id}-lista`}
          role="listbox"
          aria-label={etiqueta}
          className="absolute z-[1200] mt-1 max-h-72 w-full overflow-y-auto rounded-md border border-borde bg-superficie py-1 shadow-[0_8px_24px_rgba(22,32,26,0.14)]"
        >
          {opciones.length === 0 ? (
            <li className="px-3 py-2 text-sm text-tinta-3">Ningún lugar coincide con “{texto}”.</li>
          ) : (
            opciones.map((lugar, i) => (
              <li
                key={lugar.id}
                id={`${id}-${lugar.id}`}
                role="option"
                aria-selected={lugar.id === valor}
                // mousedown en vez de click: así se elige antes de que el campo pierda el foco
                onMouseDown={(e) => {
                  e.preventDefault()
                  elegir(lugar)
                }}
                onMouseEnter={() => setActivo(i)}
                className={`flex cursor-pointer items-baseline justify-between gap-3 px-3 py-2 ${i === activo ? 'bg-activo' : ''}`}
              >
                <span className={lugar.id === valor ? 'font-semibold' : ''}>{lugar.nombre}</span>
                <span className="shrink-0 text-[13px] text-tinta-3">{lugar.municipio}</span>
              </li>
            ))
          )}
        </ul>
      ) : null}
    </div>
  )
}
