// Los mismos colores de index.css (@theme), para Leaflet y Recharts, que los escriben como
// atributos SVG (allí var(--color-...) no siempre funciona).
export const COLOR = {
  tinta: '#16201a',
  tinta3: '#5a655c',
  primario: '#1c3a29',
  cereza: '#a63220', // algoritmo propio / óptimo (Dijkstra, QuickHull, Held-Karp)
  azul: '#2b5c7a', // comparador (versión lineal, SciPy, la voraz)
  guadua: '#3c7334',
  tostado: '#7a4b1e',
  regla: '#e5e9df',
  borde: '#d3d9cb',
  negativo: '#96201a',
}

// Color y tamaño de cada categoría del catálogo en el mapa
export const ESTILO_CATEGORIA: Record<string, { color: string; radio: number }> = {
  cabecera: { color: COLOR.tinta, radio: 7 },
  atractivo: { color: COLOR.cereza, radio: 6 },
  finca: { color: COLOR.guadua, radio: 6 },
  acopio: { color: COLOR.tostado, radio: 6 },
}
