# claude-skills

Configuração pessoal **completa e portável** do Claude Code ([@Bobagi](https://github.com/Bobagi)):
skills, slash-commands, plugins, `CLAUDE.md` global, `settings.json` e o hook skill-first — tudo
versionado aqui e aplicado por **um único script idempotente** (`sync.sh`). Objetivo: abrir o Claude
numa máquina nova e, com um comando, deixar tudo **igual em qualquer máquina**.

---

## ⚡ Sincronizar (máquina nova ou re-sync)

Pré-requisitos: `git` e o **Claude Code** instalados.

```bash
curl -fsSL https://raw.githubusercontent.com/Bobagi/claude-skills/main/sync.sh | bash
```

Ou peça pra IA: **"sincronize meu Claude com o repo github.com/Bobagi/claude-skills"** — ela acha o
`sync.sh` e roda. Com o repo já presente, dá pra rodar de novo a qualquer momento com **`/sync-claude`**
ou `bash <repo>/sync.sh`. Depois, **reinicie o Claude** (um `claude` novo) para carregar plugins e hooks.

> Variáveis úteis: `CLAUDE_SKILLS_DIR=/caminho` (onde clonar, padrão `~/.claude/claude-skills`) e
> `SYNC_SKIP_PLUGINS=1` (só arquivos/symlinks, sem instalar plugins).

### O que o `sync.sh` faz (idempotente, com backup)
1. **Clona/atualiza** este repo (detecta se já está em `/opt/claude-skills` ou `~/.claude/claude-skills`).
2. **Symlinks**: `~/.claude/skills → repo` e `~/.claude/commands → repo/commands`.
3. **Copia config** para `~/.claude/`: `CLAUDE.md`, `settings.json`, `skill-first-reminder.txt`
   (faz backup do que existia em `~/.claude/backups/`).
4. **Plugins**: adiciona o marketplace `claude-plugins-official` e instala todos de `config/plugins.txt`.

### O que ele **não** toca
- `~/.claude/settings.local.json` (permissões específicas da máquina).
- Segredos / memórias (`~/.claude/projects/*/memory/*`, ex.: credenciais do VPS) — nunca vão pro repo.
- MCP `claude.ai Gmail`/`Google Drive`: voltam sozinhos após **login na conta claude.ai** (ver `config/mcp.md`).

---

## 📦 Inventário versionado

### Skills (raiz do repo → `~/.claude/skills`)
| Skill | Comando | Descrição |
|-------|---------|-----------|
| `vps` | `/vps` | Acessa/gerencia o VPS pessoal via SSH (credenciais ficam **fora** do repo, na memória). |
| `frontend-review` | `/frontend-review` | Revisor de front-end/UX agnóstico: screenshots multi-viewport + crítica de espaçamento/responsividade + review de código + a11y, contra uma `rubric.md` versionada que melhora a cada uso. |
| `security-sweep` | `/security-sweep` | **Varredura de segurança agnóstica que ENCONTRA, TESTA ao vivo (dispara o ataque) e CORRIGE** — não só reporta. Cobre race conditions/TOCTOU, IDOR/autorização, enumeração, injeção, SSRF, upload, XSS, segredos, sessão/CSRF/step-up, crypto, exposição de dados, lógica financeira, OAuth/federada, trilha+anomalia de login e defaults seguros, contra uma `rubric.md` versionada que cresce. Use em "varredura de segurança"/"pentest"/"está seguro?" **e** ao fim de toda feature sensível. **Par da `app-essentials`** (uma constrói, a outra blinda). |
| `app-essentials` | `/app-essentials` | **Implementa** (não só audita) as funcionalidades que todo sistema web sério precisa: login e-mail+senha, **login Google (OAuth)**, verificação de e-mail, reset de senha, sessões/cookies seguros, página de conta + **exclusão (hard delete)**, **Termos+Privacidade versionados com aceite server-side**, **banner de cookies (LGPD) com scripts de 3º só sob consentimento**, trilha de login + alerta de novo dispositivo, e-mail transacional, i18n completa, step-up. Detecta o que falta, implementa adaptado à stack e **fecha com `security-sweep` (blinda) + `test-forge` (trava)**. Use em "adicione login com Google/termos/cookies/verificação de e-mail" e "o que falta pro app ficar sério?". |
| `test-forge` | `/test-forge` | **Cria e RODA testes úteis e confiáveis** (determinísticos, que podem falhar), priorizando o caminho crítico (dinheiro/auth/limites/parsers/idempotência) sobre % de cobertura; roda até passar e conserta o código se um teste acha bug. Use em "crie testes"/"o projeto não tem testes" **e** ao fim de toda feature crítica. |
| `code-standards` | `/code-standards` | Audita **padrões de código e boas práticas** (consistência com o próprio repo, camadas, erros, código morto, i18n completa, linter) e aplica correções seguras. Use em "está seguindo os padrões?"/"boas práticas". Complementa `/code-review` e `/simplify`. |
| `resume` | `/resume` | Resume um vídeo do YouTube a partir do link. |
| `sync-claude` | `/sync-claude` | Roda o `sync.sh` (padroniza a config desta máquina). |
| `google-play` | `/gplay` | Releases na Play Store via Play Developer API (service account): sobe AAB, tracks, promoção, rollout gradual, reviews e listing. Credenciais fora do repo (`~/.config/bobagi-google/`); setup único do operador em `google-play/SETUP.md`. |
| `admob` | `/admob` | Relatórios AdMob via API (receita, eCPM, impressões por dia/ad unit/país) + inventário de ad units. OAuth do dono da conta (setup único em `admob/SETUP.md`); escrita de inventário é restrita pelo Google (fallback manual documentado). |
| `google-ads` | `/gads` | Relatórios Google Ads via API (somente leitura): status/orçamento de campanha, gasto por dia, CPI, conversões por campanha/grupo. Exige developer token com acesso Básico aprovado (setup único em `google-ads/SETUP.md`); reusa o OAuth client do AdMob. |
| `cloudflare` | `/cloudflare` | Gerencia o DNS da zona `bobagi.space` no Cloudflare via API (`scripts/cf-dns.sh`): cria/altera/remove subdomínios (A/CNAME, proxied/DNS-only) e registros **TXT** (`txt`/`txt-del`, usados pela verificação do Search Console). DNS é SÓ no Cloudflare (Hostinger morto desde 2026-07-06). Credenciais fora do repo (`/root/.config/cloudflare/` no VPS, chmod 600); de outra máquina, executa via skill `vps` (SSH). |
| `google-search-console` | `/gsc` | **Cadastra e monitora sites no Google sem abrir o navegador**: verifica a posse sozinha (token DNS + TXT criado pela skill `cloudflare`), adiciona a propriedade, submete sitemap e lê desempenho de busca (cliques, impressões, CTR, posição, top queries/páginas). Reusa a service account do `google-play` — sem consent screen, sem senha do operador. Setup único em `google-search-console/SETUP.md`. |

### Plugins (marketplace `claude-plugins-official` = `anthropics/claude-plugins-official`)
| Plugin | Para que serve |
|--------|----------------|
| `frontend-design` | Direção visual/estética para **criar/redesenhar** UI nova (par do `frontend-review`). |
| `claude-md-management` | Auditar/melhorar `CLAUDE.md` + capturar aprendizados de sessão. |
| `security-guidance` | Review de segurança (injeção, XSS, SSRF, segredos hardcoded). |
| `feature-dev` | Workflow de feature com agents (explorer/architect/reviewer) para itens grandes. |
| `chrome-devtools-mcp` | Inspeção/automação de browser ao vivo (perf/network/console/a11y) — fornece o MCP `chrome-devtools`. |

> **Instalar plugin do jeito certo:** `claude plugin install <nome>@claude-plugins-official`. **Só marcar
> `enabledPlugins` no JSON NÃO instala** (`claude plugin list` fica vazio e a skill não carrega). Após
> instalar, **um restart limpo** carrega; `claude --resume` recarrega skills do repo mas **não** ativa
> plugins recém-instalados. O `sync.sh` já faz a instalação correta. Conferir com `claude plugin list`.

### MCP servers — ver [`config/mcp.md`](config/mcp.md)
| MCP | Origem | Numa máquina nova |
|-----|--------|-------------------|
| `claude.ai Gmail` | Remoto, conta claude.ai | Reconecta após login (nada a instalar). |
| `claude.ai Google Drive` | Remoto, conta claude.ai | Reconecta após login. |
| `chrome-devtools` | Plugin `chrome-devtools-mcp` (stdio, `npx`) | Vem com o plugin; conecta de fato só se houver Node + Chrome. |

### Settings & hooks (`config/`)
- **`config/settings.json`** → `~/.claude/settings.json`: `model: opus`, `effortLevel: xhigh`,
  `theme: dark`, `permissions.defaultMode: auto`, os 5 plugins habilitados e **três hooks**:
  `UserPromptSubmit` (skill-first), `SessionStart` (auto-pull) e `SessionEnd` (aviso de drift) —
  ver **Auto-sync** abaixo.
- **`config/skill-first-reminder.txt`** → `~/.claude/skill-first-reminder.txt`: payload JSON que o hook
  injeta a cada prompt (com `suppressOutput`), reforçando a política skill-first.
- **`config/CLAUDE.md`** → `~/.claude/CLAUDE.md`: instruções globais (carregam em todo projeto).

---

## 🔄 Auto-sync (hooks + `scripts/claude-sync.sh`)

Depois do primeiro `sync.sh`, manter as máquinas em dia é **automático** — sem precisar lembrar de
`git pull`/`push`. Cada hook em `config/settings.json` tem **uma** variante, `shell: bash` →
`claude-sync.sh`, que roda em **Linux, macOS e Windows** (lá via Git Bash, que o Claude Code já exige
para a ferramenta Bash). O caminho é sempre o portável `~/.claude/skills/scripts/...` (resolve via
symlink no Linux/Mac e via junction no Windows). A lógica:

> **Por que não há hook `shell: "powershell"`:** o Claude Code **não tem hook condicional por SO** — se a
> variante PowerShell está declarada, ele tenta rodá-la em toda sessão e, numa máquina sem `pwsh`
> (qualquer Linux/VPS), o resultado é um **erro visível de hook** na abertura (`SessionStart:startup hook
> error … no PowerShell executable was found`). Por isso o `settings.json` versionado declara só a
> variante bash. O **`claude-sync.ps1` continua mantido** (mesma semântica) para uso manual em Windows
> nativo — `/sync-claude` o documenta — e uma máquina Windows sem Git Bash pode declarar o hook
> PowerShell no **`settings.local.json`** dela, que não é versionado nem entra no check de drift.

- **`SessionStart` → `claude-sync.sh pull`**: a cada nova sessão dá `git pull --ff-only` no repo (skills
  e commands, por serem symlink, já ficam atuais na hora). Updates de config que estavam **em sync** são
  reaplicados em `~/.claude/` (com backup); edição local não-salva **nunca** é sobrescrita — vira aviso.
- **`SessionEnd` → `claude-sync.sh check`**: ao fim da sessão, se a config local divergir do repo, avisa
  para você rodar `/sync-claude --save`. **Nunca pusha sozinho** (o repo é público — push automático
  poderia vazar segredo).
- **`/sync-claude --save` → `claude-sync.sh save`**: caminho de **captura** (push). Copia
  `~/.claude/{CLAUDE.md,settings.json,skill-first-reminder.txt}` de volta pra `config/`, faz um **scan de
  segredos** (aborta se achar credencial) e então commita + pusha — propagando às outras máquinas.

Os hooks são **não-bloqueantes** (offline/sem-repo não atrapalha a sessão). Para revisar/desligar: `/hooks`.

---

## 🔁 Política SKILL-FIRST (todos os projetos)

A IA deve **procurar e usar skills/plugins antes** de fazer a tarefa na mão — são o primeiro lugar a
olhar, não o último. Imposto por: (1) `~/.claude/CLAUDE.md` com a regra + catálogo, e (2) o hook
`UserPromptSubmit` em `settings.json` que reinjeta o lembrete a cada prompt. Fluxo: olhar skills+plugins →
se alguma encaixar (mesmo parcial) invocar → só pular se nada for relevante → combinar quando fizer
sentido (`frontend-design` cria → `frontend-review` audita → `simplify`/`code-review` limpam → `verify` confirma).

---

## 🧱 Estrutura do repo

```
claude-skills/
├── sync.sh                     # bootstrap/sync idempotente (curl|bash ou /sync-claude)
├── scripts/
│   ├── claude-sync.sh          # auto-sync (bash: Linux/Mac/Git-Bash) — é o que os hooks chamam
│   └── claude-sync.ps1         # mesma lógica em PowerShell: uso MANUAL em Windows nativo (sem hook)
├── config/                     # config aplicada em ~/.claude/ pelo sync
│   ├── CLAUDE.md               #   -> ~/.claude/CLAUDE.md (instruções globais)
│   ├── settings.json           #   -> ~/.claude/settings.json (model/effort/theme/plugins/hook)
│   ├── skill-first-reminder.txt#   -> ~/.claude/skill-first-reminder.txt (payload do hook)
│   ├── plugins.txt             #   lista de plugins que o sync instala
│   └── mcp.md                  #   inventário/notas dos MCP servers
├── vps/SKILL.md                # skill: VPS via SSH
├── frontend-review/            # skill: review de front-end (3 pilares)
│   ├── SKILL.md
│   ├── rubric.md               #   checklist/expertise versionada que cresce
│   └── scripts/capture.mjs     #   screenshots multi-viewport (Puppeteer headless)
├── resume/SKILL.md             # skill: resumo de vídeo do YouTube
└── commands/                   # slash-commands espelho (-> ~/.claude/commands)
    ├── vps.md
    ├── frontend-review.md
    └── sync-claude.md
```

> Pastas sem `SKILL.md` (`config/`, `commands/`, `scripts/`) e arquivos soltos (`README.md`, `sync.sh`)
> são ignorados pelo loader de skills — por isso podem coexistir na raiz com as skills.

---

## ➕ Adicionar / mudar algo

- **Nova skill:** crie `claude-skills/<nome>/SKILL.md`, commite e dê push. O symlink já expõe na hora;
  rode `/sync-claude` nas outras máquinas (ou `git pull`).
- **Novo plugin:** adicione a linha `<nome>@claude-plugins-official` em `config/plugins.txt`, registre no
  catálogo (este README + `config/CLAUDE.md`) e dê push. `sync.sh` instala no próximo run.
- **Mudar settings/hook/CLAUDE.md:** edite em `config/`, commit, push — **ou** edite localmente
  (`~/.claude/...`) e rode **`/sync-claude --save`**, que copia de volta pro repo, escaneia segredos e
  pusha. As outras máquinas pegam sozinhas no próximo `SessionStart` (auto-pull).
- Depois de qualquer mudança, propague com **`/sync-claude`** (ou o `curl|bash`) e reinicie o Claude.

---

## 🖥️ Dependências por skill
- **`frontend-review`** (qualquer SO): Node 18+ e um Chromium para os screenshots.
  ```bash
  npm i -D puppeteer-core
  npx puppeteer browsers install chrome   # ou: npx playwright install chromium
  # alternativa: CHROME_PATH=/caminho/para/chrome se já tiver um Chrome instalado.
  ```
- **`vps`** (qualquer SO): `sshpass`+`git` (Linux/Mac) ou PuTTY (`plink`/`pscp`) no Windows; as
  credenciais ficam em `~/.claude/projects/<projeto>/memory/vps_bobagi.md` (**fora** do repo).
- **`chrome-devtools-mcp`** (plugin): Node/npx + Chrome para o MCP conectar.

### Windows (symlink manual, se preferir não usar o sync.sh)
```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\skills","$env:USERPROFILE\.claude\commands" -ErrorAction SilentlyContinue
cmd /c mklink /J "$env:USERPROFILE\.claude\skills"   "C:\caminho\claude-skills"
cmd /c mklink /J "$env:USERPROFILE\.claude\commands" "C:\caminho\claude-skills\commands"
```
(No Linux/Mac o `sync.sh` já cria os symlinks equivalentes.)
