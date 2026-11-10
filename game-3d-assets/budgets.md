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
- 2026-10-11, mobília da mansão (BeneathTheShroud, 53 modelos Poly Haven pelo `optimize_model.py` em lote, 5 Blenders em
  paralelo, ~25 min): móveis grandes partindo de 5 mil ou da contagem original quando menor (sofá 2,7 mil, cômoda 3,9 mil,
  cama gótica 18,7 para 5 mil, armário vintage 61 para 5 mil), objetos de mão em 2 mil. **Vidro translúcido e trama vazada
  não passam pelo bake**: garrafas de vinho saíram brancas opacas (ponto quente 0,44 no máximo da faixa), o relógio de
  lareira perdeu o mostrador (o vidro da frente virou disco preto, 0,41), o cesto de vime perdeu a trama (contorno 2,9 px).
  Garrafas: material escurecido na engine; relógio e cesto ficaram fora. O ponto quente acima de 0,15 no máximo da faixa
  é o aviso: abra a comparação antes de usar. **Bug do importador glTF do Blender 5.2** (`IndexError ... out of bounds`) em
  `vintage_grandfather_clock_01` e `side_table_tall_01`: use o FBX 1k do Poly Haven (texturas .exr trocadas por .jpg). A
  fileira de baixo da comparação não mostra metal: confira o `_MetallicSmoothness.png` (a lamparina parecia bege, mas o
  canal R tinha média 0,32); os mapas de suavidade do Poly Haven são de objeto novo (0,6 a 0,73 em latão e cerâmica): numa
  cena de abandono, escale a suavidade na engine (projeto: 55%).
- 2026-10-13 (BeneathTheShroud, lista da Dayse): **GLB do Sketchfab com metal como fator** (sem mapa): o bake deixa o
  `_MetallicSmoothness` com R zero e o objeto fica claro e fosco na comparação (cálice, prato dourado, talheres). Conferir
  a linha de baixo da `_compare.png` em todo objeto metálico e, se perdeu, pôr R=255 no mapa. **Escala de móvel do
  Sketchfab**: o `--size` é o maior lado; meça pela altura conhecida (mesa de jantar 0,76 m: a "Large Dining Table" tinha
  0,52 de altura com 2,6 de comprimento, o certo era 3,77 m). **Kits modulares** do Poly Haven (modular_pipes, cables,
  airduct) chegam como peças espalhadas num plano: não servem como um objeto só. **Meshy imagem para 3D a partir de
  desenho conceitual** funcionou muito bem (cogumelo e palma fiéis ao desenho): recorte a figura, apague texto e setas por
  cor e mantenha só a maior forma conectada. Custo medido: 30 créditos por imagem para 3D com PBR, 20 o preview de texto, 10
  o refine.
