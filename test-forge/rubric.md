# test-forge — rubric (a checklist que cresce)

**É** a expertise da skill. **Agnóstica a projeto.** Lida antes de escrever testes; a auto-melhora
acrescenta lições **gerais** ao Learnings log no fim.

## O que torna um teste ÚTIL (todo teste escrito passa por aqui)
- [ ] **Pode falhar.** Se você quebrar a regra que ele cobre (inverter o `<`, remover o guard), ele fica
  vermelho. Se não, é teatro — reescreva. (Mentalidade de mutação.)
- [ ] **Testa comportamento, não implementação.** Verifica efeito observável (retorno, estado no DB, erro
  tipado, ordem colocada no fake), não que um método interno foi chamado.
- [ ] **Determinístico.** Sem `sleep`/tempo real/aleatório não-injetado/rede real/ordem entre testes.
  Tempo e aleatoriedade são **injetados**; I/O externo é **fake/stub**.
- [ ] **Isolado.** Monta o próprio estado, limpa ao fim; DB efêmero (container ou transação+rollback),
  nunca prod. Um teste não depende de outro.
- [ ] **Asserts significativos.** Não `assert notThrow`; compare o valor/estado/erro esperado.
- [ ] **Cobre happy + borda + falha.** O ramo de erro é onde o bug vive.
- [ ] **Rápido e legível.** Table-driven para variações; nome descreve o comportamento.

## O que PRIORIZAR (ordem de valor — não persiga % de cobertura)
1. **Caminho do dinheiro:** compra/venda, cálculo de saldo/lucro, aplicação de limites/quotas, cobrança,
   conversão de moeda/unidade, arredondamento (tick/step/minNotional). Um erro aqui custa dinheiro real.
2. **Auth/autz:** gates (email verificado, termos, step-up), escopo por usuário (IDOR), papéis.
3. **Invariantes:** idempotência (ex.: "1 compra por dia/símbolo"), atomicidade de limite ("só 1 passa"
   sob concorrência), monotonia/sinais (sem negativo onde não pode).
4. **Parsers/validação:** tamanho (casado à coluna), formato, unicode, bordas, entrada maliciosa.
5. **Regras de negócio** específicas do domínio.
Pule: getters/setters triviais, o que o compilador/framework já garante, UI puramente visual (isso é da
`frontend-review`).

## Anti-padrões (recuse-os)
- Testar o mock/stub em vez do código (asserção sobre o fake, não sobre o efeito).
- Over-mocking a ponto de o teste não exercitar lógica real nenhuma.
- Snapshot gigante como única asserção (quebra por qualquer mudança, não diz o quê).
- `sleep(n)` para "esperar" uma corrida — use sincronização determinística ou teste a unidade pura.
- Teste que depende de rede/relógio/fuso/locale da máquina.
- "Ajustar o teste" para passar quando ele achou um bug de verdade.
- Perseguir 100% de cobertura escrevendo testes triviais — cobertura alta com testes que não podem falhar
  é pior que menos testes bons (dá falsa confiança).

## Como rodar por stack (preencha o comando REAL do repo no relatório)
- **Go:** `go test ./...` (com `-race` para concorrência!). Se o Go não está no PATH, rode via container
  (ex.: `docker run --rm -v "$PWD":/app -w /app golang:<v> sh -c "go test -race ./..."`). Table-driven é
  idiomático. Para DB: `sqlmock`/container efêmero; para tempo: injete um relógio.
- **Node/TS:** vitest/jest (`pnpm test`/`npm test`); descubra via `package.json`. Fake timers do runner;
  `msw`/nock para HTTP; nunca rede real.
- **Python:** `pytest`; fixtures para isolamento; `freezegun` para tempo; `responses`/`respx` para HTTP.
- **Concorrência (race/atomicidade):** dispare N operações concorrentes contra o alvo e afirme o invariante
  (só 1 passou, saldo consistente) — em Go use goroutines + `-race`; em app rodando, N requests paralelos.

