# Google Ads

Invoque a skill **google-ads** (em `~/.claude/skills/google-ads/`) e siga o
`SKILL.md` dela. Ela consulta a Google Ads API (somente leitura): status e
orçamento das campanhas, gasto por dia, CPI/CPA, conversões (instalações) por
campanha e grupo de anúncios.

- Sem argumentos: rode `gads.py doctor` e `gads.py campaigns --days 7` e
  apresente um resumo (está veiculando? gastando quanto? CPI?).
- Com argumentos (`$ARGUMENTS`): interprete a intenção (ex.: "gasto por dia",
  "CPI por grupo/idioma") e use `daily`/`groups`/`search`.
- `DEVELOPER_TOKEN_NOT_APPROVED` = acesso Básico ainda não aprovado pelo
  Google — explique e aguarde; não é bug.
- Se as credenciais não existirem, mostre o passo a passo do `SETUP.md`.
- A skill NÃO altera campanha (criar/pausar/orçamento = operador na UI).
