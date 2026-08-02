# CLAUDE.md - global (Gustavo Perin / Bobagi)

Este arquivo carrega em **todos os projetos** desta máquina. Regras de máquina e de
projeto específicas continuam em `/root/CLAUDE.md`, `/opt/CLAUDE.md` e nos
`CLAUDE.md` de cada repo - este aqui é só a política transversal.

> **Fonte de verdade:** este arquivo é versionado em
> [`Bobagi/claude-skills`](https://github.com/Bobagi/claude-skills) (`config/CLAUDE.md`)
> e instalado como `~/.claude/CLAUDE.md` pelo `sync.sh`. Edite-o no repo (ou edite o
> local e rode `sync.sh`/commit) para propagar pra todas as máquinas. Ver seção
> **Sincronizar numa máquina nova** no fim.

## ★★ Estilo de escrita: PROIBIDO o em dash (travessão longo, U+2014), regra dura, todo projeto

**Nunca use o em dash (o traço longo, ponto de código Unicode U+2014) em NADA que você
produzir:** texto de UI, copy de marketing, mensagens de erro, comentários de código,
documentação, `CLAUDE.md`, mensagens de commit, descrições de PR e respostas no chat. É uma
preferência firme do Gustavo (pedido explícito 2026-07-26: "remova COMPLETAMENTE e nunca mais
use, em nenhuma máquina ou projeto"). No lugar dele, use vírgula, dois-pontos, parênteses, ponto
final, ou reescreva a frase; se precisar mesmo de um traço, use o hífen simples "-". A mesma
proibição vale para o en dash (U+2013). Ao **editar** um arquivo que já contenha um em dash,
troque a ocorrência pela pontuação adequada de passagem. Verificação rápida num projeto (usa o
code point pra não digitar o caractere): `grep -rnP "\x{2014}" <dir>` deve dar vazio no que você
escreveu.

**ISTO É EXECUTADO, não só documentado (2026-08-01):** um hook `PostToolUse` em
`Write|Edit|NotebookEdit` roda `~/.claude/no-em-dash-check.sh` no arquivo que você acabou de
gravar; se houver travessão ele sai com **código 2** e devolve as linhas ofensoras como feedback,
te obrigando a corrigir antes de seguir. Ele olha SÓ o arquivo tocado (arquivo legado com
travessão não vira ruído) e ignora binário. **Separador de título:** prefira `·` em vez de hífen.
**Atenção ao varrer um projeto:** conteúdo derivado (banco, build, índice de busca) guarda uma
CÓPIA do texto - trocar o fonte não basta, é preciso reprocessar o pipeline e conferir a página
renderizada.

## ★ Política SKILL-FIRST (vale para todo comando, em todo projeto)

**Antes de executar qualquer tarefa, procure ativamente uma skill ou plugin que ajude
e use-o.** Não trate skills como último recurso - são o primeiro lugar a olhar.

Fluxo obrigatório em cada pedido:
1. **Olhe a lista de skills** nos `<system-reminder>` e na ferramenta `Skill`, e os
   **plugins habilitados** (ver abaixo).
2. **Se alguma encaixar - mesmo parcialmente - invoque-a** (via `Skill` ou o slash-command),
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
rode a skill **`security-sweep`** escopada na feature ANTES de encerrar - ela **encontra, TESTA ao vivo
(dispara o ataque de verdade) e CORRIGE**, não só reporta. Isso é não-negociável, como a regra de front.
Quando o usuário disser **"faça uma varredura de segurança" / "pentest" / "está seguro?"**, invoque
`security-sweep` (varredura completa da app). Complementos: `/security-review` (review estático do diff) e
o plugin `security-guidance` (lente) - rode-os junto, mas a `security-sweep` é a que **fecha o loop
testando e consertando**. Motivo desta política: um review estático já **deixou passar** uma race condition
financeira real - só o teste adversarial ao vivo pega esse tipo de falha.

**Junto com segurança, ao fim de feature crítica:** rode **`test-forge`** (trava o comportamento com um
teste confiável que roda e pode falhar - priorize o caminho do dinheiro) e, em features grandes,
**`code-standards`** (consistência/boas práticas) + `/code-review` (bugs) + `/simplify`. Gatilhos diretos:
"crie testes" → `test-forge`; "está seguindo os padrões?"/"boas práticas" → `code-standards`.

### Skills disponíveis (repo pessoal `claude-skills`, symlinked em `~/.claude/skills`)
- **`frontend-review`** - auditor de front-end agnóstico: screenshots multi-viewport +
  a11y + consistência, com rubric versionada que melhora a cada uso. Use para **avaliar/revisar** UI.
- **`security-sweep`** - **varredura de segurança agnóstica que ENCONTRA, TESTA ao vivo e CORRIGE**
  (não só reporta): race conditions/TOCTOU, IDOR/autz, enumeração, injeção, SSRF, upload, XSS, segredos,
  sessão/CSRF/step-up, crypto, exposição de dados, lógica financeira, OAuth/federada, trilha+anomalia de
  login, defaults seguros, infra/headers - contra uma `rubric.md` versionada que cresce. Use em "varredura
  de segurança"/"pentest"/"está seguro?" **e** ao fim de toda feature sensível. É NOSSA (não confie só no
  `/security-review` estático). **Par da `app-essentials`:** aquela CONSTRÓI a feature de base, esta a BLINDA.
- **`app-essentials`** - **implementa** (não só audita) as funcionalidades que todo sistema web sério tem:
  login e-mail+senha, **login Google (OAuth)**, verificação de e-mail, reset de senha, sessões/cookies
  seguros, página de conta + **exclusão hard-delete**, **Termos+Privacidade versionados com aceite
  server-side**, **banner de cookies (LGPD) com scripts de 3º só sob consentimento**, trilha de login +
  alerta de novo dispositivo, e-mail transacional, i18n completa, step-up. Detecta o que falta, implementa
  adaptado à stack e **fecha com `security-sweep` (blinda) + `test-forge` (trava)** - cada item do catálogo
  aponta a classe de segurança que o protege. Use em "adicione login com Google/termos/cookies/verificação
  de e-mail", "o que falta pro app ficar sério/pronto pra produção?".
- **`test-forge`** - **cria e RODA testes úteis e confiáveis** (determinísticos, que podem falhar),
  priorizando o caminho crítico (dinheiro/auth/limites/parsers/idempotência) sobre % de cobertura; roda
  até passar e conserta o código se um teste acha bug. Use em "crie testes"/"o projeto não tem testes"
  **e** ao fim de toda feature crítica. Complementa `/verify` (que só confirma uma vez).
- **`code-standards`** - audita **padrões de código e boas práticas** (consistência com o próprio repo,
  camadas, erros, código morto, i18n completa, mágicos, linter/formatter) e aplica correções seguras. Use
  em "está seguindo os padrões?"/"boas práticas". Complementa `/code-review` (bugs) e `/simplify`.
- **`ai-delegate`** - **orquestra IAs gratuitas para economizar tokens do Claude**: delega tarefas
  braçais delimitadas (boilerplate, testes de função existente, docstrings, i18n, commit msgs,
  resumos) para Ollama local (qwen3.5:9b/4b, qwen2.5-coder:14b), Groq (gpt-oss-120b ~470 tok/s,
  não treina; teto real 200K tokens/dia) e Gemini Flash (ctx 1M, **TREINA**: só código não
  sensível). Fluxo: Claude escreve a spec → worker gera texto → Claude revisa e aplica (worker
  NUNCA edita arquivo; modelos ≤14B quebram diffs). Inclui `scripts/ai.sh` (workers prontos) e o
  **Cline CLI** (`cline -y`, headless) como executor agêntico com Groq/Ollama. Setup por máquina:
  Ollama + modelos + keys em `~/.config/ai-workers/`. Use em "delega pra IA barata/local",
  "economiza tokens", lotes de tarefas repetitivas.
- **`vps`** - gerenciar o VPS bobagi.space via SSH.
- **`resume`** - resumir um vídeo do YouTube a partir do link.
- **`google-play`** - releases na Play Store via Play Developer API (service account): sobe
  AAB, tracks, promoção, rollout, reviews, listing. Produção exige confirmação explícita do
  operador. Credenciais em `~/.config/bobagi-google/` (setup único: `google-play/SETUP.md`).
- **`admob`** - relatórios AdMob via API (receita, eCPM, impressões por dia/ad unit/país) +
  inventário. OAuth do dono da conta (setup único: `admob/SETUP.md`); escrita de inventário
  é restrita pelo Google (fallback manual).
- **`google-ads`** - relatórios Google Ads via API (**somente leitura**): status/orçamento de
  campanha, gasto por dia, CPI, conversões (instalações) por campanha/grupo. Exige developer
  token com acesso Básico aprovado (setup único: `google-ads/SETUP.md`); reusa o OAuth client
  do AdMob. Criar/pausar/editar campanha = operador na UI.
- **`cloudflare`** - DNS da zona `bobagi.space` no Cloudflare via API (`scripts/cf-dns.sh`):
  criar/alterar/remover subdomínios (A/CNAME, proxied/DNS-only) e registros **TXT**
  (`txt`/`txt-del` - o `txt` não toca no registro A e troca o token de mesma chave em vez de
  acumular; `delete <sub>` continua apagando TODOS os tipos do nome, cuidado). **DNS é SÓ no
  Cloudflare** (painel Hostinger morto desde 2026-07-06 - nameservers movidos). Use ao
  subir/derrubar serviço web no VPS ou em "crie um subdomínio"/"altere o DNS". Credenciais só
  no VPS (`/root/.config/cloudflare/`, chmod 600); de outra máquina, executar via skill `vps`.
- **`google-search-console`** - **cadastra e monitora sites no Google sem o operador abrir o
  navegador**: pega o token de verificação, cria o TXT via `cloudflare`, verifica a posse,
  adiciona a propriedade (`sc-domain:`), submete o sitemap e lê o desempenho de busca
  (cliques, impressões, CTR, posição média, top queries e páginas). Reusa a **service account
  do `google-play`** - sem consent screen, sem refresh token que expira e **sem senha do
  operador**. Use em "cadastre o site no Google", "submeta o sitemap", "por quais buscas meu
  site aparece", "relatório de SEO". Limite honesto: a API **não força indexação** (a Indexing
  API oficial só vale p/ JobPosting/BroadcastEvent) - sitemap + tempo é o caminho legítimo.
