import csv,sys,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import promover_streams
assert promover_streams.host_ok('stream3.camara.gov.br','https://www.camara.leg.br/tv/')
assert promover_streams.host_ok('tvbrasil-stream.ebc.com.br','https://tvbrasil.ebc.com.br/')
assert not promover_streams.host_ok('example.com','https://www.camara.leg.br/tv/')
print('TESTE STREAMS: OK')
