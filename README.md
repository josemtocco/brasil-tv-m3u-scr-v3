# 🇧🇷 Brasil TV M3U — Cadastro Nacional

Projeto para catalogar emissoras de TV brasileiras e gerar uma playlist M3U compatível com SS IPTV.

## Regra principal

**Maximizar a quantidade de emissoras identificadas, mas não maximizar artificialmente a quantidade de streams.**

O catálogo pode conter uma emissora mesmo quando não existe HLS/M3U8 confiável. A playlist M3U somente recebe streams que passam pelos critérios de origem e validação definidos no projeto.

## Categorias pesquisadas

- Comerciais / abertas
- Públicas
- Legislativas federais, estaduais e municipais
- Universitárias
- Institutos federais
- Comunitárias
- Regionais / locais
- Institucionais
- Religiosas quando houver emissora/canal identificável e fonte oficial

## Fontes aceitas

1. Site ou servidor oficial da emissora/instituição.
2. Infraestrutura oficial de órgão público, universidade ou legislativo.
3. CDN externa comprovadamente usada pela própria emissora.
4. IPTV-org apenas como fonte auxiliar de descoberta/validação.
5. YouTube oficial como referência de presença digital; não é convertido automaticamente em HLS.

## Fontes rejeitadas

- Xtream Codes / painéis privados
- links com usuário/senha
- IPTV pago
- streams tokenizados sem origem oficial verificável
- URLs de fóruns/listas de terceiros sem confirmação
- streams sem procedência identificável

## Arquivos

- `data/emissoras.csv` — cadastro nacional.
- `data/streams.csv` — streams candidatos/validados.
- `data/fontes.csv` — fontes de descoberta.
- `output/brasil-tv.m3u` — playlist principal.
- `output/brasil-tv-abertos.m3u` — somente grupos públicos/abertos conforme cadastro.
- `output/brasil-tv-universitarios.m3u` — universitários.
- `output/brasil-tv-legislativos.m3u` — legislativos.
- `scripts/gerar_m3u.py` — gerador.
- `scripts/validar.py` — validação do cadastro.
- `scripts/descobrir_iptv_org.py` — cruza o catálogo com dados públicos do IPTV-org sem substituir a fonte oficial.
- `scripts/atualizar_catalogo.py` — estrutura para atualizações futuras.
- `.github/workflows/atualizar.yml` — atualização automática a cada 6 horas.

## Compatibilidade SS IPTV

A playlist usa `#EXTM3U`, `#EXTINF`, `tvg-name`, `tvg-id`, `tvg-logo` e `group-title`. O título exibido após a vírgula é sempre o **nome da emissora**, e nunca "Guia de programação".

A documentação do SS IPTV define `#EXTINF` + URI como o par básico da playlist e aceita atributos como `tvg-name` e `tvg-logo`.

## Atualização

O GitHub Actions executa:

1. descoberta/atualização do catálogo;
2. validação;
3. geração das playlists;
4. commit apenas quando houver alteração.

A agenda é de 6 em 6 horas.

## Importante

O cadastro nacional é deliberadamente mais amplo que a playlist. Assim, uma emissora pode ser descoberta e documentada sem que um stream não verificado seja colocado no M3U.

## Importação automática do SCR/MCom

A cada execução do GitHub Actions, `scripts/importar_scr.py` consulta o
Conjunto de Dados de Radiodifusão (SCR) do Ministério das Comunicações,
filtra TV, GTVD, PBTVD, RTV e RTVD e cruza os registros por **emissora +
UF + município**.

O SCR é usado para ampliar e confirmar o catálogo, não para inventar streams.
Retransmissoras/estações são registradas como dados técnicos da emissora
quando possível, evitando multiplicar artificialmente o número de emissoras.

Se o download oficial falhar ou o arquivo vier inválido/inesperadamente
pequeno, a rotina termina sem substituir o catálogo existente. Assim uma
indisponibilidade temporária do MCom não apaga dados já coletados.

Fonte oficial do SCR:
https://s3.mcom.gov.br/radcom/SCR_DADOS_RADIODIFUSAO_TV_GTVD_RTV_RTVD_FM_OM.csv
