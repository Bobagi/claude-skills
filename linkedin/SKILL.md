---
name: linkedin
description: Lê e edita o perfil do LinkedIn do usuário via Playwright + Chrome com debug remoto, e audita o perfil contra boas práticas de visibilidade para recrutador. Use quando o usuário pedir para ver, revisar, auditar ou alterar qualquer coisa do LinkedIn dele (headline, Sobre, experiências, competências, projetos, Em destaque, idiomas, formação, dados de contato) ou perguntar como aparecer mais em buscas de recrutador.
allowed-tools: Bash, Read, Write, Edit
---

# LinkedIn — leitura, edição e auditoria do perfil

Toda operação passa por **um CLI só**: `scripts/li.mjs`. Não escreva scripts Playwright
avulsos — o que você precisa já está aqui, e o CLI carrega as armadilhas do LinkedIn
(campos que apagam dados, listas virtualizadas, saves silenciosamente perdidos) que
custaram muitas sessões para mapear.

## Regra de ouro

**Escrita é dry-run por padrão.** Sem `--commit`, o comando preenche o formulário,
tira um print e vai embora sem salvar. O fluxo obrigatório é:

1. rodar sem `--commit` → 2. `Read` no print → 3. **confirmar com o usuário** →
4. rodar de novo com `--commit` → 5. o próprio comando recarrega a página e verifica.

O perfil é público e ao vivo. Nunca pule o passo 3.

## Setup

```bash
cd ~/.claude/skills/linkedin/scripts        # é junction p/ D:\projetos\claude-skills\linkedin
node li.mjs doctor
```

`CHROME_DOWN` → suba o Chrome dedicado (o login persiste no `user-data-dir`, loga uma vez só):

```bash
powershell -Command "Start-Process 'C:\Program Files\Google\Chrome\Application\chrome.exe' -ArgumentList '--remote-debugging-port=9222','--user-data-dir=D:\dev\linkedin\chrome-profile'"
```

`NOT_LOGGED_IN` → o usuário precisa logar manualmente nessa janela do Chrome, uma vez.

## Comandos

Leitura (barato):

```bash
node li.mjs doctor                       # chrome + login + nome + tamanho da headline
node li.mjs stats                        # visualizações, aparições em busca, conexões
node li.mjs get skills                   # UMA seção no stdout
node li.mjs read --sections experience,skills   # várias -> .out/profile.txt
node li.mjs pencils experience           # aria-labels dos lápis (use como --match)
node li.mjs audit                        # 15 checagens de visibilidade + score
```

Escrita (sempre preview primeiro):

```bash
node li.mjs set-text headline --file h.txt          # e depois --commit
node li.mjs set-text about --file about.txt
node li.mjs set-exp-desc --match "Unifique" --file desc.txt
node li.mjs set-exp-title --match "Unifique" --value "Software Engineer"
node li.mjs set-edu --match "USP" --degree "Bacharelado" --field "Ciência da Computação"
node li.mjs add-skill "TypeScript" "Kafka" "gRPC"
node li.mjs add-language "Inglês" advanced          # elementary|limited|professional|advanced|native
node li.mjs add-featured https://exemplo.com/ --title "CV"
node li.mjs add-project --file proj.json            # { name, description, url }
node li.mjs set-site https://bobagi.space/
```

## Economia de tokens

- Prefira `get <seção>` a `read`; prefira `audit` a ler o perfil inteiro e julgar no olho.
- `read` grava tudo em `.out/profile.txt` e imprime só os tamanhos — leia o arquivo
  **só se** precisar do conteúdo, e prefira `--sections` a puxar tudo.
- Texto longo vai em arquivo (`--file`), nunca inline na linha de comando: o CLI
  preserva quebras de linha via `insertText`, e argumentos de shell não.
- Os prints vão para `.out/`; abra com `Read` apenas o print da mudança em questão.
- Não redirecione stdout para arquivo para depois lê-lo — a saída já é curta de propósito.

## Antes de editar

Leia `references/best-practices.md` — o que realmente move visualização de recrutador,
e os limites de cada campo. Para escolher o alvo da edição, `audit` já diz o que está
falhando e com que número.

Se um comando falhar de um jeito novo, `references/dom-notes.md` tem o mapa do DOM e
das armadilhas provadas; `references/capabilities.md` diz o que a skill **não** faz
(e o que precisa ser feito à mão).

## Limites

headline 220 · Sobre 2.600 · descrição de experiência 2.000 · descrição de projeto 2.000 ·
competências 100 (só 3 fixadas aparecem no perfil). O contador do LinkedIn cobra ~1
caractere a mais por quebra de linha; o CLI já desconta isso e aborta antes de estourar.
