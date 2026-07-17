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
  `Promise.all`) contra o endpoint. Faça **DUAS** rodadas: (a) idênticos e (b) **DISTINTOS no eixo do
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
- **2026-07-17 (via investidor10 — leitor server-side de API JSON de 3º, SSRF classe 6):** Quando um
  serviço lê uma API externa a partir de um **id/URL do usuário** mas extrai **só um id numérico** e monta
  toda request contra um **host fixo**, o desenho já é SSRF-safe — mas a classe 6 tem DOIS pontos cegos que
  um review estático quase sempre esquece e que valem P2 de defense-in-depth (dispare-os): **(a) PIN de host
  no REDIRECT** — `requests`/`fetch` seguem 3xx por padrão; um open-redirect no host confiável levaria a um
  alvo interno. Prove stubando o cliente HTTP pra devolver uma resposta cujo `response.url` final é
  `http://169.254.169.254/...` e confirmando que o código **valida o host FINAL** (`urlparse(response.url)
  .hostname` na allowlist), não só o host que ele mesmo montou. **(b) valor da RESPOSTA do 3º que reflui pra
  um segmento de PATH** (ex.: um "type"/"category" vindo do próprio JSON externo que vira `.../actives/{id}/
  {type}`) — não muda o host (o `@`/`../` cai no path porque a autoridade termina no 1º `/`), mas um token
  com `../` atinge um path arbitrário no host confiável; **whitelist com regex de identificador**
  (`^[A-Za-z][A-Za-z0-9_-]{0,40}$`) ANTES de montar a URL, filtrando na descoberta e guardando no fetch
  (token ruim ⇒ `[]`, zero request). **Método de prova de SSRF sem rede:** instrumente `requests.get` pra
  **gravar o hostname de CADA URL de saída**, jogue os payloads hostis (`169.254.169.254`, `localhost:<porta
  interna>`, `evil.com`, sufixo `investidor10.com.br.evil.com`, userinfo `investidor10.com.br@evil.com`,
  `file://`, `gopher://`) e afirme DUAS coisas: os hostis **levantam antes de qualquer request** (contador
  em 0) e um id válido contata **só** o host allowlistado. O truque de **userinfo** (`host-bom@host-mau`) e o
  de **sufixo** (`host-bom.host-mau`) são os dois que um `in`/`startswith` ingênuo deixa passar — `urlparse`
  resolve o hostname certo (host-mau), então validar `host == ALVO or host.endswith("." + ALVO)` pega ambos.
  Nota de gotcha de teste: ao passar a validar `response.url`, os fakes de resposta dos testes existentes
  precisam expor um atributo `.url` (senão AttributeError vira "erro" em massa que MASCARA o resultado real).

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
- **2026-07-08 (via CoinHub — sweep completa, 0 achados):** Duas lições de método. (1) **Num host
  compartilhado (vários projetos/containers), atribua CADA porta em escuta ao container DONO antes de
  reportar "DB exposto".** Um `0.0.0.0:5432` no `ss -tlnp` pode ser de um projeto VIZINHO, não do alvo — e
  o DB do alvo pode estar **sem porta no host** (só rede interna do Docker). Rode `docker ps --format
  '{{.Names}} {{.Ports}}'` e case a porta ao serviço; senão você reporta um falso-positivo (ou pior, culpa
  o app errado). (2) **No teste de limite/quota (classe 1), zere a contagem antes** (delete os itens do
  usuário de teste) — se a conta já está no limite, o endpoint devolve 403 por LIMITE e mascara o que você
  queria medir (ex.: o clamp de tamanho da classe 5 nunca é exercido porque o create morre antes). Um 403
  inesperado num teste que não é de limite = provável limite/gate anterior no caminho; isole-o.
- **2026-07-11 (via CoinHub):** Ao auditar um endpoint que ESCREVE no banco a partir de um cache/estado
  server-side (ex.: importar histórico agregado), duas provas fecham a idempotência sem precisar do fluxo
  real de dados: (1) **prove o índice único parcial DIRETO no DB** — insira a linha, depois tente a
  duplicata idêntica com `ON CONFLICT (...) WHERE <predicado> DO NOTHING` e confirme `INSERT 0 0`; e
  insira uma linha de OUTRA categoria com a mesma chave natural (ex.: mesmo order_id mas initiated_by
  diferente) para provar que o índice PARCIAL não bloqueia o que não deve (`INSERT 0 1`). (2) A dedup de
  aplicação (pular o que já existe) vale testar com mutation-check nos unit tests. Juntas cobrem re-import
  E concorrência quando o fluxo E2E exige credencial externa que você não deve usar. LIÇÃO META: para
  idempotência de escrita, um índice único (não um SELECT-then-INSERT) é a defesa de concorrência — e
  quando escopado por um predicado parcial, teste os DOIS lados (bloqueia o alvo, ignora o resto).
