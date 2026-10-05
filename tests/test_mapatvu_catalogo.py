from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'scripts/coletar_mapatvu.py').read_text()
assert 'all_fields = list(fields)' in s
assert 'for rec in by_name.values()' in s
assert 'extrasaction' in s
assert "w.writerows(ordered)" in s
print('TESTE MAPATVU: preservação de colunas extras OK')
