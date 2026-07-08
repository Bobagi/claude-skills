# security-sweep — rubric (a checklist que cresce)

Este arquivo **é** a expertise da skill. É **agnóstico a projeto**: nunca coloque fatos de um projeto
específico aqui. Cada sweep aplica todas as classes; a auto-melhora acrescenta lições **gerais** ao
**Learnings log** no fim.

**Severidade:** **P0** = explorável já, alto impacto (bypass de auth, roubo de dados/dinheiro, RCE) ·
**P1** = explorável sob condição, impacto sério · **P2** = defense-in-depth / difícil de explorar.

**Cada classe testável tem `▶ Testar ao vivo`. Se você não disparou o ataque, marque a classe como
NÃO TESTADA no relatório — não a dê como coberta.** Toda conta/dado de teste é deletado ao final.

---

## 1. Race conditions / TOCTOU  ⚠️ CLASSE QUE UM REVIEW ESTÁTICO JÁ DEIXOU PASSAR — comece por ela
Qualquer **check-then-act** sobre um recurso finito é suspeito: limite de plano/quota (ex.: "N robôs/itens
por usuário"), ação única (resgatar cupom/reembolso uma vez), saldo/carteira, "só o 1º ganha". Se o código
faz `contar/ler em memória → decidir → inserir/atualizar` em passos separados (fora de uma transação com
lock), **é vulnerável**: N requests concorrentes leem o mesmo estado velho e todos passam.
- [ ] Todo limite/quota/saldo é enforçado **atomicamente**: transação + **advisory lock por usuário**
  (`pg_advisory_xact_lock`), ou **constraint no banco** (unique/check), ou **UPDATE condicional**
  (`UPDATE ... SET x=x+1 WHERE x < limite` e checar `RowsAffected`). Nunca um `SELECT COUNT` em Go/JS
  seguido de `INSERT`.
- [ ] O lock é liberado ao fim da transação (xact lock) e não colide com outros locks (namespaces distintos;
  no Postgres, a forma de 1 bigint e a de 2 int32 são espaços separados).
- [ ] Constraints do banco cobrem o invariante real. **Cuidado: um índice único que não é o invariante
  mascara o bug** — ex.: unique `(user, tipo, item)` NÃO impede furar um limite de CONTAGEM com itens
  DIFERENTES.
- **▶ Testar ao vivo:** dispare **N requests concorrentes** (`for ...; do curl ... & done; wait`, ou
  `Promise.all`) contra o endpoint. Faça **DUAS** rodadas: (a) idênticos e (b) **DISTINValidos no eixo do
  invariante** (ex.: moedas/itens diferentes — este é o teste que expõe o bypass de contagem; sem ele o
  índice único finge que está seguro). Depois **conte no DB**: se passou do limite, é P0/P1. **LIÇÃO
  DURÁVEL: garanta que cada request é distinto no eixo certo, senão você testa a constraint errada e tem
  um falso "passou".** (E confira que o campo/parâmetro do teste é o que a app realmente lê — um nome de
  campo errado no curl vira falso-positivo/negativo.)
- **Fix:** mover contagem+escrita para uma transação sob advisory lock por usuário (ver o padrão
  `CreateRobotForUserWithinLimit` do CoinHub), ou constraint/UPDATE condicional. Re-teste até só 1 passar.

## 2. Autorização / IDOR / escalonamento de privilégio
- [ ] **Toda** leitura/mutação de recurso é escopada ao dono da SESSÃO: `WHERE id=$1 AND user_id=$sessão`.
  O `user_id`/owner vem **da sessão**, nunca do payload/URL do cliente.
- [ ] Flags de privilégio (`is_admin`, plano, limite) são derivadas **server-side**; o payload não tem
  campo `is_admin`/`role`/`user_id` que o handler respeite.
- [ ] Rotas admin checam o papel no servidor (403 caso contrário), não só escondem no front.
- **▶ Testar ao vivo:** com a conta A, crie um recurso e pegue seu id. Com a conta B (outra descartável),
  tente **ler/editar/deletar** o recurso de A por id. Tente também mandar `user_id`/`is_admin` no corpo.
  Deve dar 403/404/"não encontrado", nunca sucesso.
- **Fix:** adicionar `AND user_id=$sessão` na query; derivar papéis só da sessão; ignorar campos de
  identidade no payload.

## 3. Enumeração de usuário / oráculos
- [ ] Login, signup e "esqueci a senha" retornam resposta **idêntica** (status + corpo) para email
  existente vs inexistente. "Esqueci a senha" sempre 200. Login sempre o mesmo erro genérico.
- [ ] **Timing constante:** no caminho de "usuário não existe", ainda rode um `VerifyPassword` contra um
  hash placeholder, senão o tempo de resposta vaza a existência do email.
- [ ] Registrar tentativa falha (audit) para conta existente **não** muda a resposta ao cliente.
- **▶ Testar ao vivo:** `login` com email que não existe vs email real + senha errada — compare status E
  corpo E ordem de grandeza do tempo. `forgot-password` idem. Devem ser indistinguíveis.
- **Fix:** erro genérico único; comparar contra hash placeholder no ramo "não existe".

## 4. Injeção (SQL / comando / template)
- [ ] SQL só com placeholders (`$n`/`?`), **nunca** `Sprintf`/concatenação com input. Nomes de coluna/tabela
  são constantes, não input.
- [ ] Nada de `exec`/`sh -c`/`eval` com input do usuário. Comandos com args em array, não string.
- **▶ Testar ao vivo:** mande metacaracteres (`' OR 1=1 --`, `"; DROP`, `${}`) nos campos e confirme que
  são tratados como dado literal (erro de validação ou armazenado como texto), sem erro de SQL nem efeito.
- **Fix:** parametrizar; whitelist para identificadores dinâmicos.

## 5. Validação de tamanho / poluição de banco / limites numéricos
- [ ] Todo campo string controlado pelo usuário tem **cap de tamanho** que chega ao DB, **casado com a
  largura da coluna** — passar do `varchar(n)` vira **HTTP 500** (não é só estética; é erro não tratado).
  Contar **runas**, não bytes. Email, nome, símbolo, etc.
- [ ] Cap global no corpo da requisição (`MaxBytesReader`/body limit).
- [ ] Campos numéricos têm bounds (ex.: teto por ordem, percentuais 0–100, sem negativos onde não faz
  sentido).
- **▶ Testar ao vivo:** mande um campo com **> largura da coluna** (ex.: 500 chars numa coluna de 80) e
  confirme **200 com truncamento** ou **400**, nunca **500**. Cheque o comprimento armazenado no DB.
- **Fix:** clamp por runas casado à coluna (truncar) ou rejeitar com 400; bounds numéricos no service.

## 6. SSRF (fetch server-side de URL influenciada pelo usuário)
- [ ] Se o servidor busca uma URL derivada de input (avatar, webhook, importador, proxy de imagem): **host
  pinado por allowlist** (e nos redirects também), **https-only**, **bloquear IPs internos/loopback/
  link-local/metadata** (169.254.169.254, 127.0.0.0/8, 10/8, 192.168/16, ::1), **cap de corpo**, validar
  `Content-Type`. SSRF que só controla o PATH (host fixo) é baixo risco; controlar **host/protocolo** é P0/P1.
- **▶ Testar ao vivo:** aponte a URL (se o usuário controla) para `http://169.254.169.254/…`, `http://localhost:<porta-interna>`, um host arbitrário e um redirect para host interno. Deve recusar antes de conectar.
- **Fix:** allowlist de host + checagem de IP resolvido + https-only + limites. (No CoinHub o avatar é
  pinado a `*.googleusercontent.com` e a URL não é escolhida pelo usuário — re-valide que continua assim.)

## 7. Upload de arquivo
- [ ] Valida **magic bytes/MIME real**, não só a extensão; cap de tamanho; nome/caminho sanitizado (sem
  path traversal `../`); não serve o upload de origem executável.
- **▶ Testar ao vivo:** suba um arquivo com extensão de imagem mas conteúdo/magic de outra coisa (HTML/PHP);
  suba algo enorme; tente `../` no nome. Deve rejeitar.
- **Fix:** checar assinatura + tamanho; gerar nome próprio; armazenar fora da raiz servida.

## 8. Segredos & gestão de credenciais
- [ ] **Zero segredos hardcoded** no código **e no histórico do git** (chaves de API, senhas, tokens).
  `.env` gitignored + `chmod 600`. Backups com segredos = 600, fora do repo.
- [ ] Segredos de usuário (chaves de exchange, tokens) **cifrados em repouso** (AES-256-GCM com **nonce
  aleatório por mensagem** + validação de tamanho da chave). **Fail-closed** se a chave de cifra faltar
  (recurso desabilitado, nunca plaintext).
- [ ] Senhas com **bcrypt/argon2** (custo ≥ 12 / params fortes); rejeitar senha fora de 8–72 (bcrypt trunca
  em 72). Tokens de sessão/reset **opacos e aleatórios**, guardados só como **hash** (SHA-256).
- **▶ Testar (estático + histórico):** `git log -p | grep -iE 'secret|password|api_key|token='` e grep no
  source. Confirme `.gitignore` do `.env`.
- **Fix:** rotacionar o segredo vazado, purgar do histórico (**destrutivo → confirmar com operador**; se a
  chave de cifra for a mesma que decifra dados, planejar re-encrypt antes). Tornar repo privado se público.

## 9. Sessão / cookies / CSRF / step-up
- [ ] Cookie de sessão `HttpOnly` + `Secure` (default-on) + `SameSite=Strict/Lax`. Só o **hash** do token no
  DB. Logout revoga; reset de senha revoga todas as sessões.
- [ ] **CSRF:** guarda de mesma-origem (Origin/Referer) nos métodos que mudam estado, ou tokens anti-CSRF.
- [ ] **Step-up (re-auth) para ações de dinheiro** (salvar chave, operar). OAuth: `state` aleatório +
  checado por cookie; no step-up via OAuth, casar o `subject`.
- [ ] Gates server-side de verificação de email / aceite de termos nos endpoints sensíveis (não só no front).
- **▶ Testar ao vivo:** chame um endpoint de mutação com `Origin` cross-site; sem cookie; com cookie de
  outro usuário; sem step-up. Deve barrar.
- **Fix:** setar flags do cookie; guarda de origem; exigir step-up; enforçar gates no servidor.

## 10. XSS / injeção no front
- [ ] Framework com auto-escape (Svelte/React/Vue) e **sem** `innerHTML`/`{@html}`/`dangerouslySetInnerHTML`/
  `v-html` com dado controlado pelo usuário. Nomes/campos do usuário renderizados como texto.
- [ ] **CSP** restritiva (`script-src 'self'`; sem `unsafe-inline` em script) e `X-Content-Type-Options:
  nosniff`. Scripts de 3º (analytics/ads) carregados só sob consentimento e, de preferência, em `<iframe>`
  isolado (o JS do 3º não roda na nossa origem).
- **▶ Testar ao vivo:** ponha `<script>`/`<img onerror>` num campo (nome, etc.) e veja se renderiza como
  texto. Cheque os headers CSP/nosniff na resposta.
- **Fix:** usar o escape do framework; nunca `@html` com input; endurecer CSP.

## 11. Crypto (uso correto)
- [ ] Algoritmos fortes (AES-GCM/ChaCha20, SHA-256+), **nonce/IV aleatório por operação**, sem ECB, sem
  MD5/SHA-1 para segurança. HMAC (chave dedicada, idealmente subchave via HKDF) para assinar cookie/
  fingerprint. Aleatoriedade de fonte segura (`crypto/rand`, não `math/rand`).
- **Fix:** trocar algoritmo/modo; nonce por mensagem; HKDF para separar propósitos de chave.

## 12. Rate limiting / lockout / brute-force
- [ ] Throttle por endpoint (login, reset, criar conta) com lockout temporário; camada de rede
  (nginx/fail2ban) para brute-force distribuído; IP do cliente lido de fonte **não forjável** (atrás de
  proxy: `X-Real-Id`/`$remote_addr`, não o `X-Forwarded-For` mais à esquerda que o cliente controla).
- **▶ Testar ao vivo:** dispare muitos logins errados e veja se trava/atrasa. (Não conte DoS como achado —
  foco é bypass/força-bruta.)
- **Fix:** throttle no app + fail2ban; ler o IP real do header confiável do proxy.

## 13. Exposição de dados / logs / erros
- [ ] Erros ao cliente não vazam stack/SQL/caminhos internos (500 genérico; detalhe só no log server-side).
- [ ] **Sem PII nem segredos em log** (chaves, senhas, tokens, corpo com credencial). Logar URL é ok; logar
  segredo não.
- [ ] Minimização/retenção de PII (ex.: purgar log de acesso após N dias). Endpoints não devolvem campos
  sensíveis desnecessários (hash de senha, chave cifrada) nos JSONs.
- **▶ Testar:** provoque um erro e leia a resposta; `grep` nos logs por segredo/PII; inspecione os JSONs
  de resposta dos endpoints de conta.
- **Fix:** mensagem genérica + log interno; remover segredo do log; job de retenção; enxugar o payload.

## 14. Lógica de negócio / financeira
- [ ] Ordem de operações com dinheiro não pode gerar valor do nada: reembolso após saque, saque antes de
  confirmar venda, comprar sem debitar, cupom/comissão + reembolso combinados. Sem valores negativos que
  invertam o sinal. Idempotência/replay em callbacks de pagamento (assinatura/nonce).
- **▶ Testar ao vivo:** encadeie as operações no pior caso (comprar→reembolsar→sacar em ordens diferentes,
  em paralelo — cruza com a classe 1) e confira o saldo/estado final.
- **Fix:** transações atômicas; máquina de estados explícita; validar sinais/limites; verificar assinatura
  do webhook.

## 15. Infra / headers / TLS / superfície exposta
- [ ] TLS 1.2/1.3 só; HSTS; `Permissions-Policy` negando o que não se usa; `X-Content-Type-Options`,
  `X-Frame-Options`/frame-ancestors. Portas de DB/admin **não** públicas (bind 127.0.0.1 + túnel/proxy).
  Serviços internos atrás de firewall (cuidado: **Docker fura o UFW** — regra em `DOCKER-USER`).
- [ ] Atrás de CDN/Cloudflare: origem travada aos **ranges do CDN** (senão o atacante bate direto no IP e
  contorna o WAF) e o **IP real** lido de `CF-Connecting-IP` (para audit/geo/fail2ban corretos).
- **▶ Testar:** `curl -I` os headers; do lado de fora, `nc`/scan das portas que deviam ser internas.
- **Fix:** ajustar nginx/headers; rebind 127.0.0.1; regra de firewall na chain certa.

## 16. Autenticação federada (OAuth/SSO) — sequestro de conta e state
- [ ] O fluxo OAuth tem **`state` aleatório** guardado em cookie e **conferido no callback** (anti-CSRF).
- [ ] O e-mail do provedor é **verificado** (`email_verified`) antes de auto-linkar; **auto-link por e-mail
  não pode sequestrar** uma conta existente cujo e-mail o atacante consiga fazer o provedor emitir sem
  verificar. Guarda-se o **`subject`** (id estável), não só o e-mail.
- [ ] Feature **config-driven**: sem as envs do OAuth, o provider fica **off** e o botão some (não vira uma
  rota meio-configurada explorável).
- [ ] No **step-up via OAuth**, casar o `subject` da sessão com o do re-consent (não basta "logou no Google").
- **▶ Testar ao vivo:** callback com `state` ausente/trocado ⇒ rejeitar. Com conta B, tentar linkar ao
  e-mail da conta A ⇒ não pode assumir a conta de A. Sem as envs, `/auth/providers` reporta `google:false`.
- **Fix:** state em cookie conferido; exigir e-mail verificado + subject; feature-flag por env.

## 17. Trilha de auditoria & alerta de anomalia de login
- [ ] Existe **trilha append-only** de acessos (IP+UA+método+fingerprint+sucesso/falha) que sobrevive à
  expiração da sessão. **Login falho para conta existente é registrado, mas a resposta ao cliente não muda**
  (não pode virar oráculo de enumeração — cruza com a classe 3).
- [ ] **Alerta de novo dispositivo** só quando o fingerprint é novo **E** já houve acesso anterior (1º
  login/signup nunca alerta); o gate do alerta conta **só sucessos** (uma falha do atacante não pode
  mascarar o "novo dispositivo" do login real seguinte).
- [ ] O IP da trilha vem de fonte **não-forjável** atrás do proxy (cruza com a classe 12); a trilha tem
  **retenção** (purga > N dias) e cai no cascade do delete da conta (é PII — cruza com a classe 13).
- **▶ Testar ao vivo:** logar de um "novo" UA/IP após um acesso anterior ⇒ e-mail de alerta; 1º acesso ⇒
  sem alerta; falha de login ⇒ linha `success=false` sem alerta e sem mudar a resposta ao cliente.
- **Fix:** registrar acesso off-request (best-effort); gate de alerta (novo E ≥1 anterior E só sucesso);
  IP do header confiável; job de retenção.

## 18. Defaults seguros para ações perigosas / irreversíveis
- [ ] O caminho **perigoso** (dinheiro real/produção) é **recusado até opt-in explícito** (ex.: contas novas
  começam em sandbox/testnet; produção exige uma flag que o usuário liga sabendo). O **irreversível** (excluir
  conta, rotacionar chave, apagar em massa) exige **confirmação** (idealmente step-up), nunca por acidente.
- [ ] Exclusão de conta é **hard delete + auditoria não-identificável** (fingerprint HMAC), não soft-delete
  que retém PII (cruza com a classe 13 e o direito de eliminação da LGPD).
- **▶ Testar ao vivo:** disparar a ação de produção/dinheiro **sem** a flag de opt-in ⇒ deve recusar
  (400/403); a exclusão sem confirmação ⇒ não executa.
- **Fix:** gate de opt-in server-side; confirmação/step-up nas irreversíveis; hard delete com auditoria HMAC.

---

## Par com a skill `app-essentials` (construir ↔ blindar)
A `app-essentials` **implementa** as funcionalidades de base (login Google, termos, privacidade, cookies,
verificação de e-mail, reset, exclusão de conta, trilha de login, i18n…); esta skill **garante que cada uma
nasce segura**. O catálogo da `app-essentials` aponta, por módulo, a **classe desta rubric** que o testa ao
vivo. Regra: toda feature que a `app-essentials` cria fecha com uma sweep desta skill escopada nela — é assim
que a proteção fica **idêntica entre projetos** (falha que não existe numa app não existe na outra). Se um fix
de segurança novo nasce numa das skills, replique o conceito na outra rubric — as duas devem concordar.

---

## Apêndice — defesas a RE-VALIDAR em toda app (não regredir)
Estas já foram implementadas/verificadas em apps nossas; a sweep deve **confirmar que continuam firmes**:
- Chaves de exchange/segredos do usuário cifrados AES-256-GCM, nonce por mensagem, fail-closed sem chave.
- Sessão opaca aleatória, só hash no DB, cookie HttpOnly+Secure+SameSite; reset revoga sessões.
- bcrypt custo 12; senha 8–72; forgot-password sempre 200; tokens guardados como hash.
- Sem SQLi (tudo `$n`), sem IDOR (tudo `WHERE user_id`), papéis derivados da sessão.
- SSRF de avatar/proxy pinado a host + https + cap + content-type + gate de sessão.
- CSRF por mesma-origem; step-up para ações de dinheiro; verificação de email/termos server-side.
- IP do cliente lido de fonte não-forjável atrás do proxy.
- Race de limite/quota atômica (advisory lock/constraint/UPDATE condicional) — **testada com requests
  distintos no eixo do invariante**.
- Caps de tamanho de input casados à largura das colunas (sem 500 por overflow).
- Scripts de 3º (analytics/ads) só sob consentimento, ads em iframe isolado; CSP sem `unsafe-inline` em script.
- OAuth com `state` conferido + e-mail verificado + subject-match; provider config-driven (off sem env).
- Trilha de login append-only; alerta de novo dispositivo (novo E ≥1 anterior E só sucesso); falha registrada
  sem enumerar; retenção da trilha; IP não-forjável atrás do proxy.
- Origem travada aos ranges do CDN + IP real via `CF-Connecting-IP` quando atrás de Cloudflare.
- Ação de dinheiro/produção recusada sem opt-in explícito (sandbox/testnet por default); exclusão = hard
  delete + auditoria HMAC (sem reter PII).
- E-mail transacional/SMTP config-driven e no-op sem env; segredo/token nunca em log.

---

## Learnings log (append-only, geral)
- **2026-07-08 (via CoinHub — compilado de segurança + par com `app-essentials`):** destiladas de uma app
  madura de dinheiro três classes que faltavam explícitas: **16 (OAuth/federada)** — state conferido,
  e-mail verificado, subject-match, provider off sem env; **17 (trilha + anomalia de login)** — audit
  append-only, alerta de novo dispositivo com gate correto (novo E ≥1 anterior E só sucesso), falha
  registrada sem enumerar, retenção; **18 (defaults seguros)** — perigoso exige opt-in, irreversível exige
  confirmação, exclusão = hard delete + auditoria HMAC. Lição meta: as funcionalidades "comuns de todo
  sistema sério" (login social, termos, cookies, verificação de e-mail, trilha de acesso) têm, cada uma,
  uma superfície de ataque conhecida — a skill `app-essentials` as CONSTRÓI e esta as BLINDA; manter as
  duas rubrics em concordância é o que garante paridade de proteção entre projetos.
- **2026-07-07 (via CoinHub — pentest de app "vibe-coded"):** Padrões clássicos de "não confie no
  front", todos = **autorização/gate que tem que ser server-side, nunca escondido só no cliente**.
  Como testar cada um AO VIVO: (1) **Role tampering** — o atacante reescreve a RESPOSTA (Burp
  Match&Replace `"role":"student"`→`"admin"`) e, se a aba admin aparecer E as requisições funcionarem, o
  backend confia no cliente. Teste: com uma conta NÃO-admin, **chame o endpoint admin diretamente** (curl)
  → deve dar 403; e confirme que nenhum campo do payload (`is_admin`/`role`/`user_id`/`plan`) é respeitado
  (papéis vêm da sessão/DB). (2) **Gate de conteúdo só no front** (ex.: `released:false`→`true` interceptado)
  — todo cadeado da UI (conteúdo pago, aba bloqueada, "verifique o e-mail") precisa ser reenforçado no
  servidor: chame a AÇÃO por trás do cadeado sem cumprir o pré-requisito → deve barrar (403/400).
  (3) **Cookie de sessão SEM `Secure`/`HttpOnly`** deixa XSS roubar a sessão — cheque `Set-Cookie` (curl -i):
  precisa de `HttpOnly; Secure; SameSite`. (4) **Endpoint de listagem vazando PII de OUTROS usuários**
  (comentários com email/CPF/telefone) — todo endpoint que lista precisa filtrar por dono; teste com a
  conta B tentando ler recursos/dados da conta A por id. (5) **Campo "HTML/CSS custom" de admin injetado
  nas páginas sem sanitização** = XSS armazenado que compromete todos — se existir tal feature, ela É a
  vulnerabilidade (grep por sinks `{@html}`/`innerHTML`/`dangerouslySetInnerHTML`; e qualquer HTML de
  usuário/admin renderizado). LIÇÃO META do vídeo: o defensor tem que proteger TODAS as rotas; o atacante
  só precisa de UMA — então a classe 2 (autz/IDOR) tem que ser rodada **rota a rota**, chamando cada
  endpoint mutável/admin diretamente com uma conta sem privilégio, não confiando no que a UI esconde.
- **2026-07-06 (via CoinHub, origem da skill):** Um review ESTÁTICO passou por uma race condition financeira
  real (bypass de limite pago criando N recursos concorrentes com chaves DIFERENTES; o índice único
  `(user,env,symbol)` só barrava duplicatas do MESMO item). Lições: (1) análise estática não basta —
  **dispare o ataque concorrente**; (2) no teste de race, os requests têm que ser **distintos no eixo do
  invariante** (itens diferentes), senão uma constraint irrelevante mascara o bug e dá falso "seguro";
  (3) confira que o **nome do campo** no seu curl é o que a app lê (um payload ignorado vira falso
  resultado); (4) ao adicionar clamp de tamanho, **case com a largura real da coluna** (cortar em 120
  numa coluna de 80 troca poluição de banco por um 500); (5) fix de race = contagem+escrita numa
  transação sob `pg_advisory_xact_lock` por usuário (forma 2-int32 não colide com o leader-lock 1-bigint).
