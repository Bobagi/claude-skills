# game-audio: registro de usos

## 2026-10-02 · Beneath the Shroud (Unity), primeira versão da skill

- Pedido: baixar a lista de sons que o ChatGPT achou (28 links) + o que faltava no GDD, e pôr no jogo.
- Licenças: os 28 conferidos na página, todos CC0. Mais 32 candidatos achados por busca CC0 (queda de energia,
  parede, garras, criaturas menores, drone da Lumina, pilhas, porta metálica com teclado). Kenney Interface Sounds.
- Download: 1º clique abriu "salvar como" (opção do Chrome ligada); `fetch` da página falhou (CDN sem CORS);
  vários `<a>.click()` travaram a página. Funcionou: usuário desligou a pergunta + `navigate` por URL `/download/`
  em `browser_batch` (55 arquivos em 2 lotes, sem diálogo).
- Detector de eventos v1 (média de 10 ms, limiar relativo ao pico) perdia cliques de 1 ms; v2 usa envelope de pico
  a cada 5 ms e limiar em dB acima do piso de ruído.
- Correções vistas na imagem da saída: estalo do apagão terminando seco (faltava fade no recorte); arrastar molhado
  agudo e com tom fixo em 5 kHz (pitch -12 a -3 + low-pass 3,2 kHz); pancada da parede 0,65 s atrasada em relação
  ao objeto sumindo na tela (recorte começando 0,45 s depois).
- Ficaram prontos sem sistema no jogo: magnum (tiros, gatilho em seco, cão, tambor), impacto em carne, criaturas
  menores (grunhidos, guinchos, mortes).

## 2026-10-03 · vermes, trinca do visor, abertura (motor, chuva, mar, música)

- `freesound.py check` pede `usuario/id` (só o id falha com "não entendi").
- Loop de textura molhada (vermes): pedaços curtos de squelch com pitch +3 a +9 semitons espalhados com semente fixa,
  high-pass 300 e low-pass 6,5 kHz, loop de 10 s com 1,5 s de crossfade. O som dos vermes antes era só um arranhão a
  cada 6 a 15 s com queda em 10 m: o Gustavo não ouviu nada. Ambiente de objeto pede um loop contínuo + um evento.
- Trinca de vidro: para-brisa trincando (806423) e o pedaço 0,78 a 1,25 s do "crack and crunch" (422623). Toque na hora
  da trinca, a trinca aparece inteira de uma vez (era suave e parecia defeito).
- Música CC0 boa de terror melancólico: szegvari (Freesound) tem dezenas de faixas cinematográficas em 5.1; o
  `convert_sounds.py` dobra 5.1 para estéreo (`_surround_to_stereo`). Corte de 66 s com o pico onde entra o título.
- Música na Unity: a regra de importação de loop (Vorbis streaming) vale também para `/Music/`, estéreo mantido; o
  arquivo importado antes da regra compilar ficou mono e foi preciso `ImportAsset(ForceUpdate)`.
- Chuva sintetizada (`ProceduralAudio.RainLoop`) soa como estática numa cena aberta: na abertura o LightningStorm fica
  sem `rainSource` e a chuva e o mar são loops gravados, baixos (0,14 e 0,18) sob a música (0,6).

## 2026-10-07 · cápsulas e impacto de bala (Beneath the Shroud)

- Freesound devolveu HTTP 502 para a busca por script (duas tentativas); Kenney "Impact Sounds" (CC0, zip direto em
  kenney.nl/assets/impact-sounds) resolveu sem login.
- Cápsula de latão = `impactMetal_light` +5 a +8 semitons (centroide 2,9 -> 3,9 kHz): tique pequeno e agudo.
- Bala na parede não existe pronta no Kenney: camadas `impactMining` (+5 st, high-pass 700) + `impactWood_heavy`
  (low-pass 2,5 kHz, high-pass 90) + `impactGlass_light` 40 ms depois. **Cortar cada camada em ~0,13 s**: a 1ª versão
  tinha a picareta ressoando como tons fixos de 1 a 5 kHz e um 2º golpe aos 0,3 s (só apareceu no espectrograma).

## 2026-10-10 · rangido de lamparina e chamado abissal (menu do Beneath the Shroud)

- "Rugido abafado" que soa como arroto: grunhido curto (0,8 s) com pitch para baixo e low-pass a 700 Hz. Um chamado de
  monstro do fundo precisa ser LONGO e tonal: canto de baleia (taure 361423, J.R.Mythical 563690) 7 a 11 semitons
  abaixo + um rugido largo bem embaixo (-12 st, low-pass 600, -7 dB) + cauda de reverb por convolução (ruído com
  decaimento de 4,5 s, low-pass 1,8 kHz, pré-delay 80 ms, wet -4 dB). Conferir que sobra energia entre 200 e 600 Hz:
  só sub (<120 Hz) some em alto-falante de notebook.
