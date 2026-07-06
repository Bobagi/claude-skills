---
name: test-forge
description: Cria e RODA testes automatizados úteis e confiáveis (não tautológicos, não flaky) para qualquer projeto, priorizando o caminho crítico (dinheiro, auth, limites, parsers, idempotência) sobre cobertura por %. Detecta a stack e o runner do repo, escreve testes determinísticos que FALHAM quando o comportamento quebra, roda-os até passarem, e conserta o código se um teste expõe um bug real. Contra uma rubric versionada que cresce. Use quando o usuário pedir "crie testes", "escreva testes", "cobertura de testes", "o projeto não tem testes", "teste essa funcionalidade" — e ao final de QUALQUER feature nova para travar o comportamento com um teste.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, WebFetch
---

# test-forge — cria e roda testes que realmente pegam regressão

Skill **agnóstica** que escreve testes **confiáveis e úteis** e os **executa**. A inteligência mora em
**`rubric.md`** (o que é um bom teste + o que priorizar + anti-padrões + como rodar por stack). **Leia-a
antes.**

> **Complementa, não duplica:** `/verify` confirma uma mudança ponta-a-ponta uma vez; `test-forge` cria a
> **suíte durável** que roda sempre. `/code-review` acha bugs; `test-forge` os trava com um teste.

## Princípio (o que separa teste útil de teatro)
Um teste só vale se **pode falhar quando o código quebra**. Teste que testa o mock, que sempre passa, ou
que só compara um snapshot, é ruído. **Mentalidade de mutação:** ao escrever um teste, pergunte "se eu
inverter/quebrar a regra que ele cobre, ele fica vermelho?". Se não, reescreva.

## Quando usar
- Pedido explícito de testes, ou "o projeto não tem testes".
- **Obrigatório** (política nos CLAUDE.md + hook): ao terminar uma feature no **caminho crítico** (dinheiro,
  auth, limites/quotas, parsers, conversões, idempotência), escreva um teste que trave o comportamento.
- `$ARGUMENTS` costuma ser o alvo (arquivo/módulo/fluxo) ou "este projeto".

## Metodologia
### 1. Detectar stack + runner + COMO rodar NESTE repo
Descubra o framework (Go `testing`, vitest/jest, pytest, JUnit…) e o **comando exato** deste repo — inclua
gotchas (ex.: Go não está no PATH ⇒ rodar via Docker; front via pnpm/nvm). Registre o comando no relatório.
### 2. Mapear o que IMPORTA testar (prioridade, não %)
Priorize, nesta ordem: **caminho do dinheiro** (compra/venda/saldo/limites/cobrança), **auth/autz**
(gates, escopo por usuário), **invariantes** (idempotência por dia/chave, "só 1 passa", conversões de
moeda/unidade), **parsers/validação** (tamanho, formato, bordas), **regras de negócio**. Ignore getters
triviais e o que o framework já garante.
### 3. Escrever testes CONFIÁVEIS
- **Determinísticos:** sem `sleep`, sem rede real, sem relógio/aleatório não-injetado, sem depender de
  ordem. Injete tempo/relógio; use fakes/stubs para I/O externo (exchange, SMTP, HTTP); use **testnet/
  sandbox** para dinheiro, nunca ordens reais.
- **Isolados:** cada teste monta seu estado e limpa; sem dependência entre testes; DB de teste efêmero
  (container/transação com rollback), nunca o banco de produção.
- **Table-driven** para muitos casos; nomes que dizem o comportamento (`sells_when_price_hits_target`).
- **Asserts significativos:** cheque o efeito real (estado/retorno/erro tipado), não "não deu panic".
- **Cobrir happy + borda + FALHA:** o caminho de erro é onde mora o bug (ex.: cota estourada, cotação
  ausente, entrada gigante, moeda misturada).
### 4. Rodar → verde. Se um teste acha bug REAL, consertar o código (ou sinalizar se for decisão do dono)
Nunca "ajuste o teste" pra esconder um bug. Se o comportamento certo é ambíguo, PARE e pergunte.
### 5. Relatório + auto-melhora
Relatório curto: comportamentos cobertos, o **comando pra rodar**, bugs achados/consertados. Depois,
acrescente lições gerais ao `rubric.md` (Learnings log) e **commit + push** na pasta da skill.

## Regras rígidas
- Nunca rode testes que disparem efeitos reais (ordem de dinheiro, email de verdade, escrita em prod).
- Nunca comite segredos/fixtures com dados reais sensíveis.
- Um teste flaky é um bug do teste — conserte a causa (determinismo), não adicione retry/sleep.
- Não persiga % de cobertura; persiga **comportamentos críticos cobertos por testes que podem falhar**.

## Auto-melhora (sempre ao final)
Que lição geral (não do projeto X) este uso ensinou? Edite `rubric.md` (Learnings log; promova se
recorrente). `git add -A && git commit -m "test-forge: <lição> (via <projeto>)" && git push`.
