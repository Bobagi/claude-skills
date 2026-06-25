# claude-skills

Skills e configuracoes pessoais do Claude Code ([@Bobagi](https://github.com/Bobagi)).

## O que sao skills

Skills sao slash commands customizados para o Claude Code. Ficam em `~/.claude/skills/<nome>/SKILL.md` e sao invocadas com `/<nome>`.

## Skills disponiveis

| Skill | Comando | Descricao |
|-------|---------|-----------|
| vps | `/vps` | Acessa e gerencia o VPS pessoal via SSH |
| frontend-review | `/frontend-review` | Revisor de front-end/UX agnostico: screenshots multi-viewport + critica de padding/espacamento/responsividade, review de codigo do front e auditoria de a11y/consistencia. Rubric versionada que melhora a cada uso. |

<<<<<<< Updated upstream
=======
## Politica SKILL-FIRST (todos os projetos)

Em **qualquer** projeto desta maquina, a IA deve **procurar e usar skills/plugins antes**
de fazer a tarefa na mao. Skills sao o primeiro lugar a olhar, nao o ultimo. Isso e imposto por:

- **`~/.claude/CLAUDE.md`** (carrega em todo projeto) com a regra skill-first + o catalogo.
- **Hook `UserPromptSubmit`** em `~/.claude/settings.json` que roda
  `cat ~/.claude/skill-first-reminder.txt` e reinjeta o lembrete a cada prompt
  (saida em JSON com `suppressOutput`, entao vai pro contexto sem poluir o transcript).
  Revisar/desligar: comando `/hooks`.

Fluxo: olhar a lista de skills + plugins -> se alguma encaixar (mesmo parcial) invocar ->
so pular se nada for relevante -> combinar quando fizer sentido
(ex.: `frontend-design` cria -> `frontend-review` audita -> `simplify`/`code-review` limpam -> `verify` confirma).

## Plugins instalados (marketplace `claude-plugins-official`)

| Plugin | Para que serve | Nota |
|--------|----------------|------|
| `frontend-design` | Direcao visual/estetica para **criar/redesenhar** UI nova | Par do `frontend-review`. Em app com design system travado, restrinja aos tokens; solte em telas novas |
| `claude-md-management` | Auditar/melhorar `CLAUDE.md` + capturar aprendizados | Bom quando um `CLAUDE.md` cresce/desatualiza |
| `security-guidance` | Review de seguranca (injecao, XSS, SSRF, segredos) | Relevante em apps que tocam dinheiro/credenciais |
| `feature-dev` | Workflow de feature com agents (explorer/architect/reviewer) | Para itens grandes de backlog (billing, websockets, etc.) |

> **Instalar plugin do jeito certo:** `claude plugin install <nome>@claude-plugins-official` (ou o menu
> `/plugin`). **Só marcar `enabledPlugins` no JSON NAO instala** — `claude plugin list` fica "No plugins
> installed" e a skill do plugin nao carrega. Apos instalar, **um restart limpo** (`claude` novo) carrega;
> **`claude --resume` recarrega as skills do repo (`~/.claude/skills`) mas NAO ativa plugins recem-instalados.**
> Conferir com `claude plugin list`.

>>>>>>> Stashed changes
## Setup em uma maquina nova

### 1. Clonar o repositorio no lugar certo

```bash
git clone https://github.com/Bobagi/claude-skills.git D:\projetos\claude-skills
```

### 2. Criar junction para o Claude Code encontrar as skills

Abra o PowerShell e rode:

```powershell
# Remover pastas vazias se existirem
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\skills" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:USERPROFILE\.claude\commands" -ErrorAction SilentlyContinue

# Criar junctions (skills ficam na RAIZ do repo: cada pasta <nome>/SKILL.md e uma skill)
cmd /c mklink /J "$env:USERPROFILE\.claude\skills" "D:\projetos\claude-skills"
cmd /c mklink /J "$env:USERPROFILE\.claude\commands" "D:\projetos\claude-skills\commands"
```

> No Linux/Mac, equivalente: `ln -s /caminho/claude-skills ~/.claude/skills` e
> `ln -s /caminho/claude-skills/commands ~/.claude/commands` (ou symlink por skill).
> Pastas sem `SKILL.md` (como `commands/`, `README.md`) sao ignoradas pelo loader de skills.

### 3. Instalar dependencias

**Windows:**
```powershell
winget install PuTTY.PuTTY
winget install GitHub.cli
```

**Linux/Mac:**
```bash
sudo apt install sshpass git   # Ubuntu/Debian
brew install sshpass gh        # macOS
```

**Para o `frontend-review`** (qualquer SO): Node 18+ e um Chromium para os screenshots.
```bash
npm i -D puppeteer-core              # wrapper do browser (pode ser por-projeto ou na pasta da skill)
npx puppeteer browsers install chrome # baixa um Chromium; ou: npx playwright install chromium
# Alternativa: aponte CHROME_PATH=/caminho/para/chrome se ja tiver um Chrome instalado.
```
O `scripts/capture.mjs` acha o Chromium em caches conhecidos (Playwright/Puppeteer) ou via `CHROME_PATH`.

### 4. Configurar credenciais do VPS

Crie o arquivo de memoria em `~/.claude/projects/<projeto>/memory/vps_bobagi.md` com as credenciais de acesso. Esse arquivo nao fica no repositorio por seguranca.

## Como adicionar uma nova skill

```bash
mkdir D:\projetos\claude-skills\minha-skill
# criar o arquivo SKILL.md dentro da pasta

cd D:\projetos\claude-skills
git add .
git commit -m "Add minha-skill"
git push
```

## Usar o `frontend-review` em qualquer projeto

A skill e **agnostica a projeto** e fica neste repo compartilhado — entao em qualquer
maquina/projeto onde os junctions/symlinks acima existem, ela ja esta disponivel. O fluxo:

1. Em qualquer projeto, peca: **"avalie o front"** / **"revise a UI"** / `/frontend-review <URL>`.
2. Informe o **alvo**: uma URL rodando (prod ou `localhost:<porta>` do dev server).
3. Se houver area logada, **voce** decide como autenticar naquele momento — fornece um login/cookie
   de teste, manda criar conta via signup, ou pede so as paginas publicas. **As credenciais sao usadas
   so naquela sessao e nunca ficam salvas** (nada de credencial vai pra este repo ou pra memoria).
4. A skill roda os 3 pilares, gera o relatorio em `<projeto>/.claude/frontend-review/<timestamp>/` e,
   ao final, **melhora a propria `rubric.md`** e da push aqui — entao a proxima review (em qualquer
   projeto) ja vem mais afiada. Voce melhora num lugar so e propaga pra todos.

A "expertise" mora em **`frontend-review/rubric.md`** (a checklist que cresce). Edite-a a mao quando
quiser ensinar uma preferencia sua (ex.: "sempre cheque X"); e versionada como o resto.

## Estrutura

```
claude-skills/
├── vps/
│   └── SKILL.md            # Skill: gerenciar o VPS pessoal via SSH
├── frontend-review/
│   ├── SKILL.md            # Skill: revisor de front-end agnostico (3 pilares)
│   ├── rubric.md           # Checklist/expertise versionada que cresce a cada uso
│   └── scripts/
│       └── capture.mjs     # Motor de screenshots multi-viewport (Puppeteer headless)
└── commands/
    ├── vps.md              # Slash-command espelho de /vps
    └── frontend-review.md  # Slash-command espelho de /frontend-review
```
