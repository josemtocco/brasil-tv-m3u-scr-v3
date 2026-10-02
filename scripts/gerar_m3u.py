#!/usr/bin/env python3
import csv, re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "output"

def rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def clean(v):
    return (v or "").strip()

def esc(v):
    return clean(v).replace('"', "'")

def stream_allowed(s):
    url = clean(s["url"]).lower()
    if not url.startswith(("http://", "https://")):
        return False
    forbidden = ("xtream", "get.php", "player_api", "username=", "password=", "token=")
    if any(x in url for x in forbidden):
        return False
    if clean(s["origem"]) not in {"official", "government", "university", "iptv_org", "official_external_cdn"}:
        return False
    if clean(s["status"]) not in {"active", "validated"}:
        return False
    return True

def main():
    OUT.mkdir(exist_ok=True)
    channels = {x["id"]: x for x in rows(DATA / "emissoras.csv") if clean(x.get("id"))}
    streams = [x for x in rows(DATA / "streams.csv") if stream_allowed(x)]

    entries = []
    for s in streams:
        c = channels.get(clean(s["emissora_id"]))
        if not c:
            continue
        name = clean(c["Emissora"])
        group = clean(c["Tipo"]).replace("_", " ").title()
        tvgid = clean(c["tvg-id"]) or clean(c["id"])
        logo = clean(c["Logo"])
        attrs = [
            f'tvg-name="{esc(name)}"',
            f'tvg-id="{esc(tvgid)}"',
            f'group-title="{esc(group)}"',
        ]
        if logo:
            attrs.append(f'tvg-logo="{esc(logo)}"')
        # IMPORTANT: name after comma is the channel name, never an EPG label.
        entries.append(f'#EXTINF:-1 {" ".join(attrs)},{name}\n{clean(s["url"])}')

    entries.sort(key=lambda x: x.lower())
    playlist = "#EXTM3U\n" + "\n".join(entries) + ("\n" if entries else "")
    (OUT / "brasil-tv.m3u").write_text(playlist, encoding="utf-8")

    for suffix, predicate in [
        ("universitarios", lambda c: c["Tipo"] == "universitaria"),
        ("legislativos", lambda c: "legisl" in c["Tipo"]),
        ("publicos", lambda c: c["Tipo"] in {"publica", "institucional", "governamental"}),
    ]:
        ids = {c["id"] for c in channels.values() if predicate(c)}
        body = [e for e in entries if any(f'tvg-id="{i}"' in e for i in ids)]
        (OUT / f"brasil-tv-{suffix}.m3u").write_text(
            "#EXTM3U\n" + "\n".join(body) + ("\n" if body else ""), encoding="utf-8"
        )
    print(f"Emissoras no catálogo: {len(channels)}")
    print(f"Streams aprovados: {len(entries)}")

if __name__ == "__main__":
    main()
