---
name: code-standards
description: Audita se o projeto segue padrões de código e boas práticas — consistência com as próprias convenções do repo, camadas/SOLID, tratamento de erro, código morto, i18n completa, números mágicos, higiene de logs/deps, formatação/linter — e aplica correções seguras, reportando o resto. Agnóstica, contra uma rubric versionada que cresce. Use quando o usuário pedir "está seguindo os padrões?", "boas práticas", "revise a qualidade/consistência do código", "code standards/lint", "está bem escrito?". Complementa /code-review (bugs) e /simplify (simplificação).
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, WebFetch
---

# code-standards — auditor de padrões e boas práticas

Skill **agnóstica** que verifica se o código segue **as convenções do próprio projeto** e boas práticas
gerais, e **corrige o que é seguro**. A inteligência mora em **`rubric.md`**. **Leia-a antes.**

> **Complementa:** `/code-review` acha **bugs de correção**; `/simplify` **simplifica**; `security-sweep`
> cuida de **segurança**; esta cuida de **consistência/padrões/manutenibilidade**. Rode em conjunto.

## Princípio: a régua é o PRÓPRIO projeto primeiro
A boa prática nº1 é **consistência com o que o repo já faz** (nomes, camadas, estilo de erro, i18n,
tokens). Um desvio do padrão local é achado mesmo que "no geral" fosse aceitável. Só depois vêm as boas
práticas universais. Leia `CLAUDE.md`/`README`/os padrões vigentes antes de julgar.

## Quando usar
- Pedido de auditoria de qualidade/padrões/consistência.
- **Recomendado** ao final de uma feature grande (depois de `/code-review` e antes de fechar).
- `$ARGUMENTS` = alvo (diff, módulo, "este projeto").

## Metodologia
1. **Aprender a régua:** leia as convenções do repo (arquivos `CLAUDE.md`, config de lint/formatter,
   e os padrões de fato no código vizinho). Rode o **formatter/linter oficial** do projeto se existir
   (`gofmt`/`go vet`/`golangci-lint`, `eslint`/`prettier`, `ruff`/`black`, `svelte-check`) e capture o que
   ele aponta — isso é padrão objetivo.
2. **Auditar** contra a `rubric.md` (consistência, camadas, erros, código morto, i18n, mágicos, logs,
   deps, docs). Mapeie cada achado a `arquivo:linha` e diga **por que desvia** (do padrão local, de
   preferência).
3. **Corrigir o seguro** (formatação, imports, nome inconsistente óbvio, dead code comprovadamente não
   usado, string faltando no i18n) e **re-rodar o linter**. O que for arriscado/ambíguo (refactor de
   camada) vai como recomendação, não aplicado sozinho.
4. **Relatório** priorizado + **auto-melhora** da rubric + commit/push.

## Regras rígidas
- Não mude comportamento a pretexto de "padrão" — mudanças de padrão são de risco baixo por definição; se
  uma "limpeza" muda semântica, é refactor (pare/só recomende).
- Não brigue com o formatter do projeto; adote a config existente.
- Remoção de código só quando **comprovadamente** sem uso (grep de chamadores em todo o repo).

## Auto-melhora (sempre ao final)
Lição geral → `rubric.md` (Learnings log). `git add -A && git commit -m "code-standards: <lição> (via <projeto>)" && git push`.
