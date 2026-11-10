---
name: game-3d-assets
description: Pipeline de modelos 3D para jogo em tempo real. Importa modelos de alta contagem (Meshy, Tripo, Fab, Sketchfab, Poly Haven, scan, MetaHuman), reduz para o orçamento de triângulos do tipo de objeto começando pelo MÍNIMO da faixa, assa o relevo e as texturas do original na malha leve, mede a perda contra o original (contorno e sombreamento) e só sobe a contagem se a perda aparecer; depois importa na engine (Unity URP por padrão) com material certo e confere no jogo. Use SEMPRE que for mexer com a parte 3D: importar/baixar/gerar um modelo, "reduz os polígonos", "coloca esse modelo no lugar do placeholder", "quantos triângulos", "o modelo está pesado", trocar malha, textura de modelo, LOD, personagem, criatura, e ao avaliar se um asset (ex.: MetaHuman, pacote do Fab) serve para o jogo.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, WebSearch
---

# game-3d-assets: modelo pesado entra leve, sem perder o que se vê

Regra de ouro (pedido do Gustavo, 2026-09-29: "não quero ter que ficar te cobrando"): **todo modelo entra no
orçamento do seu tipo, começando pelo mínimo da faixa**, e só sobe se a comparação lado a lado mostrar perda.
O número final e a comparação vão no relatório, sempre. Passou da faixa: explique com a captura na mão.

Leia **`budgets.md`** antes de decidir números (tabela, fontes, texturas) e registre nele o que aprender.

## 0. Gerar no Meshy direto pela API (desde 2026-10-08, plano Pro do Gustavo)

`scripts/meshy.py` (chave em `~/.config/ai-workers/meshy.key`, fora de qualquer repo; `meshy.py balance` mostra os
créditos). Texto/imagem para 3D (preview, depois refine), retexture, remesh, rigging, animação (biblioteca de 200+
`action_id`, `library --q`), text-to-image e image-to-image, tudo com `create <tipo> --body '{json}' --wait --out pasta`.
Custos medidos/documentados: imagem 3 a 9, rigging 5, animação 3 por clipe, retexture 10. Baixar em
`SourceAssets/Downloads/AI/meshy/<objeto>/` e passar pelo `optimize_model.py` (nunca importar o original). Regras do
GDD valem: prompt completo com pose e simetria, T-pose (`pose_mode`) para roupa e personagem, topologia quad para o que
dobra. Gerar em alta, reduzir no Blender. Gasto de crédito grande (refine 4k, lotes): avisar o saldo antes e depois.

**Modelo do Meshy (pesquisado 10/11/2026, docs.meshy.ai/api):** `ai_model` aceita `latest` (= **meshy-7.1**, desde
30/10/2026), `meshy-7.1`, `meshy-6`, `meshy-6-lite`; `meshy-7` está obsoleto (ainda responde). Smart Topology
(`model_type: smart-topology`): `meshy-t2` e `meshy-t2.5` (triângulos, partes separadas, `target_polycount` até 15 mil
e 30 mil). Créditos de imagem para 3D: 7.1/7/6 = 20 só malha, **30 com textura 2K/4K**, 35 com 8K; 6-lite e t2/t2.5 =
5 só malha, 15 com textura. Retexture 10, remesh 5, rigging 5, animação 3 por ação. Teste de 10/11 (lamparina, imagem
do Juggernaut, `meshy-7.1`, `enable_pbr`, sem remesh): 30 créditos, ~4 min, 961 mil triângulos, forma mais limpa e
simétrica que a dos geradores locais, vidro opaco leitoso. `symmetry_mode` foi descontinuado (não faz efeito).

## 0b. Gerar LOCAL na GPU (desde 2026-11-10): TRELLIS.2 venceu

```
python <skill>/scripts/gen3d_local.py --image ref.png --out <pasta>/<Nome>.glb [--res 1024] [--seed 42]
```
Imagem com fundo neutro, objeto inteiro, vista 3/4 (o BiRefNet recorta o fundo). Sem crédito, ~1,5 min por objeto
numa RTX 3060 Ti 8 GB. O script cuida da trava `C:\ComfyUIFiles\temp\gpu.lock` (espera a de outro agente), sobe e
derruba o servidor próprio e grava `<Nome>.json` com tempo e VRAM. Depois, `optimize_model.py` no GLB, como sempre.
`render_compare.py` (Blender, Cycles na CPU) + `make_sheet.py` montam a folha lado a lado de vários GLB/FBX.

