---
name: frontend-review
description: Avalia o front-end/UX de uma página ou app rodando, de forma agnóstica ao projeto. Tira screenshots em vários viewports e critica padding/espaçamento/responsividade/alinhamento + faz review do código de front e auditoria de a11y/consistência, tudo contra uma rubric versionada que melhora a cada uso. Use quando o usuário pedir para avaliar/revisar a UI, o front-end, o layout, a responsividade ou "o que um usuário perceberia" numa página.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, WebFetch
---

# frontend-review — especialista de front-end reutilizável

Um revisor de front-end **agnóstico a projeto** que age como um especialista que se aprimora.
Roda três pilares e entrega um relatório priorizado; depois atualiza a própria `rubric.md`.

A inteligência mora em **`rubric.md`** (a checklist que cresce). Leia-a sempre antes de revisar.

## Quando usar
Usuário pediu para "avaliar o front", "revisar a UI/layout", "ver paddings/espaçamentos errados",
"checar responsividade", "ver o que o usuário percebe" — em **qualquer** projeto. `$ARGUMENTS`
costuma ser a URL alvo (ou um caminho de projeto / "este projeto").

## Inputs e resolução do alvo
1. **URL alvo** — uma URL pública/rodando (ex.: `https://app.exemplo.com`), OU subir o dev server
   local do projeto e usar `http://localhost:<porta>`, OU servir o build estático. Prefira a URL que
   o usuário deu; se não houver, descubra a porta de dev no `package.json`/compose e suba.
2. **Repo do front** — localize o código (`apps/web`, `frontend/`, `src/`, etc.) para os pilares 2 e 3.
3. **Auth** (se o miolo está atrás de login): peça ao usuário **como** autenticar —
   (a) ele fornece um cookie de sessão / login de teste, (b) você cria conta via signup, ou
   (c) só páginas públicas. Nunca invente credenciais. **Não** ecoe nem comite senha/cookie.
4. **Rotas** — liste as telas que importam (home, login, dashboard, conta, modais, estados vazios).
   Em SPA com hash router, use rotas tipo `#/account`.

## Pilar 1 — Visual (screenshots + crítica)
Use o motor `scripts/capture.mjs` (Puppeteer headless; resolve Chrome e `puppeteer-core` sozinho via
caches conhecidos — veja "Setup" abaixo). Capture cada rota em vários viewports.

```bash
node "$SKILL_DIR/scripts/capture.mjs" \
  --base "<URL>" --out "<OUT_DIR>" \
  --viewports 390x844,768x1024,1280x900,1440x900 \
  --routes "/:home,#/login:login,#/account:account" \
  [--cookie "<name>=<value>"] [--cookie-domain <host>] --wait 1400
```
Para áreas autenticadas, obtenha o cookie de sessão **fora** do browser (ex.: `curl` no endpoint de
login com as credenciais que o usuário passou) e injete via `--cookie`. A senha não entra em arquivo
nem em log.

Para abas/sub-abas/modais/formulários (SPA), use `--scenarios <json>`: uma lista de
`[{label, url?, viewport?, actions?, full?}]`, onde `actions` aceita `{clickText|click|fill|press|wait}`.
Assim você captura o app inteiro (Trade/Connection/B3, sub-abas, editor, modais), não só a rota default.
`--scenarios-only true` pula a grade rota×viewport. `--fold true` adiciona o shot above-the-fold;
`--scale 2` para detalhe nítido de padding.

Depois **leia cada PNG** (ferramenta Read enxerga imagens) e critique contra o Pilar 1 da `rubric.md`.
Cruze os viewports para achar bugs de responsividade. Use os `signals` do `manifest.json` como pistas
(overflow horizontal, elementos fora da tela, alt faltando, controles sem nome, alvos pequenos, erros
de console) — sempre **confirmando na imagem**.

## Pilar 2 — Código do front
Identifique a stack (Svelte/React/Vue/etc.). Leia os tokens de design (variáveis CSS/tema), os
componentes e os estilos. Aplique o Pilar 2 da `rubric.md`: px mágicos vs tokens, unidades
responsivas, breakpoints consistentes, estilo duplicado, estados (loading/empty/error), i18n
completo (toda língua tem a chave). Mapeie cada achado para `arquivo:linha`. Opcional: rodar o
`/code-review` do repo para bugs de correção.

**Sempre** verifique responsividade **no código** (não só nos screenshots): dê grep nas linhas
`display:flex`/`display:grid` com vários itens e confirme que reflowam (`flex-wrap`, `min-width:0` ou
media query) — uma linha flex sem `flex-wrap` com filhos de largura fixa estoura no celular mesmo que
o dado atual caiba; e procure larguras `px` fixas que não cabem num telefone. E **sempre** confira o
ritmo vertical: gaps entre blocos empilhados devem ser uniformes (cuidado com margens que colapsam/se
somam entre um componente e o vizinho).

## Pilar 3 — UX / a11y / consistência
Aplique o Pilar 3 da `rubric.md`: HTML semântico, foco/teclado, nomes acessíveis, alt, contraste,
tap targets, formulários, consistência (largura de cards, posição de sub-tabs, padrões de tabela),
i18n por locale. Os `signals` automáticos do Pilar 1 já apontam muitos destes.

## Relatório (entregável)
Gere **um** Markdown em `<projeto>/.claude/frontend-review/<timestamp>/report.md` (screenshots ao
lado). Estrutura:
- **Resumo** — 3–6 linhas + contagem por severidade.
- **Top correções** — lista priorizada P0→P3 (o que mexer primeiro).
- **Achados por pilar** — cada um com severidade, onde (rota+viewport+arquivo de screenshot e/ou
  `arquivo:linha`), por que lê errado, e a correção concreta (em tokens, não px, quando houver escala).
- **Pontos fortes** — o que já está bom (para não regredir).
Apresente o resumo + top correções no chat; aponte o caminho do relatório completo.

## Setup de dependências (uma vez por máquina)
- **Node 18+**. **Chromium**: o script acha o do Playwright/Puppeteer em cache, ou setes `CHROME_PATH`.
- **puppeteer-core**: o script resolve de `node_modules` local, de `PUPPETEER_DIR`, ou do cache `~/.npm/_npx`.
  Se não houver, instale: `npm i -D puppeteer-core` (no projeto ou na pasta da skill). O Chromium pode vir
  via `npx playwright install chromium` ou `npx puppeteer browsers install chrome`.
- `$SKILL_DIR` = a pasta desta skill (onde está este SKILL.md).

## Auto-aprimoramento (rode SEMPRE ao final)
Esta skill melhora num lugar só e propaga pra todos os projetos. Ao terminar a review:
1. Reflita: que **lição geral** (não específica do projeto) este review ensinou? Que check faltava?
2. Edite `rubric.md`: acrescente uma linha datada no **Learnings log** e, se for recorrente, promova
   para a checklist do pilar certo. Mantenha tudo **agnóstico** (nada do projeto X).
3. **Commit automático** (modo escolhido pelo dono): na pasta da skill,
   `git add -A && git commit -m "frontend-review: <lição> (via <projeto>)" && git push`.
   O relatório e os screenshots ficam no projeto revisado (não no repo da skill).
Nunca comite segredos, cookies, senhas ou screenshots de dados sensíveis no repo da skill.