- 2026-10-14 (Beneath the Shroud, Sketchfab da lista da Dayse): KitchenTableSet 9.790 -> 4.998 (large, mesa e 4 cadeiras numa malha; o --size de 1,7 deixou a mesa com 0,85 m: escala 0,9 no jogo), ToolBox 17.931 -> 3.750, SplitAC 11.404 -> 2.999, CeilingAC 960, VictorianWallLamp 2.970, MetalCase 1.576 (originais abaixo do mínimo). Lições: (1) **Windows não diferencia maiúsculas**: copiar `ToolBox` para `Props/` sobrescreveu o `Toolbox` que já existia (refeito); conferir nome existente sem caixa antes de copiar. (2) o bake perdeu o metal do latão da arandela de novo (GLB com metal por fator): R=255 onde a cor é latão. (3) a escala dos GLB do Sketchfab vem em qualquer unidade (cm, mm, 1000x): medir a proporção real (altura da mesa) e não só o maior lado. (4) unidade de teto vem com a grelha para cima: virar no jogo.
- 2026-10-22 (Beneath the Shroud, porta interna, Sketchfab "Mid-poly Wooden Door with Animations" de GUIBEL, CC BY): folha 3.181 -> 2.499 (hand, 2048), batente 986 (abaixo do mínimo, fica). Lições: (1) **GLB esqueletizado** (armature, mesmo trivial: o autor animava a folha por um osso na dobradiça) guarda os vértices crus em Y-up do glTF e deixa a conversão no rest pose do armature: `flatten_model.py` agora aplica os modificadores antes (sem isso a porta chegava deitada quando o otimizador descarta o armature); uma "Icosphere" solta sem material (forma de osso) tem de ser descartada. (2) **Peça que gira na engine (folha de porta)**: separar pela pesagem dos ossos (folha/maçaneta/trinco no osso da dobradiça, batente na raiz), pôr o pivô no eixo da dobradiça medido no próprio osso (aresta da folha, na face para onde abre, no chão) e `--pivot keep` no otimizador; batente exportado com a MESMA origem para montar no mesmo transform. (3) Malhas juntadas de um GLB podem deixar várias camadas UV (uma por malha de origem); o smart project só enchia a ativa e a engine lê a primeira: `fresh_uvs` agora zera as camadas e cria uma só. (4) Métricas passaram a 2.000 (contorno 0,002 px, ponto quente 0,036), mas o close-up a 45 cm mostrou um canto mordido na placa da maçaneta: +25% (2.499) fechou. **Objeto que se vê a um palmo: render de perto além da folha de contato.** (5) Metal por fator no GLB (maçaneta e placa factor 1) assou certo (R 255 nas duas); trinco e contra-chapa são factor 0 no original (escolha do autor, mantida).
- 2026-10-23 (Happy Harvest, 17 props da cabine: Poly Haven CC0, Sketchfab CC BY, poly.pizza CC0; preparados por `SourceAssets/Blender/prep_props.py` em partes com pivô próprio e montados por `assemble.py`): AmmoCrate 10.476 -> 2.000, OilCan 16.746 -> 2.000, Stool 10.946 -> 2.000, Lantern 33.902 -> 5.000 (vidro opaco, ponto quente 0,148), Compass 10.997 -> 5.000, Radio 16.074 -> 4.882 (contorno 1,17 por plugs finos, platô), Generator 26.419 -> 6.000 (large), Gauge 3.320, SpotSwitch 5.480 -> 2.000 + Toggle 2.072 -> 800. Lições: (1) **qualquer PNG ao lado do GLB de entrada vira a textura base** (`resolve_source` pega a maior imagem da pasta): um render de conferência `_check.png` na mesma pasta assou 7 props pretos com manchas rosa, e a linha de cima do `_compare.png` (original) já mostrava o erro. Pasta de entrada só com o GLB. (2) **Disco de vidro na frente de um mostrador** (manômetro) assa como disco branco opaco por cima do dial: apague a peça de vidro antes. (3) Material só por fator (Kenney, Quaternius, CreativeTrio, primitivos próprios) sem nenhuma imagem cai no `source_material` cinza: ligar uma imagem uniforme 16x16 na cor base de cada material resolve (`flatten_materials` no prep). (4) Peça que gira (alavanca, lâmina de chave, ponteiro): separar por loose parts + caixa de limites, pivô na dobradiça, `--pivot keep` sem `--size` (pré-escalado em metros, senão cada parte escala sozinha) e guardar o deslocamento em JSON para o assemble parentar.
- 2026-10-24 (Happy Harvest, marcos da fazenda vistos a ~100 m: celeiro, silo, moinho; dono: "MUITO ruins, nem pesquisou"). Celeiro: Sketchfab "3December 2022 - Barn" (Jack Kelly, CC BY, 3.277 tris só o prédio) + galpão lateral, 2 cúpulas, rodapé de concreto e desgaste feitos no Blender = 4.157 tris, 2048. Silo: nenhum CC0/CC BY de silo de aduela com cúpula serviu (busca na API do Sketchfab: só silos de chapa ou fotogrametria de 1 a 5 mi); feito no Blender com texturas Poly Haven = 1.856 tris, 1024. Moinho: Sketchfab "Windmill pump farm" (e.font, CC BY, 108.200) -> corpo 3.999 (contorno 0,65, ponto quente 0,043) + roda 2.600 separada para girar (ponto quente parado em 0,15 a 0,18 em toda a escada: pás finas de dupla face, não é contagem). Lições: (1) **prédio grande = construir alto e assar num atlas só** (`SourceAssets/Blender/build_farm.py` do Happy Harvest): materiais em camadas (textura PBR + sujeira por altura + escorrido vertical por ruído esticado em Z + AO do Cycles na cor), cópia com UV smart e bake selected-to-active com cage 1 cm; 2048 dá ~70 px/m num celeiro de 16 m, sobra para 100 m. (2) **Tinta acima de 1 no MULTIPLY** traz uma textura cinza-marrom (tábuas, linear ~0,2) para o vermelho do resto do prédio; tinta < 1 deixou o galpão marrom-escuro. (3) Branco de acabamento: cor chapada + desgaste, não textura de madeira multiplicada (saiu bege). (4) API de busca do Sketchfab (`/v3/search?type=models&downloadable=true&license=by|cc0&q=`) com miniaturas numa folha só escolhe candidato em 1 minuto.
- 2026-10-24, Happy Harvest (cabine): 13 props do Poly Haven como enfeite de fundo a 1-2 m passaram no contorno e no ponto quente com 300 a 1200 tris e textura 512 (machado 500, martelo 300, caixa de ferramentas 1200, balde 1200 por causa da alça fina); interior inteiro vestido com ~15 mil tris. Descartar na triagem o que denuncia época/lugar (extintor coreano com base escrita, saco de cimento moderno, latas modernas) e construir no Blender.
- 2026-10-24, Happy Harvest (javali e trator): javali só como silhueta escura (material chapado, sem bake): "Boar" de Teh_Bucket (OpenGameArt, CC0, 1.144 tris com pose do esqueleto) -> subsurf 1 nível + decimate a 3.500 + crina de 198 espinhos (pirâmides de 6 tris, assentadas no dorso por raycast BVH, mais altas na cernelha) + presas curvas = 4.344 tris, 1,5 m (`SourceAssets/Blender/build_hog.py`). Achar o topo do dorso por fatia de vértices pegou a barriga em metade das fatias; raycast de cima resolve. Trator Poly by Google (poly.pizza, CC BY 3.0, 2.766 tris) já na faixa: sem redução, só UV nova + bake 1024 (ponto quente 0,09). Caí de novo na lição da miniatura: o PNG da página copiado ao lado do GLB virou a textura base (`sources_found.base` mostrou); pasta de entrada só com o modelo.
- 2026-10-26, Happy Harvest (árvores de fundo e fardo redondo): Poly Haven island_tree_01 (1,6 mi), island_tree_02 (1,07 mi),
  tree_small_02 (2,06 mi) -> 1.500 cada pelo `tree_cards.py` (madeira 525 + 244 cartões), e island_tree_01 -> 4.000 para a
  árvore grande do menu. Lições: (1) o collapse uniforme encolheu o tronco a poucas faces e a passada de partes soltas
  (por contagem de faces) jogou o tronco fora: copa flutuando. Agora `--wood-area 0.9` descarta antes os galhinhos de
  menor ÁREA e a passada final ordena por área. (2) Soldar costuras antes do collapse virou o tronco do tree_small_02 numa
  cunha gorda: `--weld` ficou desligado. (3) jacaranda_tree (folhas em fronde, 19 m) travou o collapse em 8 a 9 mil
  (madeira numa peça só, não-manifold) e o `leaf_cards.py` não acha folhas em fronde nem em atlas de folhas ligadas por
  talo (tree_small_02): trocar de árvore, ou `--colour-from` para usar folhas de outro atlas com a cor média da planta.
  (4) `--card-scale 1,7` (padrão) deixou a copa um bolo 1,5x maior que o original; 0,9 deu 1,2x e galhos à mostra.
  (5) Copa escurecia: o `leaf_cards.py` agora casa a cor média do cartão com a das folhas originais. Conferência por
  `tree_compare.py` (original x resultado na mesma escala, cobertura e IoU por vista). Fardo: nenhum fardo redondo CC0
  com PBR (Sketchfab só CC BY com login; OpenGameArt CC0 é octógono com textura 256): modelado em
  `SourceAssets/Blender/build_hay_bale.py` (33 mil) com a textura CC0 reed_roof_04 e reduzido pelo `optimize_model.py`
  a 999 (contorno 0,55 px, ponto quente 0,04 de primeira). UV polar no tampo com volta simples deixou uma emenda clara/
  escura no raio: espelhar o V (0 -> 0,88 -> 0) resolveu.
