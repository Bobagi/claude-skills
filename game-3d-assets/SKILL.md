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
- **Objeto na mão atrás da própria luz** (lanterna) fica preto no escuro: luz de vazamento fraca a ~20 cm
  do corpo, sem sombra, ligada junto com o facho (a 5 cm a queda com o quadrado da distância estoura).
- **Vidro do Meshy** vem opaco na textura: para frasco/vidro de verdade, gere a peça de vidro à parte
  (malha simples) com material transparente, ou deixe o vidro opaco-sujo se a leitura funcionar.
- **Poly Haven**: FBX às vezes com a malha na raiz em escala 100; LODs com transição padrão desenham LOD0
  longe. Para fundo, só o LOD mais leve e fora da sombra.
- **Criatura que dobra**: gerar em Quad no Meshy, peça única, depois remesh em quads + UV nova + bake +
  esqueleto (cadeia de ossos, pesos automáticos). Peças rígidas encaixadas mostram emenda de perto.
- **Transparentes na URP**: desligar "Preserve Specular" (`_BlendModePreserveSpecular` 0) senão o reflexo
  fica com força total no vidro.

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

## 6. Feche aprendendo

Todo uso que ensinar algo novo (defeito que as métricas não pegaram, faixa que precisou subir, formato novo)
vira uma linha no **Registro** de `budgets.md` com data, objeto e número.