| Engine | Onde (neste PC) | Licença | Uso |
|---|---|---|---|
| **TRELLIS.2** (Microsoft, 4B), `--engine trellis2` (padrão) | nós **nativos** do ComfyUI v0.45 numa instância **separada**: `C:\ComfyUIFiles\tools\trellis2\ComfyUI` (venv Python 3.12, torch 2.14.1+cu130, porta 8190); pesos `Comfy-Org/TRELLIS.2` (`trellis_2_int8_convrot`, 2 VAEs, `dino_v3_vit_l`) + `Comfy-Org/BiRefNet` | **MIT** | pode ir para o jogo |
| Hunyuan3D-2mini + paint v2-0-turbo (Tencent), `--engine hunyuan --texture` | `C:\ComfyUIFiles\tools\hunyuan3d` (repo oficial, venv 3.12, torch 2.14.1+cu130, transformers 4.57, diffusers 0.35; `custom_rasterizer` compilado com o CUDA 13.5 redist em `tools\hunyuan3d\cuda135`, script `build_texgen.bat`) | **Tencent Hunyuan Community: NÃO vale na UE, Reino Unido e Coreia do Sul** | **só teste**; nada dele vai para o jogo sem decisão do dono |

Medido em 10/11 (lamparina e afogado, mesma imagem; folhas em `BeneathTheShroud/SourceAssets/BlenderExports/GenCompare/`):
TRELLIS.2 512 = 40 a 48 s, **1024 = 72 a 97 s**, 1536 = 135 a 222 s (tempos com a carga do modelo); o ComfyUI enche a
VRAM livre (pico 7,1 a 8,0 GB da placa inteira, com o Unity aberto) e descarrega o resto, sem OOM. Hunyuan 2mini = 124
a 129 s com textura, pico torch 4,8 GB (placa 7,7 GB). Qualidade: **TRELLIS.2 1024** pega rosto, rugas, alga e o arame
da lamparina; 1536 quase igual ao 1024 pelo dobro do tempo; 512 amolece. Hunyuan amolece o rosto (some o olho), funde
detalhe fino, textura mais escura e borrada. Pelo `optimize_model.py`: afogado TRELLIS.2 300 mil -> **10.000**
(`creature`, mínimo da faixa: contorno 0,43 px, ponto quente 0,039); lamparina 300 mil -> **2.500** (`hand`, contorno
0,67 px; o ponto quente fica em 0,18 em todos os degraus por causa do vidro, ver armadilha do vidro, use `--max-tris`).

**Quando usar o quê:**

| Situação | Caminho |
|---|---|
| Prop ou criatura nova a partir de uma imagem (arte do GDD, Juggernaut), muitas iterações | **local TRELLIS.2 1024** (grátis, 1,5 min; gere 2 ou 3 seeds e escolha) |
| Objeto rígido simétrico onde a forma limpa importa e vale 30 créditos | Meshy 7.1 (`latest`) com `enable_pbr` |
| Personagem ou roupa que vai ganhar esqueleto (T-pose, quad, rigging, animação) | Meshy (`pose_mode`, `topology: quad`, rigging e animação na mesma API) |
| Objeto real e comum (móvel, lâmpada, louça) | Poly Haven (CC0) ou Sketchfab (CC BY, crédito) primeiro: feito à mão, UV e topologia boas |
| Hunyuan3D | só comparação; não usar em asset do jogo (licença) |

