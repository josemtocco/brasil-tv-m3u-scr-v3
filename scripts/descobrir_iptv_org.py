#!/usr/bin/env python3
"""Descobre candidatos de stream no IPTV-org sem publicar tudo automaticamente."""
import csv, re, urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"
URL = "https://iptv-org.github.io/iptv/countries/br.m3u"


def norm(s):
    s = (s or "").lower()
    return re.sub(r"[^a-z0-9]+", "", s.encode("ascii", "ignore").decode())


def parse_m3u(text):
    cur = None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#EXTINF:"):
            attrs = dict(re.findall(r'(\w+(?:-\w+)*)="([^"]*)"', line))
            title = line.split(",", 1)[-1].strip()
            cur = (attrs, title)
        elif cur and line and not line.startswith("#"):
            attrs, title = cur
            yield attrs, title, line
            cur = None


def score(channel, attrs, title):
    a = norm(channel.get("Emissora"))
    b = norm(title)
    if not a or not b:
        return 0
    if a == b:
        return 100
    if a in b or b in a:
        return 88
    # remove generic TV/TVU markers for university/public names
    aa = re.sub(r"^(tv|tv\s*)", "", channel.get("Emissora", "",).strip(), flags=re.I)
    bb = re.sub(r"^(tv|tv\s*)", "", title.strip(), flags=re.I)
    aa, bb = norm(aa), norm(bb)
    if aa and bb and (aa == bb or aa in bb or bb in aa):
        return 82
    return 0


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "brasil-tv-m3u/2.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        text = r.read().decode("utf-8", "replace")

    channels = list(csv.DictReader(open(DATA / "emissoras.csv", encoding="utf-8-sig", newline="")))
    candidates = []
    for c in channels:
        best = []
        for attrs, title, url in parse_m3u(text):
            sc = score(c, attrs, title)
            if sc >= 82:
                best.append((sc, title, url, attrs.get("tvg-id", ""), urlparse(url).netloc.lower()))
        best.sort(key=lambda x: (-x[0], x[1], x[2]))
        for sc, title, url, tvgid, host in best[:10]:
            candidates.append([c["id"], c["Emissora"], c["Estado"], c["Cidade"], c["Tipo"], str(sc), title, tvgid, host, url])

    OUT.mkdir(exist_ok=True)
    path = OUT / "iptv-org-candidatos.csv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["emissora_id","emissora","estado","cidade","tipo","score","nome_iptv_org","tvg_id","host","url"])
        w.writerows(candidates)
    print(f"IPTV-org: {len(candidates)} candidatos gravados em {path}")


if __name__ == "__main__":
    main()
