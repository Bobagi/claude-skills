# Google Play

Invoque a skill **google-play** (em `~/.claude/skills/google-play/`) e siga o
`SKILL.md` dela. Ela gerencia releases na Play Store via API (service account):
upload de AAB, tracks, promoção, rollout, reviews e listing.

- Sem argumentos: rode `gplay.py doctor` e depois `gplay.py tracks` e apresente
  um resumo do estado das releases.
- Com argumentos (`$ARGUMENTS`): interprete como a intenção (ex.: "subir o aab
  X no internal", "promover pra produção", "responder o review Y") e use os
  subcomandos correspondentes do `gplay.py`.
- Lembre: escrever no track `production` exige confirmação explícita do
  operador na conversa (aí sim `GPLAY_CONFIRM_PROD=yes`).
- Se as credenciais não existirem, mostre o passo a passo do `SETUP.md`.
