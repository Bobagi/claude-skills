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
- 2026-10-24, Happy Harvest (regra permanente do dono): interior da torre liso e celeiro/moinho/silo pobres. Antes de
  modelar ou texturizar na mão, PESQUISAR online texturas PBR (Poly Haven, ambientCG), shaders e efeitos prontos
  (paredes, chuva, sangue, faíscas, fogo, vidro) e modelos CC0. Superfície grande sem textura/normal map é nota 2 em A2/C1.
- 2026-10-24, Happy Harvest: celeiro/silo/moinho refeitos (Sketchfab CC BY + construção no Blender com Poly Haven). A folha
  inteira contra a referência dá distância de histograma alta por causa do milho e do céu (não dos modelos): para julgar
  um modelo, recorte a mesma região (o grupo de prédios) da referência e da captura lado a lado, além da folha cheia.
  Moinho branco galvanizado sumia contra o céu; escurecer o aço (como a referência) devolveu a silhueta (C4/E3).
- 2026-10-24, Happy Harvest: interior da cabine 'liso'. Medido: área plana 0,30 antes; depois de PBR Poly Haven nas paredes/piso/teto, estrutura aparente e objetos de cena, 0,03 a 0,15 por vista e densidade de bordas +30 a 70%. Para interior, capturar as 4 paredes + teto pelo ponto de vista do jogador (CabinLean.Look) e exigir área plana <= 0,2 em cada uma.
- 2026-10-24, Wilkins Pest Control (ex-Happy Harvest): milho trocado por cevada de verão feita de cartões finos. De dia lê
  muito bem (menu dourado); de noite, pela janela e de cima, os cartões viram riscos verticais claros que lembram chuva (C3
  nota 3). Para plantação baixa que esconde gente, testar com uma "fila" fixa (bicho, pessoa agachada, pessoa em pé lado a
  lado, tempo parado, holofote ligado) e recortar+clarear a captura: é o único jeito de confirmar que o agachado some e o
  em pé aparece.
- 2026-10-24, Wilkins Pest Control: o dono achou três coisas que a revisão não pegou, porque ela só olhava capturas paradas.
  (1) Volumes em Options eram "<  80%  >" que mudavam por passo: em PC, número contínuo é **slider arrastável** e escolha
  curta é **palavras clicáveis** (a escolhida destacada) ou liga/desliga; seta só como atalho de teclado/controle (D: nota 2).
  (2) Botão "How it works" sobrando com um tutorial interativo no jogo: menu não repete o que o tutorial ensina.
  (3) Minigame de timing impossível: `ProjectSettings/TimeManager.asset` ficou com `m_TimeScale: 7` (um teste acelerou o
  tempo fora do Play e o editor salvou), e o build saiu 7x rápido. **Regra nova G1/G2 abaixo.**

## G. Jogabilidade medida (não só a imagem)
- **G1 Escala de tempo**: antes de capturar ou buildar, `grep m_TimeScale ProjectSettings/TimeManager.asset` deve dar 1, e
  o jogo deve forçar `Time.timeScale = 1` ao iniciar. Teste que acelera o tempo restaura em `finally` e só roda em Play.
- **G2 Janela de timing**: todo minigame de reflexo tem a janela medida em segundos reais (largura / velocidade do marcador).
  Abaixo de ~0,35 s por passagem é nota 2 para jogo de jam; jogar o minigame pelo MCP (esperar a janela, clicar) e
  confirmar que fecha. Erro deve custar um passo, não zerar tudo.
- **G3 Controles de opção**: volume/sensibilidade = slider; poucas escolhas = palavras clicáveis; nada de "< valor >" como
  único jeito de mudar com o mouse.
- 2026-10-25, Wilkins Pest Control: aro redondo da janela em volta de um furo quadrado e moldura low poly sem textura (C1/C4).
  Forma do elemento interno tem de seguir a moldura; moldura torneada (perfil com chanfros + parafusos) com PBR CC0 recolorido
  para a paleta. Medido na vista frontal: área plana 0,28 para 0,16. Capturas de olhar para baixo (piso escuro) dão área plana
  alta (0,37) sem ser placeholder: julgar interior pelas vistas de parede, não pelo piso.
- 2026-10-26, Wilkins Pest Control: menu ainda "placeholder" para o dono: (1) botões na Special Elite com sombra ficavam
  grossos demais (D1): botão usa serifa leve (Zilla Slab Regular), máquina de escrever fica para papéis; (2) legenda dourada
  (Corn) sobre cevada dourada sumia (D2): cor de texto nunca igual à cor dominante do fundo, use creme com contorno escuro e
  deixe o dourado num filete; (3) título só em fonte não é logo: faça um selo/emblema (ComfyUI SDXL + LoRA LogoRedmond para a
  ilustração central, texto curvo e anéis desenhados em PIL para o texto ficar nítido) e reuse o mesmo selo no jogo (timbre
  da carta). Gerador: `SourceAssets/Tools/make_logo.py`.