- **`product-review`** - **atua como Product Manager do portfolio inteiro do VPS**: coleta dados
  reais de todos os produtos (tráfego do nginx separando humano/robô/ataque, usuários nos bancos,
  receita do Google Ads/AdMob, SEO do Search Console, tráfego/estrelas do GitHub, consumo e saúde
  do box), analisa o que tem valor / consome / é usado, e gera ou atualiza um **Artifact único**
  (sempre republicado no mesmo link) com diagnóstico e recomendações priorizadas P0/P1/P2. Reusa as
  skills google + o `gh` + os bancos. Roda no VPS; assets versionados na própria skill; diretório de
  trabalho e doc operacional em `/opt/pm-dashboard/`. Um cron de sistema já deixa o `metrics-<data>.txt`
  fresco (segundas), mas quem publica o Artifact é o Claude numa sessão. Use em "revisão de produto",
  "como estão os projetos", "relatório de PM", "atualize o dashboard de produto".

> **Limite transversal Google (Play/AdMob/Ads):** o que a API oficial não cobre (pagamentos,
> data safety, criar ad unit/mediação, consent screen) é feito PELO OPERADOR guiado passo a
> passo (prints em `/root/prints` ajudam a diagnosticar). **Automação de navegador logado no
> Google (Playwright etc.): nunca na VPS** - anti-bot/2FA + risco de travar a conta dona do
> Play/AdMob; último recurso é chrome-devtools-mcp NA MÁQUINA DO OPERADOR, com ele presente.
> Detalhes na seção "Limites" dos `SKILL.md` de `google-play`, `admob` e `google-ads`.

