#!/usr/bin/env python3
import csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'; OUT=ROOT/'output'

def rows(path):
    if not path.exists(): return []
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def clean(v):return (v or '').strip()
def esc(v):return clean(v).replace('"',"'")
def allowed(s):
    u=clean(s.get('url')).lower(); o=clean(s.get('origem')); st=clean(s.get('status'))
    if not u.startswith(('http://','https://')): return False
    if any(x in u for x in ('xtream','get.php','player_api','username=','password=','token=')): return False
    return o in {'official','government','university','official_external_cdn'} and st in {'active','validated'}

def main():
    OUT.mkdir(exist_ok=True)
    channels={x['id']:x for x in rows(DATA/'emissoras.csv') if clean(x.get('id'))}
    allstreams=rows(DATA/'streams.csv'); streams=[s for s in allstreams if allowed(s)]
    entries=[]; rejected=0
    for s in streams:
        c=channels.get(clean(s.get('emissora_id')))
        if not c: rejected+=1; continue
        name=clean(c.get('Emissora')) or clean(s.get('emissora_id'))
        typ=clean(c.get('Tipo')) or 'tv'
        group=typ.replace('_',' ').title()
        tvgid=clean(c.get('tvg-id')) or clean(c.get('id'))
        attrs=[f'tvg-name="{esc(name)}"',f'tvg-id="{esc(tvgid)}"',f'group-title="{esc(group)}"']
        if clean(c.get('Logo')): attrs.append(f'tvg-logo="{esc(c["Logo"])}"')
        entries.append(f'#EXTINF:-1 {" ".join(attrs)},{name}\n{clean(s["url"])}')
    entries.sort(key=str.lower)
    body='#EXTM3U\n'+('\n'.join(entries)+'\n' if entries else '')
    (OUT/'brasil-tv.m3u').write_text(body,encoding='utf-8')
    predicates=[('universitarios',lambda c:c.get('Tipo')=='universitaria'),('legislativos',lambda c:'legisl' in c.get('Tipo','')),('publicos',lambda c:c.get('Tipo') in {'publica','institucional','governamental'})]
    for suf,pred in predicates:
        ids={c['id'] for c in channels.values() if pred(c)}
        es=[e for e in entries if any(f'tvg-id="{i}"' in e for i in ids)]
        (OUT/f'brasil-tv-{suf}.m3u').write_text('#EXTM3U\n'+('\n'.join(es)+'\n' if es else ''),encoding='utf-8')
    diag=OUT/'m3u-diagnostico.txt'
    diag.write_text(f'Emissoras no catálogo: {len(channels)}\nStreams no CSV: {len(allstreams)}\nStreams aprovados para M3U: {len(streams)}\nEntradas geradas: {len(entries)}\nStreams sem emissora correspondente: {rejected}\nArquivo principal: {OUT/"brasil-tv.m3u"}\n',encoding='utf-8')
    print(diag.read_text())
if __name__=='__main__':main()
