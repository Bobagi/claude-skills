# app-essentials — rubric (o catálogo de funcionalidades de base)

Este arquivo **é** a expertise da skill. É **agnóstico a projeto**: os padrões abaixo são conceitos
generalizados das nossas apps, para **adaptar à stack** do alvo — nunca cole fatos de um projeto aqui.

Cada módulo traz: **O quê** · **Por que todo app sério precisa** · **Padrão canônico** (como implementar) ·
**Conformidade** (LGPD/GDPR quando aplica) · **🛡 Blinda com** (a classe da `security-sweep` que testa isso
ao vivo) · **🔒 Trava com** (o que a `test-forge` deve travar). Ao implementar um módulo, ao final rode as
skills apontadas — é isso que faz "se a falha não existe numa app, não existe na outra".

**Prioridade padrão:** Auth/sessão → Conta/exclusão → Legal (termos+privacidade+consentimento) →
Verificação de e-mail/reset → Trilha de login/alertas → i18n/erros → Observabilidade/infra.

---

## ⚠️ REGRA TRANSVERSAL Nº1 — DINHEIRO/LIMITE/SALDO É SEMPRE ATÔMICO (anti-race, anti-fraude)
Vale para QUALQUER módulo desta skill que crie uma função sobre um **recurso finito**: saldo/carteira,
cobrança, limite de plano/quota ("N robôs/itens por usuário"), cupom/reembolso de uso único, "só o 1º ganha",
estoque, créditos. **É o vetor de fraude mais comum em app vibe-coded** e um review estático já deixou passar
um caso real (bypass de limite pago com N requests concorrentes). Portanto, ao CONSTRUIR qualquer coisa
assim:
- **NUNCA** `contar/ler em memória → decidir → inserir/atualizar` em passos separados (check-then-act/TOCTOU).
  N requests concorrentes leem o mesmo estado velho e **todos passam**.
- Enforce o invariante **atomicamente**, por um destes:
  1. **transação + advisory lock por usuário** (`pg_advisory_xact_lock(chave, user_id)`), fazendo
     contagem+escrita dentro do lock (padrão `CreateRobotForUserWithinLimit` do CoinHub);
  2. **constraint no banco** (unique/check) que seja **o invariante real** — cuidado: um unique
     `(user, tipo, item)` **NÃO** barra furar um limite de CONTAGEM com itens DIFERENTES;
  3. **UPDATE condicional** (`UPDATE saldo SET x=x-$v WHERE x>=$v` e checar `RowsAffected`).
- Locks em **namespaces distintos** para não colidir (no Postgres, a forma de 1 bigint e a de 2 int32 são
  espaços separados).
- **🛡 Blinda com a `security-sweep` CLASSE 1 (race/TOCTOU) + CLASSE 14 (lógica financeira)** — e o teste
  ao vivo tem que disparar **N requests concorrentes DISTINTOS no eixo do invariante** (moedas/itens
  diferentes), senão uma constraint irrelevante finge que está seguro. **🔒 Trava com `test-forge`**:
  10 creates/débitos simultâneos ⇒ só 1 (ou só o saldo permite) passa.
- **Idempotência/replay** em callbacks de pagamento (verificar assinatura + nonce/id único), senão um
  webhook reenviado credita duas vezes.

**Enquanto esta skill não tiver um módulo próprio de billing/saldo, esta regra é a lei para qualquer função
de dinheiro que você criar — construir sem ela é criar a fraude junto.**

---

## 1. Autenticação e-mail + senha (a base)
- **O quê:** signup/login/logout com senha.
- **Por quê:** identidade é o alicerce de tudo que é por-usuário.
- **Padrão canônico:** senha com **bcrypt custo ≥12** (ou argon2id); rejeitar senha fora de **8–72** (bcrypt
  trunca em 72). **Sessão = token opaco aleatório** (`crypto/rand`, 32 bytes) entregue em **cookie**; no DB
  guarda-se **só o hash SHA-256** do token, nunca o token. Logout revoga a sessão. Nunca um JWT com claims de
  papel que o cliente possa forjar — papel vem do DB/sessão.
- **🛡 Blinda com:** security-sweep classes 8 (segredos/hash), 9 (sessão/cookies), 3 (enumeração).
- **🔒 Trava com:** test-forge — hash/verify de senha, expiração/revogação de sessão.

