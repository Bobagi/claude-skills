# Sync Claude

Sincroniza a configuração do Claude Code desta máquina com o repo
[`Bobagi/claude-skills`](https://github.com/Bobagi/claude-skills): skills, comandos,
plugins, `~/.claude/CLAUDE.md`, `~/.claude/settings.json` e o hook skill-first.

## Instruções

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
