---
name: whatsapp-export
description: Exporta uma conversa do WhatsApp Web (texto, áudios, imagens, figurinhas, documentos) de um período e transcreve os áudios localmente com Whisper na GPU, usando o projeto Bobagi/whatsapp-export (D:\Projetos\whatsapp-export no PC de casa). Use SEMPRE que o usuário pedir para "pegar/coletar/salvar/exportar as mensagens da conversa com Fulano", "transcrever os áudios do WhatsApp", "o que a Fulana me mandou nos últimos dias", "resumir a conversa do WhatsApp", "salvar os áudios do zap", ou qualquer pedido de tirar conteúdo de uma conversa do WhatsApp para fora dele. Não refaça a solução do zero: o projeto já existe.
---

# whatsapp-export

O projeto já existe e funciona (primeiro uso em 2026-11-16: conversa com a Dayse, 181 mensagens, 26 áudios
transcritos). **Não reescreva do zero.** Repo: `Bobagi/whatsapp-export` (público, só código). No PC de casa:
`D:\Projetos\whatsapp-export` (ler o `README.md` de lá antes de começar). Em outra máquina: `gh repo clone
Bobagi/whatsapp-export` e instalar conforme o README.

## Fluxo (pedido típico: "exporta a conversa com Fulano dos últimos N dias")

1. **Navegador da máquina da sessão** (no PC de casa, o Brave; ver a regra de navegador no CLAUDE.md global e a
   memória `navegador-desta-maquina`). Carregue as ferramentas do Claude in Chrome num único `ToolSearch`.
2. Abra uma aba própria em `https://web.whatsapp.com` (a sessão do usuário já está logada no perfil; abrir a
   aba nova "toma" a sessão da aba dele, avise no fim que ele clica em "Usar aqui" na aba dele).
3. Injete o conteúdo de `exporter.js` com `javascript_tool` e rode
   `await waExport({ chat: 'Fulano', hours: 24 * N })` (ou `since: 'AAAA-MM-DD'`). `chat` casa por trecho do
   nome; se houver mais de uma conversa, use o nome exato. Retorna uma linha com contagens.
4. O JSON cai na pasta de downloads do navegador (no PC de casa: `D:\Downloads\wa-<chat>-<data>.json`; a
   pasta real está em `Preferences` do Brave, chave `download.default_directory`).
5. `D:\Projetos\whatsapp-export\.venv\Scripts\python.exe process.py <json>` grava em
   `conversas/<chat>/<AAAA-MM-DD_HHMM>/`: `conversa.md`/`.txt` (áudio transcrito inline), `mensagens.json`,
   `midia/`. Rodar de novo não retranscreve (cache `.txt` por áudio).
6. Leia o `conversa.md` para resumir ou extrair o que o usuário pediu. Feche a aba que você abriu.

## Armadilhas já resolvidas

- **O `javascript_tool` bloqueia saída com cara de cookie/query string** (`[BLOCKED: Cookie/query string
  data]`, por exemplo um mimetype com `codecs=opus`). Por isso os dados saem por **download de arquivo**, nunca
  pelo retorno da ferramenta. Retorne só contagens e textos simples.
- `loadEarlierMsgs({ chat })` recebe um **objeto** (em 2026-11); passar o chat direto dá
  `Cannot read properties of undefined (reading 'pendingInitialLoading')`.
- Mídia: `msg.downloadMedia({downloadEvenIfExpensive:true, rmrReason:1, isUserInitiated:true})` e depois o
  blob de `WAWebMediaInMemoryBlobCache` ou `mediaObject.mediaBlob.forceToBlob()` (como o whatsapp-web.js faz).
  Se os módulos internos mudarem, ver `src/structures/Chat.js` e `src/util/Injected/Utils.js` do whatsapp-web.js.
- **PyAV 19+ quebra o faster-whisper 1.2.1** (`metadata_errors`): o `requirements.txt` fixa `av<17`.
- O Whisper erra nomes próprios ("Claude" vira "Cloud"/"Claudio", "Meshy" vira "Mesh"); leve isso em conta
  ao resumir.

## Privacidade

`conversas/` e os JSON exportados são dados pessoais: ficam fora do Git (`.gitignore`) e nunca vão para IA
externa (resuma você mesmo, não delegue a Groq/Gemini). Ao levar trechos para um documento compartilhado
(GDD, etc.), leve só o que é do assunto e aponte para o arquivo local em vez de copiar a conversa.
