# CLAUDE.md - global (Gustavo Perin / Bobagi)

Carrega em **todos os projetos**. Regras de máquina/projeto ficam em `/root/CLAUDE.md`, `/opt/CLAUDE.md` e no
`CLAUDE.md` de cada repo; aqui só a política transversal. **Fonte de verdade:** `Bobagi/claude-skills`
(`config/CLAUDE.md`), instalado como `~/.claude/CLAUDE.md` pelo `sync.sh`. **Detalhe de cada skill, plugins,
MCP e infra pessoal: `~/.claude/skills/config/REFERENCIA.md`** (ler quando o assunto aparecer). Mantenha este
arquivo curto: detalhe novo vai para a REFERENCIA, não para cá.

## ★★ Proibido em dash e en dash (U+2014, U+2013), todo projeto

Nunca em nada que você produzir (UI, copy, erros, comentários, docs, `CLAUDE.md`, commits, PRs, chat; pedido
de 2026-07-26). Use vírgula, dois-pontos, parênteses, ponto ou hífen simples; separador de título: `·`. Ao editar
arquivo que já tenha, troque de passagem. Um hook `PostToolUse` (`~/.claude/no-em-dash-check.sh`) barra o arquivo
gravado com código 2. Ao varrer projeto: conteúdo derivado (banco, build, índice) guarda cópia, reprocessar e
conferir a página renderizada. Verificar: `grep -rnP "\x{2014}" <dir>`.

## ★★ Não rebaixe escopo para "limite conhecido"

Entregar parte e chamar o resto de "limitação honesta" é escopo cortado sem autorização. "Adicione o idioma X"
inclui o conteúdo escrito à mão; "faça o site funcionar" inclui a página de erro; "cadastre no Google" inclui o
sitemap. Só é legítimo se for **tecnicamente impossível** ou **decisão de produto do dono**, dito com a medição na
mão. "É muito trabalho" não é motivo: faça, e se não couber na sessão, diga quanto falta e continue.

## ★★ Pesquise na internet sempre

Todo problema (erro, crash, travamento, "fica carregando", log estranho, regressão) e toda decisão que depende de
informação que muda (versão, preço, limite, API, política de loja) começa com `WebSearch` **na primeira rodada**,
em paralelo com os logs locais, sem esperar o Gustavo mandar (cobrado em 2026-10-23). Carregue `WebSearch`/`WebFetch`
pelo `ToolSearch` se estiverem diferidas; sintoma + produto + versão exata, erro literal, release notes/issue
tracker; `WebFetch` nas fontes de staff/mantenedor; pesquise de novo se não resolver; cite as fontes. Skill
`web-research`. Só pule se o problema é 100% do código do projeto e o stack trace aponta a linha.

## ★★ Assuma a máquina: clique você mesmo em janelas de app (2026-11-04)

Janela de app nativo esperando escolha (instalador, "Allow"/"Continue"): clique você. Ordem: (1) `computer-use`;
(2) AppleScript/System Events pelo Bash (`get entire contents of window 1`, achar o botão, `click button N of group
M of window "<nome>"`, conferir que mudou); (3) só então peça a ele, dizendo qual opção e por quê. Nunca digite
senha de login/admin, aceite termos ou conceda permissão de sistema sem ele pedir aquilo.

## ★★ claude-skills: sempre commit + push (2026-11-04)

Toda alteração no repo `Bobagi/claude-skills` termina com commit + push na hora, sem perguntar. Antes de editar,
`git pull --ff-only`; depois copie `config/CLAUDE.md` para `~/.claude/CLAUDE.md` (ou `sync.sh`). Adicione só os
arquivos que mexeu (nada de `git add -A`).

## ★★ Todo projeto vai para o GitHub (2026-11-05)

Projeto sem repositório: `gh repo create Bobagi/<nome> --source . --push`, sem perguntar, em qualquer máquina.
Público por padrão; privado só com segredo ou dado de terceiro. Trabalho terminado em repo existente: commit + push
na hora. `gh` deslogado: peça `! gh auth login` no começo. Publicar em loja (Steam, Play, Chrome Web Store) **não**
entra: isso é com o Gustavo.

## ★ Skill-first (todo pedido)

