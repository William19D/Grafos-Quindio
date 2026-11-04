"""R3 - Figuras a partir de los resultados guardados:
- resultados/figuras/r3_envolvente.png: nodos de la red + polígono (nodos.csv + envolvente.json)
- resultados/figuras/r3_tiempos.png: tiempo propio vs SciPy por conjunto (r3_envolvente.csv)
"""
import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from quindio.config import FIGURAS, NODOS, RESULTADOS


def figura_envolvente():
    nodos = pd.read_csv(NODOS)
    env = json.loads((RESULTADOS / "envolvente.json").read_text(encoding="utf-8"))
    xs = [v["x_utm"] / 1000 for v in env["vertices"]]
    ys = [v["y_utm"] / 1000 for v in env["vertices"]]
    fig, ax = plt.subplots(figsize=(7, 8))
    ax.scatter(nodos["x_utm"] / 1000, nodos["y_utm"] / 1000, s=1, color="gray", alpha=0.5,
               label=f"Nodos de la red ({env['n_puntos']})")
    ax.fill(xs, ys, facecolor="tab:green", alpha=0.08)
    ax.plot(xs + xs[:1], ys + ys[:1], "-o", color="tab:green", markersize=4,
            label=f"Envolvente convexa ({env['n_vertices']} vértices, {env['area_km2']} km²)")
    ax.set_xlabel("Este UTM 18N (km)")
    ax.set_ylabel("Norte UTM 18N (km)")
    ax.set_title("Envolvente convexa de la red vial del Quindío (QuickHull)")
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIGURAS / "r3_envolvente.png", dpi=150)
    plt.close(fig)


def figura_tiempos():
    df = pd.read_csv(RESULTADOS / "r3_envolvente.csv")
    posiciones = range(len(df))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar([p - 0.2 for p in posiciones], df["tiempo_propio_ms"], width=0.4, label="QuickHull propio (Python)")
    ax.bar([p + 0.2 for p in posiciones], df["tiempo_scipy_ms"], width=0.4, label="SciPy ConvexHull (Qhull, C)")
    for p, (_, f) in zip(posiciones, df.iterrows()):
        ax.annotate(f"x{f['cociente']}", (p, f["tiempo_propio_ms"]), textcoords="offset points",
                    xytext=(-12, 3), fontsize=8)
    ax.set_xticks(list(posiciones))
    ax.set_xticklabels([f"{c}\n(n={n})" for c, n in zip(df["conjunto"], df["n"])], fontsize=8)
    ax.set_yscale("log")
    ax.set_ylabel("Tiempo (ms), mediana de 5, escala log")
    ax.set_title("Envolvente convexa: implementación propia vs SciPy")
    ax.grid(alpha=0.3, axis="y")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURAS / "r3_tiempos.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    FIGURAS.mkdir(parents=True, exist_ok=True)
    figura_envolvente()
    figura_tiempos()