## Learnings log (append-only, geral)
- **2026-07-18 (via CoinHub — mutation check que COMPILA, não build-fail):** Ao mutar um guard cuja quebra
  deixaria um símbolo **não-usado** (ex.: neutralizar `if host != H && !strings.HasSuffix(host, "."+H) {`
  removendo o corpo torna `H`/`strings` órfãos → em Go isso é **erro de compilação**, não teste vermelho).
  Um build-fail ainda prova que a linha é load-bearing, mas NÃO prova que o **teste** pega a regressão (o
  compilador pegou, não o teste). Para um mutation check limpo, **inverta a DECISÃO mantendo os símbolos
  referenciados**: aqui, anexar `&& false` à condição de rejeição (`... && false {`) faz o bloco nunca
  executar → hosts hostis são ACEITOS → os testes de SSRF ficam vermelhos com asserção significativa
  ("aceitou input hostil"). Regra geral: a melhor mutação é a que **compila e muda o comportamento**, não a
  que apaga código. Padrão análogo em outras stacks: troque `x < limite` por `x <= limite` / `true`, não
  delete a variável. (Fecha o caminho crítico da importação: parser anti-SSRF + matemática de cooldown 30min/
  2min + flatten com drop de ticker vazio — 3 mutações, 3 vermelhos; Go via container com `CGO_ENABLED=1` +
  `apk add gcc musl-dev` quando quiser `-race`, senão `-race` reclama "requires cgo".)
- **2026-07-17 (via investidor10):** Testar um parser **SSRF-safe do tipo "extraia um id de uma URL não
  confiável e depois SEMPRE bata num host fixo"** (aqui: `parse_wallet_id` → só o id numérico flui adiante,
  toda request é montada contra `API_BASE`). Dois testes fecham a propriedade sem rede: (1) a lista de
  entradas hostis DEVE incluir o **truque de sufixo** `https://investidor10.com.br.evil.com/...` (não só um
  host claramente estrangeiro) — a validação certa é `host == "investidor10.com.br" or
  host.endswith(".investidor10.com.br")`, e o sufixo-trick só é rejeitado porque NÃO termina em
  `.investidor10.com.br` (termina em `.evil.com`); um `in`/`startswith` ingênuo passaria; (2) um teste que
  afirma `parse(...)` retorna `int` + que a constante `API_BASE` é o host esperado trava o "nunca contata
  host arbitrário" mesmo offline. Mutation check revelador: trocar o guard de host por `if False:` — as
  entradas hostis (metadata SSRF + sufixo-trick) devem ficar vermelhas. Bônus: para JSON de API externa com
  **campos que variam por tipo** (Tesouro usa `avg_price_treasure`/`current_price_treasure`, ações usam
  `avg_price`/`current_price`), o teste do normalizador tem que cobrir CADA forma; a mutação "remover o
  fallback `... or _to_float(row.get('avg_price_treasure'))`" prova que o teste do Tesouro pega (avg_price→None).


- **2026-07-15 (via CoinHub):** Testar código **fuso-dependente por design** (ex.: converter uma DATA local
  YYYY-MM-DD nas fronteiras do dia — início/fim — para um instante UTC) de forma determinística: **pine o
  fuso** com `process.env.TZ` no TOPO do script (antes de qualquer uso de `Date`), e **escolha um fuso
  NÃO-UTC** (ex.: `America/Sao_Paulo`, UTC-3). Sob UTC a meia-noite local == meia-noite UTC e o teste NÃO
  distingue "construiu em hora local" de "construiu em UTC"; sob UTC-3 a meia-noite local vira 03:00Z, então
  a asserção prova as DUAS coisas de uma vez (a matemática início/fim do dia E que usa hora local — uma
  mutação para `Date.UTC(...)` daria 00:00Z e ficaria vermelha). Regra geral: para lógica dependente de
  fuso/locale, não FUJA do fuso (rubric "sem depender de fuso") — **fixe um fuso específico e revelador** e
  asserte o valor exato. 2 mutation-checks que fecharam o valor: inverter fim-do-dia→início-do-dia (script
  node vermelho) e `UnixNano→UnixMilli` no codec do cursor keyset (round-trip perde os microssegundos → o
  teste de round-trip com nanos .123456000 fica vermelho). LIÇÃO META p/ **paginação keyset**: o teste do
  codec do cursor DEVE usar um timestamp com precisão de sub-segundo (microssegundo) no valor esperado,
  senão um downgrade de precisão (nano→milli) passa silencioso e PULA/REPETE linhas na fronteira em produção.