Antes de qualquer tarefa, olhe as skills nos `<system-reminder>`/ferramenta `Skill` e os plugins; se alguma
encaixar, mesmo parcialmente, **invoque-a** em vez de fazer ad-hoc. Combine quando fizer sentido (`frontend-design`
-> `frontend-review` -> `simplify`/`code-review` -> `security-sweep` -> `verify`). O hook `UserPromptSubmit`
(`~/.claude/skill-first-reminder.txt`) reinjeta isso a cada prompt.

## ★★ Segurança e testes sempre

Ao terminar feature nova/alterada que toque **auth, dinheiro, limites/quotas, permissões, input do usuário,
upload, fetch de URL server-side ou dados sensíveis**: rode `security-sweep` escopada nela antes de encerrar
(encontra, TESTA ao vivo e CORRIGE; um review estático já deixou passar uma race condition financeira real).
`/security-review` e o plugin `security-guidance` complementam. Junto: `test-forge` no caminho crítico e, em
feature grande, `code-standards` + `/code-review` + `/simplify`.

## Skills do repo (uma linha cada; detalhe na REFERENCIA)

- `frontend-review` revisar UI · `frontend-design` (plugin) criar UI nova
- `security-sweep` varredura que testa e corrige · `app-essentials` login/OAuth/termos/cookies/conta, fecha com sweep + test-forge
- `test-forge` cria e roda testes úteis · `code-standards` padrões e boas práticas
- `ai-delegate` tarefas braçais para IAs grátis (Ollama, Groq; Gemini treina: só código não sensível)
- `ghostwriter` todo texto publicado em nome do Gustavo (antes da 1ª palavra) · `linkedin` perfil via CDP
- `unity-mcp-skill` Unity Editor via MCP · `game-3d-assets` todo modelo 3D no orçamento de triângulos
- `game-audio` sons de jogo (CC0, análise, loop) · `game-visual-review` olhar a tela real antes de dizer pronto
- `web-research` pesquisa antes de diagnosticar · `store-promo-video` vídeo da ficha da loja
- `servidor-dev` delegar desenvolvimento ao Claude do servidor (`srv`) · `vps` servidor bobagi.space (VM `servidor` no Mac mini)
- `google-play` releases/reviews/ficha (produção só com confirmação) · `chrome-web-store` publicar extensão
- `admob` (+ AdSense só leitura) · `google-ads` só leitura · `google-search-console` cadastro, sitemap, SEO
- `cloudflare` DNS de bobagi.space (DNS **só** no Cloudflare; subdomínio novo pelo Tunnel `mac-mini`)
- `product-review` PM do portfolio (Artifact único) · `game-overlay` HWiNFO + RTSS · `resume` vídeo do YouTube

Regras que valem fora das skills:
- **Jogo**: sempre pesquisar online texturas PBR, shaders, efeitos prontos e modelos CC0 antes de fazer na mão (24/10).
- **Google (Play/AdMob/Ads)**: o que a API não cobre é feito pelo operador guiado; automação de navegador logado
  no Google **nunca na VPS** (último recurso: chrome-devtools-mcp na máquina dele, com ele presente).
- **Plugin**: instalar com `claude plugin install <nome>@claude-plugins-official` (marcar `enabledPlugins` não
  instala) e reiniciar limpo (`--resume` não ativa plugin novo).
- Skill/plugin novo: uma linha aqui, detalhe na REFERENCIA e no README.

## Infra pessoal

Servidor principal = VM `servidor` no Mac mini (VPS Hostinger aposentada). Oracle Cloud Always Free (tenancy
`Bobagi1`, VM `relay-terraria`): detalhes e armadilhas na REFERENCIA. IP, OCIDs e chaves nunca neste repo (público).

## Sincronizar numa máquina nova

`curl -fsSL https://raw.githubusercontent.com/Bobagi/claude-skills/main/sync.sh | bash` (ou pedir "sincronize meu
Claude com o repo github.com/Bobagi/claude-skills"; já com o repo: `/sync-claude`). Clona/atualiza, cria os
symlinks `~/.claude/skills` e `~/.claude/commands`, copia `CLAUDE.md`/`settings.json`/hooks (com backup) e instala
os plugins. Depois, reinicie o `claude`. Não toca em `settings.local.json`.
