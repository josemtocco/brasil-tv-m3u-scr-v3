import csv, os, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
catalog=ROOT/"data/emissoras.csv"
original=catalog.read_bytes()
fixture=Path(tempfile.mktemp(suffix=".csv"))
try:
    rows=[
      {"SiglaServico":"GTVD","Entidade":"TV TESTE","UF":"RS","Municipio":"Cachoeira do Sul","Canal":"25","Situacao":"ATIVA"},
      {"SiglaServico":"RTVD","Entidade":"TV TESTE","UF":"RS","Municipio":"Cachoeira do Sul","Canal":"26","Situacao":"ATIVA"},
      {"SiglaServico":"FM","Entidade":"RADIO TESTE","UF":"RS","Municipio":"Cachoeira do Sul","Canal":"100","Situacao":"ATIVA"}]
    with fixture.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys(),delimiter=";"); w.writeheader(); w.writerows(rows)
    env=os.environ.copy(); env["SCR_FIXTURE"]=str(fixture)
    r=subprocess.run([sys.executable,str(ROOT/"scripts/importar_scr.py")],cwd=ROOT,env=env,text=True,capture_output=True)
    assert r.returncode==0,(r.stdout,r.stderr)
    with catalog.open(encoding="utf-8-sig",newline="") as f: data=list(csv.DictReader(f))
    found=[x for x in data if x["Emissora"].lower()=="tv teste"]
    assert found, "registro de teste não foi importado"
    assert found[0]["Estado"]=="Rio Grande do Sul" and found[0]["Cidade"]=="Cachoeira do Sul"
    assert found[0]["scr_servico"]=="GTVD,RTVD"
    before=catalog.read_bytes()
    env.pop("SCR_FIXTURE"); env["SCR_URL"]="http://127.0.0.1:1/arquivo.csv"; env["SCR_RETRIES"]="1"; env["SCR_TIMEOUT"]="1"
    r=subprocess.run([sys.executable,str(ROOT/"scripts/importar_scr.py")],cwd=ROOT,env=env,text=True,capture_output=True)
    assert r.returncode==0,(r.stdout,r.stderr)
    assert catalog.read_bytes()==before
    print("TESTES SCR: OK")
finally:
    catalog.write_bytes(original)
    try: fixture.unlink()
    except: pass
