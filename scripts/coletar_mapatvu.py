#!/usr/bin/env python3
"""Atualiza TVs universitárias a partir do Mapa TVU 4.0.

A fonte informa identidade, cidade/UF, site, meios de transmissão e presença digital.
Nenhuma URL de stream é promovida automaticamente.
"""
import csv, re, time
from pathlib import Path
from urllib.request import Request, urlopen
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
CSV=ROOT/'data/emissoras.csv'
BASE='https://www.mapatvu.org.br'
INDEX=BASE+'/index.php/mapa/mapa-detalhado'

class LinkParser(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self, tag, attrs):
        if tag=='a':
            d=dict(attrs); href=d.get('href',''); text=''
            self.links.append([href,text])
    def handle_data(self,data):
        if self.links: self.links[-1][1]+=data

def get(url):
    req=Request(url,headers={'User-Agent':'brasil-tv-m3u/1.0'})
    with urlopen(req,timeout=30) as r: return r.read().decode('utf-8','replace')

def txt(html):
    s=re.sub(r'<script.*?</script>|<style.*?</style>',' ',html,flags=re.S|re.I)
    s=re.sub(r'<[^>]+>',' ',s)
    return re.sub(r'\s+',' ',s).strip()

def value(text,label):
    m=re.search(re.escape(label)+r'\s*[:|]\s*([^|]+?)(?=\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][^|]{0,35}:|$)',text,re.I)
    return m.group(1).strip() if m else ''

def slug(name):
    x=re.sub(r'[^A-Za-z0-9]+','',name).strip()
    return (x or 'TV')+'.br'

html=get(INDEX)
p=LinkParser(); p.feed(html)
urls=[]
for href,name in p.links:
    if 'mapa-detalhado?id=' in href and 'layout=edit' in href:
        if href.startswith('/'): href=BASE+href
        elif href.startswith('http') is False: href=BASE+'/'+href
        if href not in urls: urls.append(href)

rows=[]
for i,url in enumerate(urls,1):
    try:
        h=get(url); t=txt(h)
        m=re.search(r'Cidade/Estado\s*:\s*([^|]+?)\s*[/|]\s*([A-Z]{2})',t,re.I)
        city=m.group(1).strip() if m else ''
        uf=m.group(2).upper() if m else ''
        # title is usually the first heading after the menu; use known label pattern.
        nm=re.search(r'<h1[^>]*>\s*([^<]+)\s*</h1>',h,re.I)
        name=nm.group(1).strip() if nm else ''
        site=''
        sm=re.search(r'Site:\s*\|\s*(?:<[^>]+>)*([^<\s]+)',h,re.I)
        if sm: site=sm.group(1).strip()
        ym=re.search(r'YouTube:\s*\|\s*(?:<[^>]+>)*([^<\s]+)',h,re.I)
        youtube=ym.group(1).strip() if ym else ''
        if name and city and uf:
            rows.append({'id':slug(name),'Emissora':name,'Estado':uf,'Cidade':city,'Tipo':'universitaria','Site oficial':site,'Página ao vivo':'','YouTube oficial':youtube,'tvg-id':'','Logo':'','EPG':'','Presente no IPTV-org':'','Status':'confirmada','Observação':'Mapa TVU 4.0'})
    except Exception as e:
        print('falha',url,e)
    time.sleep(0.05)

# Merge with existing catalog; existing manually curated rows remain when richer.
fields=['id','Emissora','Estado','Cidade','Tipo','Site oficial','Página ao vivo','YouTube oficial','tvg-id','Logo','EPG','Presente no IPTV-org','Status','Observação']
existing=[]
if CSV.exists():
    with open(CSV,encoding='utf-8-sig',newline='') as f: existing=list(csv.DictReader(f))
by_name={(r['Emissora'].strip().lower(),r['Cidade'].strip().lower(),r['Estado'].strip().upper()):r for r in existing}
for r in rows:
    k=(r['Emissora'].lower(),r['Cidade'].lower(),r['Estado'])
    if k not in by_name: by_name[k]=r
    else:
        old=by_name[k]
        for k2 in fields:
            if not old.get(k2) and r.get(k2): old[k2]=r[k2]
with open(CSV,'w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(sorted(by_name.values(),key=lambda r:(r['Estado'],r['Cidade'],r['Emissora'])))
print(f'Mapa TVU: {len(rows)} páginas coletadas; catálogo final: {len(by_name)} emissoras')
