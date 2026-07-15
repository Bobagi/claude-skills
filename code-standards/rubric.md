# code-standards — rubric (a checklist que cresce)

**É** a expertise da skill. **Agnóstica.** A régua nº1 é a **consistência com o próprio projeto**; boas
práticas universais vêm depois. Lida antes de auditar.

## 0. Ferramentas objetivas primeiro (rode e capture)
- [ ] Formatter/linter oficial roda **limpo**: `gofmt -l` + `go vet` (+ `golangci-lint` se houver);
  `eslint`/`prettier --check`; `ruff`/`black --check`; `svelte-check`/`tsc --noEmit`. O que ele aponta é
  padrão objetivo — corrija.

## 1. Consistência com o projeto (o mais importante)
- [ ] Nomes seguem a convenção local (idioma dos identificadores, casing, prefixos) — mesmo que o chat
  seja em outra língua, os identificadores seguem o padrão do repo.
- [ ] Estrutura/camadas seguem o padrão vigente (ex.: handler → service → repository; nada de SQL no
  handler se o resto usa repository; nada de regra de negócio no repository).
- [ ] Estilo de erro consistente (erros tipados/sentinela vs strings; wrap com contexto; mesma forma de
  responder erro no HTTP).
- [ ] Novos textos de UI vão pela camada de i18n, com **todas** as línguas preenchidas (nenhuma chave
  faltando num dicionário).
- [ ] Tokens de design/config centralizados usados em vez de literais repetidos.

## 2. Boas práticas universais
- [ ] **Tratamento de erro:** nada de erro engolido silenciosamente; caminho de erro tratado ou propagado
  com contexto; sem `panic` em fluxo normal; recursos fechados (`defer close`).
- [ ] **Sem números/strings mágicos** repetidos — extrair para constante nomeada.
- [ ] **Sem código morto** (funções/vars/imports sem uso — confirmar com grep de chamadores em todo o
  repo antes de remover).
- [ ] **Funções coesas** (uma responsabilidade; evitar monstros de 200 linhas com muitos níveis de
  aninhamento) — só recomende refactor grande, não aplique sozinho.
- [ ] **Higiene de log:** nível adequado, sem PII/segredo, sem spam em loop quente.
- [ ] **Concorrência:** estado compartilhado protegido; sem race (rode `-race`/checagem quando aplicável).
- [ ] **Dependências:** sem libs abandonadas/duplicadas; versões fixadas; nada de dep pesada para algo
  trivial.
- [ ] **Comentários** explicam o *porquê* (restrição/decisão), não o óbvio; sem comentário morto/enganoso.
- [ ] **Documentação:** README/CLAUDE.md refletem o estado atual quando o projeto os mantém.
- [ ] **Consistência de API:** mesma forma de request/response, paginação, nomes de campo entre endpoints.

## 3. O que NÃO é escopo (mande pra skill certa)
Bugs de correção → `/code-review`. Simplificação pura → `/simplify`. Segurança → `security-sweep`.
Testes → `test-forge`. UI/UX → `frontend-review`.

## Learnings log (append-only, geral)
- **2026-07-06 (via CoinHub, origem da skill):** A régua mais valiosa é a **consistência com o próprio
  projeto** (camadas handler→service→repository, erros tipados `*UserFacingError`, i18n com en/pt/es
  sempre completos, tokens de CSS em vez de px mágico). Rodar o linter/`svelte-check`/`go vet` do repo
  primeiro dá o padrão objetivo de graça; código morto só some após grep de chamadores no repo inteiro.
- **2026-07-15 (via todo):** Higiene de deps num front **sem bundler (libs via CDN)** engana em dois
  sentidos, então SEMPRE cruze `require()`/`import` de módulos bare vs `package.json` **E leia o
  Dockerfile/CI**: (1) libs que só entram por CDN em runtime (ex.: `react`/`react-dom` via unpkg)
  aparecem **declaradas-mas-sem-uso** pelo Node — enganoso, sugerem um build que não existe; (2) uma lib
  `require()`d de verdade pelo servidor (ex.: `stripe`) pode estar **faltando** no `package.json` porque
  um `RUN npm install X` ad-hoc no Dockerfile a instala — aí `npm install` puro (fora do Docker) gera app
  quebrado, e `npm ci` nem roda. O Dockerfile/entrypoint costuma esconder tanto deps não-declaradas
  quanto um **segundo sistema de migrations** (SQL aplicado por psql no boot) que torna um `runMigrations()`
  JS **morto**. Footgun recorrente: script `"test": "docker compose down -v && …"` — o `-v` **apaga o
  volume do banco**; rodar `npm test` destrói dados. Sinalize e neutralize (placeholder não-destrutivo).
