---
name: app-essentials
description: Implementa (não só audita) as funcionalidades que TODO sistema web multiusuário sério precisa ter — login e-mail+senha, login social (Google OAuth), verificação de e-mail, reset de senha, sessões/cookies seguros, página de conta (editar/trocar senha/excluir conta), Termos de Uso + Política de Privacidade versionados com aceite server-side, banner de cookies com scripts de 3º só sob consentimento (LGPD/GDPR), trilha de login + alerta de novo dispositivo, e-mail transacional, i18n completa, step-up para ações sensíveis, tratamento de erro/toasts. Detecta o que falta, implementa seguindo padrões comprovados e ADAPTADOS à stack do projeto, e no fim chama security-sweep (blinda) + test-forge (trava) + frontend-review (se UI). Use quando o usuário pedir "adicione login com Google", "coloque termos de uso/política de privacidade", "banner de cookies", "verificação de e-mail", "o que falta pro app ficar sério/pronto pra produção", "adicione as funcionalidades básicas que todo sistema tem".
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, WebFetch, Skill
---

# app-essentials — implementa as funcionalidades de base de um app sério (e as blinda)

Uma skill **agnóstica a projeto** que **implementa** a plumbing que todo sistema web multiusuário sério
precisa ter — e que a maioria dos apps "vibe-coded" esquece ou faz pela metade. A inteligência mora em
**`rubric.md`**: o catálogo de módulos essenciais, cada um com o **padrão canônico** (generalizado das
nossas apps), o ângulo de **conformidade** (LGPD/GDPR) e a **classe da `security-sweep`** que o protege.
**Leia a `rubric.md` inteira antes de agir.**

> **Par com a `security-sweep`:** esta skill CONSTRÓI a feature; a `security-sweep` GARANTE que ela está
> segura (testando o ataque ao vivo). São complementares e **devem rodar juntas**: toda feature que esta
> skill implementa cai na política SEGURANÇA-SEMPRE → ao terminar, invoque `security-sweep` escopada nela.
> Regra dura: **nenhum módulo desta skill é "concluído" sem passar pela `security-sweep` + `test-forge`.**
> Se a vulnerabilidade não existe numa app nossa, ela não pode existir na próxima — é esse o objetivo.

## Objetivo (o que o operador quer)
Que **todos os projetos** que rodarem esta skill terminem com o MESMO conjunto de funcionalidades de base,
implementadas do mesmo jeito comprovado, e com a MESMA proteção. Login Google, termos, privacidade,
cookies, verificação de e-mail etc. deixam de ser reinventados (mal) a cada app: viram um catálogo que a
skill instala e a `security-sweep` blinda.

## Quando usar
- Pedido explícito: "adicione login com Google", "coloque termos de uso e política de privacidade",
  "banner de cookies (LGPD)", "verificação de e-mail", "reset de senha", "página de conta / excluir conta",
  "o que falta pra esse app ficar sério / pronto pra produção?", "adicione o básico que todo sistema tem".
- Ao **iniciar** um app multiusuário novo (bootstrap da base de auth/conta/legal).
- Ao **auditar** um app existente para achar quais módulos essenciais faltam (modo só-diagnóstico).

## Inputs e resolução do alvo
1. **Stack** — detecte backend (Go/Node/Python/…), banco (Postgres/MySQL/SQLite), front (Svelte/React/Vue/…),
   e como a app roda/deploya. TODO padrão da rubric é um **conceito**, não um trecho copiável — **adapte à
   stack e às convenções do repo** (o `code-standards` é bom parceiro para casar o estilo).
2. **O que já existe** — faça o inventário (Fase 0) antes de propor. Nunca duplique um módulo que já existe;
   melhore/complete o que está pela metade.
3. **Config-driven, fail-safe** — toda integração externa (OAuth, SMTP, analytics, ads) é **ligada por env**:
   sem a env, a feature fica **desligada e o botão/ço escondido** (nunca quebra o app, nunca vaza segredo).
