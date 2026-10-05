#!/usr/bin/env python3
"""
Importa o Conjunto de Dados de Radiodifusão (SCR) do MCom e cruza com
data/emissoras.csv.

Princípios:
- fonte oficial do MCom;
- somente serviços de televisão: TV, GTVD, PBTVD, RTV e RTVD;
- uma retransmissora/estação não vira automaticamente uma nova emissora;
- preserva registros já existentes e seus streams;
- identifica novos registros por nome + UF + município;
- nunca substitui o catálogo por um download vazio/inválido;
- falha de rede não apaga o cadastro atual.
"""
from __future__ import annotations
import csv, io, re, sys, unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
URL = __import__("os").environ.get("SCR_URL", "https://s3.mcom.gov.br/radcom/SCR_DADOS_RADIODIFUSAO_TV_GTVD_RTV_RTVD_FM_OM.csv")
TARGET_SERVICES = {"TV", "GTVD", "PBTVD", "RTV", "RTVD"}

FIELDS = [
    "id","Emissora","Estado","Cidade","Tipo","Site oficial","Página ao vivo",
    "YouTube oficial","tvg-id","Logo","EPG","Presente no IPTV-org","Status",
    "Observação","scr_servico","scr_tipo_registro","scr_canal","scr_situacao",
    "scr_ultima_atualizacao"
]

UF_NAMES = {
    "AC":"Acre","AL":"Alagoas","AP":"Amapá","AM":"Amazonas","BA":"Bahia",
    "CE":"Ceará","DF":"Distrito Federal","ES":"Espírito Santo","GO":"Goiás",
    "MA":"Maranhão","MT":"Mato Grosso","MS":"Mato Grosso do Sul","MG":"Minas Gerais",
    "PA":"Pará","PB":"Paraíba","PR":"Paraná","PE":"Pernambuco","PI":"Piauí",
    "RJ":"Rio de Janeiro","RN":"Rio Grande do Norte","RS":"Rio Grande do Sul",
    "RO":"Rondônia","RR":"Roraima","SC":"Santa Catarina","SP":"São Paulo",
    "SE":"Sergipe","TO":"Tocantins"
}
UF_BY_NAME = {v.upper(): k for k,v in UF_NAMES.items()}

def norm(s):
    s = str(s or "").strip()
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    return re.sub(r"\s+", " ", s).strip().upper()