**Armadilhas da instalação (10/11):** (1) os pesos oficiais `microsoft/TRELLIS.2-4B` pedem `facebook/dinov3-vitl16` e
`briaai/RMBG-2.0`, ambos **fechados no Hugging Face** (login + aceite; o RMBG-2.0 ainda é não comercial). O pacote
`Comfy-Org/TRELLIS.2` traz o DINOv3 junto e o BiRefNet é aberto, por isso o caminho é o nativo do ComfyUI, que também
dispensa flash-attn, CuMesh, FlexGEMM, o-voxel e nvdiffrast compilados. (2) O repo oficial diz Linux e 24 GB; no
nativo com o int8 coube em 8 GB. (3) Hunyuan: `transformers` 5.x renomeou as chaves do DINOv2 (`q_proj`) e quebra o
carregamento: fixar 4.57 + diffusers 0.35. (4) O wheel `nvidia-cuda-nvcc` do pip no Windows não traz `nvcc.exe`; use
os zips "redist" da NVIDIA (sem instalador, sem admin). CUDA 12.8 com o MSVC 14.51 (VS 2026) derruba o `cudafe++`
(0xC0000005); CUDA 13.5 compila com `-allow-unsupported-compiler -Xcompiler /Zc:preprocessor` e torch cu130. (5) O
paint turbo carrega `unet/diffusion_pytorch_model.bin` (7,3 GB); o `.safetensors` do mesmo repo tem chaves de
IP-adapter a mais e não serve no lugar. (6) GLB de gerador traz a própria textura: o `optimize_model.py` agora usa o
material de dentro do GLB (antes pegava a imagem de entrada que ficava na pasta como cor base e saiu tudo preto).

## 1. Orçamento (triângulos na engine, depois de triangular)

| Tipo (`--type`) | Faixa | Textura padrão | Exemplos |
|---|---|---|---|
| `background` | 1 a 3 mil | 1024 | rocha, árvore, casa vista pela janela |
| `hand` | 2 a 5 mil | 1024 (2048 se fica na mão, colado na câmera) | frasco, máscara, lanterna, rádio, lousa |
| `large` | ~5 mil (até 8 mil com captura justificando) | 2048 | tanque, bancada, armário visto de perto |
| `creature` | 10 a 20 mil **somando as peças** | 2048 | criatura grande |
| `character` | 10 a 30 mil | 2048 | jogador, NPC |

Relevo (parafuso, ruga, costura, riscos) vai para o **normal map**. Só **silhueta** (tentáculo, dente,
barbatana, alça) justifica subir triângulos. Referências e contas em `budgets.md`.

## 2. Processo (script pronto, Blender em segundo plano)

1. **Original fora do projeto da engine**: extraia em `SourceAssets/Downloads/<ferramenta>/<objeto>/` (nunca
   importe o original: Meshy vem com 0,3 a 1,2 milhão de triângulos e texturas 4096).
2. **Rode o otimizador** (Blender 4.1+; neste PC `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`):
   ```
   blender -b --factory-startup --python <skill>/scripts/optimize_model.py -- \
     --src <zip|pasta|.fbx|.glb> --name DiveTorch --out <Assets/.../Props/DiveTorch> \
     --previews <SourceAssets/BlenderExports/Props> --type hand --size 0.24 [--tex 2048] [--no-metal]
   ```
   - `--size` = maior lado real em metros (o Meshy normaliza tudo para ~1,9 m). Meça a referência real.
   - `--no-metal` quando a IA chutou metal onde não há (pele, borracha, tecido): aconteceu na criatura.
   - O script: junta as partes, põe o pivô na base, reduz no **mínimo** da faixa, mede o **contorno** em 4
     vistas (desvio médio <= 0,75 px num quadro de 512), faz **UV nova** (smart project), **assa todos os
     canais** do original (cor, metal, rugosidade por emissão; normal com geometria + normal map original),
     renderiza original x resultado com a mesma câmera e luz e mede um **ponto quente de sombreamento**
     (percentil 99,5 da diferença em blocos de 16 px, <= 0,12). Falhou um dos dois: sobe 25% e refaz, até o
     máximo da faixa. **Platô** (+25% de triângulos e menos de 5% de melhora no contorno): volta um degrau, a
     perda não é de contagem. **Travou** (o collapse não desce de 130% do alvo, típico de partes finas
     emaranhadas): refaz a partir de um remesh em voxel (`--remesh-res`, padrão 200 voxels no maior lado). Saída: `<Name>.fbx`, `<Name>_BaseColor.png`, `<Name>_Normal.png`,
     `<Name>_MetallicSmoothness.png` (R metal, A suavidade: layout da URP) + `<Name>_compare.png` e
     `<Name>_report.json`.
3. **Olhe o `_compare.png`** (linha de cima original, de baixo resultado). As métricas pegam contorno e rasgo,
   mas o olho confere cor e material. Viu defeito que as métricas não pegaram: `--tris` maior e anote o caso
   em `budgets.md`.
4. **Importe na engine** (checklist Unity abaixo) e **compare no jogo**, no mesmo ângulo e luz em que o
   jogador vai ver. Conte os triângulos na engine (`MeshFilter.sharedMesh.triangles.Length / 3`).
