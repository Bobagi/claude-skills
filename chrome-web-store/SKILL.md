---
name: chrome-web-store
description: Publica extensoes do Chrome na Chrome Web Store via API oficial (upload de pacote .zip + publish/enviar pra revisao), do mesmo jeito que a google-play faz com apps. Use quando o usuario pedir para lancar/subir/publicar/atualizar uma extensao do Chrome, subir uma nova versao do .zip/.crx na loja, reenviar apos rejeicao, ou checar o estado (uploadState/em revisao) de um item da Chrome Web Store. Extensao padrao - Farolivro (comparador de livros).
allowed-tools: Bash, Read
---

# Chrome Web Store (Publish API)

Automatiza subir uma versao nova de uma extensao e publicar, via a **Chrome Web
Store API v1.1**. Tudo pelo script **`scripts/cws.py`** (python3 + urllib, sem pip).

## Credenciais (uma vez; nunca imprimir o conteudo)

Em `~/.config/bobagi-google/` (chmod 600, FORA de qualquer repo):
- `cws-client.json` : OAuth client tipo **Aplicativo da Web**
  `{"web":{"client_id":"...","client_secret":"..."}}`
- `cws-token.json`  : `{"refresh_token":"..."}` (escopo `chromewebstore`)
- `cws-items.json`  : (opcional) apelidos -> itemId + default
  `{"default":"farolivro","items":{"farolivro":"jnkjabpgnocifbnnceoepijbcggmkkek"}}`

Se `cws-client.json`/`cws-token.json` nao existirem, o **setup unico do operador
ainda nao foi feito** -> mostre `SETUP.md` a ele e pare (o refresh token so a
conta dona da extensao gera). Comece qualquer sessao com `cws.py doctor`.

## Comandos

```bash
S=~/.claude/skills/chrome-web-store/scripts/cws.py

python3 $S doctor                                   # valida auth + estado do item
python3 $S status                                   # uploadState / erros do rascunho
python3 $S upload --zip backend/static/ext/x.zip    # sobe um pacote novo
python3 $S publish --target default                 # publica (envia pra revisao)
python3 $S upload-publish --zip dist/ext.zip        # sobe + publica de uma vez
python3 $S items                                    # apelidos configurados
```

`--item <apelido|itemId>` escolhe a extensao (sem ele, usa o `default` do
`cws-items.json`). `--target`: `default` (todos com o link / publico) ou
`trustedTesters`.

## Fluxo de uma release

1. `cws.py doctor` (confirma auth + le o item; anota o `crxVersion` publicado).
2. Garanta que o **`version` do manifesto** no zip e MAIOR que o publicado
   (a loja rejeita versao igual/menor).
3. `cws.py upload-publish --zip <zip>` -> `uploadState: SUCCESS` e `status: OK`.
4. A extensao entra em **revisao do Google** (1-3 dias; um host novo em
   `host_permissions` pode demorar mais). Quem ja tem a versao antiga
   auto-atualiza quando aprovar.

## Limites (honesto, deixe claro ao operador)

- A API sobe **pacote + publica**. NAO edita a **descricao longa da ficha**,
  screenshots, icone da loja nem categoria - isso continua no **painel**. O
  `name`/`description` (do manifesto, limite **132 chars** no description) e as
  permissoes/host_permissions atualizam junto com o pacote.
- Publicar **passa por revisao** do Google (nao e instantaneo).
- **Keyword spam:** NAO liste nomes de lojas/marcas de 3os na descricao da ficha
  (motivo real de rejeicao ja visto); a lista de sites suportados fica no site do
  produto, nao na ficha.
- **Validade:** a API v1.1 morre em **2026-10-15**; depois disso migrar o script
  para a v2 (endpoints mudam, a ideia e a mesma).
- **Refresh token:** se o app OAuth (tela de permissao) estiver em **"Testando"**,
  o Google expira o refresh token em **7 dias**. Publicar o app OAuth ("Em
  producao") torna permanente. Ver `SETUP.md`.

## Complementa

`google-play` (apps na Play), `admob`/`google-ads` (receita/campanha),
`google-search-console` (SEO). Reusa o mesmo diretorio de credenciais
`~/.config/bobagi-google/`, mas com OAuth **proprio** (client "Aplicativo da Web"
+ refresh token de escopo `chromewebstore`), separado do service account do Play.
