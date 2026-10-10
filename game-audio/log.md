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