## 2. Sessão + cookies seguros + CSRF
- **O quê:** como a sessão viaja e se defende.
- **Por quê:** cookie mal-configurado = roubo de sessão por XSS ou CSRF.
- **Padrão canônico:** cookie **`HttpOnly` + `Secure` (default-on, desligável só por env explícita) +
  `SameSite=Strict`** (ou Lax se precisar de navegação cross-site); **CSRF por guarda de mesma-origem**
  (checar `Origin`, cair pro `Referer`; requisição sem nenhum dos dois = server-to-server, passa) nos métodos
  que mudam estado (POST/PUT/DELETE/PATCH); **cap de corpo** (ex.: 1 MiB) em todo request.
- **Conformidade:** o cookie de sessão é **essencial** → não precisa de consentimento (só os não-essenciais).
- **🛡 Blinda com:** classe 9 (sessão/CSRF) + classe 10 (CSP/nosniff).

## 3. Login social / OAuth (Google e afins) — CONFIG-DRIVEN
- **O quê:** "Entrar com Google" (o pedido clássico).
- **Por quê:** reduz atrito de cadastro; muitos usuários preferem não criar senha.
- **Padrão canônico:** **ligado por env** (`GOOGLE_OAUTH_*`) — sem as envs, a feature fica **off e o botão
  some** (`/auth/providers` reporta `google:false`). Fluxo: `state` aleatório guardado em **cookie** e
  conferido no callback (anti-CSRF do OAuth); trocar `code`→token; **verificar o e-mail** do provedor;
  **auto-linkar por e-mail verificado** a uma conta existente (uma conta manual mantém a senha); guardar o
  `subject` (id estável do provedor), não confiar só no e-mail. Escopos **mínimos** (`openid email profile`
  = não-sensíveis → publicar o consent screen **não exige verificação** do Google; **não suba logo custom**
  no consent, dispara "brand verification"). Avatar do provedor: **proxy server-side** com host pinado
  (anti-SSRF), não `<img src>` direto (CSP).
- **Passo do OPERADOR (documentar, não automatizar):** criar o OAuth client no Google Cloud Console, o
  redirect URI, publicar o consent screen. **Nunca** dirigir navegador logado no Google na VPS.
- **🛡 Blinda com:** classe 9 (state/subject-match no step-up), classe 6 (SSRF do avatar), classe 2 (o
  link-por-e-mail não pode sequestrar conta alheia).
- **🔒 Trava com:** test-forge — auto-link só com e-mail verificado; state inválido rejeitado.

## 4. Verificação de e-mail (enforced server-side)
- **O quê:** confirmar que o e-mail é do usuário antes de liberar ações sensíveis.
- **Por quê:** e-mail não verificado = spam, contas falsas, reset sequestrável.
- **Padrão canônico:** tabela `auth_tokens` guardando **só o hash** do token (como a sessão);
  `email_verified_at` no usuário (contas antigas **grandfathered** = verificadas; signups Google
  **pré-verificados**). **Enforçar no SERVIDOR**: endpoints sensíveis retornam **403 `email_unverified`**
  até verificar (não só banner no front). Reenvio de link. Envio é **no-op** se SMTP não configurado
  (a app roda sem e-mail, só não força verificação).
- **🛡 Blinda com:** classe 9 (gate server-side), classe 3 (reenvio não enumera).
- **🔒 Trava com:** test-forge — token expira/uso-único; endpoint sensível barra sem verificação.

## 5. Reset de senha ("esqueci a senha")
- **O quê:** recuperar acesso sem suporte humano.
- **Por quê:** sem isso, esquecer a senha = perder a conta.
- **Padrão canônico:** `forgot-password` **sempre responde 200** (nunca revela se o e-mail existe); token
  guardado **hasheado**, expira; **`reset` revoga TODAS as sessões** do usuário (expulsa um atacante que já
  estava dentro). Página/rota de reset dedicada.
- **Conformidade/segurança:** anti-enumeração é requisito, não enfeite.
- **🛡 Blinda com:** classe 3 (enumeração — resposta idêntica), classe 8 (token hasheado), classe 9
  (reset revoga sessões).
- **🔒 Trava com:** test-forge — token uso-único/expira; reset invalida sessões antigas.

