// Formato de números en español de Colombia: 1.234,5

const formatos = new Map<number, Intl.NumberFormat>()

export function numero(valor: number, decimales = 0): string {
  let formato = formatos.get(decimales)
  if (!formato) {
    formato = new Intl.NumberFormat('es-CO', { minimumFractionDigits: decimales, maximumFractionDigits: decimales })
    formatos.set(decimales, formato)
  }
  return formato.format(valor)
}

// 12,26 h -> "12 h 16 min"; 10 h -> "10 h" (no "10 h 0 min")
export function horasMinutos(horas: number): string {
  const totalMin = Math.round(horas * 60)
  const h = Math.floor(totalMin / 60)
  const min = totalMin % 60
  if (h === 0) return `${min} min`
  return min === 0 ? `${h} h` : `${h} h ${min} min`
}

// Quita tildes y pasa a minúsculas, para buscar "calarca" y encontrar "Calarcá"
export function normalizar(texto: string): string {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

export const NOMBRE_CATEGORIA: Record<string, string> = {
  cabecera: 'Cabecera municipal',
  atractivo: 'Atractivo turístico',
  finca: 'Finca cafetera u hotel rural',
  acopio: 'Centro de acopio de café',
}
