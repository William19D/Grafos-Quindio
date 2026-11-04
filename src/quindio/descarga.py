"""Descarga de la red vial con OSMnx, con servidores Overpass alternos si el principal está saturado."""
import time

import osmnx as ox

SERVIDORES = [
    "https://overpass-api.de/api",
    "https://overpass.private.coffee/api",
    "https://overpass.kumi.systems/api",
    "https://maps.mail.ru/osm/tools/overpass/api",
]


def con_reintentos(fn, *args, **kwargs):
    """Llama fn probando cada servidor Overpass; reintenta con espera creciente."""
    ox.settings.use_cache = True
    ox.settings.requests_timeout = 600
    espera = 10
    for intento in range(3):
        for url in SERVIDORES:
            ox.settings.overpass_url = url
            try:
                return fn(*args, **kwargs)
            except Exception as e:  # noqa: BLE001 - errores HTTP de Overpass
                print(f"[{url}] falló: {str(e)[:120]}")
        time.sleep(espera)
        espera *= 2
    raise RuntimeError("Ningún servidor Overpass respondió")