5. **Relatório**: original -> final (triângulos), degraus tentados, métricas, textura, captura no jogo.

## 3. Checklist Unity (URP)

- **Modelo**: `ModelImporter.materialImportMode = None` (o material é criado por código), `importNormals =
  Import` (mantém as bordas duras do "smooth by angle"), `importTangents = CalculateMikk` (bate com o bake do
  Blender), escala 1 (o FBX já sai em metros). O FBX do Blender chega com rotação na raiz (z-up para y-up):
  **componha** com `asset.transform.localRotation`, nunca sobrescreva.
- **Texturas**: `_Normal` com `textureType = NormalMap`; `_MetallicSmoothness` com `sRGBTexture = false`;
  `_BaseColor` sRGB. `maxTextureSize` = o tamanho gerado.
- **Material** URP Lit: `_BaseMap`, `_BumpMap` + `_NORMALMAP`, `_MetallicGlossMap` + `_METALLICSPECGLOSSMAP`,
  `_Smoothness` 1 (o mapa manda). Vidro/transparente: veja armadilhas.
- **Colisor**: caixa ajustada aos bounds, não MeshCollider da malha visual.
- **Sombras**: objeto pequeno de mão perto da câmera (lanterna na mão) sem cast shadow; cenário de fundo fora
  das passadas de sombra.

## 4. Armadilhas medidas (leia antes de improvisar)

- **Modelo saiu branco puro = textura base não achada** (2026-10-01, 9 props do Poly Haven: albedo 1,0, pareciam
  feitos de LED no jogo). O Poly Haven guarda as texturas em `textures/` (e o glTF em `gltf/`, uma pasta abaixo).
  O script agora assa a partir dos materiais do próprio original quando eles têm textura (vários materiais
  inclusive) e procura em `textures/`; mesmo assim, **confira `textures.base` e `sources_found` no relatório** e
  olhe a comparação colorida antes de importar.
- **IoU engana em peça fina** (lousa vista de lado: 0,95 mesmo idêntica). Use o desvio de contorno.
- **Decimar arrasta as UVs nas costuras**: reaproveitar a textura original na malha decimada deslocou manchas.
  Sempre assar; UV nova (smart) dá o resultado mais fiel.
- **Sombreamento suave em peça fina** (frente e verso dividindo a borda) entorta as normais e o normal map
  briga: cunhas escuras. Use "smooth by angle" 40 graus antes do bake (o script já faz).
- **Rasgo/dobra de triângulo** não muda o contorno: só o ponto quente de sombreamento pega (lousa: 0,27 com
  rasgo a 2 mil, 0,045 a 2,5 mil).
- **Meshy chuta metal** em pele e borracha: `--no-metal` ou zere o canal R.
- **Orientação do Meshy varia**: uns vêm em pé, outros deitados (lanterna, máscara). No Unity a malha mantém
  os eixos do Blender (Z para cima) e a raiz do FBX (rotação 270 em X) converte: Z da malha vira Y do mundo e
  Y da malha vira -Z. Confira pelos bounds da malha e ache a frente medindo (ex.: a ponta mais larga é a
  lente) antes de escolher a rotação. Nada de supor pelo render.
- **Compare no ângulo e na distância de uso de CADA parte**: no corpo em primeira pessoa as mãos passaram no LOD2,
  mas o peito, a um palmo da lente olhando para baixo, facetou.
- **Corpo em primeira pessoa**: câmera nos olhos da cabeça animada, corpo parado nos pés do jogador; esconda só a
  cabeça (sombra). Ancorar o corpo na câmera faz o pé deslizar; esconder ombros/peito abre buraco no tronco.
- **Não mude a aparência do asset por conta própria** (textura, roupa, cor): o dono pode ter planos para ele.
- **Objeto na mão atrás da própria luz** (lanterna) fica preto no escuro: luz de vazamento fraca a ~20 cm
  do corpo, sem sombra, ligada junto com o facho (a 5 cm a queda com o quadrado da distância estoura).
- **Vidro do Meshy** vem opaco na textura: para frasco/vidro de verdade, gere a peça de vidro à parte
  (malha simples) com material transparente, ou deixe o vidro opaco-sujo se a leitura funcionar.
