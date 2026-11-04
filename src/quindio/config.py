"""Rutas y constantes compartidas por todo el proyecto."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DATA = RAIZ / "data"
RAW = DATA / "raw"
PROCESADO = DATA / "processed"
RESULTADOS = RAIZ / "resultados"
FIGURAS = RESULTADOS / "figuras"

CATALOGO = DATA / "catalogo.csv"
GRAFO_RAW = RAW / "quindio_drive.graphml"
GRAFO_SCC = PROCESADO / "grafo_scc.graphml"
NODOS = PROCESADO / "nodos.csv"            # osmid,lat,lon,x_utm,y_utm
ARISTAS = PROCESADO / "aristas.csv"        # u,v,distancia_m,tiempo_s
LUGARES_NODOS = PROCESADO / "lugares_nodos.csv"
MATRIZ_TIEMPOS = RESULTADOS / "matriz_tiempos.csv"

LUGAR = "Quindío, Colombia"
PLAZA_BOLIVAR_ARMENIA = (4.532571193032303, -75.6728794763243)  # (lat, lon)
CRS_UTM = "EPSG:32618"  # WGS 84 / UTM zona 18N
SEMILLA = 2026
LIMITE_S = 300  # protocolo: 5 minutos
REPETICIONES = 5
