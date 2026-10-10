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