- 2026-10-26 · casa da fazenda (Wilkins, `build_farm.py farmhouse`, construída com caixas, sem original pesado): 3.207
  triângulos, atlas 2048. Atlas de prédio feito de muitas caixas finas saiu com 38% de cobertura e ~40 px/m: o
  `pack_islands` padrão desperdiça; `rotate_method='ANY'` + margem 0,002 subiu para 48%, e tirar faces enterradas
  (fundo da telha sob o sótão trocado por beiral fechado, topo do rodapé, forro sob o telhado da varanda) levou a
  ~48 px/m. Scan de tábua (ambientCG WoodSiding009) repetia em blocos de 2 x 1 m e cintilava no bake a essa densidade:
  cor vira tinta lisa com 25% do scan, normal do scan a 0,35 e a linha da tábua procedural (bump a cada 0,125 m).
- 2026-10-26, gerador portátil do Poly Haven (prop `large` no chão a ~1 m do olho, painel com logo e etiquetas): assado a
  1024 a partir da fonte 2k o logo e as etiquetas viraram borrão. Fonte 4k (o .bin é o mesmo do 2k, só a textura muda) +
  `--tex 2048`: etiquetas e tomadas legíveis a 1 m. Com a mesma malha o contorno pediu 7500 (6000 = 0,82 px, 7500 = 0,62).
  Regra: prop com texto/decalque visto a 1 m pede fonte com o dobro da resolução do bake.