4. **Segredos** — nunca invente credenciais nem as comite. Chaves de OAuth/SMTP ficam no `.env` (gitignored,
   `chmod 600`). O que exige conta externa (criar OAuth client, DNS, verificação de marca) é passo do
   **operador** — documente-o, não tente dirigir navegador logado no Google na VPS.

## Metodologia (5 fases)

### Fase 0 — Inventário: o que a app já tem vs. o catálogo
Para cada módulo da `rubric.md`, procure no código se existe e em que estado (ausente / parcial / completo).
Produza uma **matriz** (módulo → estado → gap). Marque dependências (ex.: "verificação de e-mail" precisa de
"e-mail transacional"; "alerta de novo dispositivo" precisa de "trilha de login" + "e-mail transacional").

### Fase 1 — Plano priorizado
Ordene os gaps por valor/risco. Prioridade típica: **auth (sessão segura) → conta/exclusão → legal
(termos+privacidade+consentimento) → verificação de e-mail/reset → trilha de login/alertas → i18n/erros**.
Apresente o plano curto ao operador; siga sem travar nos itens reversíveis; **pare e pergunte** só no que
exige decisão dele (cobrar dinheiro, escolher provedor pago, texto legal que precisa de advogado).

### Fase 2 — Implementar (adaptado à stack)
Implemente cada módulo escolhido seguindo o **padrão canônico** da rubric, nas convenções do repo:
- **Migrations aditivas e versionadas**; escopo por usuário no código (`WHERE user_id`).
- **i18n desde o início**: toda string nova entra no dicionário de TODAS as línguas suportadas, nunca inline.
- **Feature-flag por env** para integrações externas; **no-op seguro** quando a env falta.
- **Gate server-side** para tudo sensível (verificação de e-mail, aceite de termos, papel admin) — nunca só
  esconder no front.

### Fase 3 — BLINDAR (obrigatório) — chama a `security-sweep`
Ao terminar cada módulo sensível (auth, dados, permissões, input, URL fetch, dinheiro), **invoque a skill
`security-sweep`** escopada nele: ela dispara os ataques da classe correspondente (a rubric aponta qual) e
CORRIGE. **Não declare o módulo pronto sem isso.** É a metade que garante que a feature nova nasce segura.

### Fase 4 — TRAVAR + verificar UI + auto-melhora
- **`test-forge`** no caminho crítico do módulo (auth/limites/tokens/idempotência) — teste determinístico que
  roda e pode falhar.
- **`frontend-review`** se o módulo tem UI (banner de cookies, gate de termos, página de conta, botão Google).
- **Deploy + commit** (regra permanente do repo alvo): nunca deixe a feature undeployed/uncommitted.
- **Auto-melhora desta skill** (ver abaixo).

## Regras rígidas
- Nunca invente credenciais nem texto legal como "conselho jurídico" — o texto de Termos/Privacidade é um
  **template de engenharia**; avise que um advogado deve revisar antes de cobrar dinheiro (LGPD exige
  controlador identificável + contato; base legal; direitos do titular; retenção).
- Nunca comite `.env`/segredos. Integrações externas sempre config-driven + no-op sem env.
- Migrations **aditivas**; jamais uma migration destrutiva sem confirmar com o operador.
- Ações irreversíveis (excluir conta, rotacionar chave) exigem confirmação/step-up e são **hard delete
  com auditoria não-identificável** (fingerprint HMAC), não soft-delete que retém PII.
- Terminou feature sensível ⇒ `security-sweep` + `test-forge`. Sem exceção (é a política SEGURANÇA-SEMPRE).

## Auto-melhora (rode SEMPRE ao final)
1. Que **módulo/padrão geral** faltava no catálogo, ou que variação de stack ensinou algo? (agnóstico!)
2. Edite `rubric.md`: novo módulo ou linha no **Learnings log**; se um padrão de fix nasceu aqui e é de
   segurança, garanta que a **`security-sweep`** também o conhece (as duas rubrics devem concordar).
3. **Commit + push** na pasta da skill: `git add -A && git commit -m "app-essentials: <lição> (via <projeto>)" && git push`.
   Nunca comite segredos; relatórios/artefatos ficam no projeto alvo (gitignored lá).