## 6. Página de conta (perfil / trocar senha / idioma / excluir)
- **O quê:** o usuário gerencia a própria conta.
- **Por quê:** editar nome, trocar senha, mudar idioma e **sair/excluir** são expectativa mínima.
- **Padrão canônico:** endpoints escopados à sessão (`WHERE user_id=$sessão`); trocar senha exige a senha
  atual (ou step-up); **excluir conta** ver módulo 7.
- **🛡 Blinda com:** classe 2 (IDOR — só a própria conta), classe 9 (step-up p/ trocar senha).

## 7. Exclusão de conta — hard delete que preserva privacidade
- **O quê:** apagar a conta e os dados de verdade.
- **Por quê:** LGPD/GDPR dão ao titular o **direito à eliminação**; soft-delete que retém PII não cumpre.
- **Padrão canônico:** **hard delete** com **cascade** por FKs (apaga PII + segredos cifrados + operações);
  grava **uma linha não-identificável** de auditoria (fingerprint **HMAC do e-mail** — irreversível sem a
  chave do servidor — + método de auth, data de criação, teve credencial?, nº de operações), **best-effort**
  (nunca bloqueia a exclusão). Confirmação explícita na UI.
- **Conformidade:** direito de eliminação (LGPD art. 18); a auditoria anônima é legítima (não é PII).
- **🛡 Blinda com:** classe 2 (só a própria conta), classe 13 (a auditoria não vaza PII).
- **🔒 Trava com:** test-forge — cascade apaga tudo; fingerprint não reversível.

## 8. Termos de Uso + Política de Privacidade — aceite versionado server-side
- **O quê:** consentimento auditável aos Termos e à Privacidade.
- **Por quê:** um checkbox no front **não é enforçável nem auditável**; a resposta legal é server-side.
- **Padrão canônico:** tabela **append-only** `user_agreement_acceptances` (user, **versão do documento**,
  IP, UA, timestamp) = a prova durável; constante **`CurrentAgreementVersion`** (data-ordenável) — ao mudar
  o texto materialmente, **bumpar** → toda aceitação anterior deixa de casar → **todos re-aceitam** (gate
  bloqueante no front + **enforce no servidor**: 403 `terms_not_accepted` nos endpoints sensíveis,
  **fail-closed** em erro de leitura). **Páginas públicas versionadas** `#/terms` + `#/privacy`. Texto
  trilíngue (ou nas línguas da app): não-custodial/risco, cobrança/cancelamento (se houver), publicidade/3º,
  LGPD/dados, responsabilidade, foro (Brasil), **direito de arrependimento CDC art. 49 (7 dias)** se cobra,
  **18+ + titularidade** da conta/chave no aceite.
- **Privacidade (conteúdo mínimo):** controlador identificável + **contato/encarregado**, bases legais,
  compartilhamento/operadores, transferência internacional, **retenção**, segurança, cookies, **direitos do
  titular**, crianças, mudanças→re-aceite. **A política tem que bater com o que a app REALMENTE faz** (não
  dizer "não rastreamos" enquanto carrega analytics — é bug de conformidade, não de texto).
- **⚠ Limite:** é template de engenharia, **não conselho jurídico** — avise que um advogado revise antes de
  cobrar; e cobrar robô/serviço financeiro pode exigir CNPJ + parecer regulatório (ex.: CVM no Brasil).
- **🛡 Blinda com:** classe 9 (gate server-side de aceite), classe 2 (aceite só do próprio usuário).
- **🔒 Trava com:** test-forge — sem aceite ⇒ 403; bump de versão ⇒ re-aceite forçado.

## 9. Banner de cookies + scripts de 3º só sob consentimento (LGPD)
- **O quê:** consentimento real antes de qualquer script não-essencial.
- **Por quê:** LGPD/GDPR exigem opt-in para analytics/ads; carregar antes do aceite é violação.
- **Padrão canônico:** **nenhum tag estático** de analytics/ads no `index.html` — injetar em **runtime só
  quando `cookieConsent==='accepted'`** (Accept/Reject com **prominência igual**, sem dark pattern). "Gerenciar
  cookies" (**retirar consentimento**) recarrega e derruba scripts já carregados. **Bumpar a chave do
  consentimento** quando adicionar uma nova categoria (ex.: passou a ter ads) → todos re-decidem. Ads/embeds
  de 3º em **`<iframe>` isolado** (o JS do 3º não roda na nossa origem; CSP só precisa de `frame-src`).