- 2026-10-26 (Happy Harvest, caneca esmaltada feita aqui: `SourceAssets/Blender/build_mug.py` + `bake_mug.py`; o Sketchfab
  tinha boas canecas CC BY, mas o download exige login e o Chrome do chrome-devtools-mcp não está logado): alta 40.992 ->
  1.824 (hand, 1024). Lições: (1) **casca fina (parede de 1 a 2 mm)**: com parede de 1,1 mm os raios do bake (cage 1% do
  tamanho) atravessavam até a face de dentro e o corpo saiu preto; parede de 2 mm resolveu. (2) **Sólido de revolução pelo
  collapse** deixa triângulos da altura inteira da parede com normais de vértice tortas (média com a borda/fundo): faixas
  claras e escuras no bake, ponto quente 0,31 em TODOS os degraus de 2 a 5 mil (contorno ok, 0,04 a 0,12). Saída: construir a
  malha leve limpa (mesmo perfil, 32 lados, laços de apoio na parede) e assar com as funções do próprio `optimize_model.py`
  (`bake_mug.py` faz `exec` do script sem o `main()`): contorno 0,36 px, ponto quente 0,039 com 1.824. Ponto quente constante
  entre degraus = problema de topologia, não de contagem. (3) Ferrugem pura dentro do lascado lia como tinta dourada a 0,8 m:
  misturar 60% de óxido escuro.
- 2026-10-26 · chapéu de palha modelado por script (HappyHarvest, `SourceAssets/Blender/build_hat.py`, 141,6 mil): passou
  nas métricas já a 2.000 (contorno 0,33 px, ponto quente 0,084), mas o laço e os ilhoses de latão viraram mancha;
  ficou 3.000 (0,24 px, 0,085) por olho. Trama fina (palha 5,6 mm) assada com as 4 amostras do otimizador saiu
  chuviscada: `optimize_blend.py` (roda o otimizador num .blend, mantém nós procedurais) assa com 64 amostras e a
  trama foi engrossada para 6,6 mm para caber em 1024. Métrica não pega peça pequena de detalhe (laço) virando ruído.