- **GLB do Sketchfab**: peças sob nós girados desmontam no otimizador; rode antes `scripts/flatten_model.py <in.glb> <out.glb>` e confira a `_compare.png` de olho (as duas linhas saem igualmente erradas). Vidro translúcido vira opaco no bake: o ponto quente de sombreamento não cai com mais triângulos, use `--max-tris`. **GLB vem com os vértices separados em cada costura de UV**: num scan (atlas com centenas de ilhas) o collapse abria rachaduras escuras por toda a peça e travava; desde 10/11 o otimizador solda os vértices coincidentes ao importar GLB (`WELD a -> b` no log; `--no-weld` desliga). Scan com chão/tronco: recorte antes com `SourceAssets/Tools/scan_prep.py` do BeneathTheShroud (máscara por face + matriz de rotação/escala/pivô, refaz material unlit como Principled).
- **Poly Haven**: FBX às vezes com a malha na raiz em escala 100; LODs com transição padrão desenham LOD0
  longe. Para fundo, só o LOD mais leve e fora da sombra.
- **Criatura que dobra**: gerar em Quad no Meshy, peça única, depois remesh em quads + UV nova + bake +
  esqueleto (cadeia de ossos, pesos automáticos). Peças rígidas encaixadas mostram emenda de perto.
- **Folhagem com recorte em alfa** (folhas, grama, arbustos): não use o `optimize_model.py` (o bake perde o alfa). Use
  `scripts/foliage_reduce.py --src <pasta do Poly Haven> --name X --out <...> --tris 1000`: descarta folhas inteiras e
  colapsa o resto mantendo as UVs; põe o alfa no A da cor. Na Unity: Lit com alpha clip 0,5, duas faces e
  `mipMapsPreserveCoverage` na textura de cor (senão a planta "afina" de longe).
  **Árvore ou arbusto de copa cheia** (centenas de mil folhas): o `foliage_reduce.py` deixa a copa pelada. Use
  `scripts/leaf_cards.py <diff> <alpha> <out>/<Name>_cards_BaseColor.png` e depois `scripts/tree_cards.py --src <pasta>
  --name X --out <...> --tris 1500 --leaf leaves --height <m> --card-scale 0.9 --wood-area 0.9` (copa em cartões de cacho de
  folhas; ver Registro em `budgets.md`) e confira com `scripts/tree_compare.py --src <pasta> --result <Name>.fbx --name X
  --leaf leaves --height <m>` (gera `_compare.png` e `_report.json`; olhe a imagem: tronco presente, copa sem virar bolo).
- **Transparentes na URP**: desligar "Preserve Specular" (`_BlendModePreserveSpecular` 0) senão o reflexo
  fica com força total no vidro.

## 4b. Esqueleto de humanoide (criatura ou NPC em T-pose)

Ordem: **reduzir primeiro** (seção 2), depois pôr o esqueleto na malha leve. Para humanoide, os nomes do
Mixamo (`mixamorig:Hips`...) servem para tudo: as animações do Mixamo e o avatar Humanoid da Unity mapeiam sozinhos.

1. **Mixamo auto-rig** (site, Chrome logado): Upload Character (zip com FBX ou OBJ + textura de cor), marcar
   queixo, pulsos, cotovelos, joelhos e virilha. Em 2026-10-02 falhou 3 vezes com "Unknown error while generating
   motion" numa malha perfeita (peça única, fechada); não insista mais que duas vezes.
2. **No Blender, `scripts/rig_humanoid.py`** (o caminho que funcionou):
   ```
   blender -b --factory-startup --python <skill>/scripts/rig_humanoid.py -- --src <Name>.fbx --out <Rigged>/<Name>.fbx --previews <Rigged>
   ```
   Mede as articulações na própria malha (centroide da seção do braço, perna e tronco), força simetria pela linha
   do meio dos limites (cracas e fungos de um lado puxam o centroide), cria 22 ossos com nomes do Mixamo, calcula
   pesos automáticos numa **cópia voxelizada fechada** e transfere para a malha real (heat direto falha em malha
   com detalhe solto), limita a 4 influências. Proporções por argumento (`--chin`, `--elbow`...) quando o corpo
   foge do padrão; confira as `_pose_*.png`.
3. **Animação**: Mixamo > Animations, escolha e baixe "FBX Binary" (sem pele serve; pacotes como o "Scary Zombie Pack"
   vêm num zip e os nomes batem com o conteúdo).
