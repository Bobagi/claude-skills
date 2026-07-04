---
name: admob
description: Consulta a conta AdMob via AdMob API — receita/ganhos por dia, eCPM, impressões e cliques por ad unit/país/formato, lista de apps e ad units. Use quando o usuário perguntar quanto o app está rendendo, pedir relatório de anúncios/receita/eCPM do AdMob, listar unidades de anúncio, ou pedir para criar/ajustar ad units (criação via API é restrita; a skill tenta e cai para o passo manual). App padrão - Tic Tac Verse.
allowed-tools: Bash, Read
---

# AdMob (AdMob API)

Relatórios de monetização e inventário da conta AdMob (publisher
`ca-app-pub-5349785075769585`). Tudo roda pelo script **`scripts/admob.py`**
(python3 puro, sem pip).

## Credenciais

A AdMob API **não aceita service account** — é OAuth do usuário dono da conta:

- `~/.config/bobagi-google/admob-client.json` — OAuth client (Desktop) do GCP.
- `~/.config/bobagi-google/admob-token.json` — refresh token gerado uma vez
  por `admob.py auth` (consentimento no navegador do operador; ver `SETUP.md`).

Se qualquer um faltar, mostre o passo a passo de `SETUP.md` e pare. Nunca
imprima o conteúdo desses arquivos.

## Comandos

```bash
S=~/.claude/skills/admob/scripts/admob.py

python3 $S doctor                      # valida credencial + acesso à conta
python3 $S report --days 7             # receita/eCPM por dia (US$)
python3 $S report --days 30 --by AD_UNIT
python3 $S report --days 30 --by COUNTRY
python3 $S apps                        # apps registrados no AdMob
python3 $S adunits                     # ad units + IDs (para conferir com o código)
python3 $S create-adunit --app APP_ID --name "Rewarded skins" --format REWARDED
```

## O que a API permite (e o que não)

- **Leitura/relatórios: sempre funciona** (escopo `admob.readonly`). É a fonte
  para "quanto rendeu", eCPM real por formato/país e sanity-check dos ad unit
  IDs usados no `ad_unit_id_provider.dart` do app.
- **Escrita (criar ad unit / mediação): "limited access" do Google** — contas
  sem account manager recebem 403. O `create-adunit` tenta e, se negado,
  imprime o caminho manual (apps.admob.com → Apps → Ad units → Add). Mudanças
  de mediação/eCPM floor também são manuais na UI.
- Relatórios de dias muito recentes podem vir zerados/parciais (delay do AdMob).

## Regras

1. Dados financeiros: apresentar como estimativas do AdMob (a receita final
   pode mudar até o fechamento do mês).
2. Se o refresh token expirar (consent screen em modo "Testing" expira em 7
   dias), oriente o operador a publicar o consent screen e rodar `auth` de
   novo — está no `SETUP.md`.
3. Nunca automatizar login por navegador na conta Google; só a API oficial.
