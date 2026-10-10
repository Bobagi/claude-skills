# Orçamentos, fontes e registro

## Triângulos por tipo (na engine)

| Tipo | Faixa | Começar em | Por quê |
|---|---|---|---|
| Fundo (visto de longe, pela janela) | 1 a 3 mil | 1 mil | ocupa poucos pixels; vira sombra de cascata se não for tirado dela |
| Objeto de mão / pequeno | 2 a 5 mil | 2 mil | fica perto da câmera, mas o relevo vai no normal map |
| Objeto grande visto de perto | ~5 mil (até 8 mil) | 5 mil | tanque de laboratório: 5 mil ficou idêntico a 12 mil lado a lado |
| Criatura grande (total das peças) | 10 a 20 mil | 10 mil | Reaper Leviathan do Subnautica: ~8,6 mil |
| Personagem (jogador, NPC) | 10 a 30 mil | 10 mil | personagens de PC atuais: 10 a 30 mil no LOD0 |

Referências usadas no levantamento (2026-09-29, BeneathTheShroud): Reaper do Subnautica ~8,6 mil triângulos;
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
- 2026-09-30 · corpo do jogador, 2a rodada: o LOD2 (8,2 mil) igualava nas mãos, mas olhando para baixo o peito e os
  ombros ficam a um palmo da lente e mostraram facetas grandes. Subi para o LOD1 (22 mil, dentro da faixa) e passei
  cabeça, pescoço, ombros e peito alto para só-sombra. Lição: compare a malha no ângulo e na DISTÂNCIA em que o jogador
  vê cada parte (as mãos não representam o peito). Não troque a textura original de um asset (pus uma roupa de
  mergulho por conta própria e o Gustavo queria o MetaHuman como veio, de cueca, para vestir depois).

- 2026-10-01 · móveis Poly Haven da casa (BeneathTheShroud): lustre 21,5 mil para 5 mil, fogão 13,9 mil para 5 mil, mesa de
  centro 10,4 mil para 5 mil, aparador 7,6 mil para 5 mil, arandela 9,8 mil para 2 mil, micro-ondas 8,1 mil para 2 mil,
  pendente 5,6 mil para 2 mil, cadeira de jantar 22 mil para 5 mil: todos passaram no primeiro degrau. Exceção: o
  gravador de fita (4,8 mil) a 2 mil passou nas métricas, mas o `_compare.png` mostrou uma mancha escura no painel da
  janela; a 3 mil sumiu (ponto quente 0,058). Objeto que fica na mesa e é olhado de perto: confira o painel liso no
  compare, não só os números. Use `--size` com a medida real da API do Poly Haven (`/info/<id>` → `dimensions`, em mm).

- 2026-10-02 · traje hazmat do Meshy (estátua, 180 mil, sem esqueleto) como **reskin do corpo MetaHuman** em primeira
  pessoa (BeneathTheShroud, `SourceAssets/Tools/hazmat_suit_rig.py`). Contorno e sombreamento passaram a 10 mil, mas em
  primeira pessoa, olhando para baixo, o peito a 15 cm do olho facetou: subiu para 20 mil (traje 16,5 mil + capuz/máscara
  2,9 mil só-sombra + luvas 6,1 mil = 25,5 mil, dentro de `character`). Processo que funcionou: posar o esqueleto na pose
  da estátua (alvos de cotovelo/punho/joelho/tornozelo medidos), pesos dos 4 vértices mais próximos do corpo **do mesmo
  membro** (membro = osso mais próximo **com a superfície virada para fora dele**: sem isso o quadril colado no antebraço
  virou saia de pontas), inverter o skinning para a pose de repouso. Faces que ligam luva/manga ao quadril (estátua
  fundida) não se apagam nem se fecham com tampa (a tampa ia da manga ao quadril e virou estilhaço com o braço à frente):
  as quinas do lado do braço ganham vértice próprio e o retalho fica no quadril. Luvas do Meshy são bloco fundido: no
  lugar, as mãos do próprio MetaHuman em borracha preta (dedos, pegada e IK intactos). Esqueleto exportado igual ao do
  corpo (342 ossos, 0,002 mm): na Unity basta religar os ossos por nome. Roupa volumosa: limitar quanto a cabeça abaixa,
  senão o olho entra no peito.
- 2026-10-02 · Afogado (criatura menor humanoide, Meshy, 847 mil triângulos, sem esqueleto): 10 mil no 1º degrau
  (contorno 0,19 px, ponto quente 0,018). Auto-rig do Mixamo falhou 3 vezes ("Unknown error while generating motion",
  malha fechada e de peça única); rigado por `scripts/rig_humanoid.py` (22 ossos com nomes do Mixamo, pesos via proxy
  voxel de 13 mil vértices, 4 vértices sem peso corrigidos pelo vizinho). Humanoid válido na Unity. Correção: a
  primeira importação dos clipes deixava pé flutuando e afundando (avatar do arquivo sem pele, raiz mal configurada);
  com o avatar copiado do X Bot com pele e a raiz da seção 4b, os 12 clipes ficam entre -0,08 e +0,03 m do chão no
  filme em tempo real. Ragdoll: 94% da pele dentro ou a 3 cm de um colisor; com a caixa no pé, repouso a -0,9 cm.