4. **Unity, importação dos clipes (medido 2026-10-02; o primeiro jeito deixou pé flutuando e afundando e o dono
   viu antes de mim)**: tudo **Humanoid**, mas o **avatar dos clipes copiado de um personagem com pele**
   (`avatarSetup = CopyFromOther`, o X Bot do Mixamo baixado com pele): o arquivo "without skin" tem pose de repouso
   errada e o retarget sai torto. Raiz: `lockRootRotation` e `keepOriginalOrientation` (rotação assada),
   `lockRootHeightY` + `heightFromFeet` (altura pelos pés), XZ **livre** com `keepOriginalPositionXZ` (o root motion
   anda). Clipe deitado (rastejar, morder no chão) ainda afunda uns 8 cm: `heightOffset` **negativo sobe** (-0,07).
   Reimportar não pode apagar o Animator Controller (perde a referência da cena): reaproveite o asset.
5. **Validar em tempo real, nunca no Play+Update(0)**: toque cada clipe de verdade e capture quadros em momentos
   fixos medindo o ponto mais baixo da pele (BakeMesh) e osso abaixo do chão; `Animator.Play` + `Update(0)` dá pose
   diferente a cada chamada. Compare com o clipe original amostrado como Generic no X Bot. **Animator de teste em
   `AlwaysAnimate`** (com culling a câmera de captura pega pose velha). Não explique anomalia com "o pacote é assim"
   antes de provar com o original lado a lado: o defeito era a importação.
6. **IK de mão humanoide é de corpo inteiro**: puxar a mão para o chão torceu o tronco e jogou as pernas para cima
   no rastejar, mesmo com peso pequeno. Para garra/mão no chão, dobre o pulso no `LateUpdate` mirando a ponta real
   (vértices mais distantes da mão na bind pose).
7. **Avatar automático de MetaHuman**: a Unity pega os **metacarpos** (`index_metacarpal_r`) como falange proximal
   e deixa a ponta (`_03`) de fora; dobrar os dedos dobra a palma. Mapeie `_01/_02/_03` à mão no `humanDescription`.
8. **Ragdoll**: o construtor da Unity (6.5: classe comum em `UnityEditor.PhysicsModule`, por reflexão) não cria
   corpo para o pé; deitado, o dedo afundou 13 cm. Ajuste cada colisor à pele do próprio osso (raio pelo percentil 80
   só dos vértices do osso, senão o pé engorda a canela) e ponha uma caixa no osso do pé (sem Rigidbody, entra no
   corpo da canela). Meça a cobertura (vértice dentro de colisor via `ClosestPoint`) e o ponto mais baixo em repouso.

## 4c. Tentáculo e criatura radial (polvo): `scripts/rig_tentacles.py`

```
blender -b --factory-startup --python <skill>/scripts/rig_tentacles.py -- --src <Name>.fbx --out <Rigged>/<Name>.fbx   --previews <Rigged> --arms 1|N [--bones 12] [--core 0.2] [--path-tol 0.12] [--debug-csv <arq>]
```
- `--arms 1`: tentáculo solto; a cadeia começa na ponta grossa (medida pela seção nas duas pontas).
- `--arms N`: criatura radial. Grafo das **arestas da própria malha** (kNN pula de um braço para o manto encostado),
  ilhas soltas (ventosas) ligadas ao vizinho mais perto; distância geodésica a partir da boca; as N pontas por
  amostragem do ponto mais distante; vértice é do braço k se está **no caminho** boca -> ponta k
  (d_boca + d_ponta - d_boca(ponta) < tolerância), senão é manto. Separar por ângulo no plano falhou: o manto
  alongado no plano virou "braço" e juntou dois braços de verdade.
- Juntas = centroides das faixas de mesma distância geodésica (segue a ponta enrolada); peso entre os dois ossos
  cujo meio cerca a distância do vértice (sem bone heat, que falha com ventosa solta).
- **Conte os braços olhando o resultado, não o prompt**: o polvo pedido com 8 veio com 7; a 8a "ponta" achada era o
  topo da cabeça (comprimento metade dos outros). `--debug-csv` + um gráfico do plano mostra cada braço colorido.
- Na Unity: Generic sem avatar, sem Animator; animação procedural por osso (onda da base à ponta) e cápsula por osso
  ajustada à pele. Meça onde a criatura apoia: braço que desce do corpo até a ponta não fica no plano do manto.

