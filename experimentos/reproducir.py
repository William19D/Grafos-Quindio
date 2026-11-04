"""Reproduce todos los experimentos del proyecto, en orden, con subprocess.

Uso (desde la raíz del repositorio):
    python experimentos/reproducir.py            # todo (descarga la red si falta; tarda > 20 min)
    python experimentos/reproducir.py --rapido   # omite los pasos lentos o que usan internet
    python experimentos/reproducir.py --listar   # solo muestra los pasos, no ejecuta nada

Cada script se ejecuta con el mismo intérprete de Python y con PYTHONPATH=src.
Si un paso falla, se detiene y muestra cuál fue.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

# (script, descripción, lento): "lento" = tarda varios minutos o necesita internet.
# En --rapido se omiten; los datos procesados que generan ya están en data/processed y resultados/.
PASOS = [
    ("experimentos/catalogo.py", "Catálogo: verificación geográfica y mapa (usa internet)", True),
    ("experimentos/r1_red.py", "R1: pesos, componente fuertemente conexa y grafo procesado (usa data/raw)", True),
    ("experimentos/r1_scc.py", "R1: tiempo de la componente en redes de 2, 5, 10 y 20 km (descarga redes)", True),
    ("experimentos/r1_figuras.py", "R1: gráfica tiempo de la componente vs V+E", False),
    ("experimentos/r1_geometrias.py", "R1: forma real de cada tramo para dibujar rutas en el mapa", False),
    ("experimentos/r1_lugares.py", "R1: asociar cada lugar a su nodo más cercano", False),
    ("experimentos/r2_dijkstra.py", "R2: medición de Dijkstra lineal y con cola (25 pares)", False),
    ("experimentos/r2_matriz.py", "R2: matriz de tiempos 46 x 46", False),
    ("experimentos/r2_figuras.py", "R2: gráfica tiempo vs nodos explorados", False),
    ("experimentos/r3_envolvente.py", "R3: QuickHull propio vs SciPy y envolvente.json", False),
    ("experimentos/r3_figuras.py", "R3: figuras de la envolvente y de los tiempos", False),
    ("experimentos/r4_exactos.py", "R4: fuerza bruta y Held-Karp, k = 5..12 (~10 min o más)", True),
    ("experimentos/r4_calidad.py", "R4: calidad de la heurística voraz", False),
    ("experimentos/r4_itinerario.py", "R4: itinerario de un día desde Armenia", False),
    ("experimentos/r4_figuras.py", "R4: gráfica tiempo vs k", False),
]


def descargar_red_si_falta():
    """Descarga la red del Quindío solo si no está en data/raw (r1_red.py la necesita)."""
    sys.path.insert(0, str(RAIZ / "src"))
    from quindio.config import GRAFO_RAW, LUGAR, RAW

    if GRAFO_RAW.exists():
        print(f"Red cruda ya existe: {GRAFO_RAW}")
        return
    import json
    from datetime import date

    import osmnx as ox
    from quindio.descarga import con_reintentos

    print("Descargando la red vial (puede tardar unos minutos)...")
    RAW.mkdir(parents=True, exist_ok=True)
    inicio = time.perf_counter()
    G = con_reintentos(ox.graph_from_place, LUGAR, network_type="drive")
    ox.save_graphml(G, GRAFO_RAW)
    metadatos = {
        "fecha_descarga": date.today().isoformat(),
        "osmnx": ox.__version__,
        "servidor": ox.settings.overpass_url,
        "V": G.number_of_nodes(),
        "E": G.number_of_edges(),
        "seg": round(time.perf_counter() - inicio, 1),
    }
    (RAW / "descarga.json").write_text(json.dumps(metadatos, indent=1), encoding="utf-8")
    print(f"Red guardada: V = {metadatos['V']}, E = {metadatos['E']}")


def main():
    parser = argparse.ArgumentParser(description="Reproduce los experimentos en orden.")
    parser.add_argument("--rapido", action="store_true", help="omite los pasos lentos o que usan internet")
    parser.add_argument("--listar", action="store_true", help="solo lista los pasos")
    args = parser.parse_args()

    pasos = [p for p in PASOS if not (args.rapido and p[2])]
    omitidos = [p for p in PASOS if args.rapido and p[2]]

    if args.listar:
        if not args.rapido:
            print(" 0. (descarga de la red si falta en data/raw)")
        for i, (script, descripcion, lento) in enumerate(pasos, start=1):
            marca = " [lento]" if lento else ""
            print(f"{i:2d}. {script}  -  {descripcion}{marca}")
        for script, _, _ in omitidos:
            print(f"    omitido por --rapido: {script}")
        return

    if not args.rapido:
        descargar_red_si_falta()

    entorno = dict(os.environ, PYTHONPATH=str(RAIZ / "src"), PYTHONIOENCODING="utf-8")
    for i, (script, descripcion, _) in enumerate(pasos, start=1):
        print(f"\n=== Paso {i}/{len(pasos)}: {script} - {descripcion}", flush=True)
        inicio = time.perf_counter()
        resultado = subprocess.run([sys.executable, script], cwd=RAIZ, env=entorno)
        segundos = time.perf_counter() - inicio
        if resultado.returncode != 0:
            print(f"*** Falló {script} (código {resultado.returncode}) tras {segundos:.1f} s")
            sys.exit(resultado.returncode)
        print(f"--- {script} terminó en {segundos:.1f} s")
    print("\nListo: resultados en resultados/ y figuras en resultados/figuras/.")


if __name__ == "__main__":
    main()