- 2026-10-02 · traje hazmat, 2ª versão: **regerado no Meshy em T-pose, membros afastados, alças coladas** (994 mil para
  20 mil). Resolveu os rasgos da 1ª (que tinha braços colados no quadril). Duas armadilhas novas da T-pose: abas do capuz
  com normal para baixo pegaram peso de `upperarm_out` e viraram espinhos quando o braço desceu para a A-pose do
  MetaHuman (correção: acima da base do pescoço e perto do centro é sempre cabeça) e uns poucos vértices com membro
  errado (correção: vértice cujo deslocamento difere mais de 4 cm da média dos vizinhos recebe os pesos deles; 34, 7,
  3, 2 em 4 rodadas). Roupa para virar pele de personagem: pedir sempre T-pose ou A-pose com nada encostando.
- 2026-10-02 · traje hazmat, 3ª rodada (personagem com esqueleto): **sombra fatiada** = arestas duras do "smooth by
  angle 40" dividem os vértices e o viés de normal da sombra (URP, 1) empurra as cópias para lados diferentes, abrindo
  rachaduras na sombra (com viés 0 ficava sólida; o MetaHuman, todo liso, não tinha). Correção: `--smooth-angle 180`
  (opção nova do `optimize_model.py`) para personagem com esqueleto; o ponto quente não piorou (0,015). Solas com peso
  da canela viravam espinho ao andar: abaixo do tornozelo é sempre pé. Corpo visto em primeira pessoa: textura 4096.
- 2026-10-02 · tentáculo solto (Meshy, 733 mil, reto, 3 m): 6 mil no 1º degrau (contorno 0,37 px, ponto quente 0,024),
  abaixo do mínimo de criatura porque é uma peça de 3 m vista pela janela. Rig: `rig_tentacles.py --arms 1`, 12 ossos;
  5 pontos do grafo sem vizinho fora do próprio grupo viravam espinhos jogados para a ponta (corrigido: herdam a
  distância do vizinho alcançado).
- 2026-10-02 · polvo colossal (Meshy, 1 milhão, estrela, 12 m): 10 mil no 1º degrau (contorno 0,22 px, ponto quente
  0,041). **7 braços**, não os 8 do prompt. Rig: `rig_tentacles.py --arms 7` (87 ossos). Braços descem do corpo até a
  ponta (base 1,9 m acima) e o saco do manto pende 0,4 m abaixo das pontas: apoiar pelo ponto mais baixo da pele inteira
  deixou o polvo "de pé" sobre o saco com os braços no ar.
- 2026-10-03, MetaHuman preset Mateo montado Optimized/Medium: corpo 11,8k/5,5k/1,5k, rosto 6,9k/1,5k/0,4k, roupa padrão 25k/7,6k/2,1k/1k, cabelo em cards LOD2 10k, sobrancelha 1k. NPC no orçamento (~30k) = corpo LOD1 + rosto LOD0 + roupa LOD1 + cabelo LOD2.
- 2026-10-03, Erick (MHC_Base_Male + Survivor Outfit do Fab), pele no esqueleto do jogo: roupa 25,8k -> 12,9k (Blender 50%; LOD1 da Unreal 6,5k e Blender 35% 9k perderam), corpo à mostra 5,5k (de 15,6k), cabeça só-sombra 1,9k, cabelo cards LOD3 3,2k, barba cards LOD3 2,5k: total 26,2k.
- 2026-10-03, plantas do Poly Haven para a ilha da abertura (fundo): o `optimize_model.py` não serve para folhagem (o
  bake em UV nova perde o recorte em alfa). `scripts/foliage_reduce.py`: descarta folhas inteiras até 5x o alvo e depois
  colapsa mantendo as UVs. As folhas do Poly Haven são malhas de ~120 triângulos, não cartões: só descartar deixou a
  samambaia com 8 de 53 folhas. Saída: samambaia 6,2k -> 1k, sorrel 3,3k -> 1k, calathea 16,7k -> 1k, arbustos 27k ->
  2k (os galhos sozinhos passam de 1k). Pachira (77k, quase tudo tronco) e as árvores (1,7 a 4,7 milhões) ficaram de
  fora: precisam de outro caminho (impostor ou modelo próprio).
- 2026-10-03, olhos do Erick (MetaHuman) para close na cutscene: o corpo inteiro exportado do MetaHuman traz a cabeça
  SEM globos oculares e com cílios e cascas do olho soldados na pele (pintados de pele, viram pálpebra fechada). Globos
  do exporte da cabeça (`*_Head.fbx`, submalhas "Eyes", LOD2 440 tri cada) e a pele da mesma cabeça (submalha "Head",
  LOD3 4,8k) cortada no pescoço; as duas cabeças batem a 0,2 mm. Peças soltas: o exporte separa vértices em toda
  emenda, então agrupar por POSIÇÃO, não por índice. Script do projeto: `SourceAssets/Tools/erick_eyes.py`.
