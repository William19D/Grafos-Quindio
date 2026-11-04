"""R2 - Figura tiempo vs nodos explorados, generada a partir de resultados/r2_dijkstra.csv."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from quindio.config import FIGURAS, RESULTADOS

ESTILO = {  # versión -> (etiqueta, color, marcador)
    "cola_prioridad": ("Cola de prioridad, O((V+E) log V)", "#2a78d6", "o"),
    "lineal": ("Recorrido lineal, O(V²)", "#eb6834", "s"),
}


def main():
    tabla = pd.read_csv(RESULTADOS / "r2_dijkstra.csv")
    tabla = tabla[tabla["completada"]]
    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5.5), facecolor="#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    for version, (etiqueta, color, marcador) in ESTILO.items():
        datos = tabla[tabla["version"] == version]
        ax.scatter(datos["nodos_explorados"], datos["tiempo_ms"], s=55, c=color, marker=marcador,
                   edgecolors="#fcfcfb", linewidths=1.5, label=f"{etiqueta} ({len(datos)} consultas)", zorder=3)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Nodos explorados (escala logarítmica)", color="#52514e")
    ax.set_ylabel("Tiempo de la consulta, mediana de 5 (ms, escala logarítmica)", color="#52514e")
    ax.set_title("Dijkstra: tiempo frente a nodos explorados", color="#0b0b0b", loc="left")
    ax.grid(True, which="major", color="#e4e3df", linewidth=0.8, zorder=0)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(colors="#52514e")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    salida = FIGURAS / "r2_tiempo_vs_nodos.png"
    fig.savefig(salida, dpi=150)
    print(f"Figura guardada en {salida}")


if __name__ == "__main__":
    main()
