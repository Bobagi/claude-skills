---
name: game-audio
description: Pipeline de sons para jogo. Busca sons livres de crédito (Freesound filtrado por CC0, Kenney), confere a licença na página de cada um, baixa os originais pelo Chrome logado do usuário sem diálogo, ANALISA sem ouvir (níveis, piso de ruído, faixa de frequência, eventos com tempos, imagem de forma de onda + espectrograma), EDITA (corta, separa eventos, monta camadas, loop sem emenda, filtros, pitch) e converte para WAV 16 bits 48 kHz no formato que a engine quer; depois liga no jogo (Unity: regras de importação + SoundLibrary por papel) e confere em Play. Use SEMPRE que mexer com áudio de jogo: "baixe/busque sons", "esse som serve?", "corta/edita/converte esse áudio", "faz um loop", "troca o som sintetizado por gravado", lista de sons do GDD, sons que o usuário baixou e quer no jogo.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, WebSearch
---

# game-audio: do link ao som tocando no jogo, sem perder nada no caminho

Três scripts em `scripts/` (Python 3 + numpy, scipy, soundfile, Pillow; m4a/aac precisam de `pip install imageio-ffmpeg`):

| Script | Faz |
|---|---|
| `freesound.py` | `search "<termo>"` (só CC0 por padrão) e `check <url ou usuario/id>`: licença lida da **página do som**, duração, formato e a URL `/download/` |
| `analyze.py` | `python analyze.py <arquivos ou pastas> --png <pasta>`: formato, pico, RMS, piso de ruído, energia por faixa, eventos com início/fim, imagem por arquivo |
| `audiokit.py` | biblioteca de edição importada pelo script de conversão do projeto (copie para a pasta de ferramentas do projeto) |

Registre no fim de `log.md` o que aprender em cada uso (o que travou, que corte funcionou, que fonte é boa).

## 1. Licença primeiro (regra do Gustavo: "sons que não precisem dar créditos")

- **Só CC0** (domínio público) sem perguntar. CC-BY exige crédito: só com o ok dele. **Nunca** NC (não comercial)
  nem Sampling+: o jogo vai para a Steam.
- **Confira na página de cada som** (`freesound.py check`). Lista vinda de outra IA ou de busca não vale como prova:
  em 02/10 os 28 links que o ChatGPT marcou como CC0 estavam certos, mas a conferência é o que garante.
- Fontes CC0 boas: **Freesound** (filtro `license:"Creative Commons 0"`), **Kenney** (pacotes inteiros, download
  direto sem login: `kenney.nl/assets/<pacote>`, o .zip está na página), **Sonniss GDC Game Audio Bundle** (gratuito,
  royalty-free, sem crédito, mas são dezenas de GB: só com o ok do usuário). **As páginas de produto da Sonniss**
  (Creatures Zone, Dark Creature Sounds, Foley Essentials...) **são pagas**: não baixar, citar como opção de compra.
- Anote cada original no arquivo de créditos do projeto (página, autor, licença) mesmo sendo CC0.

## 2. Buscar o que falta

Para cada som pedido sem link: 2 ou 3 buscas com termos em inglês (`power down electrical`, `claws scratching`,
`keypad beep`, `metal door open`), `freesound.py search` mostra licença e duração. Baixe **vários candidatos** (é
barato) e escolha pela análise. Um som que não existe pronto se **monta por camadas** (seção 5): queda de energia =
estalo + zumbido morrendo + baque grave; parede caindo = desabamento + entulho + impacto.

## 3. Baixar (original, sem lossy)

O original do Freesound exige sessão logada; o preview HQ é mp3 público (perde qualidade, último recurso).

1. Use o **Chrome do usuário** (claude-in-chrome). Veja se está logado (avatar no topo). Se não estiver, peça o login.
2. **Antes do lote**: a opção do Chrome "Perguntar onde salvar cada arquivo" precisa estar **desligada**
   (`chrome://settings/downloads`). A extensão **não acessa** páginas `chrome://` nem janelas do Windows: peça ao
   usuário para desligar (uma vez). Sintoma de que está ligada: o arquivo fica como `<guid>.tmp` / `Não confirmado
   *.crdownload` na pasta de downloads.
