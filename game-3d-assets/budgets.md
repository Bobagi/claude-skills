# Orçamentos, fontes e registro

## Triângulos por tipo (na engine)

| Tipo | Faixa | Começar em | Por quê |
|---|---|---|---|
| Fundo (visto de longe, pela janela) | 1 a 3 mil | 1 mil | ocupa poucos pixels; vira sombra de cascata se não for tirado dela |
| Objeto de mão / pequeno | 2 a 5 mil | 2 mil | fica perto da câmera, mas o relevo vai no normal map |
| Objeto grande visto de perto | ~5 mil (até 8 mil) | 5 mil | tanque de laboratório: 5 mil ficou idêntico a 12 mil lado a lado |
| Criatura grande (total das peças) | 10 a 20 mil | 10 mil | Reaper Leviathan do Subnautica: ~8,6 mil |
| Personagem (jogador, NPC) | 10 a 30 mil | 10 mil | personagens de PC atuais: 10 a 30 mil no LOD0 |

Referências usadas no levantamento (2026-09-29, horrorProj): Reaper do Subnautica ~8,6 mil triângulos;
personagens de jogos de PC atuais 10 a 30 mil; teste próprio do tanque (844 mil -> 12 mil e 5 mil, sem
diferença visível entre os dois no jogo).

## Texturas

| Uso | Tamanho |
|---|---|
| Fundo | 512 a 1024 |
| Objeto pequeno numa mesa, bancada | 1024 |
| Objeto que fica na mão, colado na câmera | 2048 |
| Objeto grande visto de perto, criatura, personagem | 2048 |

Nunca importar as 4096 do Meshy direto. Metal + rugosidade viram um único mapa MetallicSmoothness (URP).

## Critérios do otimizador (scripts/optimize_model.py)

- **Contorno**: desvio médio entre os contornos do original e do leve, em pixels num quadro de 512, pior das 4
  vistas. Aprovado: <= 0,75 px.
- **Ponto quente de sombreamento**: percentil 99,5 da diferença de luminância em blocos de 16 px entre o render
  do original e o do leve (mesma câmera e luz). Aprovado: <= 0,12. Calibração: lousa com rasgo 0,27; lousa sem
  diferença visível 0,045.
- Subida: +25% por degrau, até o máximo da faixa.

## Registro (cresce a cada uso)

- 2026-09-29 · tanque (Meshy, 844 mil): 12 mil entregue e cobrado; 5 mil ficou idêntico. Começar no mínimo.
- 2026-09-29 · criatura em 3 peças (Meshy): 24 mil no total (6 + 5x3 + 3), acima da faixa; emendas visíveis de
  perto. Próximas criaturas: peça única + esqueleto.
- 2026-09-30 · lousa de mergulho (Meshy, 1,16 milhão): IoU dava 0,95 a 5 mil (peça fina engana); contorno já
  passava a 2 mil (0,54 px), mas um rasgo perto da corrente só apareceu no sombreamento (0,27). Final: 2,5 mil,
  UV nova, todos os canais assados. Reaproveitar a textura original na malha decimada deslocava as manchas.
- 2026-09-30 · lote de 6 props do Meshy para a casa alagada (todos `hand`, pivô na base, tamanho real):

  | Objeto | Original | Final | Degraus | Contorno | Sombreamento | Textura |
  |---|---|---|---|---|---|---|
  | Lousa de mergulho | 1,16 mi | 2.500 | 2000 (rasgo) > 2500 | 0,48 px | 0,045 | 1024 |
  | Frasco com fragmento | 2,08 mi | 2.500 | travou em 10,7 mil; remesh; platô a 3125 | 1,27 px | 0,113 | 1024 |
  | Lanterna de mergulho | 1,26 mi | 3.906 | 2000 > 2500 > 3125 > 3906 (alça e anel na silhueta) | 0,71 px | 0,052 | 2048 (fica na mão) |
  | Máscara | 1,34 mi | 3.124 | 2000 > 2500 > 3125 | 0,68 px | 0,055 | 1024 |
  | Garrafa de ar (pony) | 302 mil | 2.000 | passou no mínimo | 0,41 px | 0,035 | 1024 |
  | Rádio de ondas curtas | 681 mil | 2.500 | 2000 > 2500 | 0,61 px | 0,040 | 2048 |

  Lições: (1) o collapse do Blender trava num piso em peças finas e emaranhadas (tentáculos dentro do frasco):
  qualquer alvo dava 10,7 mil e a malha saía rasgada; remesh em voxel antes resolveu. (2) Depois do remesh o
  contorno estacionou (~1,2 px de 2,5 a 5 mil): a perda era do remesh, não da contagem; regra de platô criada.
  (3) O Meshy entrega alguns objetos DEITADOS (lanterna, máscara) e outros em pé: confira os eixos na engine
  pelos bounds da malha e ache a "frente" medindo (a lente é a ponta mais larga) antes de girar. (4) O Meshy
  deixou um lado do vidro do frasco aberto: casca de vidro transparente simples por fora. (5) Lanterna na mão,
  atrás do próprio facho, fica preta embaixo d'água: luz de vazamento fraca a ~20 cm (a 5 cm estourou).
- 2026-09-30 · MetaHuman base masculino (Fab, UE 5.8): FBX de corpo inteiro com LODs prontos: LOD0 95 mil,
  LOD1 22 mil, LOD2 8,2 mil, LOD3 2,3 mil triângulos; esqueleto de 341 ossos (a cabeça separada tem 874 ossos e
  64 mil no LOD0). Para `character` (10 a 30 mil) o LOD1 já está na faixa sem reduzir nada; o LOD2 fica abaixo
  do mínimo. O DCC export dá texturas de cabeça e corpo em 4 conjuntos (Basecolor, Normal, SRMF = specular,
  roughness, metal, fuzz). Sem cabelo, sem roupa, sem animação facial fora do Unreal.
- 2026-09-30 · corpo do jogador (MetaHuman, primeira pessoa): comparei as mãos de perto (o que mais aparece na tela)
  entre LOD1 (22 mil) e LOD2 (8,2 mil): iguais. Ficou o LOD2, abaixo do mínimo de `character`, sem perda. Personagem em
  primeira pessoa: separar a cabeça (só sombra), a câmera fica dentro dela. Nomes de osso do MetaHuman: `indextoe`,
  `middletoe`... começam como os dos dedos da mão; filtre "toe" ao separar mãos por peso.