- 2026-10-03, árvores e arbustos com copa (Poly Haven island_tree_02 1,07 mi, searsia_lucida 377 mil) para a ilha da
  cutscene: o `foliage_reduce.py` deixou 400 de 35 mil folhas, a árvore virou tronco pelado (de longe, a ilha careca).
  Copa = **cartões de cacho de folhas**: `scripts/leaf_cards.py` monta a textura com as folhas recortadas do atlas do
  próprio Poly Haven e `scripts/tree_cards.py` troca as folhas por 2 cartões cruzados por célula de uma grade sobre as
  folhas originais (contorno e densidade iguais), normais saindo do centro da copa, madeira colapsada (e galhinho solto
  descartado quando o collapse trava). Árvore 4.000 (madeira 2.200 + 450 cartões), arbusto 2.498 (798 + 425).
  Plantas pequenas do Poly Haven (fern_02 0,45 m, shrub_03 é um raminho de 0,4 m, shrub_sorrel 0,15 m) não aparecem a
  30 m: conferir `dimensions` na API antes de escolher planta para paisagem.
- 2026-10-03, props de fundo do Poly Haven no LOD mais leve ainda pesavam 100 a 214 mil cada (coast_rocks_02 LOD3 157
  mil, root_cluster_02 214 mil): 7,4 mi de triângulos no quadro. Pela skill: 1 a 3 mil cada (CoastRocks 2,06 mi ->
  1.952, platô em 2.440). E `coast_rocks_01/02` são praias de seixos de 46 m, não rochas: viram lajes sobre o morro.
- 2026-10-03, porta da mansão (Sketchfab "Classic Wooden Double Door", GLB 4k, 252 mil): o otimizador juntou as peças
  sem as rotações dos nós pais do GLB e a porta saiu desmontada (folhas e moldura giradas 90 graus entre si); a própria
  `_compare.png` mostrava o mesmo embaralhado nas duas linhas, então as métricas passaram. Antes de reduzir GLB do
  Sketchfab: `scripts/flatten_model.py` (aplica a transformação de cada nó e solta a hierarquia) e conferir as medidas.
  Final 6.250 (large): o ponto quente de sombreamento (0,29) era o vidro translúcido assado opaco, não falta de
  triângulos; subir até 8 mil não mudava nada, então `--max-tris` no degrau em que o contorno passou.
- 2026-10-03, porta da mansão de novo ("maçaneta quadrada"): a 6.250 triângulos assados a barra curva do puxador virou
  polígono visível em primeira pessoa a 30 cm. Objeto em primeiríssimo plano: as partes de silhueta (folhas + puxadores)
  ficam com a geometria original afinada só nas áreas planas (Decimate DISSOLVE 1 grau, delimit UV/material/sharp: 27 ->
  13,8 mil, curvas intactas) e os mapas originais; o resto (moldura entalhada) pela skill a 5 mil. Total ~19 mil,
  acima da faixa "large", justificado pela captura: é o que a câmera vê de mais perto na cena.
- 2026-10-05 · Roblox, IA de malhas do Studio (`generate_mesh`, sem Blender): itens de mão a 3 mil, peitoral a
  5 mil. "Armadura de peito" veio duas vezes como cavaleiro inteiro: o prompt precisa dizer "single wearable
  piece only, no head, no arms, no legs, no person, hollow neck hole". Recolorir por `SurfaceAppearance.Color`
  multiplica a textura (rosa x dourado = oliva): para variante "dourada" de uma textura colorida use cor sólida
  sem textura. Frente medida: item solto olha -Z; acessório vestido mostra o +Z da malha.
- 2026-10-09 · lote de 5 props pela API do Meshy (vara com gancho, escada de sótão, painel de segurança, tablet rachado,
  desumidificador destruído): **GLB da API + PNGs soltos ao lado = textura assada errada** (a vara saiu com listras
  brancas e pretas no cabo; o script acha os `texture0_*.png` e os aplica nas UVs do GLB, que têm o V invertido em
  relação a eles). Com o `model.fbx` do mesmo pedido saiu igual ao original. **Use sempre o `.fbx` da API como --src.**
  O ponto quente de sombreamento (0,078) não pegou as listras: só o olho na `_compare.png`. Escada pelo texto veio
  incoerente duas vezes (escada simples; depois armação em pé e escada deitada); **text-to-image (3 créditos) e
  image-to-3d (30) a partir da imagem aprovada** acertou na 1ª. Desumidificador (2,5 mi) travou no collapse e foi
  para o remesh em voxel: a 5 mil com `--remesh-res 200` perdeu os fios e a grade do ventilador atrás do painel
  rasgado; 8 mil com `--remesh-res 360` devolveu a grade (contorno 0,40 px). Painel 2,5 mil, tablet 3,9 mil,
  escada 5 mil (contorno 0,09 px), vara 2 mil (contorno 1,39 px no limite pedido de 2 mil, gancho fino).
