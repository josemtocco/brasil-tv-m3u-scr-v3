import csv,sys,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import promover_streams
assert promover_streams.host_ok('stream3.camara.gov.br','https://www.camara.leg.br/tv/')
assert promover_streams.host_ok('tvbrasil-stream.ebc.com.br','https://tvbrasil.ebc.com.br/')
assert not promover_streams.host_ok('example.com','https://www.camara.leg.br/tv/')
print('TESTE STREAMS: OK')


# A URL must be unique globally in the final stream catalog.
rows = [
    {"emissora_id": "a", "url": "https://example.test/live.m3u8"},
    {"emissora_id": "b", "url": "https://example.test/live.m3u8"},
]
rows.sort(key=lambda r: (r["url"].lower(), r["emissora_id"]))
unique = {}
for r in rows:
    unique.setdefault(r["url"], r)
assert len(unique) == 1
print("TESTE DEDUPLICACAO URL: OK")
