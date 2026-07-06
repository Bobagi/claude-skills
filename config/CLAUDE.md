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
   `frontend-review` audita → `simplify`/`code-review` limpam → `security-sweep` testa+corrige → `verify` confirma).

Um **hook `UserPromptSubmit`** (`~/.claude/settings.json` → `cat "$HOME/.claude/skill-first-reminder.txt"`)
reinjeta esse lembrete a cada prompt. Para revisar/desligar: comando `/hooks`.

## ★★ Política SEGURANÇA-SEMPRE (obrigatória, todo projeto)
Ao **terminar qualquer feature nova ou alterada** que toque **autenticação, dinheiro/cobrança,
limites/quotas, permissões, input do usuário, upload, fetch de URL server-side ou dados sensíveis**,
rode a skill **`security-sweep`** escopada na feature ANTES de encerrar — ela **encontra, TESTA ao vivo
(dispara o ataque de verdade) e CORRIGE**, não só reporta. Isso é não-negociável, como a regra de front.
Quando o usuário disser **"faça uma varredura de segurança" / "pentest" / "está seguro?"**, invoque
`security-sweep` (varredura completa da app). Complementos: `/security-review` (review estático do diff) e
o plugin `security-guidance` (lente) — rode-os junto, mas a `security-sweep` é a que **fecha o loop
testando e consertando**. Motivo desta política: um review estático já **deixou passar** uma race condition
financeira real — só o teste adversarial ao vivo pega esse tipo de falha.

**Junto com segurança, ao fim de feature crítica:** rode **`test-forge`** (trava o comportamento com um
teste confiável que roda e pode falhar — priorize o caminho do dinheiro) e, em features grandes,
**`code-standards`** (consistência/boas práticas) + `/code-review` (bugs) + `/simplify`. Gatilhos diretos:
"crie testes" → `test-forge`; "está seguindo os padrões?"/"boas práticas" → `code-standards`.

### Skills disponíveis (repo pessoal `claude-skills`, symlinked em `~/.claude/skills`)
- **`frontend-review`** — auditor de front-end agnóstico: screenshots multi-viewport +
  a11y + consistência, com rubric versionada que melhora a cada uso. Use para **avaliar/revisar** UI.
- **`security-sweep`** — **varredura de segurança agnóstica que ENCONTRA, TESTA ao vivo e CORRIGE**
  (não só reporta): race conditions/TOCTOU, IDOR/autz, enumeração, injeção, SSRF, upload, XSS, segredos,
  sessão/CSRF/step-up, crypto, exposição de dados, lógica financeira, infra/headers — contra uma
  `rubric.md` versionada que cresce. Use em "varredura de segurança"/"pentest"/"está seguro?" **e** ao
  fim de toda feature sensível. É NOSSA (não confie só no `/security-review` estático).
- **`test-forge`** — **cria e RODA testes úteis e confiáveis** (determinísticos, que podem falhar),
  priorizando o caminho crítico (dinheiro/auth/limites/parsers/idempotência) sobre % de cobertura; roda
  até passar e conserta o código se um teste acha bug. Use em "crie testes"/"o projeto não tem testes"
  **e** ao fim de toda feature crítica. Complementa `/verify` (que só confirma uma vez).
- **`code-standards`** — audita **padrões de código e boas práticas** (consistência com o próprio repo,
  camadas, erros, código morto, i18n completa, mágicos, linter/formatter) e aplica correções seguras. Use
  em "está seguindo os padrões?"/"boas práticas". Complementa `/code-review` (bugs) e `/simplify`.
- **`vps`** — gerenciar o VPS bobagi.space via SSH.
- **`resume`** — resumir um vídeo do YouTube a partir do link.
- **`google-play`** — releases na Play Store via Play Developer API (service account): sobe
  AAB, tracks, promoção, rollout, reviews, listing. Produção exige confirmação explícita do
  operador. Credenciais em `~/.config/bobagi-google/` (setup único: `google-play/SETUP.md`).
- **`admob`** — relatórios AdMob via API (receita, eCPM, impressões por dia/ad unit/país) +
  inventário. OAuth do dono da conta (setup único: `admob/SETUP.md`); escrita de inventário
  é restrita pelo Google (fallback manual).

> **Limite transversal Google (Play/AdMob):** o que a API oficial não cobre (pagamentos,
> data safety, criar ad unit/mediação, consent screen) é feito PELO OPERADOR guiado passo a
> passo (prints em `/root/prints` ajudam a diagnosticar). **Automação de navegador logado no
> Google (Playwright etc.): nunca na VPS** — anti-bot/2FA + risco de travar a conta dona do
> Play/AdMob; último recurso é chrome-devtools-mcp NA MÁQUINA DO OPERADOR, com ele presente.
> Detalhes na seção "Limites" dos `SKILL.md` de `google-play` e `admob`.

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
