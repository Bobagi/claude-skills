# Setup único — Google Play Developer API (só o operador pode fazer)

Resultado final: um arquivo `~/.config/bobagi-google/play-service-account.json`
na máquina onde o Claude roda, com a service account convidada na Play Console.
Leva ~10 minutos, uma única vez.

## 1. Projeto no Google Cloud

1. Acesse https://console.cloud.google.com logado na **mesma conta Google do
   Google Play Console**.
2. Crie um projeto (sugestão de nome: `bobagi-apps-automation`) — ou reuse um.
   > Este mesmo projeto poderá ser usado depois para AdMob API e Firebase.

## 2. Ativar a API

1. Menu **APIs & Services → Library**.
2. Procure **"Google Play Android Developer API"** → **Enable**.

## 3. Criar a service account + chave

1. **IAM & Admin → Service Accounts → Create service account**.
2. Nome: `claude-play-publisher`. Não precisa de role no GCP (as permissões
   vêm da Play Console). **Done**.
3. Na lista, clique na service account → aba **Keys → Add key → Create new key
   → JSON** → baixa um arquivo `.json`.

## 4. Convidar a service account na Play Console

1. https://play.google.com/console → **Usuários e permissões → Convidar novos
   usuários**.
2. E-mail: o da service account (algo como
   `claude-play-publisher@bobagi-apps-automation.iam.gserviceaccount.com`).
3. Em **Permissões do app**, adicione **Tic Tac Verse** e marque:
   - *Lançar apps em faixas de teste* (testing tracks)
   - *Lançar apps em produção* (production releases)
   - *Editar a presença na loja* (store listing)
   - *Responder avaliações* (reply to reviews)
4. **Enviar convite** (service account aceita na hora, sem e-mail).

## 5. Colocar a chave na máquina do Claude

Do seu PC (PowerShell/Git Bash), envie o JSON baixado para a VPS **por scp**
(não cole o conteúdo no chat):

```bash
scp caminho/para/arquivo.json root@bobagi.space:/root/.config/bobagi-google/play-service-account.json
```

Se a pasta não existir, peça ao Claude para criá-la (`mkdir -p` + `chmod 700`)
ou rode antes: `ssh root@bobagi.space "mkdir -p /root/.config/bobagi-google"`.

## 6. Validar

Peça ao Claude: **"rode o doctor da skill google-play"** — ele executa
`gplay.py doctor` e confirma acesso de ponta a ponta (o doctor também ajusta
o chmod 600 se você pedir).

## Notas

- A chave dá poder de publicar releases — trate como senha. Se vazar:
  GCP → Service Accounts → Keys → deletar a chave e gerar outra.
- A API **não** consegue: criar app novo, preencher data safety/app content.
  Isso continua na Play Console.