## 5. Avaliar um asset de fora (Fab, MetaHuman, Sketchfab)

Antes de prometer: formato (a engine lê?), licença (uso comercial fora da engine de origem?), contagem de
triângulos e LODs, esqueleto (Humanoid?), texturas, e o que se perde na conversão. **MetaHuman** (`.mhpkg`):
é um pacote de Unreal Engine (`.uasset`), editável, sem malha pronta; precisa do Unreal (a versão do
manifesto) + MetaHuman Creator para montar e exportar FBX, e escolher um LOD perto do orçamento de
`character`. A licença (desde junho de 2025) permite usar em Unity/Godot; o rig facial (RigLogic) não roda
fora do Unreal. Detalhes e números em `budgets.md`.

**Exportar MetaHuman para FBX (UE 5.8, testado):** o Creator não tem botão de FBX. Com o editor aberto e a
execução remota do Python ligada **pelo usuário** (Project Settings > Plugins > Python > Enable Remote
Execution), use o cliente oficial `Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python/remote_execution.py`
e rode no editor: `MetaHumanCharacterEditorSubsystem.try_add_object_to_edit(ch)`, depois
`MetaHumanCharacterExportBlueprintLibrary.export_geometry(ch, MetaHumanGeometryExportParams(full_body_skeletal_mesh=True, ...))`
(cria malhas esqueletais no projeto) e `unreal.Exporter.run_asset_export_task` com `FbxExportOption`
(`level_of_detail=True`) para cada malha. `export_dcc` grava só DNA + texturas (sem FBX).

**MetaHuman vestido (UE 5.8, testado 2026-10-03):** presets, cabelo e roupa exigem o **MetaHuman Creator Core
Data** (Launcher > 5.8 > Opções; sem ele `Content/Optional` não existe e o log diz "Optional Content folder not
found"). `export_geometry` não leva roupa nem cabelo: duplique o preset (`/MetaHumanCharacter/Optional/Presets/<Nome>`),
`try_add_object_to_edit`, `request_auto_rigging` e `request_texture_sources` (nuvem da Epic, abre login no
navegador na 1a vez; ~25 s e ~8 s), espere `can_build_meta_human` virar True e monte com
`build_meta_human(ch, MetaHumanCharacterEditorBuildParameters(pipeline_type=OPTIMIZED, pipeline_quality=MEDIUM,
absolute_build_path=...))`. Sai a roupa como **malha esqueletal comum** (`Clothing/<Nome>_Outfits`, mesmos 341 ossos
do corpo) e o cabelo como cards estáticos com LODs; exporte cada um com `FbxExportOption(level_of_detail=True)`.
**Roupa do Fab no MetaHuman (testado 2026-10-03):** procure no Fab com o filtro MetaHuman e Free; baixe o
`.mhpkg` (Outfit Clothing) e importe com `AssetImportTask` (`automated=True`, sem diálogo). Vista com
`collection.try_add_item_from_wardrobe_item('Outfits', wi)` + `default_instance.set_single_slot_selection('Outfits', key)`
e monte Optimized. Roupa de pacote vem com **um LOD só** (Survivor: 25,8 mil). O LOD gerado pela Unreal
(`SkeletalMeshEditorSubsystem.regenerate_lod`, só 25%/12,5%; a porcentagem não é exposta ao Python) pôs pontos claros
e vincos; **Decimate do Blender a 50%** ficou igual ao original e 35% já arrastou a UV nas bordas dos bolsos.
Pele por baixo da roupa atravessa nas dobras: corte do corpo as faces cobertas (vértice atrás da roupa pela normal
mais próxima, a menos de 6 cm; nunca mãos, pescoço e cabeça). Cabelo: a malha "Helmet" do groom cobre o rosto como
um capuz; use os **cards** (`*_CardsMesh_Group0_LODn`, UV `UVmap_0`, apague `LightMapUV`) com a textura
`*_CardsAtlas_Attribute` (R = cobertura vira o alfa, B = variação por mecha; a cor vem do personagem), presos 100%
no osso `head`. Normais da Unreal são DirectX: inverta o verde para a Unity. ORM: R oclusão, G rugosidade, B metal.

## 6. Feche aprendendo

Todo uso que ensinar algo novo (defeito que as métricas não pegaram, faixa que precisou subir, formato novo)
vira uma linha no **Registro** de `budgets.md` com data, objeto e número.
