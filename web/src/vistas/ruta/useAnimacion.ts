// Reproduce un contador de 0 a `total` en `segundos` (como un video): play/pausa, reinicio y salto.
// El avance depende del reloj y no de cuántos cuadros se dibujen: si el navegador va lento,
// se salta pasos pero la animación dura lo mismo.
import { useEffect, useRef, useState } from 'react'

export function useAnimacion(total: number, segundos: number) {
  const [paso, setPaso] = useState(0)
  const [reproduciendo, setReproduciendo] = useState(false)
  const pasoActual = useRef(0) // el último paso, para retomar desde ahí al reanudar
  useEffect(() => {
    pasoActual.current = paso
  }, [paso])

  useEffect(() => {
    if (!reproduciendo || total === 0) return
    const pasoInicial = pasoActual.current >= total ? 0 : pasoActual.current
    const pasosPorMs = total / (segundos * 1000)
    const inicio = performance.now()
    const control = { cuadro: 0 }
    const avanzar = (ahora: number) => {
      const siguiente = Math.min(total, Math.round(pasoInicial + (ahora - inicio) * pasosPorMs))
      setPaso(siguiente)
      if (siguiente >= total) {
        setReproduciendo(false)
        return
      }
      control.cuadro = requestAnimationFrame(avanzar)
    }
    control.cuadro = requestAnimationFrame(avanzar)
    return () => cancelAnimationFrame(control.cuadro)
  }, [reproduciendo, total, segundos])

  const alternar = () => setReproduciendo(!reproduciendo)
  const reiniciar = () => {
    setReproduciendo(false)
    setPaso(0)
  }
  const saltarA = (nuevo: number) => {
    setReproduciendo(false)
    setPaso(nuevo)
  }
  return { paso, reproduciendo, alternar, reiniciar, saltarA, setPaso, setReproduciendo }
}
