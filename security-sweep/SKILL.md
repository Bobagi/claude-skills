---
name: security-sweep
description: Varredura de segurança agnóstica a projeto que ENCONTRA, TESTA ao vivo (adversarialmente) e CORRIGE vulnerabilidades — não só reporta. Cobre race conditions/TOCTOU, IDOR/autorização, enumeração de usuário, injeção (SQL/command), SSRF, upload, XSS, segredos, sessão/auth, crypto, exposição de dados e lógica de negócio, contra uma rubric versionada que cresce a cada uso. Use quando o usuário pedir "varredura de segurança", "faça um pentest", "está seguro?", "audite a segurança", "verifique vulnerabilidades", ou ao final de QUALQUER feature que toque autenticação, dinheiro, permissões, input do usuário, upload ou dados sensíveis.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, WebFetch
---

# security-sweep — auditor de segurança reutilizável que TESTA e CORRIGE

Um auditor de segurança **agnóstico a projeto** que age como um pentester + engenheiro que **conserta**.
A inteligência mora em **`rubric.md`** (a checklist que cresce). **Leia-a inteira antes de auditar** — ela
codifica TODAS as classes de vulnerabilidade já validadas nas nossas apps, incluindo as defesas que já
existem e que devem ser **re-validadas** (nunca regredir), não só as que já falharam uma vez.

> **Diferença para o `/security-review` embutido e o plugin `security-guidance`:** aqueles fazem review
> ESTÁTICO de um diff e **reportam**. Esta skill audita o app **inteiro**, **TESTA ao vivo** (dispara o
> ataque de verdade contra a app rodando) e **CORRIGE + re-testa** até o ataque falhar. Rode os três: use
> `/security-review` no diff, `security-guidance` como lente, e esta skill como a varredura que fecha o loop.

## Regra de ouro (a lição que originou esta skill)
Um review estático **passou** por uma race condition financeira real (bypass de limite pago via requests
concorrentes). **Análise estática não basta — o ataque tem que ser DISPARADO.** Toda classe testável nesta
skill tem um "**Como testar ao vivo**" na rubric; execute-o. Se você só leu o código e não disparou o
ataque, você NÃO auditou aquela classe — diga isso no relatório.

## Quando usar
- Pedido explícito: "varredura/auditoria de segurança", "pentest", "está seguro?", "tem vulnerabilidade?".
- **Obrigatório** (política nos CLAUDE.md + hook): ao terminar QUALQUER feature nova/alterada que toque
  **auth, dinheiro/cobrança, limites/quotas, permissões, input do usuário, upload, URL fetch server-side,
  ou dados sensíveis** — rode a sweep escopada na feature (test + fix) ANTES de encerrar.
- `$ARGUMENTS` costuma ser o alvo (caminho do projeto / URL rodando / "este projeto") e/ou o escopo
  (ex.: "só o fluxo de robôs").

## Inputs e resolução do alvo
1. **Código** — localize o backend (o que valida/persiste é o que importa: `apps/api`, `server/`, `src/`).
   Autorização, atomicidade e validação são **sempre server-side**; código client (JS/TS) não conta como defesa.
2. **App rodando** — a URL pública/local para os testes ao vivo. Sem app rodando, você só faz a metade
   estática — deixe explícito no relatório quais classes ficaram **não testadas**.
3. **Auth** — a maioria do miolo está atrás de login. Prefira **criar uma conta descartável via signup**
   (e, se preciso, promover verificação/flags direto no DB de teste), rodar os ataques, e **DELETAR a conta
   ao final** (cascade). Nunca invente credenciais reais; nunca use a conta do operador para ataques
   destrutivos. **Nunca ecoe nem comite senha/cookie/segredo.**
4. **Ambiente de dinheiro** — teste em **testnet/sandbox** sempre que a app suportar; jamais dispare ordens
   reais de dinheiro num teste.

## Metodologia (5 fases)

### Fase 0 — Mapear a superfície de ataque
Liste, do código: endpoints (rotas), o **caminho do dinheiro** (compra/venda/saldo/limites/cobrança),
autenticação/sessão, uploads, todo **input controlado pelo usuário** que chega ao DB ou a um comando/URL,
e onde ficam segredos. Marque o que é **admin-only** vs público (superfície pública é a prioridade).

### Fase 1 — Estático (grep/read) → candidatos
Para cada classe da `rubric.md`, procure o padrão de defesa. Ausência ou desvio = **candidato**. Não pare
aqui.

### Fase 2 — Teste adversarial AO VIVO (o núcleo)
Para cada candidato testável, **dispare o ataque** contra a app rodando com a conta descartável, seguindo o
"Como testar ao vivo" da rubric. Ex.: para race condition, dispare N requests **concorrentes e DISTINTOS no
eixo certo** (ver a lição do índice único); para IDOR, tente acessar o recurso de outro usuário por id; para
enumeração, compare respostas de email existente vs inexistente. **Confirme com evidência** (status, contagem
no DB, corpo). Limpe os dados de teste.

### Fase 3 — CORRIGIR + re-testar
Para cada achado **confirmado**, aplique a correção (a rubric dá o padrão de fix). Rebuild/deploy. **Re-rode
o mesmo ataque** e prove que agora **falha**. Um achado sem re-teste pós-fix não está fechado.

### Fase 4 — Relatório + auto-melhora
Gere **um** Markdown em `<projeto>/.claude/security-sweep/<timestamp>/report.md`:
- **Resumo** + contagem por severidade (P0/P1/P2) e **quais classes foram TESTADAS ao vivo vs só estáticas**.
- **Achados**: cada um com classe, `arquivo:linha`, severidade, **exploit concreto (com a evidência do teste)**,
  **fix aplicado**, e a **prova de re-teste** (ataque agora falha).
- **Re-validado OK** (defesas que já existiam e continuam firmes — para não regredir).
- **Não testável aqui** (e por quê).
Apresente o resumo + top correções no chat; aponte o caminho do relatório.

## Regras rígidas
- Nunca invente credenciais. Nunca ecoe/comite segredos, cookies ou senhas.
- Toda conta/dados de teste criados são **deletados ao final** (verifique o cascade).
- Ações destrutivas só contra dados de teste, nunca contra dados reais do operador.
- Se um fix é destrutivo/irreversível (rotação de chave que torna dados indecifráveis, purge de histórico),
  **PARE e confirme com o operador** — não aplique sozinho.
- Reporte fielmente: se uma classe não deu para testar ao vivo, diga; não finja cobertura.

## Auto-melhora (rode SEMPRE ao final)
1. Que **lição geral** (não específica do projeto) este sweep ensinou? Que padrão de ataque/def faltava?
2. Edite `rubric.md`: acrescente ao **Learnings log** (datado) e, se recorrente, promova para a classe certa.
   Mantenha **agnóstico** (nada de fatos do projeto X). Se descobriu uma defesa nova que já existia numa app,
   registre-a como item a **re-validar** em qualquer app.
3. **Commit + push** na pasta da skill: `git add -A && git commit -m "security-sweep: <lição> (via <projeto>)" && git push`.
   O relatório fica no projeto auditado (gitignored lá), **nunca** segredos no repo da skill.
