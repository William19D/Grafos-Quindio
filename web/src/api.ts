// Tipos de las respuestas de la API (api/main.py) y funciones para pedirlas.

export type Lugar = {
  id: string
  nombre: string
  categoria: 'cabecera' | 'atractivo' | 'finca' | 'acopio'
  municipio: string
  lat: number
  lon: number
  nodo: number
  dist_nodo_m: number
  duracion_visita_min: number | null
}

export type Punto = [number, number] // [lat, lon]

export type Ruta = {
  origen: { id: string; nombre: string }
  destino: { id: string; nombre: string }
  tiempo_s: number
  tiempo_min: number
  distancia_km: number
  nodos_explorados: number
  nodos_ruta: number
  nodos_grafo: number
  ms: number
  polilinea: Punto[]
}

// Árbol de exploración de Dijkstra: un tramo (predecesor -> nodo) por cada nodo explorado,
// en el orden en que salió de la cola, con su distancia definitiva en segundos.
export type Arbol = {
  origen: { id: string; nombre: string }
  destino: { id: string; nombre: string }
  tiempo_s: number
  nodos_explorados: number
  nodos_grafo: number
  tramos: Punto[][]
  tiempos_s: number[]
  ruta: Punto[]
}

export type Envolvente = {
  vertices: { lat: number; lon: number; x_utm: number; y_utm: number }[]
  n_vertices: number
  n_puntos: number
  area_km2: number
  ms: number
}

export type FilaDia = {
  orden: number | 'Regreso'
  lugar: string
  nombre: string
  desplazamiento_desde_anterior_min: number
  visita_min: number | null
  tiempo_acumulado_h: number
}

export type Recorrido = {
  orden: string[]
  filas: FilaDia[]
  tramos: { desde: string; hasta: string; tiempo_min: number; polilinea: Punto[] }[]
  total_desplazamientos_min: number
  total_visitas_min: number
  jornada_h: number
  limite_h: number
  cabe: boolean
  ms: number
}

export type Itinerario = {
  partida: string
  held_karp: Recorrido
  voraz: Recorrido
  diferencia_min: number
  diferencia_pct: number
}

export type Celda = string | number
export type Tabla = {
  archivo: string
  requerimiento: string
  titulo: string
  columnas: string[]
  filas: Celda[][]
}
export type Resultados = {
  tablas: Tabla[]
  figuras: { archivo: string; requerimiento: string; url: string; ancho: number; alto: number }[]
}

async function pedir<T>(url: string, opciones?: RequestInit): Promise<T> {
  const respuesta = await fetch(url, opciones)
  if (!respuesta.ok) {
    // FastAPI devuelve {detail: "texto"} o {detail: ["texto", ...]}
    const cuerpo = await respuesta.json().catch(() => null)
    const detalle = cuerpo?.detail
    const mensaje = Array.isArray(detalle) ? detalle.map((d) => (typeof d === 'string' ? d : d.msg)).join(' ') : detalle
    throw new Error(mensaje || `El servidor respondió ${respuesta.status}`)
  }
  return respuesta.json()
}

export const pedirLugares = () => pedir<Lugar[]>('/api/lugares')
export const pedirRuta = (origen: string, destino: string) =>
  pedir<Ruta>(`/api/ruta?origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
export const pedirArbol = (origen: string, destino: string) =>
  pedir<Arbol>(`/api/arbol?origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
export const pedirEnvolvente = () => pedir<Envolvente>('/api/envolvente')
export const pedirResultados = () => pedir<Resultados>('/api/resultados')
export const pedirItinerario = (partida: string, atractivos: string[]) =>
  pedir<Itinerario>('/api/itinerario', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ partida, atractivos }),
  })
