---
name: store-promo-video
description: Produz o vídeo promocional da ficha da loja (Google Play, e serve de base para anúncios) de um app ou jogo, no padrão "dopamina": gancho nos primeiros 2 s, cortes no compasso da música, zoom de impacto, tremor, flash, câmera lenta no clímax, legendas curtas que funcionam no mudo, música CC0 com o drop no maior momento, efeitos sonoros do próprio app sincronizados ao quadro, fecho curto com o ícone animado (ComfyUI/Wan 2.2), um vídeo por idioma da ficha, e coloca o link do YouTube na ficha pela API. Tudo dentro das regras da Play (jogo real nos primeiros 10 s, 80% de uso real, sem CTA de download, sem barras pretas). Use em "faça o vídeo da loja/da Play", "vídeo promocional", "trailer do app", "vídeo para a ficha", "vídeo engajante/viciante do jogo", "promo video".
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, WebSearch, Agent, Skill
---

# store-promo-video: do app rodando ao vídeo na ficha

Feito pela primeira vez no **Blockaboom** (2026-10-07). A implementação completa e testada está em
`scripts/blockaboom-example/` (cópia de `D:\Projetos\blockaboom\scripts\promo\`) e o README de lá mostra o
resultado. **Copie para o projeto novo e adapte**: as partes genéricas (relógio virtual, áudio offline, editor)
não mudam; o que muda são as cenas, os ganchos de debug do app, as legendas e a música.

Regras e técnicas com fontes: **`reference/play-video-rules.md`**. Leia antes de roteirizar.

## 0. Princípios (o que não se negocia)
1. **Tudo dentro do cartão é o app real**, gravado do build de verdade. A edição só corta, enquadra, dá zoom,
   treme, pisca, desacelera e legenda. IA (ComfyUI) só no fecho de marca (1 a 3 s), nunca fingindo uso.
2. **Gancho em 0 a 2 s** com o momento mais satisfatório do app, e o **drop da música cai nele**.
3. **Mudo primeiro**: uma legenda de 3 a 5 palavras por cena. Sem "Baixe agora", "#1", "Grátis", preço.
4. **Um vídeo por idioma** da ficha (UI do app no idioma + legendas traduzidas). Ficha sem vídeo próprio
   (ex.: es-ES) recebe o do idioma irmão (es-419).
5. **Música CC0** (sem Content ID): vídeo pode ficar com monetização desligada, como a Play exige.
6. Antes de entregar, **abra quadros do vídeo final** (folha de contato) e confira enquadramento e legendas.

## 1. Pesquisa e roteiro
- Se já faz tempo desde 2026-10, rode um Agent de pesquisa para atualizar `reference/play-video-rules.md`
  (regras da Play mudam).
- Liste os 6 a 8 **momentos** mais fortes do app (no jogo: explosão grande, corrente de combos, quase-derrota
  virando vitória, recurso de progresso tipo vila/coleção, recurso diário, final "tudo limpo"). Para app não-jogo:
  a transformação principal (antes/depois), o resultado aparecendo, a tela "uau".
- Estrutura de 27 s: gancho (1 compasso) → ritmo → tensão + câmera lenta → variedade (1 corte por recurso) →
  clímax → fecho com ícone (2 compassos). Cada corte num compasso da música.

## 2. Captura do app (o coração: quadros perfeitos, sem depender da velocidade da máquina)

### App/jogo web (Phaser, canvas, React, Flutter web, Capacitor): relógio virtual
`record.mjs` injeta antes do app um relógio falso: `requestAnimationFrame`, `setTimeout/setInterval`,
`performance.now` e `Date.now` passam a obedecer `window.__vt.advance(ms)`. O gravador avança 1/60 s, fotografa
(CDP `Page.captureScreenshot`, jpeg 93) e repete: **60 fps perfeitos**, mesmo que cada quadro leve 50 ms.
- Viewport do celular (360x640) com **`--force-device-scale-factor=3`** na linha de comando do Chrome
  (no Windows o `deviceScaleFactor` do puppeteer é IGNORADO no headless e sai 360x640; armadilha real).
- Chrome do sistema: `C:/Program Files/Google/Chrome/Application/chrome.exe` (ou `CHROME_BIN`).
- Durante o carregamento, avance o relógio em laço até o app estar pronto (não use `waitForFunction` com
  polling por rAF: o rAF está congelado).
- **Cenas montadas**: cada cena semeia o `localStorage` (jogador veterano + estado montado à mão: tabuleiro quase
  cheio, bandeja escolhida, contadores perto do prêmio) e depois faz jogadas **reais** por toque sintético
  (`touchStart/Move/End` com easing, 14 a 22 quadros de deslize, segurar 4 a 24 quadros antes de soltar dá tensão).
  Valide o estado montado em código (ex.: nenhuma linha já cheia) antes de gravar.
- **Silencie o que polui**: toasts, avisos de missão/conquista, dicas (marque tudo como já visto no save e
  troque o método de toast por no-op só na gravação).
- `take.mark('boom')` no quadro da jogada grande: o editor usa para zoom/tremor/flash e câmera lenta.
- Autoplayer guloso (mais linhas, depois encaixe mais justo) para trechos "naturais".
- **Não determinístico?** Cenas com aleatoriedade (bandeja sorteada) mudam a cada gravação: confira os `marks`
  impressos e ajuste o trecho usado no editor.

### App nativo (Flutter mobile, Kotlin, Unity no Android)
- Gravação de tela real: `scrcpy --record=cena.mp4 --max-fps=60 --video-bit-rate=20M` (scrcpy já instalado via
  winget) com o aparelho/emulador; som do app com `--audio-codec=aac` (Android 11+).
- Toques automáticos: `adb shell input swipe x1 y1 x2 y2 dur` ou testes de integração (Flutter `integration_test`,
  Espresso) para repetir a mesma cena em cada idioma (`adb shell cmd locale` ou `setprop persist.sys.locale`).
- Unity: `Time.captureFramerate = 60` + `ScreenCapture.CaptureScreenshot` por quadro = o mesmo "relógio virtual"
  da versão web.
- Sem o log de efeitos, o som vem da própria gravação (scrcpy) ou dos sons do app colocados à mão nos marks.

## 3. Som do app sincronizado (versão web)
O app expõe o objeto de efeitos no modo debug (no Blockaboom: `__bb.sfx`, só com `?debug=1`). O gravador
embrulha cada método e registra `{nome, args, t}`. `render-audio.mjs` abre o app com `AudioContext` trocado por
um `OfflineAudioContext` cujo `currentTime` é um getter que devolve a hora do evento, replaya as mesmas chamadas
e renderiza um WAV: **o som real do sintetizador do app, alinhado à amostra**. O editor remapeia os horários para
a linha do tempo editada (inclusive dentro da câmera lenta) e renderiza uma faixa única.
App que toca arquivos de áudio (não sintetiza): registre `{arquivo, t}` e mixe os arquivos no ffmpeg com `adelay`.

## 4. Música
- Skill **`game-audio`**: `freesound.py search "<termo>"` (só CC0), `check <usuario/id>` lê a licença na página.
  Termos que funcionaram: "edm drop", "happy edm loop", "future bass", "1 min edm loop".
- O preview HQ (mp3 público do CDN, `cdn.freesound.org/previews/...-hq.mp3`) basta para YouTube; pegue a URL
  no HTML da página do som com `curl`.
- `python scripts/find_drop.py musica.mp3`: BPM, compasso, curva de energia e o drop provável. Escolha uma
  faixa com subida e drop claros e ~30 s de energia alta depois do drop.
- No editor: `offset = drop_na_faixa - momento_do_gancho_no_video`; cortes em `T0 + n * compasso`.

## 5. Fecho com o ícone animado (ComfyUI, opcional e curto)
- Suba o ComfyUI headless (`C:\ComfyUIFiles\scripts\start-comfyui-server.ps1`) e rode
  `python D:\Projetos\comfyui\scripts\wan_loop.py --image <icone 1024.png> --name <app>_icon_loop --width 640
  --height 640 --frames 49 --fps 16 --interp 2 --seed 777 --prompt "<elementos do ícone> gently float and bob in
  place, tiny sparkles twinkle, soft glow pulses, light rays slowly rotate behind, static camera, smooth motion"`
  (~10 min no 3060 Ti; loop sem emenda porque o primeiro e o último quadro são o ícone).
- Extraia o mp4 de 32 fps (`..._32fps_..._00002.mp4`) para PNGs e toque no fecho a 32/60 da velocidade.
- Confira uma folha de contato: se deformar o ícone, troque a seed ou use o ícone parado com "pop" (o editor
  já cai nesse modo se a pasta não existir).

## 6. Edição (`compose.py`)
- `TIMELINE`: (cena, início, fim, trechos de velocidade `[(de, até, velocidade)]`, legenda, câmera). Câmera lenta
  = trecho com 0,35 a 0,4; o editor mescla quadros vizinhos para suavizar.
- Efeitos por `mark`: zoom de impacto 7,5% decaindo em ~4 quadros, tremor 16 px decaindo, flash 38% por 2 quadros
  (metade para marks menores). Entrada de cena 1,05→1,0 em 8 quadros. Câmera "push" para cenas largas (vila):
  1,05→1,18, sem cortar bordas nem cabeçalho (**conferir num quadro**; 1,45 cortou a ilha).
- Cartão 86% com cantos arredondados sobre fundo borrado do próprio quadro (sem barras pretas); legenda com a
  fonte do app (woff2 → ttf com `fontTools`; variável: `set_variation_by_axes([700])`), contorno escuro, "pop"
  com ease-out-back.
- Saída: H.264 CRF 16, yuv420p, 1080x1920 60 fps, AAC 256k, música + efeitos com `loudnorm=I=-14`.
- ffmpeg sem instalar: `C:\ComfyUIFiles\.venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe`.
- `--preview` (540x960, rápido) para iterar; final por idioma leva ~5 min.

## 7. Conferir e publicar
1. Folha de contato a 2 fps de cada idioma (ffmpeg `fps=2,scale=180:320` + PIL) e leia a imagem. Medir
   `ebur128` (I ≈ -14 LUFS). Peça ao dono para **ouvir** uma vez (a análise não substitui o ouvido).
2. O dono sobe no YouTube (ou você, pelo Chrome dele, **só com ok explícito**: é publicar na conta dele):
   **não listado**, monetização desligada, sem restrição de idade, "não é conteúdo para crianças" conforme o caso.
3. Link na ficha pela skill **`google-play`**:
   `gplay.py --package <pkg> listing-set --lang pt-BR --video "https://www.youtube.com/watch?v=ID"` para cada
   idioma (inclusive a ficha sem vídeo próprio, ex. es-ES com o vídeo es-419).
4. Sugira um **experimento da ficha** (com vídeo x sem vídeo) para medir de verdade.
5. Documente no projeto (README da pasta promo + CLAUDE.md do projeto) e registre o aprendizado em `log.md`.

## Armadilhas já pagas
- `deviceScaleFactor` ignorado no Chrome headless do Windows → `--force-device-scale-factor=3`.
- Toasts/avisos de missão sujam o gancho → save com tudo visto + toast no-op na gravação.
- Autoplayer em cena sorteada muda entre idiomas → confira os marks de cada gravação.
- Zoom alto em cena larga corta o conteúdo → teste o enquadramento num quadro antes do render final.
- Hook do Claude Code bloqueia `rm` de glob relativo depois de `cd` → escreva em pasta nova em vez de limpar.
- **Flutter web** (Tic Tac Verse, exemplo em `D:/Projetos/tictacverse/tool/promo/`): o relógio virtual funciona,
  mas `setTimeout(0)` em cadeia (rolagem) trava o `advance` num laço infinito → atraso mínimo de 1 ms. Sem
  ganchos de debug no app: clique em `flt-semantics-placeholder` liga a árvore de acessibilidade e os botões
  viram nós com `aria-label` (ache pelo texto do ARB de cada idioma). Som do `audioplayers`: embrulhe
  `HTMLMediaElement.prototype.play` e registre `{src, t}`; o caminho vem como `assets/assets/...`.
- **Partida contra a CPU**: aleatoriedade (partículas também gastam `Math.random`) faz cada idioma jogar outra
  partida → no editor, corte por **marca** (`boom`, `modal`, `boom-700`), nunca por número de quadro. Ler a
  jogada da CPU na tela: espere o tremor de captura acabar; quando a CPU fecha um mini-tabuleiro a peça grande
  cobre tudo, então deduza pela regra dela.
- **Pillow sem libraqm** (Windows) quebra conjuntas de hindi/bengali/nepali → renderize as legendas no Chrome
  (PNG transparente, fonte embutida em base64; `file://` não carrega em `setContent`).
- `loudnorm` de uma passada fica ~1,5 dB abaixo do alvo → duas passadas (mede com `print_format=json`, aplica).
- Wan no ícone pode deformar a marca: rode 2 ou 3 sementes com "stay rigid and keep their exact shape" e confira
  a folha de contato; se nenhuma servir, anime o ícone real por código.
