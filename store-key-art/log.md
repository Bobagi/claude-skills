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