- Rangido que funciona para objeto pendurado: atrito de corda num balanço (Valerie-Vivegnis 862995, 30 rangidos
  limpos a cada 1,4 s, piso -78 dB). Tocar na VIRADA do balanço (produto escalar velocidade x ângulo troca de sinal),
  não por cronômetro: fica sincronizado com o que se vê.
- Disparo por limiar de velocidade nunca disparava (balanço real ~1,5 grau/s contra limiar 2,5): medir a variável em
  Play antes de escolher o limiar.
- Prévia HQ do Freesound (mp3, sem login) pega por curl na página do som (`cdn.freesound.org/previews/...-hq.mp3`)
  serve para pré-selecionar sem baixar originais, e como fonte de som que vai ser muito processado.
- (mesmo dia) O Gustavo tirou o rangido e os chamados de baleia; ficou o rugido antigo mais baixo + um rugido "da
  criatura colossal bem longe, ouvido de baixo": 837799 -5 st, low-pass 420 Hz, cauda de reverb de 7 s com o wet
  ACIMA do seco (+2 dB), intervalo de 45 a 90 s. Lição de processo: oferecer a pasta com os candidatos para ele
  ouvir ANTES de montar camadas; o gosto é dele e a análise não mede "parece rangido".
- 2026-10-13 (BeneathTheShroud, casa das artes novas): 6 sons CC0 baixados navegando para as URLs `/download/` sem
  problema (porta de vidro 736559, chacoalho 583228, chuva no vidro 869851, água fervendo 370217, batimento 369017, bolhas
  521392). Água fervendo de -48 dB RMS no arquivo subiu limpa com `make_loop` (loudness -24). Batimento de coração para uma
  planta: pitch -3 + low-pass 900 Hz deixa de soar humano. Busca "rain on glass" volta vazia; "rain window" acha.

## 2026-10-17 · sons do final da demo (Beneath the Shroud)

- O Chrome do usuário estava DESLOGADO do Freesound (botão "Log in" na home) e ele não estava presente: sem originais.
  Saída: previews HQ (mp3 320 kbps) por `curl` na página do som (`https://freesound.org/people/<user>/sounds/<id>/`,
  regex `https://cdn.freesound.org/previews/[^"' ]*-hq.mp3`); a URL da página precisa do `/sounds/<id>/` (sem ele a
  busca do preview volta vazia). Pasta `Sounds/Finale` + `SOURCES.md` dizendo que são previews e como trocar pelos originais.
- `freesound.py search` funcionou de primeira hoje (sem 502). Termos que acharam: "revolver" (tambor Remington 795318,
  8 cliques limpos a cada 0,9 s), "revolver reload" (177863 abre/fecha), "brass drop concrete", "zombie breathing",
  "metal pot drop", "door break kick", "gunshot indoor"; termos que voltaram vazio: "revolver cylinder open", "shell
  casing single drop", "pan falling floor kitchen", "gunshot reverb tail indoor", "power outage hum".
- Respiração de zumbi 426409 vem a -50 dB RMS: `make_loop` com `rms_target_db=-26` resolve; 847400 (idle) dá 5 chamados
  separados por segmento (eventos do analyzer 5, 7, 9, 14, 19).

## 2026-10-23 · Happy Harvest, musica do menu (country alegre) e sting da loja
- OpenGameArt e a melhor fonte para MUSICA CC0 com download direto (curl funciona nos links `/sites/default/files/`); o Freesound so tem loops curtos de banjo. incompetech nao tem filtro de genero country/bluegrass. Escolhido "Gone Fishin" (Memoraphile, CC0 confirmado pelo autor nos comentarios); rejeitados: Sunny Side Up (17k amostras clipadas), Country1 (mp3 64 kbps), Down The River (fade longo no fim), Apple Cider (chiptune).
- Ponto de loop de musica: autocorrelacao do envelope de onsets da o compasso (2,2427 s), depois correlacao do espectrograma entre `d[L:L+xf]` e `d[0:xf]` em multiplos de 4 compassos escolhe L (36 compassos, corr 0,94); crossfade de 1 compasso alinhado na grade. Conferir a emenda com RMS por janela e onsets ao redor da juncao.
- LUFS sem pyloudnorm: `ffmpeg -af ebur128=peak=true -f null -` (binario do imageio-ffmpeg) e ler o Summary; OGG Vorbis q5 tambem pelo ffmpeg (`-c:a libvorbis -q:a 5`). Script do projeto: `SourceAssets/Tools/convert_music.py`.

## 2026-10-23 · Happy Harvest · voz neural
- SAPI rejeitado pelo dono ("MUITO robótica, zero emoção"). Qwen3-TTS CustomVoice local com instrução por fala resolveu: 29 falas em 10 min de GPU, emoção mensurável no F0 (100 Hz frio, 230 Hz grito). Filtro de rádio suavizado para não achatar. Script genérico em `scripts/tts_voice.py`, seção 8 do SKILL.md.