3. **Baixe navegando** a aba para cada URL `/download/` (um `navigate` por arquivo; dá para mandar dezenas num
   `browser_batch`). O que **não** funciona: `fetch()` do arquivo na página (o download redireciona para o CDN de
   outra origem, sem CORS: "Failed to fetch") e vários `<a download>.click()` seguidos (o Chrome bloqueia "vários
   downloads" e a página trava).
4. Arquivo grande (um drone de 8 min tem 150 MB) chega depois: confira `*.crdownload` antes de mover.
5. Mova para `SourceAssets/Downloads/Sounds/<Categoria>/` (fora de `Assets`): o nome do Freesound
   (`<id>__<usuario>__<titulo>`) já guarda a origem.
6. A barra "Claude começou a depurar este navegador" aparece em todo uso da extensão; só some abrindo o Chrome com a
   flag `--silent-debugger-extension-api` (no atalho). Explique isso se o usuário reclamar.

## 4. Analisar (sem ouvir)

```
python <skill>/scripts/analyze.py SourceAssets/Downloads/Sounds/Power --png <scratchpad>/png
```

Leia o texto e **abra a imagem** (Read) dos que têm várias partes. Como ler:
- **eventos**: início e fim de cada trecho acima do piso de ruído. `--gap` junta trechos próximos (0,4 para frases e
  rugidos, 0,06 para impactos colados), `--above` sobe o limiar (24 a 30 em gravação com ruído de fundo).
- **energia por faixa** diz o que é: sub/grave dominante = trovão, drone, baque; agudo/ar = clique, chiado, metal.
  Centroide acima de 6 kHz num som que deveria ser grande = pequeno demais, desça o pitch.
- **piso de ruído** alto (acima de -45 dB) num one-shot: corte justo ou `gate`.
- **CLIP** = amostras saturadas na gravação: prefira outro trecho ou baixe o ganho, normalizar não conserta.
- No **espectrograma**, linha horizontal fixa = tom (zumbido, apito); corte vertical seco = emenda ruim.

Depois de editar, **analise a saída também** e olhe a imagem: foi assim que apareceram o estalo terminando seco do
apagão e o arrastar agudo demais da criatura (corrigidos com fade e pitch -12 a -3 + low-pass).

## 5. Editar e converter (audiokit)

O script do projeto (ex.: `SourceAssets/Tools/convert_sounds.py`) importa o `audiokit` e tem **uma função por
seção** (`water`, `doors`, `storm`...), cada corte com um comentário de **por que** aquele trecho. Rodar por seção:
`python convert_sounds.py storm house`. Receitas:

| Preciso de | Função |
|---|---|
| um evento inteiro de um arquivo | `oneshot(src, dst)` (mono, apara silêncio, fade, pico -1 dB) |
| um trecho por tempo | `segment(src, dst, inicio, fim, fade_out)` |
| N eventos de uma gravação (passos, pingos, tosses) | `split(src, "Pasta/nome_{0}.wav", N, min_gap, max_len)` |
| loop sem emenda | `make_loop(src, dst, segundos, crossfade)` ou `save(loudness(loop(d, s, xf)), dst)` |
| um som feito de vários | `mix((a, 0.0, 0), (b, 0.12, -6))` (dado, deslocamento s, ganho dB) e `concat(a, b)` |
| "atrás da parede", abafado, distante | `lowpass(d, 2200)` (parede), `lowpass(d, 600 a 900)` (trovão longe) |
| maior / menor | `pitch(d, -12 a +12)` (muda tempo junto, como fita) |
| textura em loop (arrastar molhado) | espalhe cópias curtas com pitch, ganho e espaço aleatórios (semente fixa) + ruído grave filtrado, e faça `loop` |

**Formato de saída** (Unity; outra engine segue a mesma ideia): WAV PCM 16 bits, 48 kHz. One-shot **mono** (fonte 3D
mixa para mono de qualquer jeito), pico -1 dB, silêncio aparado, fade curto. Loop: estéreo se for ambiente 2D, RMS
-24 dB, crossfade de 1 a 3 s. Unity não importa FLAC; MP3 como fonte deixa folga no início e estraga loop.
Normalize todos ao mesmo pico e deixe o **volume de cada uso** no código/ajustes (no Beneath the Shroud, `GameTuning`).

## 6. Ligar no jogo (Unity)

- Regras de importação por pasta/nome (`AssetPostprocessor`): `_loop` = Vorbis streaming; one-shot = ADPCM
  descomprimido na carga, mono; voz = Vorbis comprimido na memória.
- **Por papel, não por arquivo**: um ScriptableObject `SoundLibrary` com os papéis (`Thunder(close)`, `Cough()`,
  `Claws()`...) preenchido por um menu que procura os arquivos pelo prefixo; o código pede o papel e cai no som
  sintetizado se faltar. Som novo = arquivo com o prefixo certo + atualizar a biblioteca, sem mexer em código.
- Som que pertence a um objeto montado por builder (porta, alçapão, máscara) vai no builder; depois rode o rebuild.
- **Conferir**: compilar sem erro, a biblioteca sem papel vazio, os componentes da cena com os clipes certos
  (SerializedObject) e um Play disparando os eventos pela API pública, lendo o console. Peça ao usuário para
  **ouvir**: a análise acha defeito técnico, o gosto é dele.
- Som para um sistema que ainda não existe (ex.: combate): converta e registre na biblioteca assim mesmo, e diga
  que falta o sistema.

## 7. Fechar

- GDD/lista de pedidos: marque o que entrou e diga o que ficou de fora e por quê (sem CC0 bom, depende de compra).
- Créditos atualizados, `log.md` com a lição do dia.
