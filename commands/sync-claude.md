# Sync Claude

Sincroniza a configuração do Claude Code desta máquina com o repo
[`Bobagi/claude-skills`](https://github.com/Bobagi/claude-skills): skills, comandos,
plugins, `~/.claude/CLAUDE.md`, `~/.claude/settings.json` e o hook skill-first.

## Instruções

> **Se `$ARGUMENTS` contiver `--save`** (capturar a config local desta máquina de volta
> pro repo): rode o `claude-sync` no modo `save` conforme o SO:
> - **Linux/Mac/Git-Bash:** `bash "$HOME/.claude/skills/scripts/claude-sync.sh" save`
> - **Windows nativo (pwsh):** `pwsh -NoProfile -ExecutionPolicy Bypass -File "$HOME/.claude/skills/scripts/claude-sync.ps1" save`
>
> Ele copia `~/.claude/{CLAUDE.md,settings.json,skill-first-reminder.txt}` para `config/`,
> faz um **scan de segredos** (aborta se achar credencial — o repo é público) e então
> commita + pusha. Mostre a saída e **pare aqui** (não rode o `sync.sh` completo).

1. Localize o `sync.sh`:
   - Se `~/.claude/skills/sync.sh` existir (symlink do repo), use esse caminho.
   - Senão, se `/opt/claude-skills/sync.sh` ou `$HOME/.claude/claude-skills/sync.sh` existir, use-o.
   - Se nenhum existir (máquina nova), faça o bootstrap baixando o script:
     `curl -fsSL https://raw.githubusercontent.com/Bobagi/claude-skills/main/sync.sh | bash`
2. Caso já exista localmente, rode `bash <caminho>/sync.sh`.
3. O script é **idempotente** e faz backup do que substituir em `~/.claude/backups/`.
   Ele **não** mexe em `~/.claude/settings.local.json` (permissões por máquina).
4. Ao final, mostre ao usuário o resumo (skills/plugins) e **lembre de reiniciar o
   Claude Code** (um `claude` novo) para carregar plugins e hooks recém-instalados.
5. Se `$ARGUMENTS` foi passado, repasse como flags/variáveis de ambiente ao script
   (ex.: `CLAUDE_SKILLS_DIR=/caminho` para clonar em outro lugar).

> MCP: os servers `claude.ai Gmail`/`Google Drive` voltam sozinhos após login na conta
> claude.ai; o `chrome-devtools` vem do plugin `chrome-devtools-mcp`. Nada a instalar à mão.
