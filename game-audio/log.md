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

## 2026-10-24 · Happy Harvest, troca dos sons sintetizados por gravações CC0
- 49 originais baixados de uma vez navegando para as URLs `/download/` (dois `browser_batch` de 24); Chrome logado, sem diálogo de salvar. Nesta máquina o download padrão do Chrome é `D:\Downloads` (ler `download.default_directory` em `Chrome/User Data/Default/Preferences` antes de procurar em `~/Downloads`).
- Loop de som PERIÓDICO (zumbido de rede, motor): o crossfade equal-power numa fase aleatória cancela os harmônicos graves por um instante. Escolher o ponto de corte por correlação cruzada da parte < 400 Hz e usar crossfade equal-gain quando a correlação > 0,6 (zumbido de lâmpada: 0,98). Motor de gerador real deu só 0,09 (rotação varia): aí equal-power mesmo; conferir o RMS por banda em janelas de 100 ms em volta da emenda (tocar o loop duas vezes).
- Checar a emenda: salto na volta |d[0]-d[-1]| contra o percentil 99 do passo normal + diferença de nível dos 50 ms das pontas. O wind_loop do Beneath (arquivo cru) pulava 0,027 com passo 0,0016: clique a cada 44 s.
- Estática/queima com "buracos" (quedas de 8 a 10 dB por 0,5 s) soa como defeito em loop: medir RMS por 100 ms e pegar a janela mais estável (menor desvio). Road flare 348766 tinha dois buracos; sparkler 102264 (-3 st) ficou contínuo.
- `pitch()` muda a duração: não passar como filtro num helper que corta o preenchimento por número de amostras; aplicar depois do corte.
- Grilos com ruído largo de vento/trânsito até 2 kHz: high-pass 1,2 kHz (ordem 6) deixa só os grilos (89% em 2 a 8 kHz); o vento fica com o grave.
- Achados bons (todos CC0): grilos Defelozedd94 522299, gerador Honda Skybonator 709272 (partida + marcha lenta da mesma máquina), estática AM penyasounds 730772, zumbido de lâmpada kyles 454098, catraca única CallFlan 495238, alavanca timgormly 151271, squelch magnuswaker 522164, puxada de corda gthall 222809, sirene distante TRP 568814, galo BenjaminNelan 435508, contador manual revdrmr 664698.

## 2026-10-24 · Happy Harvest, javali (hog_squeal, hog_squeal_2, hog_grunt)
- Sem Chrome logado nesta maquina: baixei os previews HQ publicos do Freesound com curl. A URL sai da pagina do som
  (`grep -oE 'https://cdn\.freesound\.org/previews/[0-9]+/[0-9_]+-hq\.mp3'`); o `freesound.py search` ja confirma CC0
  em cada pagina. Bom o bastante para one-shot ouvido a 40-80 m.
- Javali selvagem real: felix.blume 612995 "Wild boars" (4 min, CC0) tem gritos tonais perto de 1 kHz; piso de ruido
  de campo alto (-27 dB no corte), aceitavel com ambiente noturno por baixo. Highpass 180 Hz tira o vento.
- Para casar RMS alto de referencia (-13.7 dB) com pico -1 dB: `loudness(d, alvo, -1)`; som com pausa no meio
  (grunhido duplo) fica 1,5 a 2 dB abaixo do alvo, mire mais alto.

## 2026-10-27 · Wilkins Pest Control, toque do rádio e som de carregar repetido
- "Som de carregamento repetindo": o `breech_load.wav` era a gravação INTEIRA de 22 s (42 cartuchos) copiada sem corte pelo `make_audio.py`. Antes de mexer em código, rode `analyze.py` no arquivo: muitos eventos num one-shot denunciam isso na hora. Vale varrer one-shots com duração > 2,5 s.
- Chamada de rádio realista montada por camadas (sem nada pronto em CC0 com esse nome): squelch abrindo (magnuswaker 522164) + chiado AM (harrisonlace 812929, banda 300 a 3400 Hz, -7 dB) + dois bipes de roger (bruce965 321906, -11 dB: tom puro a -3 dB domina tudo) + rabo do squelch (LukaCafuka 760245). Buscas vazias: "radio incoming call", "two way radio chirp", "police radio squelch".

## 2026-11-10 · Beneath the Shroud, vozes em português do Brasil (troca do SAPI)
- Qwen3-TTS fala português com `language: "Portuguese"`, mas o SOTAQUE depende do falante: `ryan` e `serena` saem com
  cara de Portugal (vogais reduzidas ɨ, coda "s" chiada: "deʃkupɨ", "kriaturaʃ"); `aiden`, `ono_anna` e `vivian` saem
  brasileiros com a instrução certa. A instrução que funcionou (em inglês): "a Brazilian from São Paulo speaking
  Brazilian Portuguese with a paulistano accent: open unreduced vowels, 'de' and 'te' pronounced 'dji' and 'tchi'".
  Pedir "Rio de Janeiro" traz o "s" chiado carioca (fica parecido com Portugal na medição): use São Paulo.
- `uncle_fu` em português sai com F0 de 200 a 260 Hz (registro de mulher) apesar de "mature male low": medir o F0
  (librosa.pyin) de todo take; homem adulto 85 a 160 Hz. O ranking passou a penalizar F0 fora da faixa do personagem.
- Medir sotaque sem ouvir: `facebook/wav2vec2-lv-60-espeak-cv-ft` (fonemas IPA; decodificar com o vocab.json na mão,
  sem o pacote phonemizer) e contar tʃ/dʒ e vogal final plena (BR) contra ɨ e "ʃ" antes de consoante (PT/Rio). É
  enviesado para PT (o SAPI Maria, brasileiro, deu ɨ também): vale como comparação entre takes, não como absoluto.
  O classificador `rmayormartins/speech-accent-pt-br-classifier` NÃO serve: separou por voz/gênero, não por sotaque.
- Whisper `large-v3-turbo` (multilíngue, 1,5 GB) transcreve pt bem; sem ffmpeg no PATH, passar o array a 16 kHz.
  WER precisa converter dígitos ("95%", "2014") para extenso antes de comparar.
- Fluxo que ficou: 3 takes por fala (sementes diferentes) -> Whisper + fonemas + F0 + pausa + sílabas/s -> o melhor
  take por regra -> filtro (gravador/rádio) depois. Filtro de gravador suavizado (220 a 4200 Hz, drive 1,9).
- Velocidade nesta máquina com o editor da Unity aberto dividindo a GPU: ~1,8 s de cálculo por segundo de fala;
  VoiceDesign (3,5 GB a mais) ~6 s por segundo de fala e timbre muda entre falas: não serve para personagem fixo.
- Take que dispara (pausa sem fim/balbucio) ia até 2048 tokens (~2,7 min de áudio): com a GPU dividida (ComfyUI +
  Unity abertos) um take levou 20+ min. `tts_voice.py` agora limita os tokens pelo tamanho do texto (`token_cap`:
  leitura lenta de 4 caracteres/s x1,5, mínimo 6 s). Antes de um lote, olhar quem mais usa a GPU (`nvidia-smi`).
