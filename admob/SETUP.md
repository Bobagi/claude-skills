# Setup único — AdMob API (só o operador pode fazer)

Resultado final: dois arquivos em `~/.config/bobagi-google/` na máquina do
Claude (`admob-client.json` + `admob-token.json`). ~10 minutos, uma vez.
Pode (e deve) usar o MESMO projeto GCP do setup da skill `google-play`.

## 1. Ativar a API

1. https://console.cloud.google.com → projeto `bobagi-apps-automation`.
2. **APIs & Services → Library** → procure **"AdMob API"** → **Enable**.

## 2. Consent screen (tela de consentimento)

1. **APIs & Services → OAuth consent screen**.
2. Tipo **External** → preencha só o obrigatório (nome do app:
   `bobagi-automation`, seu e-mail).
3. **IMPORTANTE:** depois de criar, clique em **"Publish app"** (status
   *In production*). Em modo *Testing* o refresh token expira a cada 7 dias.
   O aviso de "app não verificado" na hora do consentimento é normal — é você
   autorizando você mesmo (clique em *Avançado → continuar*).

## 3. OAuth client

1. **APIs & Services → Credentials → Create credentials → OAuth client ID**.
2. Tipo: **Desktop app**. Nome: `claude-admob`.
3. Baixe o JSON do client e mande para a VPS (por scp, não pelo chat):

```bash
scp caminho/para/client.json root@bobagi.space:/root/.config/bobagi-google/admob-client.json
```

## 4. Consentimento único (gera o refresh token)

1. Peça ao Claude: **"rode o auth da skill admob"**. Ele imprime uma URL.
2. Abra a URL **no navegador do seu PC**, logado na conta dona do AdMob
   (a mesma do Play Console).
3. Aceite. O navegador vai tentar abrir `http://localhost:8765/?code=...` e
   **vai falhar** — é esperado. Copie a URL inteira da barra de endereços.
4. Cole a URL no chat quando o Claude pedir. Ele troca o code pelo refresh
   token e salva com chmod 600.

## 5. Validar

Peça: **"rode o doctor da skill admob"** → deve imprimir
`AdMob API : ok — publisher ca-app-pub-5349785075769585`.

## Notas

- O refresh token dá acesso de LEITURA aos relatórios (+ tentativa de escrita
  de inventário, que o Google restringe). Se vazar: GCP → Credentials →
  deletar o OAuth client (invalida tudo).
- Criar/editar ad units e mediação normalmente continua manual em
  https://apps.admob.com (a API devolve 403 para contas sem account manager).
