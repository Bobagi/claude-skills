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
- **2026-08-02 (via app mobile - VERIFICAR ARTEFATO DE BUILD: cheque o TIMESTAMP antes de acreditar
  nele).** Ao validar que uma mudanca entrou no binario (manifesto, flag, recurso), o arquivo de saida
  pode ser de um build ANTIGO que ficou no diretorio: `build/.../app-release.aab` existia com data de
  duas semanas atras, o build novo ainda estava rodando, e eu conclui "a mudanca NAO entrou" a partir do
  artefato velho. O sintoma engana porque a checagem em si funciona: ela so olhou o arquivo errado.
  **Regra: antes de inspecionar um artefato de build, compare o mtime dele com o inicio do build** (ou
  apague o artefato antes de buildar). Vale para qualquer stack com diretorio de saida persistente
  (dist/, target/, build/, out/) - e principalmente quando o build roda em background, porque ai o
  arquivo antigo continua la o tempo todo. Corolario: um teste/comando de verificacao que le um caminho
  fixo de saida deveria assertar a **frescura** do arquivo (mtime > T0), nao so o conteudo.
- **2026-08-01 (via app de jogo - o teste que passa porque o CENARIO nao alcanca o guard):** Ao
  travar um guard do tipo "so conta quando a condicao C vale" (aqui: "vitoria so conta contra a
  maquina, nao no dois jogadores"), o cenario do teste tem de ser aquele em que **o resto todo
  levaria ao efeito**, senao o guard nunca e exercitado. Caso real: para provar "partida local nao
  conta vitoria" montei `vsCpu:false, humanWon:false` e afirmei `cpuWins == 0`; ficou verde, mas o
  zero vinha de `humanWon:false` (o ramo de vitoria nem era alcancado). Mutar o guard para
  `if (vsCpu || true)` deixou o teste **verde** = inutil. Correcao: `vsCpu:false` **com
  `humanWon:true`** (e modo/dificuldade que alimentariam TODOS os contadores), afirmando que
  cpuWins/ultimateWins/hardWins seguem zerados **e** que uma sequencia previa de 4 nao foi tocada.
  Variante irma no mesmo dia: um teste de "acao repetida no mesmo dia nao conta duas vezes" que
  afirmava `streak == 1` sobreviveu a remocao do curto-circuito, porque sem ele o fluxo caia no
  ramo de *reset* e o valor batia em 1 pelo motivo oposto; so um cenario com **estado previo nao
  trivial** (streak ja em 2, segunda acao no mesmo dia, afirmar que continua 2) distingue
  "nao incrementou" de "zerou". **Regra geral: quando o valor esperado do assert e o mesmo do
  estado inicial (0, 1, vazio), desconfie - escolha um estado inicial que torne os dois caminhos
  numericamente distintos.** O mutation check e o unico jeito barato de flagrar isso.
- **2026-08-01 (via app Flutter - `catalog` injetavel isola a unidade sob teste):** Quando a funcao
  central mistura duas fontes do mesmo efeito (aqui XP vinha da partida E do bonus das conquistas
  desbloqueadas na mesma chamada), testar o valor exato fica impossivel sem reimplementar a regra
  no teste. Solucao barata que vale pra qualquer motor com "catalogo de regras": deixe a lista de
  regras ser **parametro do construtor** e, nos testes de XP puro, injete a lista **vazia**. Os
  testes ficam com valor literal esperado (`expect(xp, 35)`) em vez de aritmetica duplicada, e os
  testes de desbloqueio usam o catalogo real. Bonus: a mesma injecao permite afirmar propriedades do
  catalogo real (ids unicos, toda meta alcancavel, nada desbloqueado num estado zerado) sem tocar no
  motor.
- **2026-07-23 (via todo — o teste de rejeição que passa PELO MOTIVO ERRADO):** Ao afirmar que uma
  requisição hostil é **rejeitada** (`assert status === 400/403`), o teste só prova alguma coisa se a
  requisição for **válida em todo o resto** — senão ela morre num guard ANTERIOR e o guard que você
  queria testar nunca roda. Caso real: para provar "usuário B não pode mover item para um local do
  usuário A", mandei `{itemIds: [], toLocationId: <local de A>}`; deu 400 e o teste ficou verde —
  mas o 400 veio do `itemIds required`, e a checagem de posse do DESTINO nunca foi alcançada. Quem
  denunciou foi o **mutation check**: removi o `AND user_id=$2` da consulta do destino e o teste
  continuou **verde** (mutação sobreviveu = teste inútil). Correção: montar o cenário REAL — B cria
  um item PRÓPRIO e tenta movê-lo para o local de A — e afirmar **duas** coisas: o status E o
  **estado final** (o item de B continua apontando pro local de B). Regras duráveis: (1) todo teste
  de rejeição precisa de uma mutação que o prove vermelho — status esperado igual (400) por caminhos
  diferentes é o falso-positivo mais comum em API com várias camadas de validação; (2) quando vários
  guards devolvem o MESMO status, asserte também a **mensagem/efeito**, não só o código; (3) prefira
  afirmar o **estado depois** do ataque (o dado não mudou) — isso não tem como passar pelo motivo
  errado. Bônus de método: para mutation check em app Dockerizada, **monte o arquivo mutado como
  volume** (`docker compose run --rm -v /tmp/mut.js:/app/rota.js --entrypoint npm web test`) — roda
  em segundos, não exige rebuild, e o fonte real nunca é tocado (mata de vez o risco do
  `git checkout` das lições de 2026-07-07 e 2026-07-16).
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
- **2026-07-23 (via cartomania — assert on WRITTEN STATE via an in-memory fake, and don't let bcrypt cost
  blow the timeout):** For a service that persists via an ORM (Prisma/TypeORM), a tiny **in-memory fake**
  that stores real rows lets tests assert on the OBSERVABLE effect (what got written) instead of "a method
  was called" — e.g. `register` must write `role: USER` and Google-auth must NOT create a row for an
  UNVERIFIED email. Mutation-proof it: disable the `!email_verified` guard and the test must go red.
  Gotcha: seeding login-lockout tests with real `bcrypt.hash(pw, 12)` and then doing ~19 compares blows
  Jest's 5s timeout in ts-jest — the tests exercise the lockout COUNTER, not bcrypt strength, so seed with
  cost 4 (identical logic, ~10× faster). Keep the production hashing at 12; only the test fixture drops.
- **2026-07-26 (via cartomania — an in-memory fake that runs the REAL collaborator + mutation testing with
  REDUNDANT guards):** Two lessons. **(1)** For a service that persists via an ORM, a small in-memory fake that
  supports the ops your code actually uses — including `{ increment }` updates and a full one-time-token
  lifecycle (create / findUnique-by-hash / conditional updateMany) — lets you construct the REAL token/collaborator
  service against it, so token single-use/expiry/wrong-purpose are genuinely exercised (not stubbed). Assert on the
  written STATE (the row's `usedAt`, the user's `tokenVersion`), never on "a method was called". **(2) Redundant
  defense-in-depth defeats single-point mutation testing:** if a token's replay is rejected by BOTH a `usedAt !=
  null` check AND a conditional `updateMany ... WHERE usedAt IS NULL` (count!=1), breaking EITHER one alone leaves
  the test green — the other still catches it. That's correct hardening, but to prove the test actually bites you
  must break BOTH guards at once and watch it go red (then restore). A "mutation survived" on one guard is not a
  weak test here; confirm by mutating the whole invariant.

- **2026-08-11 (via warframe-farm-helper — o guard de "degrada bem" tem que envolver a PREPARAÇÃO, e o
  teste tem que construir o ambiente degradado DE VERDADE):** Duas lições que se completam. **(1)** Escrevi
  `try { row = stmt.get(name) } catch { row = null }` com o comentário "banco antigo, sem a tabela" — mas
  quem estoura com tabela ausente é o **`db.prepare(...)`**, executado ANTES do laço, fora do try. O
  comentário afirmava uma resiliência que o código não tinha, e a página inteira cairia com 500 num banco
  sem a tabela. Vale para todo runtime com etapa de **compilação/preparação separada da execução**
  (`prepare` de SQL, `compile` de regex/template, `Schema.parse`, `new Function`): o erro de *schema* nasce
  na preparação, o erro de *dado* nasce na execução — um `try` só na execução não cobre o primeiro. **(2)**
  O que expôs isso foi um teste que **montou um banco realmente sem a tabela** (`new Database(tmp)` + só o
  `CREATE TABLE items`), em vez de simular passando `null` ou um mock que lança. Regra: teste de
  "sobrevive ao ambiente X faltando" precisa **produzir o ambiente faltando**; mock que lança prova só que
  você trata a exceção que você mesmo escolheu lançar, não que ela nasce onde você acha.
- **2026-08-11 (via warframe-farm-helper — o assert que fixa o caminho de FALLBACK vira teste do bug):**
  Um teste antigo afirmava `assert.match(item.url, /bratonPrime/)` e passava — mas passava porque o índice
  de slug estava frio no processo de teste e a função caía na **URL legada** `/item.html?u=%2Fu%2FbratonPrime`,
  que contém o uniqueName. Quando corrigi a função para montar o índice sozinha, a URL virou a bonita
  (`/item/braton-prime`) e o teste ficou **vermelho por causa da melhoria**. O erro de método: o regex casava
  um pedaço da **entrada** (o id que eu mesmo semeei), não a **forma da saída** — então ele passava nos dois
  ramos e não dizia qual rodou. Regra geral: quando uma função tem caminho principal e fallback, asserte o
  **valor exato do caminho que você espera** (igualdade, não `match` de substring da entrada); se os dois
  ramos podem satisfazer o assert, o teste não distingue nada. Sintoma para procurar em suíte herdada:
  `assert.match(saida, /<algo que veio da fixture>/)`.

- **2026-08-13 (via um site de catálogo) - SONDA QUE VARRE A PRÓPRIA APP: separe "resposta de erro" de
  "resposta vazia", senão o rate limit vira um laudo falso de produto quebrado.** Escrevi um script que
  consultava a busca da app ~1.450 vezes em sequência para achar itens faltando; ele reportou **1.440
  faltando (99%)**. Era o **rate limit da própria app** devolvendo `429 {"error":...}`, e o script fazia
  `if (!d.results?.length) faltando.push(x)` - resposta de erro não tem `results`, então TODA requisição
  barrada foi contada como "item não existe". O produto estava certo o tempo todo (o número real era 27,
  1,9%). Três regras que saem disso: **(1)** toda sonda contra serviço próprio precisa de **pacing +
  retry explícito no 429/503**, e deve **falhar alto** se o retry esgotar, em vez de degradar para um
  resultado plausível; **(2)** trate **status != 2xx como INCONCLUSIVO**, nunca como negativo - a
  diferença entre "não achei" e "não consegui perguntar" é a diferença entre um bug e nenhum bug; **(3)**
  **desconfie de taxa de falha absurda**: quando uma varredura acusa ~100% de defeito, o suspeito número
  um é o instrumento. O que me salvou foi checar **4 casos à mão** antes de reportar, e eles passaram -
  regra barata e obrigatória: **antes de reportar um achado em massa, reproduza 3-5 casos individualmente
  pelo caminho do usuário**. (Corolário para o rubric de teste: o mesmo vale para teste de integração que
  bate em serviço com quota - um 429 não lido vira "feature ausente" verde/vermelho errado.)

- **2026-08-14 (via um site multi-idioma) - i18n tem DOIS testes que pagam sozinhos, e um footgun de
  fallback que só um teste pega.** **(1) Teste de PARIDADE de chaves entre idiomas.** Ao acrescentar
  um idioma eu extraí as chaves do idioma base com um regex `'chave': 'valor'` e achei que tinha
  traduzido tudo; o teste de paridade (que casa só a CHAVE, ignorando a forma do valor) acusou **8
  chaves faltando** - eram justamente as de valor com aspas/multi-linha, que o meu regex não pegou.
  Lição geral: **a extração que você usa para GERAR não serve para VERIFICAR** - o verificador tem
  que casar um padrão mais frouxo e independente do gerador, senão os dois erram junto. **(2) O
  footgun do fallback binário.** Uma função de tradução escrita como `const idx = lang === 'zh' ? 2 :
  1` devolve a coluna do idioma 1 para TODOS os outros - ou seja, `f(s, 'en')` retornava português.
  Não era alcançável pelos chamadores da época (todos guardados por um `if`), mas é uma bomba armada:
  o dia em que alguém chamar sem o guard, sai texto do idioma errado no meio da página, e isso é PIOR
  que não traduzir (o usuário lê uma língua que não escolheu e não entende de onde veio). Teste que
  pega: **afirmar o comportamento para um idioma NÃO suportado** (`assert f(x,'en') === x`), não só
  para os suportados. Correção: mapa explícito `{pt:1, zh:2}` com retorno cru quando não há coluna.
  Regra durável: **em qualquer seletor por idioma/moeda/unidade, o ramo "nenhum dos conhecidos" tem
  que ser NEUTRO (devolve a entrada), nunca "o primeiro da lista".**

- **2026-08-14 (via um site multi-idioma) - dois testes baratos que travam tradução: "sem literal na
  view" e "termo oficial".** **(1)** Um cabeçalho de tabela escrito na mão no componente
  (`text: 'Intact'`) aparecia em inglês nos 5 idiomas **mesmo existindo a chave no dicionário** - o
  teste de paridade de chaves não pega isso, porque a chave existe e está traduzida; ninguém a usa.
  Teste que pega: **grep no fonte da view proibindo o literal** (`assert !/text:\s*'Intact'/`) e
  exigindo a chamada da chave. Vale para qualquer string que "deveria" vir do dicionário. **(2)** Ao
  traduzir vocabulário de domínio (termos de um jogo, de uma norma, de um setor), o risco não é
  esquecer: é usar um **sinônimo plausível** no lugar do termo que o produto nomeia oficialmente.
  Trave com um teste que lista `[termo_certo, termo_errado]` e falha se o errado aparecer no código -
  ele documenta a decisão e impede a regressão quando outra pessoa "corrigir" de volta. Bônus da
  mesma família: afirmar que **caractere do idioma novo não vazou para os blocos dos outros idiomas**
  (um replace global bem-intencionado troca os 5 de uma vez - foi o que eu fiz).
