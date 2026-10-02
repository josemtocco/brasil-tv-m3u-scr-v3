#!/usr/bin/env python3
"""
Ponto de extensão para a varredura nacional.

A política é deliberadamente conservadora:
- novas emissoras podem ser adicionadas após confirmação;
- streams só entram em data/streams.csv após confirmação de origem;
- nenhuma URL encontrada em lista de terceiros é promovida automaticamente.
"""
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]
print("Atualização do catálogo: use as fontes em data/fontes.csv.")
print("Para automação futura, implemente aqui os coletores por fonte.")
print("Nenhum stream será promovido automaticamente sem validação.")
