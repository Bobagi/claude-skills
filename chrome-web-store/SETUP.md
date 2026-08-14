# Setup unico da Chrome Web Store API (so o operador faz, ~10 min)

Objetivo: dar ao Claude credenciais para subir versoes novas de uma extensao e
publicar sozinho (`scripts/cws.py`). So a **conta Google dona da extensao** pode
fazer o consent.

## 1. Ligar a API

GCP Console -> "APIs e servicos" -> "Ativar APIs" -> procure **"Chrome Web Store
API"** -> Ativar. (Pode ser em qualquer projeto seu.)

## 2. Criar um OAuth client "Aplicativo da Web"

"APIs e servicos" -> "Credenciais" -> "Criar credenciais" -> "ID do cliente
OAuth" -> tipo **Aplicativo da Web** -> em "URIs de redirecionamento autorizados"
adicione exatamente `https://developers.google.com/oauthplayground` -> Criar.
Anote **client_id** e **client_secret**.

> ⚠️ **NAO escolha "Extensao do Chrome"** (parece o certo, mas NAO e): esse tipo
> pede um "ID do item" e serve para uma extensao autenticar usuarios em APIs do
> Google de DENTRO dela, nao para publicar na loja. So o **"Aplicativo da Web"**
> aceita a URI de redirecionamento do Playground. O client "Desktop" (ex.: o do
> AdMob) tambem nao serve aqui.

## 3. Pegar o refresh token (OAuth Playground)

- Abra https://developers.google.com/oauthplayground
- Engrenagem (canto sup. direito) -> marque **"Use your own OAuth credentials"**
  -> cole client_id e client_secret do passo 2.
- No campo **"Input your own scopes"** cole a URL INTEIRA (nao a palavra
  "webstore"): `https://www.googleapis.com/auth/chromewebstore` -> **Authorize
  APIs** -> login com a conta dona da extensao -> permita. Se der "app nao
  verificado": Avancado -> "Acessar (nao seguro)" (e o seu proprio app).
- "Step 2" -> **"Exchange authorization code for tokens"** -> copie o
  **Refresh token**.

## 4. Gravar as credenciais no box (chmod 600, fora de repo)

```
# ~/.config/bobagi-google/cws-client.json
{"web":{"client_id":"...","client_secret":"..."}}
# ~/.config/bobagi-google/cws-token.json
{"refresh_token":"..."}
# ~/.config/bobagi-google/cws-items.json   (apelido -> itemId + default)
{"default":"minha-ext","items":{"minha-ext":"<32-char-itemId>"}}
```

O **itemId** esta na URL da ficha:
`chromewebstore.google.com/detail/<slug>/<ITEMID>`.

Confira: `python3 scripts/cws.py doctor`.

## Notas que evitam dor de cabeca

- O **access token** (`ya29...`) do Playground e descartavel (~1h) e NUNCA e
  usado; o `cws.py` gera o dele a partir do refresh token. Nao precisa capturar.
- **Refresh token expira em 7 dias se o app OAuth ficar em "Testando".** Para
  tornar permanente: GCP -> "Tela de permissao OAuth" -> **"PUBLICAR APP"** (status
  "Em producao"). Nao precisa de verificacao do Google para uso proprio.
- Se o refresh token morrer, e so refazer o passo 3 e regravar `cws-token.json`.
- Segredos colados em chat: rotacione o client_secret no console quando puder.
