#!/usr/bin/env python3
import csv, sys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def read(name):
    with open(DATA/name, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

channels = read("emissoras.csv")
streams = read("streams.csv")
errors = []

ids = {}
for n, c in enumerate(channels, 2):
    cid = (c.get("id") or "").strip()
    if not cid:
        errors.append(f"emissoras.csv:{n}: id vazio")
    elif cid in ids:
        errors.append(f"emissoras.csv:{n}: id duplicado: {cid}")
    else:
        ids[cid] = n
    for required in ("Emissora","Tipo","Status"):
        if not (c.get(required) or "").strip():
            errors.append(f"emissoras.csv:{n}: campo obrigatório vazio: {required}")
    if not (c.get("Estado") or "").strip():
        errors.append(f"emissoras.csv:{n}: Estado vazio")
    if not (c.get("Cidade") or "").strip():
        errors.append(f"emissoras.csv:{n}: Cidade vazia")

seen_urls = set()
for n, s in enumerate(streams, 2):
    sid = (s.get("emissora_id") or "").strip()
    url = (s.get("url") or "").strip()
    if sid not in ids:
        errors.append(f"streams.csv:{n}: emissora_id inexistente: {sid}")
    if not re.match(r"^https?://", url):
        errors.append(f"streams.csv:{n}: URL inválida: {url}")
    if url in seen_urls:
        errors.append(f"streams.csv:{n}: URL duplicada")
    seen_urls.add(url)
    low = url.lower()
    forbidden = ("xtream", "get.php", "player_api", "username=", "password=", "token=")
    if any(x in low for x in forbidden):
        errors.append(f"streams.csv:{n}: URL potencialmente privada/tokenizada")

if errors:
    print("\n".join(errors))
    sys.exit(1)

print(f"OK: {len(channels)} emissoras e {len(streams)} registros de stream.")
