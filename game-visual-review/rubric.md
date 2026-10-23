# Rubric de revisão visual de jogo (versionada, cresce a cada uso)

Pontue 1 a 5 em cada item, com uma frase de evidência tirada da captura. 2 ou menos bloqueia.

## A. Primeira impressão (o que um votante de jam vê em 3 segundos)
- **A1 Leitura imediata**: dá para saber em 3 s onde o jogo se passa e o que se faz? (menu: a fantasia
  do jogo aparece na imagem, não só no texto).
- **A2 Nada de placeholder**: nenhuma área grande com cor chapada sem gradiente, textura ou luz.
  Métrica: área plana do `contact_sheet.py` acima de 0,45 é nota 1 ou 2.
- **A3 Ponto focal**: existe um elemento principal (celeiro, torre, personagem) com tamanho e contraste
  para onde o olho vai primeiro; não é um pontinho no horizonte.
- **A4 Escala e enquadramento**: a câmera está na altura certa (não no chão nem flutuando), o elemento
  principal ocupa 15 a 40% da largura, o horizonte não corta a imagem exatamente no meio.

## B. Luz, cor e atmosfera
- **B1 Céu e hora do dia**: o céu tem gradiente, sol/lua, nuvens ou estrelas coerentes com a hora;
  fundo sólido de câmera é nota 1.
- **B2 Direção de luz**: sombras e lado iluminado coerentes com a posição do sol; nada de luz pontual
  acesa em pleno dia (lâmpada de janela brilhando ao meio-dia é erro).
- **B3 Paleta**: 3 a 6 matizes dominantes que combinam com o clima (ensolarado: azul + verde + vermelho
  do celeiro + palha; noite: azul escuro + âmbar). Métrica: variedade de matiz abaixo de 4 é suspeito.
- **B4 Exposição**: nem estourado (holofote branco cobrindo metade da lente) nem afogado no escuro; o
  pós-processo (grão, vinheta, saturação) muda por estado (menu alegre, noite tensa), não é um só.

## C. Objetos e materiais
- **C1 Props legíveis**: cada objeto interativo lê como o que é a 1 m (manivela parece manivela,
  cartucho parece cartucho). Cubo e cilindro sem detalhe para objeto que o jogador precisa reconhecer
  é nota 2.
- **C2 Affordance**: o que é clicável se destaca (brilho ao passar o mouse, pulso no tutorial, cor,
  posição) sem precisar de texto. Se o dono "nem entendeu que era clicável", nota 1.
- **C3 Vegetação e chão**: plantação/grama tem volume e variação (altura, cor, orientação); não é
  um tapete de lâminas iguais nem um plano liso.
- **C4 Silhueta e escala dos modelos**: proporções plausíveis (celeiro maior que caminhão, árvore
  redonda ou cônica conforme o lugar), pivô e orientação certos (nada enterrado, nada flutuando).

## D. Interface
- **D1 Tipografia**: título com fonte de personalidade, corpo legível; tamanhos em hierarquia
  (título > subtítulo > botões > rodapé).
- **D2 Contraste do texto**: texto sobre fundo com contraste suficiente (texto claro sobre céu claro
  precisa sombra/contorno; escuro sobre amarelo ok). Teste: ler o menor texto no `review.png`.
- **D3 Botões com estado**: repouso, hover/selecionado e pressionado distinguíveis; o selecionado
  inicial visível para teclado.
- **D4 HUD discreto**: o HUD não cobre o ponto focal, prompts duram o bastante para ler, e nenhum
  texto cita teclas que o jogador padrão não usa (jogo "só mouse" não ensina A/D).

## E. Fidelidade à referência (quando há imagem de referência)
- **E1 Posição dos elementos**: os mesmos objetos nos mesmos terços da imagem (ex.: celeiro centro-
  direita, moinho à esquerda dele, silo à direita, cerca à frente, plantação em primeiro plano).
- **E2 Hora e clima**: mesmo céu (azul com cúmulos / pôr do sol), mesma direção e cor da luz.
- **E3 Paleta e contraste geral**: distância de histograma do `contact_sheet.py` baixa e luminância
  média parecida; se a referência tem sol forte e a captura é cinza, é nota 2.
- **E4 Linguagem da UI**: tipo de botão (pincelada, caixa, texto solto), posição do título, ícones.
- **E5 O que a referência esqueceu**: se o pedido diz "ele esqueceu a plantação, coloque", a
  plantação conta como item obrigatório, não opcional.

## F. Consistência entre estados
- **F1** Menu, jogo, loja e finais parecem o mesmo jogo (mesma fonte, mesma paleta de UI, mesmo grão).
- **F2** Nenhuma regressão: comparar com a captura anterior de mesmo nome.

## Casos que ensinaram (append aqui, com data)
- 2026-10-23, Happy Harvest: menu entregue com céu sólido laranja, painel marrom escuro sobre 42% da
  tela e a torre como um pontinho; nenhuma métrica foi rodada. A rubric A2/A3/B1 teria bloqueado.
  Correção: skybox procedural (gradiente + sol + nuvens), câmera baixa no milharal, celeiro + silo +
  moinho no terço central, botões com pincelada, música alegre. Lição: toda tela nova passa por A e B
  antes de qualquer polimento.
- 2026-10-23, Happy Harvest: lâmpada da janela do celeiro ficou acesa no menu diurno e virou uma
  bola laranja no meio da imagem (B2). Luz pontual de "noite" tem de ser desligada por preset.
- 2026-10-23, Happy Harvest: holofote de 14000 de intensidade estourava a lente inteira de branco
  (B4). Testar o holofote ligado dentro da luneta, não só o estado desligado.
- 2026-10-23, Happy Harvest: prateleira de cartuchos feita de cilindros lisos; o dono não entendeu
  que era clicável (C1/C2). Prop interativo precisa de forma reconhecível E brilho de hover.
