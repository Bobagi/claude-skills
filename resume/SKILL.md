---
name: resume
description: Summarize a YouTube video from a link. Use this skill whenever the user shares a YouTube URL (youtube.com or youtu.be) and asks for a summary, recap, overview, or "resumo" of the video. Also trigger when the user says things like "me resume esse vídeo", "o que fala nesse vídeo?", "summarize this video", or pastes a YouTube link in any context where they clearly want to know what the video is about.
---

O usuário vai te fornecer um link de um vídeo do YouTube. Sua tarefa é:

1. Extrair o ID do vídeo da URL fornecida
2. Buscar a transcrição (métodos abaixo, em ordem — pare no primeiro que funcionar)
3. Gerar um resumo claro em português

## Método 1 — youtube-transcript-api (rápido, tente primeiro)

Salve o script abaixo no scratchpad usando a ferramenta **Write** (não crie o arquivo via
heredoc dentro do mesmo comando que roda pip/python — se o comando estourar timeout, o
arquivo fica pela metade ou nem é criado):

```python
from youtube_transcript_api import YouTubeTranscriptApi
import sys, re

url = sys.argv[1]
match = re.search(r"(?:v=|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})", url)
video_id = match.group(1)

api = YouTubeTranscriptApi()
transcript_list = api.list(video_id)
try:
    transcript = transcript_list.find_transcript(["pt", "pt-BR", "en"])
except Exception:
    transcript = next(iter(transcript_list))  # pega o que tiver (ex.: es)
fetched = transcript.fetch()
print(" ".join(t.text for t in fetched))
```

```bash
pip install youtube-transcript-api -q
python get_transcript.py "URL_DO_VIDEO"
```

**Se falhar com `RequestBlocked` / `IpBlocked`** ("Sign in to confirm you're not a bot"):
é o anti-bot do YouTube bloqueando requisições fora de navegador. NÃO insista repetindo —
vá direto ao Método 2. (O `yt-dlp` sem cookies falha pelo mesmo motivo, e
`--cookies-from-browser chrome/edge` falha no Windows por causa da criptografia app-bound
dos cookies — não perca tempo com isso.)

## Método 2 — navegador real via chrome-devtools MCP (passa no anti-bot)

Um Chrome de verdade não é bloqueado. Use as ferramentas do plugin `chrome-devtools-mcp`
(carregue os schemas via ToolSearch se estiverem deferred):

1. `new_page` com a URL do vídeo.
2. Abra o painel de transcrição via `evaluate_script` (expandir a descrição → clicar no
   botão de transcrição da descrição; clicar em qualquer elemento com texto "Transcrição"
   NÃO funciona — o painel fica `HIDDEN`):

```js
async () => {
  const expander = document.querySelector('tp-yt-paper-button#expand, #description-inline-expander #expand');
  if (expander) { expander.click(); await new Promise(r => setTimeout(r, 800)); }
  const btn = document.querySelector('ytd-video-description-transcript-section-renderer button');
  if (btn) { btn.click(); await new Promise(r => setTimeout(r, 2000)); }
  const panel = document.querySelector('ytd-engagement-panel-section-list-renderer[target-id*="transcript"]');
  return { visibility: panel?.getAttribute('visibility') };  // quer EXPANDED
}
```

3. Extraia o texto do painel. **Atenção:** a UI nova do YouTube não usa mais
   `ytd-transcript-segment-renderer` (seletor retorna 0 segmentos) — leia o `innerText`
   do painel e filtre timestamps/labels. Use `filePath` no `evaluate_script` para não
   estourar o contexto:

```js
() => {
  const panel = document.querySelector('ytd-engagement-panel-section-list-renderer[target-id*="transcript"]');
  const lines = panel.innerText.split('\n').map(l => l.trim()).filter(Boolean);
  const text = lines.filter(l =>
    !/^\d+:\d+(:\d+)?$/.test(l) &&
    !/^\d+\s+(segundos?|minutos?|horas?)/.test(l) &&
    l !== 'Transcrição' && l !== 'Pesquisar transcrição'
  ).join(' ').replace(/\s+/g, ' ');
  return { length: text.length, text };
}
```

Dicas: `window.ytInitialPlayerResponse.videoDetails` (title, author, lengthSeconds) e
`.captions.playerCaptionsTracklistRenderer.captionTracks` (idiomas disponíveis) já estão
na página. NÃO tente dar `fetch` no `baseUrl` das captions de dentro da página — retorna
corpo vazio (exige token PO); o painel de transcrição da UI é o caminho confiável.

## Formato do resumo

Apresente o resumo com:
- **Tema principal** do vídeo
- **Pontos mais importantes** abordados (em prosa, sem bullet points)
- **Conclusão ou mensagem final**

Seja claro e conciso. O resumo deve capturar a essência do vídeo sem ser excessivamente longo.

**Vídeos de aporte/carteira de investimentos:** se o vídeo for desse tipo (ex.: "aporte do mês",
"carteira de investimentos", canais de finanças que compram/vendem ativos ao vivo), as compras e
vendas feitas são o ponto principal — SEMPRE termine o resumo com uma tabela simples listando cada
ativo, tipo (ação/FII/cripto/ETF/renda fixa), valor e uma observação curta (motivo da compra/venda,
se mencionado). Se houve venda ou realocação, liste também, mesmo que tenha ocorrido em episódio
anterior mas seja referenciada no vídeo atual. Não pule essa tabela substituindo por prosa — é o
dado que o usuário mais quer.

**Importante:** Se a transcrição não estiver disponível em português ou inglês, use o idioma que
existir (ex.: espanhol) e informe o usuário — o resumo continua sendo em português.
