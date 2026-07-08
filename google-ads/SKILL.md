---
name: google-ads
description: Consulta a conta Google Ads via Google Ads API (somente leitura) — status e orçamento das campanhas, gasto/custo por dia, CPI/CPA, impressões, cliques e conversões (instalações) por campanha e por grupo de anúncios. Use quando o usuário perguntar como está a campanha, quanto o Ads está gastando, o CPI por idioma/grupo, se a campanha está veiculando, ou pedir relatório do Google Ads. Conta padrão - a do operador (Tic Tac Verse).
allowed-tools: Bash, Read
---

# Google Ads (Google Ads API)

Relatórios da conta Google Ads do operador. Tudo roda pelo script
**`scripts/gads.py`** (python3 puro, sem pip). **Somente leitura** (GAQL
`search`) — a skill não cria/edita/pausa campanha (isso é na UI, pelo operador).

## Credenciais

Três peças, todas fora do repo em `~/.config/bobagi-google/` (chmod 600):
- **OAuth client**: reusa o `admob-client.json` do AdMob.
- **`gads-token.json`**: refresh token com escopo `adwords` — gerado uma vez
  por `gads.py auth` (consentimento no navegador do operador).
- **`gads-config.json`**: `developer_token` (da Central da API do Google Ads),
  `customer_id`, `api_version` (auto-detectada e cacheada).

Se faltar qualquer peça, mostre o passo a passo de `SETUP.md` e pare.
**Nunca imprima o conteúdo desses arquivos.**

> ⚠️ O developer token novo nasce em nível **"Conta de teste"** e NÃO lê contas
> reais — o operador precisa solicitar **acesso Básico** na Central da API
> (aprovação ~1–3 dias úteis). Até lá, `DEVELOPER_TOKEN_NOT_APPROVED` é esperado
> e o script explica isso sozinho.

## Comandos

```bash
S=~/.claude/skills/google-ads/scripts/gads.py

python3 $S doctor                     # valida OAuth + dev token + conta + versão da API
python3 $S set-config --developer-token XXX [--customer-id 1234567890]
python3 $S auth                       # consentimento único (escopo adwords)
python3 $S accounts                   # customer IDs acessíveis
python3 $S campaigns --days 7         # status/orçamento + custo/impr/cliques/conv/CPI por campanha
python3 $S groups --days 7            # por grupo de anúncios (PT/EN/ES no tictacverse)
python3 $S daily --days 14            # totais por dia (a campanha está gastando?)
python3 $S search --gaql "SELECT ..." # GAQL cru (escape hatch)
```

- Custo e CPI saem na **moeda da conta** (BRL). "Conversões" numa campanha de
  app = instalações (conversão "Instalações Google Play" vinculada da Play).
- Dados de hoje/ontem podem estar parciais.
- Perguntas típicas → comando: "está gastando?" → `daily`; "CPI por idioma" →
  `groups`; "como está a campanha?" → `campaigns`.

## Limites — o que fica na UI, pelo operador

- Criar/editar/pausar campanha, subir criativos, orçamento, lances (a skill é
  leitura; escrita via API exige acesso Standard + muito mais risco).
- Faturamento/cartão, cupons promocionais.
- Vincular YouTube/Play, formulários de verificação do anunciante.

## Política de navegador

Mesma das skills `google-play`/`admob`: **nunca automatizar login Google na
VPS**; itens de UI = guiar o operador; último recurso = chrome-devtools-mcp na
máquina DELE. Nunca guardar cookies Google na VPS.
