"""R4 - Figura tiempo vs k, generada a partir de resultados/r4_exactos.csv
(y r4_held_karp_extendido.csv para los puntos de Held-Karp con k = 13..16)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from quindio.config import FIGURAS, LIMITE_S, RESULTADOS


def main():
    tabla = pd.read_csv(RESULTADOS / "r4_exactos.csv")
    extra = pd.read_csv(RESULTADOS / "r4_held_karp_extendido.csv")
    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5.5), facecolor="#fcfcfb")
    ax.set_facecolor("#fcfcfb")

    fb = tabla[tabla["estado_fuerza_bruta"].str.startswith("completada")]
    hk = tabla[tabla["estado_held_karp"].str.startswith("completada")]
    ax.plot(fb["k"], fb["tiempo_fuerza_bruta_ms"], "-s", color="#eb6834", label="Fuerza bruta, O(k·k!)")
    ax.plot(hk["k"], hk["tiempo_held_karp_ms"], "-o", color="#2a78d6", label="Held-Karp, O(k²·2^k)")
    ax.plot(extra["k"], extra["tiempo_held_karp_ms"], "--o", color="#2a78d6", mfc="#fcfcfb",
            label="Held-Karp, k > 12 (extra)")
    no_completada = tabla[tabla["estado_fuerza_bruta"] == "no completada"]
    for k in no_completada["k"]:
        ax.plot(k, LIMITE_S * 1000, "x", color="#eb6834", ms=10, mew=2)
        ax.annotate("fuerza bruta:\nno completada (> 5 min)", (k, LIMITE_S * 1000), textcoords="offset points",
                    xytext=(12, -12), ha="left", color="#eb6834", fontsize=9)
    ax.axhline(LIMITE_S * 1000, color="#a3a29d", lw=0.8, ls=":")
    ax.text(14.5, LIMITE_S * 1000 * 1.3, "límite de 5 min", color="#7a7974", fontsize=9)

    ax.set_yscale("log")
    ax.set_xticks(list(range(5, int(extra["k"].max()) + 1)))
    ax.set_xlabel("k (lugares a visitar además de Armenia)", color="#52514e")
    ax.set_ylabel("Tiempo, mediana de 5 (ms, escala logarítmica)", color="#52514e")
    ax.set_title("TSP exacto: tiempo frente a k", color="#0b0b0b", loc="left")
    ax.grid(True, which="major", color="#e4e3df", linewidth=0.8, zorder=0)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    ax.tick_params(colors="#52514e")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    salida = FIGURAS / "r4_tiempo_vs_k.png"
    fig.savefig(salida, dpi=150)
    print(f"Figura guardada en {salida}")


if __name__ == "__main__":
    main()
