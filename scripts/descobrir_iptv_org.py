#!/usr/bin/env python3
"""
Cruza o catálogo com a playlist pública do IPTV-org.
Não copia streams automaticamente para data/streams.csv.
A finalidade é marcar 'Presente no IPTV-org?' e gerar um relatório de candidatos
para revisão humana.
"""
import csv, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORT = ROOT / "output" / "iptv-org-candidatos.csv"
URL = "https://iptv-org.github.io/iptv/countries/br.m3u"

def norm(s):
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())

def main():
    req = urllib.request.Request(URL, headers={"User-Agent":"brasil-tv-m3u/1.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        text = r.read().decode("utf-8", "replace")

    names = []
    for line in text.splitlines():
        if line.startswith("#EXTINF:"):
            title = line.split(",", 1)[-1].strip()
            names.append(title)

    with open(DATA/"emissoras.csv", encoding="utf-8-sig", newline="") as f:
        channels = list(csv.DictReader(f))

    with open(REPORT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["emissora","cidade","estado","correspondencia_iptv_org"])
        for c in channels:
            key = norm(c["Emissora"])
            matches = [x for x in names if key and key in norm(x) or norm(x) in key]
            w.writerow([c["Emissora"], c["Cidade"], c["Estado"], "; ".join(matches[:10])])

    print(f"Relatório gerado: {REPORT}")

if __name__ == "__main__":
    main()
