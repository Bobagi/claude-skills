# CLAUDE.md — global (Gustavo Perin / Bobagi)

Este arquivo carrega em **todos os projetos** desta máquina. Regras de máquina e de
projeto específicas continuam em `/root/CLAUDE.md`, `/opt/CLAUDE.md` e nos
`CLAUDE.md` de cada repo — este aqui é só a política transversal.

> **Fonte de verdade:** este arquivo é versionado em
> [`Bobagi/claude-skills`](https://github.com/Bobagi/claude-skills) (`config/CLAUDE.md`)
> e instalado como `~/.claude/CLAUDE.md` pelo `sync.sh`. Edite-o no repo (ou edite o
> local e rode `sync.sh`/commit) para propagar pra todas as máquinas. Ver seção
> **Sincronizar numa máquina nova** no fim.

## ★ Política SKILL-FIRST (vale para todo comando, em todo projeto)

**Antes de executar qualquer tarefa, procure ativamente uma skill ou plugin que ajude
e use-o.** Não trate skills como último recurso — são o primeiro lugar a olhar.

Fluxo obrigatório em cada pedido:
1. **Olhe a lista de skills** nos `<system-reminder>` e na ferramenta `Skill`, e os
   **plugins habilitados** (ver abaixo).
2. **Se alguma encaixar — mesmo parcialmente — invoque-a** (via `Skill` ou o slash-command),
   em vez de fazer o trabalho ad-hoc.
3. **Só pule** quando nenhuma for de fato relevante. Se pular, é por não haver match,
   nunca por ter esquecido de olhar.
4. **Combine skills** quando fizer sentido (ex.: `frontend-design` cria a UI →
   `frontend-review` audita → `simplify`/`code-review` limpam → `verify` confirma).

Um **hook `UserPromptSubmit`** (`~/.claude/settings.json` → `cat "$HOME/.claude/skill-first-reminder.txt"`)
reinjeta esse lembrete a cada prompt. Para revisar/desligar: comando `/hooks`.

### Skills disponíveis (repo pessoal `claude-skills`, symlinked em `~/.claude/skills`)
- **`frontend-review`** — auditor de front-end agnóstico: screenshots multi-viewport +
  a11y + consistência, com rubric versionada que melhora a cada uso. Use para **avaliar/revisar** UI.
- **`vps`** — gerenciar o VPS bobagi.space via SSH.
- **`resume`** — resumir um vídeo do YouTube a partir do link.

### Plugins instalados (marketplace `claude-plugins-official`)
- **`frontend-design`** — direção visual/estética para **criar/redesenhar** UI nova
  (par natural do `frontend-review`: design → review). Cuidado em apps com design system
  já travado — restrinja aos tokens existentes; solte só em telas greenfield.
- **`claude-md-management`** — auditar/melhorar arquivos `CLAUDE.md` e capturar
  aprendizados de sessão. Use quando um `CLAUDE.md` crescer/desatualizar.
- **`security-guidance`** — review de segurança de código gerado (injeção, XSS, SSRF,
  segredos hardcoded, etc.). Especialmente relevante em apps que tocam dinheiro/credenciais.
- **`feature-dev`** — workflow de feature com agents (code-explorer, code-architect,
  code-reviewer) para itens grandes do backlog (ex.: billing, websockets, leader lock).
- **`chrome-devtools-mcp`** — inspeção/automação de browser ao vivo (Chrome DevTools, **Google
  oficial**): perf traces, network, console com source maps, a11y. Complementa o `frontend-review`.

> **Ativar plugin corretamente:** use **`claude plugin install <nome>@claude-plugins-official`**
> (ou o menu `/plugin`) — **só marcar `enabledPlugins` no JSON NÃO instala** (o `claude plugin list`
> fica "No plugins installed" e a skill do plugin não carrega). Depois de instalar, **um restart
> limpo** (`claude` novo) carrega; **`claude --resume` recarrega skills do repo `~/.claude/skills`
> mas NÃO ativa plugins recém-instalados**. Conferir: `claude plugin list`.

### MCP servers
- **`claude.ai Gmail`** e **`claude.ai Google Drive`** — remotos, ligados à **conta claude.ai**;
  reconectam sozinhos após login (nada a instalar). **`chrome-devtools`** — vem do plugin
  `chrome-devtools-mcp`. Detalhes em `config/mcp.md` do repo.

### Skills embutidas que valem lembrar (não duplique com plugin)
`/code-review` (≈ plugin code-review) · `/simplify` (≈ code-simplifier) · `/security-review`
· `/verify` · `/run` · `/init` · `/loop` · `/schedule`.

> Ao criar uma skill/plugin novo, **registre-o aqui e no README de `claude-skills`**
> para que esta política continue apontando para o conjunto certo.

## Sincronizar numa máquina nova

Toda a config do Claude (skills, comandos, plugins, este `CLAUDE.md`, `settings.json` e o
hook skill-first) é versionada em **`Bobagi/claude-skills`** e aplicada por um único script
idempotente, `sync.sh`. Numa máquina nova (com `git` + Claude Code instalados):

```bash
curl -fsSL https://raw.githubusercontent.com/Bobagi/claude-skills/main/sync.sh | bash
```

Ou, se quiser pedir pra IA: **"sincronize meu Claude com o repo github.com/Bobagi/claude-skills"**
→ ela acha o `sync.sh` e roda. Já com o repo presente, dá pra rodar de novo a qualquer momento
com `/sync-claude` (ou `bash <repo>/sync.sh`). O que o sync faz: clona/atualiza o repo, cria os
symlinks `~/.claude/skills` e `~/.claude/commands`, copia `CLAUDE.md`/`settings.json`/o hook (com
backup do que existia), e instala o marketplace + todos os plugins. Depois, **reinicie o Claude**
(`claude` novo) pra carregar os plugins. Não toca em `settings.local.json` (perms por máquina).
