# AdMob

Invoque a skill **admob** (em `~/.claude/skills/admob/`) e siga o `SKILL.md`
dela. Ela consulta a AdMob API: receita, eCPM, impressões por dia/ad unit/
país/formato, lista de apps e ad units.

- Sem argumentos: rode `admob.py doctor` e `admob.py report --days 7` e
  apresente um resumo da receita da semana.
- Com argumentos (`$ARGUMENTS`): interprete a intenção (ex.: "receita dos
  últimos 30 dias por país", "lista as ad units") e use os subcomandos.
- Criação/edição de ad unit via API é restrita pelo Google (403 é esperado) —
  quando negar, apresente o caminho manual que o script imprime.
- Se as credenciais não existirem, mostre o passo a passo do `SETUP.md`.