- **2026-07-15 (via CoinHub — paginação keyset/cursor e IDOR):** Um **cursor de paginação** (keyset/
  "load more", opaco base64 ou dois params `time`+`id`) **NÃO é vetor de IDOR desde que o WHERE continue
  escopado à sessão** — o cursor carrega só uma POSIÇÃO de ordenação `(sort_time, id)` aplicada como
  `(col, id) < ($t, $id)`, e a query mantém `AND user_id = <sessão>`. Forjar/roubar o cursor de outro
  usuário só reposiciona a janela do PRÓPRIO atacante dentro dos dados dele. **Como testar ao vivo (prova
  definitiva):** construa um cursor REAL logado como conta A (pegue o `next_cursor` da resposta de A),
  reenvie-o logado como conta B e confirme que B retorna só as PRÓPRIAS linhas (ou vazio), **nunca** as de
  A. Complementos: cursor malformado/tamperado ⇒ cai na 1ª página (parse tolerante → nil), nunca erro/panic
  (DoS); precisão do timestamp no cursor tem que bater com a coluna (microssegundo) senão pula/repete linha
  — isso é bug de CORREÇÃO (não de segurança), teste à parte. Promovido à classe 2 como item a re-validar.
- **2026-07-15 (via CoinHub — filtro enum num endpoint de leitura):** Ao auditar um parâmetro de
  **enum/whitelist** que alimenta um `WHERE` (ex.: `status=open|sold|all`, `initiated_by=USER|BOT`), a
  prova de segurança não é só "deu 200 sem erro de SQL" — é **contar as linhas para confirmar que o valor
  inválido caiu no DEFAULT, não foi silenciosamente aceito**. Teste ao vivo: mande `status=sold' OR 1=1--`
  e verifique que a contagem retornada é a do default (ex.: *open-only*), NÃO a de *sold* — se vier a
  contagem de sold, o whitelist falhou e o URL-encoding mascarou. Dupla defesa correta = **whitelist para
  constantes fixas no handler** (valor desconhecido → `""`/default) **+ bind param `$N`** no repo (o valor,
  mesmo whitelistado, nunca é concatenado). E confirme que o fragmento base do WHERE mantém os invariantes
  não-negociáveis (ex.: `status <> 'CANCELED'`, `user_id` da sessão) independentemente do filtro do cliente.
- **2026-07-16 (via todo — GIS ID-token login, distinto do code-flow):** O login **Google Identity
  Services** (botão `g_id_onload`/`renderButton` → `idToken` → `verifyIdToken` no server) é um fluxo
  DIFERENTE do OAuth redirect-code (client_secret + redirect + `state`): **não há redirect, logo não
  precisa de cookie `state`** — o anti-forjação é a **assinatura RS256 + audience** do próprio ID token
  (um atacante não consegue emitir token assinado pra aquele `client_id`). Os DOIS footguns reais da
  classe 16 aqui: (a) **auto-link por e-mail** — casar por `google_id OR email` deixa uma conta Google
  assumir a conta local de MESMO e-mail (takeover) assim que o signup local capturar e-mail; casar
  **só por `google_id`** (subject estável) e **exigir `payload.email_verified`**; (b) se você **injeta o
  client id (público) no HTML server-side**, **valide o formato** (`^[\w-]+\.apps\.googleusercontent\.com$`)
  antes de substituir, senão um env malformado quebra o contexto do `<script>` (class 10). Re-valide
  também: provider **off sem env** (botão sumido no front + endpoint rejeitando todo token com audience
  `""`) — nunca uma rota meio-configurada. Teste ao vivo: POST `/google-login` com JWT forjado/`alg:none`/
  `email_verified:false` ⇒ 400 (a assinatura falha primeiro); guard de injeção com valores break-out ⇒
  string vazia. Nota de método: o branch de CRIAÇÃO de conta (token Google-assinado real) só fecha e2e com
  origin autorizado no console do Google — verifique os branches de rejeição ao vivo e diga que o happy-path
  depende do passo manual do operador (não finja cobertura).
- **2026-07-11 (via CoinHub):** Padrão "delete-and-recreate de linhas DERIVADAS" (ex.: reimportar/
  ressincronizar dados externos) é seguro SE o DELETE for escopado por 3 eixos: **dono (user_id da
  sessão) + partição (env/tenant) + um marcador que separa o derivado do real** (ex.: `is_imported=true`).
  O eixo do marcador é o crítico: sem ele, um "delete tudo do usuário antes de reinserir" APAGA os dados
  REAIS/manuais do usuário junto. Teste ao vivo: semeie no DB uma linha REAL (marcador=false) e uma
  derivada (true) para o MESMO usuário + uma real de OUTRO usuário; rode o DELETE do código; prove que só
  a derivada do dono some (as duas reais sobrevivem). Serialize reimports concorrentes com advisory lock
  por usuário (namespace distinto dos outros locks) para o delete-all+insert não duplicar.
