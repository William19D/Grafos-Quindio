"""R1 - Gráfica tiempo de la componente fuertemente conexa vs V+E, a partir de resultados/r1_scc_tiempos.csv."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from quindio.config import FIGURAS, RESULTADOS


def main():
    df = pd.read_csv(RESULTADOS / "r1_scc_tiempos.csv").sort_values("V_mas_E")
    x = df["V_mas_E"].to_numpy()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(x, df["tiempo_ms"], "o-", label="largest_component (Tarjan + copia del subgrafo)")
    ax.plot(x, df["tiempo_tarjan_ms"], "s--", label="solo strongly_connected_components (Tarjan)")
    # recta por el origen ajustada por mínimos cuadrados: t = c (V + E)
    c = (x @ df["tiempo_ms"].to_numpy()) / (x @ x)
    ax.plot(x, c * x, ":", color="gray", label=f"referencia lineal t = {c * 1000:.2f} µs·(V+E)")
    for _, f in df.iterrows():
        es_depto = f["red"] == "Departamento completo"
        ax.annotate("Quindío" if es_depto else f["red"].replace("Radio de ", "r="),
                    (f["V_mas_E"], f["tiempo_ms"]), textcoords="offset points",
                    xytext=(-50, 4) if es_depto else (5, -12), fontsize=8)
    ax.set_xlabel("V + E (nodos + aristas)")
    ax.set_ylabel("Tiempo (ms), mediana de 5")
    ax.set_title("Componente fuertemente conexa más grande")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    FIGURAS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURAS / "r1_scc.png", dpi=150)
    print("tiempo/(V+E) en µs:", np.round(df["tiempo_ms"].to_numpy() / x * 1000, 3))


if __name__ == "__main__":
    main()
