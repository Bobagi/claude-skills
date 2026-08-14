# Chrome Web Store

Invoque a skill **chrome-web-store** (em `~/.claude/skills/chrome-web-store/`) e
siga o `SKILL.md` dela. Publica extensoes do Chrome via API (upload de pacote +
publish/enviar pra revisao), como a `google-play` faz com apps.

- Sem argumentos: rode `cws.py doctor` e apresente o estado do item (versao
  publicada, uploadState, se ha algo em revisao).
- Com argumentos (`$ARGUMENTS`): interprete a intencao (ex.: "sobe a nova versao
  do Farolivro", "publica o zip X", "reenvia apos a rejeicao", "qual o estado na
  loja") e use os subcomandos do `cws.py` (`upload`, `publish`, `upload-publish`,
  `status`), com `--item` quando houver mais de uma extensao.
- Antes de `upload-publish`, confirme que o `version` do manifesto no zip e MAIOR
  que o publicado (a loja recusa versao igual/menor).
- Lembre os limites: a API nao edita descricao longa/screenshots da ficha, e a
  publicacao passa por revisao do Google. NAO liste nomes de lojas/marcas na
  descricao (keyword spam).
- Se as credenciais (`~/.config/bobagi-google/cws-client.json` + `cws-token.json`)
  nao existirem, mostre o passo a passo do `SETUP.md` e pare.
