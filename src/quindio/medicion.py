"""Utilidades del protocolo experimental (sección 6 del enunciado)."""
import json
import multiprocessing as mp
import os
import platform
import statistics
import sys
import time

from .config import LIMITE_S, REPETICIONES, RESULTADOS


def medir(fn, *args, reps=REPETICIONES):
    """Ejecuta fn(*args) `reps` veces y devuelve (mediana_ms, resultado).
    Si la primera ejecución supera un minuto, solo se mide una vez (protocolo 6.3)."""
    tiempos, res = [], None
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        res = fn(*args)
        tiempos.append((time.perf_counter_ns() - t0) / 1e6)
        if tiempos[0] > 60_000:
            break
    return statistics.median(tiempos), res


def _trabajador(cola, fn, args, reps):
    cola.put(medir(fn, *args, reps=reps))


def medir_con_limite(fn, *args, reps=REPETICIONES, limite_s=LIMITE_S):
    """Como `medir`, pero en un proceso aparte que se detiene a los `limite_s` segundos.
    Devuelve (mediana_ms, resultado) o (None, None) si no se completó. fn debe ser de nivel de módulo."""
    cola = mp.get_context("spawn").Queue()
    p = mp.get_context("spawn").Process(target=_trabajador, args=(cola, fn, args, reps))
    p.start()
    p.join(limite_s)
    if p.is_alive():
        p.terminate()
        p.join()
        return None, None
    return cola.get()


def info_maquina():
    """Procesador, RAM, SO y versión del lenguaje (protocolo 6.1)."""
    import psutil
    cpu = platform.processor()
    if sys.platform == "win32":
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu = winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        except OSError:
            pass
    return {
        "procesador": cpu,
        "nucleos_logicos": os.cpu_count(),
        "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
        "sistema_operativo": platform.platform(),
        "python": platform.python_version(),
    }


def guardar_maquina():
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    (RESULTADOS / "maquina.json").write_text(json.dumps(info_maquina(), indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    guardar_maquina()
    print(info_maquina())
