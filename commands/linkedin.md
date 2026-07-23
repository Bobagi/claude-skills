# LinkedIn

Le, edita e audita o perfil do LinkedIn do usuario. A skill completa esta em
`linkedin/SKILL.md` — leia ela antes de agir.

Resumo operacional:

```bash
cd ~/.claude/skills/linkedin/scripts
node li.mjs doctor     # chrome + login ok?
node li.mjs audit      # o que consertar, com numero
node li.mjs stats      # visualizacoes / aparicoes em busca / conexoes
```

**Escrita e dry-run por padrao.** Rode sem `--commit`, leia o print em `.out/`,
**confirme com o usuario**, so entao rode com `--commit`. O perfil e publico e ao vivo.

Se der `CHROME_DOWN`, suba o Chrome dedicado:

```powershell
Start-Process 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--remote-debugging-port=9222','--user-data-dir=D:\dev\linkedin\chrome-profile'
```