- **Conformidade:** só o cookie de sessão é essencial; todo o resto é consentido e revogável.
- **🛡 Blinda com:** classe 10 (CSP/consentimento), + verificar E2E que o script só aparece após aceite.
- **🔒 Trava com:** test-forge/frontend-review — script ausente antes, presente só após Accept, nunca após Reject.

## 10. E-mail transacional (config-driven)
- **O quê:** a app manda e-mail (verificação, reset, alertas).
- **Por quê:** verificação/reset/alertas dependem disso.
- **Padrão canônico:** interface `Sender` com impl SMTP via `SMTP_*`; **no-op quando não configurado** (a app
  roda sem e-mail — só desliga verificação/alertas). Cabeçalhos `Reply-To`/`Message-ID`/`Auto-Submitted`.
  Nunca logar o corpo com token/segredo.
- **🛡 Blinda com:** classe 13 (não vazar segredo em log).

## 11. Trilha de login (sign-in history) + alerta de novo dispositivo
- **O quê:** histórico de acessos + aviso quando um dispositivo novo entra.
- **Por quê:** é o sinal nº1 de **conta comprometida** e uma expectativa de app sério (igual Google/GitHub).
- **Padrão canônico:** tabela **append-only** de acessos (IP, UA, método `PASSWORD/GOOGLE/SIGNUP`,
  **fingerprint** = hash(UA+IP), `is_new_device`, sucesso/falha, timestamp) — sobrevive à expiração da
  sessão (é a história). **IP lido de fonte não-forjável** atrás de proxy (`X-Real-IP`/`CF-Connecting-IP`,
  nunca o `X-Forwarded-For` mais à esquerda). Geolocalização **offline** (GeoLite2) opcional. **Alerta de
  novo dispositivo por e-mail** só quando o fingerprint é novo **E** já houve acesso anterior (o 1º
  login/signup nunca alerta). **Login falho registrado** (para conta existente) **sem** mudar a resposta
  (anti-enumeração); o gate do alerta conta só sucessos. **Retenção**: purgar acessos > N dias
  (minimização de PII).
- **Conformidade:** IP/UA/localização são PII → retenção limitada + apagados no delete da conta (cascade).
- **🛡 Blinda com:** classe 12 (IP não-forjável), classe 3 (falha não enumera), classe 13 (retenção/PII).
- **🔒 Trava com:** test-forge — fingerprint novo dispara alerta; 1º acesso não; falha não vira alerta.

## 12. i18n completa (multi-idioma) + auto-detecção
- **O quê:** toda string da UI num dicionário, por idioma, auto-detectado pelo locale.
- **Por quê:** app sério não tem texto hardcoded numa língua só; é acessibilidade e alcance.
- **Padrão canônico:** dicionários por idioma + `t` store + auto-detect do locale (seleção manual persiste
  por cima); **toda chave existe em TODAS as línguas** (o `code-standards` audita chave faltando); mensagens
  de erro traduzíveis por **código** (o backend manda um `code` + params; o front renderiza `err.<code>`).
  Onde mostra país/idioma, **bandeira SVG local** (emoji quebra no Windows).
- **🛡 Blinda com:** — (não é de segurança, mas é obrigatório em app sério).
- **🔒 Trava com:** code-standards — nenhuma chave falta em nenhuma língua.

## 13. Step-up re-auth para ações sensíveis ("sudo mode")
- **O quê:** re-autenticar antes de ação crítica (salvar chave, operar dinheiro, trocar senha).
- **Por quê:** limita o dano de uma sessão sequestrada/aberta em máquina compartilhada.
- **Padrão canônico:** marca na sessão (`stepped_up_until`) exigida nos endpoints críticos; via senha ou
  re-consent OAuth (casando o `subject`). Cancelar o step-up é UX gentil (toast info), não erro.
- **🛡 Blinda com:** classe 9 (step-up).

## 14. Papéis / admin (autorização) server-side
- **O quê:** distinção admin vs usuário comum.
- **Por quê:** áreas/ações administrativas não podem depender de esconder no front.
- **Padrão canônico:** flag `is_admin` no DB, exposta no `/me`; **toda** rota admin checa o papel no
  **servidor** (403), papel derivado da sessão, nunca do payload; UI só espelha.
- **🛡 Blinda com:** classe 2 (chamar a rota admin direto com conta comum ⇒ 403).

