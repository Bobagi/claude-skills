# Log de casos (cresce a cada uso)

## 2026-11-11 · Beneath the Shroud (Steam, app 5604370) · 4 rodadas ate aprovar
Imagem: `examples/beneath-the-shroud/historico_v1_a_v4.jpg`.

- **v1 (recusada com raiva)**: capsulas de 20/10 feitas no ComfyUI (Juggernaut XL + LoRA): Erick ruivo de mascara de
  gas. "Coloca um personagem que nem se parece com o nosso", "nem pesquisou como fazer banners que chamem atencao, nao
  comparou com nenhum de sucesso". Erro: arte inventada, zero pesquisa, zero comparacao.
- **v2 (melhor, recusada)**: render da cena real (casa + tentaculos do polvo ampliados), logo no arco dos tentaculos,
  tentaculo do meio passando NA FRENTE do "SHROUD". "Tentaculo passando pela frente das letras atrapalha a leitura";
  "da pra ver a casa em um modelo 3D ruim, sem texturas adequadas". O que ele GOSTOU: casa embaixo + letreiro logo acima.
- **v3 (recusada com raiva)**: silhueta por passes (bom), mas mudei o layout para logo a esquerda, ceu ficou liso e as
  janelas fracas. "A arte da casa embaixo e o letreiro logo acima que estava bom voce nao fez"; "manteve as luzes da
  casa horriveis, chamando atencao nenhuma"; "ceu completamente nada, limpo"; "nao ta pesquisando nada para ter uma
  atmosfera de terror".
- **v4 (APROVADA)**: layout da v2 (casa embaixo, letreiro acima e por cima dos tentaculos) + composicao por passes:
  foto CC0 de tempestade com relampago recolorida (azul-petroleo), brilho forte atras da casa, tentaculos escuros com
  volume, contorno de luz e textura das ventosas, casa em silhueta, TODAS as janelas acesas (passe so dos vidros) com
  caixilho, nucleo quente e halo, chuva, nevoa na linha d'agua, grao. "Gostei dessas artes."
- Pesquisa que valeu: Steam Page Analyzer (98 capas mais vendidas: 97/98 com o nome; texto-primeiro + 1 assunto + 1
  decisao de cor), presskit.gg (render da engine -> passes -> composicao 2D com nevoa/raios/contraluz), Playio
  (desenhar a small primeiro; teste em cinza; grade com 10 a 20 capas do genero), guias de cartaz de terror
  (uma luz em meio ao escuro, negativo, silhueta).
- **Upload na Steam** (Graphical Assets): a area "Drop images here" so aceita arrastar; o input de arquivo da pagina e
  o de imagens da descricao. Truque: capturar o `change` desse input e redisparar `dragenter/dragover/drop` com um
  `DataTransfer` em `#game_image_drop`; depois escolher o tipo de cada imagem no select e clicar Upload. A janela
  "Graphical Asset Rules" (declaracoes) e do dono: o sistema de permissoes bloqueia o agente de marcar.

## Wilkins Pest Control, capa do itch v7 (11/11/2026)
- Pedido: "faca ela IGUAL como esta agora, mas com plantacao e ceu mais parecidos com a anterior" + a pessoa "parece
  colagem de revista, abaixada numa pose nada a ver": silhueta aterrorizada fugindo.
- O Z-Image com ControlNet (Union 2.1) troca a torre real por uma torre generica mesmo a 0,7. Saida que funcionou:
  gerar SO o fundo (mapa sem a torre e sem o feixe no ceu, prompt sem a palavra "tower": ate "no towers" ou "away from
  the tower" fez o modelo pintar uma torre) e colar por cima a torre e o feixe da versao aprovada, com mascara do alfa
  do render MENOS o ceu vermelho da pintura antiga (a pintura nao bate pixel a pixel com o render) e o feixe pela
  luminancia. Sem torre no mapa o modelo ignora horizonte e escala a 0,6; a 0,85 obedece.
- Pessoa: corpo desenhado em capsulas (inclinado, braco contra a luz, pernas no passo, canelas somem na cevada),
  mapa borrado; o modelo pinta borda macia e meio transparente, nada de recorte.
- **Library hero recusado pelo detector da Steam** ("Store data failed to save... hero image appears to contain text or
  a logo") quando a fileira de janelas acesas ficou inteira no recorte: o OCR do Windows lia "iiii•ii" nela. Suavizar
  so a grade nao bastou; passou quando as janelas viraram brilho continuo (mascara quente dilatada + blur 28) e a casa
  foi centralizada com zoom 1,12. Testar o hero com OCR local antes de subir (`ocr.ps1` com Windows.Media.Ocr).
- A posicao do logo na biblioteca e do dono (Placement Tool); a imagem de fundo nao se move la: reexportar o hero.