### Plugins instalados (marketplace `claude-plugins-official`)
- **`frontend-design`** - direção visual/estética para **criar/redesenhar** UI nova
  (par natural do `frontend-review`: design → review). Cuidado em apps com design system
  já travado - restrinja aos tokens existentes; solte só em telas greenfield.
- **`claude-md-management`** - auditar/melhorar arquivos `CLAUDE.md` e capturar
  aprendizados de sessão. Use quando um `CLAUDE.md` crescer/desatualizar.
- **`security-guidance`** - review de segurança de código gerado (injeção, XSS, SSRF,
  segredos hardcoded, etc.). Especialmente relevante em apps que tocam dinheiro/credenciais.
- **`feature-dev`** - workflow de feature com agents (code-explorer, code-architect,
  code-reviewer) para itens grandes do backlog (ex.: billing, websockets, leader lock).
- **`chrome-devtools-mcp`** - inspeção/automação de browser ao vivo (Chrome DevTools, **Google
  oficial**): perf traces, network, console com source maps, a11y. Complementa o `frontend-review`.

> **Ativar plugin corretamente:** use **`claude plugin install <nome>@claude-plugins-official`**
> (ou o menu `/plugin`) - **só marcar `enabledPlugins` no JSON NÃO instala** (o `claude plugin list`
> fica "No plugins installed" e a skill do plugin não carrega). Depois de instalar, **um restart
> limpo** (`claude` novo) carrega; **`claude --resume` recarrega skills do repo `~/.claude/skills`
> mas NÃO ativa plugins recém-instalados**. Conferir: `claude plugin list`.

### MCP servers
- **`claude.ai Gmail`** e **`claude.ai Google Drive`** - remotos, ligados à **conta claude.ai**;
  reconectam sozinhos após login (nada a instalar). **`chrome-devtools`** - vem do plugin
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