## 15. Tratamento de erro global + feedback (toasts)
- **O quê:** erros viram feedback claro e traduzido, não tela branca nem alert cru.
- **Por quê:** consistência/UX; e evita vazar detalhe interno.
- **Padrão canônico:** toasts globais auto-dismiss; todo catch de ação roteia por um `notifyError(e)` que
  traduz por código; erros de página standalone ficam **inline** (toast some e deixaria tela vazia). Backend:
  **500 genérico ao cliente**, detalhe só no log.
- **🛡 Blinda com:** classe 13 (erro não vaza stack/SQL/caminho).

## 16. Rate limiting / lockout de login
- **O quê:** frear brute-force/credential-stuffing.
- **Por quê:** senha sozinha não aguenta força-bruta distribuída.
- **Padrão canônico:** **throttle por conta** (ex.: 5 falhas/15min → lockout temporário) no app, **além** do
  rate-limit por IP na borda (nginx) e **fail2ban** para brute-force distribuído. Lockout **temporário**
  (nunca trava o usuário legítimo pra sempre); IP do operador na allowlist.
- **🛡 Blinda com:** classe 12 (rate/lockout).
- **🔒 Trava com:** test-forge — N falhas travam; janela expira; conta certa é a chave.

## 17. Segredos de usuário cifrados em repouso
- **O quê:** se a app guarda credencial de 3º do usuário (chave de exchange, token de API), cifrar.
- **Por quê:** vazamento do DB não pode entregar as chaves em claro.
- **Padrão canônico:** **AES-256-GCM** com **nonce aleatório por mensagem** + validação de tamanho da chave;
  **fail-closed** se a chave de cifra faltar (recurso desabilitado, nunca plaintext). A chave de cifra
  **nunca rotaciona à toa** (tornaria os dados indecifráveis — planejar re-encrypt).
- **🛡 Blinda com:** classe 8 (crypto em repouso, fail-closed).
- **🔒 Trava com:** test-forge — encrypt→decrypt roundtrip; nonce distinto por chamada; chave errada não decifra.

## 18. Defaults seguros para ações perigosas / irreversíveis
- **O quê:** o caminho perigoso exige opt-in explícito; o irreversível pede confirmação.
- **Por quê:** "testnet-first" e "confirme antes de apagar" evitam o pior por default.
- **Padrão canônico:** ação com dinheiro/produção **recusada** até o usuário habilitar explicitamente
  (ex.: `live_trading_enabled`; contas novas começam em TESTNET); exclusão/rotação exige confirmação
  (idealmente step-up); nunca destrutivo por acidente.
- **🛡 Blinda com:** classe 14 (lógica de negócio) + classe 18 da security-sweep (defaults seguros).
- **Ver também a REGRA TRANSVERSAL Nº1 (topo):** se a ação perigosa mexe em dinheiro/limite/saldo, além do
  opt-in ela tem que ser **atômica** (anti-race) — as duas coisas juntas.

## 19. Backup + retenção + saúde/observabilidade (pré-produção)
- **O quê:** o app tem backup, purga PII velha e sabe dizer se está vivo.
- **Por quê:** app sério não vai a produção sem backup nem healthcheck.
- **Padrão canônico:** **backup automático** do banco (cron; dump validado; retenção; **cópia off-site**
  cifrada — backup no mesmo disco não protege contra perda do disco); **job de retenção** leader-gated purga
  PII > N dias; endpoints **`/health`** (+ `/health/worker` se há worker) para um monitor externo; a chave de
  cifra tem que ser a MESMA no restore (senão segredos ficam indecifráveis).
- **🛡 Blinda com:** classe 13 (retenção/minimização), classe 8 (backup 600, off-site cifrado).

## 20. Infra / headers / TLS / portas (endurecimento)
- **O quê:** a superfície de rede está fechada.
- **Por quê:** app seguro com infra aberta continua exposto.
- **Padrão canônico:** TLS 1.2/1.3 só; **CSP** restritiva (sem `unsafe-inline` em script), `nosniff`,
  `Permissions-Policy` negando o que não se usa, `X-Frame-Options`/frame-ancestors; **DB/admin não públicos**
  (bind 127.0.0.1 + túnel/proxy); cuidado que **Docker fura o UFW** (regra na chain `DOCKER-USER`); atrás de
  CDN/Cloudflare, travar a origem aos ranges do CDN e ler o **IP real** (`CF-Connecting-IP`).