- 2026-10-27, Paper Planes: o dono achou a cidade de fundo "muito baixa" e vermelha, longe do "Tóquio neon roxo" pedido.
  A faixa de prédios ocupava só o terço do meio da tela e o céu era a cor sólida da câmera (área plana 0,44). Em cenário de
  cidade, o fundo tem de subir até perto do topo da tela em várias camadas (torres que saem do quadro), com o céu em
  gradiente; conferir a paleta contra o que o dono descreveu em palavras, não só contra o pacote de assets baixado.
  Correção: skyline própria em 4 camadas (`make_skyline.py`), área plana 0,13.
- 2026-11-05, Inferno Aura (mod de Terraria): prints da Workshop entregues com o personagem pequeno
  em cena noturna escura; o efeito (brilho aditivo suave) não aparecia e o dono achou que "não saiu o
  efeito" e que o mod tinha sido trocado. Lições: (1) o assunto do print (o efeito) precisa ocupar o
  quadro: recorte fechado em volta dele (640x360 ampliado 3x, pixel art com NEAREST), não a tela
  inteira; (2) efeito de luz aditiva se mostra em cena escura com fundo de cor (inferno, caverna
  iluminada), não em noite preta nem em dia claro; (3) conferir se o zoom pedido entrou de fato
  (`Main.GameZoomTarget` via mod não aplicou; comparar tamanho do personagem entre capturas);
  (4) nunca alterar o produto para o print ficar bonito: o print mostra o produto como ele é.
- 2026-11-10, Conjuration (mod de Terraria): o dono reprovou duas vezes a arte do Fire Atronach ("muito ruim,
  nada parecido com Terraria"): primeiro pixel art desenhada em codigo, depois ComfyUI (SDXL + Pixel Art XL +
  Qwen-Image-Edit) reduzida para a grade 2x2. Arte gerada nunca leu como Terraria. O que funcionou: desenhar o
  personagem com o PROPRIO renderizador do jogo (Player falso vestido com itens e cores vanilla, como o Manequim;
  `Main.PlayerRenderer.DrawPlayer`), e exportar folha de town NPC quadro a quadro. Regra: em mod de jogo, antes de
  gerar arte, procurar como o jogo/modders reaproveitam o estilo da engine (templates, renderizador, helpers como
  o Player Renderer); so gerar do zero se nada servir, e sempre comparar lado a lado com sprites vanilla NA MESMA
  captura (personagem do jogador e NPCs ao lado) antes de dizer pronto.

- **Arte de loja sem rosto humano de IA** (11/11/2026, Wilkins Pest Control): a capa com um fazendeiro sorridente gerado
  no Z-Image foi recusada na hora ("homem claramente feito por IA"), mesmo com métricas melhores que a anterior. Rosto
  realista gerado por IA é nota 1. Preferir silhueta, ícone e paleta chapada de 2 a 3 cores (padrão das capas de horror
  indie na Steam: Iron Nest, Iron Sanctuary, The Windows Are Gone).
- **Arte de loja: luz que sai da fonte, olhos discretos, sem posterizar** (11/11/2026, Wilkins Pest Control, capa v4
  recusada: "desalinhamento da luz com o elemento da torre que emite luz", "olhos absurdamente grandes e chamativos",
  "parece que fizeram no Paint"). Toda imagem com feixe, cone ou raio: confira se a boca do feixe esta NA lente e no
  eixo do emissor (medir: retas das bordas extrapoladas ate a lente dao a largura da lente e centro no eixo; nenhuma
  luz forte no ceu fora do cone). Para garantir, desenhe a geometria em codigo e passe por ControlNet (Z-Image Union
  2.1, modo Gray, forca 0,6; 0,5 ja solta o feixe). Olhos que brilham em arte de loja: poucos, pontos de 1 a 2 px no
  tamanho final, sem halo grande. Nunca reduza uma pintura a 4 a 6 cores "para parecer serigrafia": vira Paint.
  Cena larga com area vazia (banner): o modelo inventa uma segunda torre ali; gere o vazio a parte com prompt sem o
  objeto. Olhe a imagem em 100% e em miniatura antes de publicar; o teste automatico tambem deixa passar coisa
  (o primeiro teste de alinhamento aprovou um banner com dois feixes).
- **Arte de loja a partir da engine: silhueta + passes, nunca o modelo cru** (11/11/2026, Beneath the Shroud). Capa 1 (rosto
  de IA que nao era o personagem) e capa 2 (render direto da cena: casa com texturas pobres visiveis, tentaculo
  passando NA FRENTE das letras) recusadas. O que funcionou: renderizar passes separados na Unity (ceu, casa, mascara
  colorida por tentaculo, completo) e compor em 2D (`SourceAssets/Tools/trailer/compose_keyart.py`): casa e criatura
  em silhueta contra ceu iluminado, contorno de luz, nevoa por profundidade, uma luz quente (janela), chuva e grao,
  como Sunless Sea / Still Wakes the Deep / The Sinking City. Logo em area limpa, nada atravessando as letras; testar
  a vitrine em cinza borrado: logo creme sobre azul medio sumia (mesma luminancia) e so leu apos escurecer o ceu atras
  dele. Sempre baixar 20+ capas do genero (CDN da Steam) e comparar na grade antes de mostrar.