- **2026-07-16 (via warframe-farm-helper — amplificação de fan-out contra API de 3º, cota de SAÍDA):**
  A classe 1 (quota/limite) tem um espelho pouco lembrado: além de proteger NOSSO recurso finito de
  requests de ENTRADA, cuide da **cota de SAÍDA quando um endpoint faz fan-out para uma API pública de
  3º**. Um endpoint que, por request, dispara **N fetches a um host externo** (agregador de estado,
  proxy, dashboard que junta várias fontes) **amplifica**: sem coalescência, uma rajada de M requests
  concorrentes na janela de **TTL vencido** vira **N×M** chamadas ao upstream — e como saem do **mesmo IP
  do servidor** (compartilhado com os outros serviços do host), um atacante não-autenticado provoca
  **rate-limit/ban do nosso IP** na API de 3º (nega a feature pra todos) com um `for`+`curl`. Defesas a
  exigir/re-validar: **(a) cache com TTL + serve-stale**; **(b) coalescência de requests concorrentes**
  (mapa `inflight` por chave → 1 Promise compartilhada; sem isso o cache não protege a janela de miss
  concorrente); **(c)** idealmente um teto de concorrência ao upstream. **▶ Testar ao vivo:** dispare
  uma rajada concorrente (`for i in $(seq 40); do curl ...& done; wait`) e, com `fetch` stubado num teste
  unitário, **conte as chamadas ao upstream** — tem que ser 1 por chave/janela, não 1 por request. Fix é
  barato e o teste do stub prova a coalescência de forma determinística. (Nota: isto é defense-in-depth
  P2, não roubo de dado — mas é DoS-por-amplificação real e trivial de disparar num app público.)
- **2026-07-16 (via warframe-farm-helper — app público read-only, sem auth/dinheiro):** Dois pontos de
  método para apps de **leitura sem login** (buscadores, dashboards públicos): (1) a superfície real é
  **input→URL externa (SSRF de PATH)** e **input→SQL/render**, não as classes de sessão/dinheiro — não
  desperdice o sweep tentando IDOR onde não há usuário. Quando o único input que toca uma URL externa é um
  `slug`/`id` que vira **só o PATH** de um host FIXO (ex.: `api.foo.com/item/<slug>`), o SSRF é baixo risco
  **desde que a validação (whitelist regex) rode ANTES de montar a URL** — prove disparando `..%2f..%2f`,
  `;`, espaço no slug e confirmando rejeição antes de qualquer fetch. (2) **CSP `style-src 'self'` SEM
  `'unsafe-inline'` quebra atributos `style=""`** (inline style attrs contam como inline-style e são
  bloqueados) — se a app usa `style=` inline, ou remove todos, ou usa `style-src 'self' 'unsafe-inline'`
  MANTENDO `script-src 'self'` estrito (é o script-src que barra XSS; style inline é risco baixo e some de
  vez se não há HTML de usuário). Testar CSP com `curl -I | grep -o "style-src[^;]*"` e confirmar que
  `script-src` NÃO ganhou `unsafe-inline` junto. Bônus: retornar **200 com `{error}`** para input inválido
  é mau cheiro de status (não-vuln) — valide na rota e devolva 400; um handler que delega a validação a uma
  função de serviço que retorna `{error}` costuma esquecer de setar o status. Re-validado que funciona bem:
  render 100% via `textContent`/DOM (nunca innerHTML com dado de API), markdown de conteúdo **sanitizado na
  INGESTÃO** (renderer do marked escapa HTML cru + remove href de esquema perigoso) — assim o cliente pode
  confiar no HTML servido; token-bucket por IP protegendo cota de API paga de 3º (CSE) + cache por query.
- **2026-07-17 (via warframe-farm-helper — SCRAPING de 3º renderizado no front):** Ao puxar dado de uma
  fonte externa que você NÃO controla (wiki/scraping, RSS, API de comunidade) e mostrá-lo, trate o conteúdo
  como HOSTIL mesmo que a fonte seja "confiável" — a wiki é editável por qualquer um, então uma recompensa
  de quest poderia conter `<img src=x onerror=...>`. Defesa em DUAS camadas, ambas necessárias: (1)
  **sanitizar na ORIGEM ao parsear** (o `cleanLines` do wikitext remove `<[^>]+>` e resolve
  links/templates para texto puro) e (2) **renderizar via `textContent`** no front (nunca innerHTML). Teste
  ao vivo: passe `<img src=x onerror=alert(1)>Evil` pelo parser e confirme que a tag some (só sobra "Evil").
  SSRF do fetch de scraping: **host FIXO + `encodeURIComponent`** do termo (que vem do dataset, não do
  usuário direto) = SSRF de path baixo risco; nunca deixe o host/scheme vir do input. Cacheie em banco com
  TTL longo (dado de wiki quase não muda) para não martelar o site de 3º. LIÇÃO META: "fonte confiável" não
  é sanitização — todo conteúdo de 3º renderizado passa por sanitização-na-origem + textContent, ponto.
