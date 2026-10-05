from pathlib import Path
import py_compile
ROOT=Path(__file__).resolve().parents[1]
for p in [ROOT/"scripts/importar_scr.py",ROOT/"scripts/validar.py",ROOT/"scripts/gerar_m3u.py"]:
    py_compile.compile(str(p),doraise=True)
print("SINTAXE: OK")
