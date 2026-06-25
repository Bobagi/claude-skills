---
name: resume
description: Summarize a YouTube video from a link. Use this skill whenever the user shares a YouTube URL (youtube.com or youtu.be) and asks for a summary, recap, overview, or "resumo" of the video. Also trigger when the user says things like "me resume esse vídeo", "o que fala nesse vídeo?", "summarize this video", or pastes a YouTube link in any context where they clearly want to know what the video is about.
---

O usuário vai te fornecer um link de um vídeo do YouTube. Sua tarefa é:

1. Extrair o ID do vídeo da URL fornecida
2. Buscar a transcrição usando o script Python abaixo via bash
3. Gerar um resumo claro em português

**Script para buscar a transcrição:**

Salve o seguinte em `/tmp/get_transcript.py` e execute com o link do vídeo:

```python
from youtube_transcript_api import YouTubeTranscriptApi
import sys, re

url = sys.argv[1]
match = re.search(r"(?:v=|youtu\.be/|/shorts/)([A-Za-z0-9_-]{11})", url)
video_id = match.group(1)

api = YouTubeTranscriptApi()
transcript_list = api.list(video_id)
transcript = transcript_list.find_transcript(["pt", "pt-BR", "en"])
fetched = transcript.fetch()
text = " ".join([t.text for t in fetched])
print(text)
```

```bash
pip install youtube-transcript-api --break-system-packages -q
python3 /tmp/get_transcript.py "URL_DO_VIDEO"
```

**Formato do resumo:**

Apresente o resumo com:
- **Tema principal** do vídeo
- **Pontos mais importantes** abordados (em prosa, sem bullet points)
- **Conclusão ou mensagem final**

Seja claro e conciso. O resumo deve capturar a essência do vídeo sem ser excessivamente longo.

**Importante:** Se a transcrição não estiver disponível em português ou inglês, informe o usuário e tente outros idiomas disponíveis listados pela API.
