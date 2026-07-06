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
- **2026-07-06 (via CoinHub, origem da skill):** Projeto de money-path com **zero testes** no núcleo de
  ordens era o maior risco pré-lançamento. Lições: (1) priorize o caminho do dinheiro e os **invariantes**
  (idempotência da compra diária, atomicidade do limite sob concorrência, conversão de moeda que nunca
  soma unidades diferentes) — é onde regressão vira prejuízo; (2) para lógica pura (conversão, clamp,
  resolução de cotação) escreva **testes de unidade table-driven** sem DB/rede — rápidos e à prova de
  flaky; (3) rode Go com **`-race`** para provar a atomicidade de fixes de concorrência; (4) um teste
  que expõe um bug real ⇒ conserte o código, nunca o teste.