def slug(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii","ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "nao-informado"

def pick(row, *names):
    normalized = {norm(k): v for k,v in row.items()}
    for n in names:
        v = normalized.get(norm(n))
        if v is not None and str(v).strip():
            return str(v).strip()
    # flexible contains matching for renamed SCR columns
    for k,v in normalized.items():
        if not str(v).strip():
            continue
        for n in names:
            nn = norm(n)
            if nn and (nn in k or k in nn):
                return str(v).strip()
    return ""

def service(row):
    """
    O SCR já mudou a nomenclatura de algumas colunas ao longo do tempo.
    Primeiro procura campos explicitamente ligados ao serviço; depois tenta
    valores que sejam exatamente siglas conhecidas. Nunca considera uma
    ocorrência de 'TV' dentro do nome da entidade como serviço.
    """
    preferred = (
        "SERVICO", "SERVIÇO", "TIPO SERVICO", "TIPO DE SERVICO",
        "TIPO DE SERVIÇO", "SERVICO DE RADIODIFUSAO",
        "SERVIÇO DE RADIODIFUSÃO", "SIGLA SERVICO", "SIGLA SERVIÇO",
        "CODIGO SERVICO", "CÓDIGO SERVIÇO", "MODALIDADE",
        "TIPO SERVIÇO", "SERVICO_RADIO", "SERVICO_RADIODIFUSAO"
    )
    vals = []
    for name in preferred:
        v = pick(row, name)
        if v:
            vals.append(norm(v))
    # Campos cujo nome contém serviço/modalidade/tipo, inclusive versões novas.
    for k, v in row.items():
        nk = norm(k)
        if any(token in nk for token in ("SERVICO", "SERVIÇO", "MODALIDADE")):
            if str(v).strip():
                vals.append(norm(v))
    aliases = {
        "TV":"TV", "TELEVISAO":"TV", "TELEVISÃO":"TV",
        "GTVD":"GTVD", "PBTVD":"PBTVD",
        "RTV":"RTV", "RTVD":"RTVD",
        "RETRANSMISSAO DE TV":"RTV",
        "RETRANSMISSORA DE TV":"RTV",
        "RETRANSMISSORA":"RTV",
    }
    for v in vals:
        if v in aliases:
            return aliases[v]
        # aceita código com texto, ex. "RTV - Retransmissão..."
        for a in ("GTVD","PBTVD","RTVD","RTV","TV"):
            if re.search(r"(^|[^A-Z0-9])"+re.escape(a)+r"([^A-Z0-9]|$)", v):
                return a

    # Fallback conservador. O nome do arquivo é especificamente a base
    # conjunta de radiodifusão; por isso só classificamos como TV quando
    # há evidência de canal/serviço de televisão.
    channel_value = norm(pick(row, "CANAL", "CANAL FISICO", "CANAL FÍSICO",
                               "CANAL DIGITAL", "CANAL TV", "CANAL DE TV"))
    tipo = norm(pick(row, "TIPO", "TIPO DE SERVICO", "TIPO DE SERVIÇO"))
    conjunto = " ".join([channel_value, tipo])
    if any(x in conjunto for x in ("PBTVD","GTVD","RTVD","RETRANSMISS", "TV DIGITAL")):
        for a in ("PBTVD","GTVD","RTVD","RTV"):
            if a in conjunto:
                return a
        return "RTV"
    # Canais físicos de televisão normalmente são inteiros de 2 a 69.
    if re.fullmatch(r"\d{1,2}", channel_value or ""):
        n = int(channel_value)
        if 2 <= n <= 69:
            return "TV"
    return ""

def uf(row):
    x = norm(pick(row, "UF", "SIGLA UF", "ESTADO", "UNIDADE DA FEDERACAO"))
    if x in UF_NAMES: return x
    return UF_BY_NAME.get(x, "")

def city(row):
    return pick(row, "MUNICIPIO", "MUNICÍPIO", "CIDADE", "LOCALIDADE",
                "MUNICIPIO DA ESTACAO", "MUNICÍPIO DA ESTAÇÃO")

def entity(row):
    return pick(row, "ENTIDADE", "NOME DA ENTIDADE", "RAZAO SOCIAL",
                "RAZÃO SOCIAL", "EMISSORA", "NOME DA EMISSORA",
                "NOME ENTIDADE", "NOME")

def channel(row):
    return pick(row, "CANAL", "CANAL FISICO", "CANAL FÍSICO", "CANAL DIGITAL")

def situation(row):
    return pick(row, "SITUACAO", "SITUAÇÃO", "STATUS", "SITUACAO ATUAL", "SITUAÇÃO ATUAL")

def classify(serv):
    if serv == "TV": return "comercial_publica_educativa"
    if serv == "GTVD": return "digital_geradora"
    if serv == "PBTVD": return "plano_basico_tv_digital"
    if serv == "RTV": return "retransmissora"
    if serv == "RTVD": return "retransmissora_digital"
    return "radiodifusao"

def download_fixture_if_requested():
    fixture = __import__("os").environ.get("SCR_FIXTURE")
    if fixture:
        path = Path(fixture)
        data = path.read_bytes()
        print(f"SCR: fixture de teste ({len(data)} bytes)")
        return data
    return None

def download():
    """Baixa o SCR com tentativas e leitura em blocos."""
    import time, os
    timeout=int(os.environ.get("SCR_TIMEOUT","180"))
    retries=int(os.environ.get("SCR_RETRIES","4"))
    last=None
    for attempt in range(1,retries+1):
        try:
            req=Request(URL,headers={"User-Agent":"Mozilla/5.0 (compatible; Brasil-TV-M3U/5.0)"})
            print(f"SCR: tentativa {attempt}/{retries} (timeout={timeout}s)")
            with urlopen(req,timeout=timeout) as r:
                chunks=[]; total=0
                while True:
                    chunk=r.read(1024*1024)
                    if not chunk: break
                    chunks.append(chunk); total += len(chunk)
                    if total % (10*1024*1024) < 1024*1024:
                        print(f"SCR: baixados {total/1024/1024:.1f} MB")
                data=b"".join(chunks)
            if len(data)<1000: raise RuntimeError("download do SCR retornou conteúdo pequeno/inválido")
            print(f"SCR: download concluído ({len(data)/1024/1024:.1f} MB)")
            return data
        except Exception as e:
            last=e; print(f"SCR: tentativa {attempt} falhou: {e}")
            if attempt<retries: time.sleep(min(30*attempt,90))
    raise RuntimeError(f"falha após {retries} tentativas: {last}")

def decode(data):
    for enc in ("utf-8-sig","utf-8","latin-1"):
        try:
            text = data.decode(enc)
            # Detecta delimitador por contagem na primeira linha.
            first = text.splitlines()[0]
            delim = ";" if first.count(";") >= first.count(",") else ","
            return list(csv.DictReader(io.StringIO(text), delimiter=delim))
        except UnicodeDecodeError:
            continue
    raise RuntimeError("não foi possível decodificar o CSV do SCR")

def main():
    try:
        data = download_fixture_if_requested()
        if data is None:
            data = download()
        raw = decode(data)
    except Exception as e:
        print(f"AVISO SCR: {e}", file=sys.stderr)
        print("Catálogo atual preservado; seguindo a atualização sem o SCR.", file=sys.stderr)
        return

    if not raw:
        raise RuntimeError("SCR sem registros")
    services = {service(r) for r in raw if service(r)}
    useful = [r for r in raw if service(r) in TARGET_SERVICES]

    # Diagnóstico explícito para facilitar manutenção quando o MCom alterar
    # novamente o layout.
    if len(useful) == 0:
        headers = list(raw[0].keys())[:40]
        sample = []
        for r in raw[:5]:
            sample.append({k: r.get(k, "") for k in headers[:12]})
        raise RuntimeError(
            "Nenhum registro de TV foi identificado no SCR. "
            f"Colunas detectadas: {headers}. "
            f"Serviços identificados: {sorted(services)}. "
            f"Amostra: {sample}"
        )
    if len(useful) < 50:
        print(
            f"AVISO: somente {len(useful)} registros de TV foram identificados; "
            "a importação continuará, mas o relatório registrará o resultado."
        )

    cat_path = DATA / "emissoras.csv"
    with cat_path.open(encoding="utf-8-sig", newline="") as f:
        current = list(csv.DictReader(f))

    # Índice por emissora + UF + município; evita criar uma entrada por retransmissora.
    idx = {}
    for i,r in enumerate(current):
        key = (norm(r.get("Emissora")), norm(r.get("Estado")), norm(r.get("Cidade")))
        if key[0]:
            idx.setdefault(key, i)

    now = datetime.now(timezone.utc).date().isoformat()
    added = 0
    enriched = 0

    # Consolida linhas SCR repetidas por entidade/localidade/serviço.
    consolidated = {}
    for r in useful:
        e, u, c, s = entity(r), uf(r), city(r), service(r)
        if not e or not u or not c:
            continue
        key = (norm(e), u, norm(c))
        consolidated.setdefault(key, []).append(r)

    for key, group in consolidated.items():
        e = entity(group[0]); u = uf(group[0]); c = city(group[0])
        servs = sorted({service(x) for x in group})
        chans = sorted({channel(x) for x in group if channel(x)})
        situations = sorted({situation(x) for x in group if situation(x)})
        primary = next((x for x in group if service(x) in {"GTVD","TV"}), group[0])

        lookup = (norm(e), norm(UF_NAMES[u]), norm(c))
        i = idx.get(lookup)
        if i is None:
            cid = slug(f"scr-{e}-{u}-{c}")
            # Collision-safe deterministic ID.
            existing_ids = {x.get("id") for x in current}
            base = cid; n = 2
            while cid in existing_ids:
                cid = f"{base}-{n}"; n += 1
            rec = {k:"" for k in FIELDS}
            rec.update({
                "id": cid,
                "Emissora": e.title() if e.isupper() else e,
                "Estado": UF_NAMES[u],
                "Cidade": c.title() if c.isupper() else c,
                "Tipo": classify(service(primary)),
                "Status": "confirmada",
                "Observação": "Identificada no SCR/MCom; stream somente será incluído após validação de origem.",
                "scr_servico": ",".join(servs),
                "scr_tipo_registro": "geradora" if any(x in {"TV","GTVD"} for x in servs) else "estacao/retransmissora",
                "scr_canal": ",".join(chans),
                "scr_situacao": " | ".join(situations),
                "scr_ultima_atualizacao": now,
            })
            current.append(rec)
            idx[lookup] = len(current)-1
            added += 1
        else:
            rec = current[i]
            old = (rec.get("scr_servico"), rec.get("scr_canal"), rec.get("scr_situacao"))
            rec["scr_servico"] = ",".join(servs)
            rec["scr_canal"] = ",".join(chans)
            rec["scr_situacao"] = " | ".join(situations)
            rec["scr_ultima_atualizacao"] = now
            if old != (rec["scr_servico"], rec["scr_canal"], rec["scr_situacao"]):
                enriched += 1

    # Ensure all fields exist.
    for r in current:
        for f in FIELDS:
            r.setdefault(f, "")

    with cat_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(current)

    report = DATA / "scr-importacao-resumo.json"
    report.write_text(
        __import__("json").dumps({
            "fonte": URL,
            "servicos_encontrados": sorted(services),
            "cabecalhos_detectados": list(raw[0].keys()),
            "registros_scr_total": len(raw),
            "registros_tv_filtrados": len(useful),
            "emissoras_novas": added,
            "emissoras_enriquecidas": enriched,
            "data_utc": now
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"SCR total: {len(raw)}")
    print(f"TV/GTVD/PBTVD/RTV/RTVD: {len(useful)}")
    print(f"Novas emissoras/localidades: {added}")
    print(f"Registros enriquecidos: {enriched}")
    print(f"Catálogo final: {len(current)}")

if __name__ == "__main__":
    main()