- **🛡 Blinda com:** classe 15 (infra/headers/portas) + classe 10 (CSP).

## 21. 2FA / TOTP (opcional — acima do mínimo, mas é o gap nº1 de app maduro)
- **O quê:** segundo fator (app autenticador TOTP) além da senha.
- **Por quê:** senha sozinha (mesmo com throttle) cai a phishing/vazamento; 2FA é a expectativa de qualquer
  app sério que guarda dinheiro/dados. **Não é mínimo** (por isso é o módulo 21, opcional), mas é o primeiro
  item a subir quando o app amadurece — e **step-up re-auth NÃO substitui 2FA** (step-up re-pede a MESMA
  senha; 2FA adiciona um fator independente).
- **Padrão canônico:** segredo TOTP **cifrado em repouso** (reusa o módulo 17), enrolamento com QR +
  confirmação de um código antes de ativar, **recovery codes** (hasheados, uso único) para não travar o
  usuário que perde o aparelho, e o desafio 2FA no login **após** a senha (não antes — não vaze existência
  de conta). Desativar 2FA exige a senha atual ou um código válido.
- **🛡 Blinda com:** classe 3 (o desafio 2FA não pode enumerar), classe 8 (segredo TOTP cifrado, recovery
  codes hasheados), classe 9 (2FA integrado à sessão/step-up).
- **🔒 Trava com:** test-forge — código TOTP válido/inválido/replay (janela), recovery code uso-único.

---

## Learnings log (append-only, geral)
> Lição geral (agnóstica) sempre que um build/audit ensinar algo. Promova recorrências para os módulos acima.

- **2026-07-08 (criação, via CoinHub):** Catálogo inicial destilado de uma app madura de dinheiro
  multiusuário. Princípios que se repetiram e valem para QUALQUER app sério: (1) **config-driven + no-op sem
  env** para toda integração externa (OAuth/SMTP/analytics/ads) — a app roda sem elas e o botão some, nunca
  quebra nem vaza; (2) **todo gate sensível é server-side** (verificação de e-mail, aceite de termos, papel
  admin) — o front só espelha; (3) **consentimento e aceite são versionados** (bump força re-decisão) e
  **auditáveis** (append-only com IP/UA), nunca um checkbox volátil; (4) **a política de privacidade tem que
  bater com o que a app faz** — divergência é bug de conformidade; (5) **exclusão = hard delete + auditoria
  anônima (HMAC)**, não soft-delete que retém PII; (6) **cada módulo desta skill fecha com `security-sweep`
  (blinda) + `test-forge` (trava)** — é o mecanismo que garante paridade de proteção entre projetos. **Par
  fixo:** esta skill CONSTRÓI, a security-sweep GARANTE; as duas rubrics devem concordar (se um fix de
  segurança nasce aqui, replicar na rubric da security-sweep).
- **2026-07-08 (reforço anti-fraude):** promovida ao TOPO a **Regra transversal nº1 — dinheiro/limite/saldo
  é sempre atômico**. Motivo: race condition financeira é o vetor de fraude mais comum e um review estático
  já a deixou passar; a skill que CONSTRÓI tem que nascer atômica (advisory lock/constraint/UPDATE
  condicional), não só a que audita. Toda função de recurso finito criada aqui fecha obrigatoriamente com a
  `security-sweep` classe 1 (teste concorrente DISTINTO no eixo do invariante) + `test-forge`
  (N simultâneos ⇒ 1 passa). Idempotência/nonce em webhooks de pagamento para não creditar em dobro.
- **2026-07-08 (inventário no CoinHub — a app-fonte):** rodar o catálogo na app de onde ele foi destilado
  deu **20/20 completos** (esperado). Valor real do modo diagnóstico: (a) confirmar zero regressão e (b)
  isolar os gaps que NÃO são do catálogo — apareceram **2FA/TOTP**, **billing/assinatura** e **alertas por
  e-mail**. Lição geral: **2FA é o gap nº1 de um app maduro** e **step-up re-auth não o substitui** (mesmo
  fator) → promovido a **módulo 21 (opcional, acima do mínimo)**. Billing, quando existir, cai inteiro na
  Regra transversal nº1 (atomicidade + idempotência de webhook). Modo diagnóstico deve sempre gerar a matriz
  (módulo→estado→evidência/gap) como artefato em `.claude/app-essentials/<data>/report.md`.