- **2026-07-07 (via CoinHub):** Ao fazer o **mutation check** (inverter uma regra pra provar que o teste
  fica vermelho), **NUNCA reverta a mutação com `git checkout <arquivo>`** se o arquivo tem mudanças
  **não-commitadas** — o checkout apaga TUDO que não foi commitado (as extrações/funções novas junto).
  Reverta a mutação com o inverso exato (sed de volta, ou re-Edit da linha), ou faça a mutação numa CÓPIA.
  Melhor ainda: rode o mutation check só DEPOIS de commitar, ou num `cp` do arquivo. (Um `git checkout`
  mascarado por `|| true` falhou silenciosamente e deixou a mutação `>` no lugar do `<=` correto — só
  não foi pra produção porque reconferi a linha.)
- **2026-07-06 (via CoinHub, origem da skill):** Projeto de money-path com **zero testes** no núcleo de
  ordens era o maior risco pré-lançamento. Lições: (1) priorize o caminho do dinheiro e os **invariantes**
  (idempotência da compra diária, atomicidade do limite sob concorrência, conversão de moeda que nunca
  soma unidades diferentes) — é onde regressão vira prejuízo; (2) para lógica pura (conversão, clamp,
  resolução de cotação) escreva **testes de unidade table-driven** sem DB/rede — rápidos e à prova de
  flaky; (3) rode Go com **`-race`** para provar a atomicidade de fixes de concorrência; (4) um teste
  que expõe um bug real ⇒ conserte o código, nunca o teste.
- **2026-07-10 (via CoinHub):** Para testar **sweeps janelados/paginados de API externa** (ex.: histórico
  em janelas de 30/90 dias, paginação por fromId), faça o fake HTTP devolver as fixtures **só quando a
  janela/página pedida as contém** (comparando start/end/fromId da query) — assim o teste exercita a
  lógica de janelamento/paginação em si, não só o parse do JSON. Grave também os parâmetros recebidos
  pelo fake (ex.: lista de fromId) e afirme sobre eles: prova que a 2ª página foi pedida do ponto certo.

- **2026-07-16 (via warframe-farm-helper):** Em **Node 22.23**, `node --test test/` (diretório como
  argumento) falha com `MODULE_NOT_FOUND: Cannot find module '/app/test'` — o runner tenta carregar o
  caminho como entrypoint CJS. Use **`node --test` sem argumentos** (descobre `./test/**/*.test.js`
  sozinho) ou um glob explícito. Sintoma enganoso: parece que o diretório não está na imagem Docker
  (fomos conferir o COPY à toa). Bônus da sessão: quando módulos leem `process.env` no **load** (const
  no topo), o teste PRECISA setar o env ANTES do `require` — em `node --test` cada arquivo é um processo
  novo, então setar `process.env.X` no topo do arquivo de teste funciona e isola por arquivo.

- **2026-07-16 (via warframe-farm-helper — a lição do git checkout mordeu DE NOVO):** Reincidência da lição
  de 2026-07-07: rodei `git checkout server/search.js` pra reverter uma mutação, mas o arquivo tinha
  melhorias NÃO-commitadas (um filtro novo + um export) → o checkout apagou tudo e voltou pro último commit,
  que era a versão ANTIGA. Sintoma: 2 testes que passavam voltaram a falhar depois do "revert". Mitigação
  reforçada: **antes de fazer mutation-check, COMMITE** (ou copie o arquivo pra /tmp e mute a cópia, ou
  reverta a mutação com o `sed` inverso exato — nunca `git checkout` de arquivo com trabalho pendente). Um
  `git status` antes do checkout teria mostrado o arquivo modificado. Segunda lição, geral: para testar
  "componente X é ingrediente (não vira sub-doc de busca)", a distinção robusta NÃO é "tem drop de relíquia"
  (exclui peças de warframe que dropam de boss) e sim **"o nome do componente é um item próprio no banco"**
  (Morphics/Orokin Cell são recursos avulsos) — com um **fallback de lista curada** para recursos que o
  dataset lista como componente mas não cataloga como item próprio (Orokin Cell/Morphics ficam num Misc não
  ingerido). Testar os dois lados: a peça vira sub-doc, o recurso avulso não.