- 2026-11-10 (BeneathTheShroud, itens de coleta): **Bandage** (latinha de primeiros socorros com rolo de gaze preso por
  tira; Meshy text-to-image 3 cr + image-to-3d 30 cr, 928 mil) travou no collapse em 14,2 mil e foi pelo remesh em voxel.
  A 2.000 e a 2.500 as métricas passaram (contorno 0,33/0,14 px, ponto quente 0,04/0,03), mas a `_compare.png` mostrou
  a tira da gaze com um fecho de metal/rasgo onde ela dobra sobre a borda da tampa: a malha leve afundou abaixo da tira
  (mais que o cage de 1%) e o bake pegou a borda da lata por baixo. 4.000 com `--remesh-res 360` limpou (0,11 px, 0,022).
  Tira fina sobre aresta saliente pede triângulos; só o olho pegou. **AmmoBox357** (caixa de papelão .357, 117,5 x 61,5 x
  40,5 mm): feita por script (atlas do rótulo genérico pintado em PIL a 8 px/mm com desgaste por ruído 3D contínuo entre
  as faces + malha alta em voxel com ruga, canto esmagado, bandeja recuada e entalhe de polegar, 288 mil) e reduzida a
  999 de primeira (contorno 0,49 px, ponto quente 0,017): caixa não precisa nem do mínimo de `hand`.
- 2026-11-10 (Beneath the Shroud, 5 fungos/vermes do Sketchfab, CC BY, recortados e com pivô por `SourceAssets/Tools/scan_prep.py`):
  OysterCluster 1,45 mi -> 3.000 (travou no collapse, voxel remesh; contorno 0,60, ponto quente 0,032), BracketFungus 50 mil
  (recortado de 227 mil, sem o tronco) -> 2.000 (contorno 0,44, ponto quente 0,019), BonnetCluster 1.728 (mantido),
  PuffballCluster 23 mil (recortado de 300 mil, sem o chão) -> 3.000 (0,60 / 0,046), RiftiaColony 39 mil -> 4.999 (large;
  0,70 / 0,113; 6.250 deu o mesmo, platô). Lições: (1) **GLB separa os vértices em cada costura de UV**: no scan do Polyporus o
  collapse deixou rachaduras escuras pela peça inteira e o contorno empacou em 1,8 px até 4 mil (cage maior não mudou nada, remesh
  em voxel de casca aberta destruiu a peça: 59 px); soldar os vértices coincidentes no import resolveu já no mínimo (2 mil, 0,44 px).
  Com a solda, o PuffballCluster caiu de 5.000 para 3.000. (2) Material unlit de scan (Emission + Light Path) não é lido pelo bake:
  refazer como Principled antes. (3) Recorte de scan: máscara por face combinando cor da textura (saturação) com altura sobre o
  substrato (cilindro ajustado ao tronco; quadrática ajustada ao chão) e componentes conexos; o limiar de distância à "semente"
  colorida apertado demais abre buracos onde a textura do fungo é escura.
- 2026-11-10 (BeneathTheShroud, geradores locais, ver SKILL 0b): **afogado TRELLIS.2 1024** 300 mil -> 10.000 de primeira
  (`creature`, contorno 0,43 px, ponto quente 0,039; a criatura inteira com alga cabe no mínimo da faixa). **Lamparina
  TRELLIS.2 1024** 300 mil -> 2.500 (`hand`, 1024; contorno 0,67 px). O ponto quente ficou em 0,18 de 2.500 a 5.000
  (platô): é o vidro da chaminé, que o GLB traz translúcido e o bake deixa opaco branco. Use `--max-tris` e faça o vidro
  como peça à parte. A primeira passada saiu preta: o otimizador pegava a imagem de entrada (`*_input.png`) ao lado do
  GLB como cor base; corrigido (GLB/glTF usa o próprio material).
