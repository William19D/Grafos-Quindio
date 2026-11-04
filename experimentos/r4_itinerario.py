"""R4 punto 4 - Itinerario de un día desde Armenia con 7 atractivos ordenados con Held-Karp.

Conjunto elegido: patrimonio cultural y miradores del eje Armenia - Calarcá - Circasia -
Filandia - Salento, todos a menos de 1 h de Armenia. No se incluyen los parques temáticos
de jornada completa (Parque del Café, PANACA: 6 h cada uno), que llenarían el día solos.
Las visitas suman 10 h, así que el día solo cabe si los desplazamientos son menores de 1 h:
el primer intento no cabe y hay que quitar atractivos (criterio en tsp.ajustar_a_jornada).

Salidas: resultados/r4_itinerario.csv (formato del anexo) y resultados/r4_itinerario.json
Uso: PYTHONPATH=src .venv/Scripts/python.exe experimentos/r4_itinerario.py
"""
import csv
import json

from quindio.config import RESULTADOS
from quindio.tsp import ajustar_a_jornada, itinerario, leer_catalogo, leer_matriz

PARTIDA = "ARM"
ATRACTIVOS = ["MOQ", "FUN", "JBQ", "CLC", "CIL", "CRS", "ACR"]
LIMITE_H = 11


def filas_csv(resultado):
    salida = []
    for f in resultado["filas"]:
        salida.append({
            "orden": f["orden"], "lugar": f["lugar"], "nombre": f["nombre"],
            "desplazamiento_desde_anterior_min": round(f["desplazamiento_desde_anterior_min"], 1),
            "visita_min": f["visita_min"], "tiempo_acumulado_h": round(f["tiempo_acumulado_h"], 2)})
    return salida


def resumen(resultado):
    return {"orden": resultado["orden"],
            "total_visitas_min": resultado["total_visitas_min"],
            "total_desplazamientos_min": round(resultado["total_desplazamientos_min"], 1),
            "jornada_h": round(resultado["jornada_h"], 2), "cabe_en_11_h": resultado["cabe"],
            "filas": filas_csv(resultado)}


def main():
    _ids, matriz = leer_matriz()
    catalogo = leer_catalogo()
    duraciones = {a: catalogo[a]["duracion_min"] for a in ATRACTIVOS}
    nombres = {lugar: datos["nombre"] for lugar, datos in catalogo.items()}

    primero = itinerario(PARTIDA, ATRACTIVOS, matriz, duraciones, LIMITE_H, nombres)
    traza = []
    final, quitados = ajustar_a_jornada(PARTIDA, ATRACTIVOS, matriz, duraciones, LIMITE_H, nombres, traza)
    print("\n".join(traza))

    filas = filas_csv(final)
    filas.append({"orden": "Total visitas (min)", "visita_min": final["total_visitas_min"]})
    filas.append({"orden": "Total desplazamientos (min)",
                  "desplazamiento_desde_anterior_min": round(final["total_desplazamientos_min"], 1)})
    filas.append({"orden": "Duración de la jornada (h)", "tiempo_acumulado_h": round(final["jornada_h"], 2)})
    columnas = ["orden", "lugar", "nombre", "desplazamiento_desde_anterior_min", "visita_min", "tiempo_acumulado_h"]
    with open(RESULTADOS / "r4_itinerario.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas, restval="")
        w.writeheader()
        w.writerows(filas)

    for q in quitados:
        for clave in ("jornada_antes_h", "jornada_despues_h", "ahorro_h", "ahorro_desplazamiento_min"):
            q[clave] = round(q[clave], 2)
    datos = {"partida": PARTIDA, "limite_h": LIMITE_H, "atractivos_iniciales": ATRACTIVOS,
             "criterio_para_quitar": "en cada ronda se quita el atractivo cuya eliminación más acorta la "
                                     "jornada (visita + desvío ahorrado), recalculando el óptimo con Held-Karp",
             "primer_intento": resumen(primero), "quitados": quitados, "final": resumen(final),
             "rondas": traza}
    (RESULTADOS / "r4_itinerario.json").write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Primer intento: {primero['jornada_h']:.2f} h; final: {final['jornada_h']:.2f} h "
          f"({final['total_visitas_min']} min de visitas + {final['total_desplazamientos_min']:.1f} min de viaje)")


if __name__ == "__main__":
    main()
