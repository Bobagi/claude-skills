---
name: game-visual-review
description: Revisa o visual de um jogo (menu, cena, cabine, HUD, modelo, iluminação) do jeito que um jogador e um diretor de arte veriam, antes de dizer que ficou pronto. Captura a tela real (Unity via MCP, build web via Chrome, ou PNGs já tirados), monta uma folha de contato lado a lado com a referência, mede o que dá para medir (contraste, saturação, variedade de cor, área plana sem detalhe, legibilidade do texto) e pontua contra uma rubric versionada; nota 2 ou menos em qualquer item bloqueia o "ficou pronto". Use SEMPRE que mexer em algo visível de jogo (menu, cena, props, luz, UI, shader) e quando o usuário disser "ficou muito ruim", "parece placeholder", "siga essa referência", "compare com a imagem".
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, WebSearch, WebFetch
---

# game-visual-review: o jogo visto por quem vai votar

Por que existe: em 23/10/2026 o menu do Happy Harvest foi entregue como "pronto" com um céu laranja
chapado, um painel marrom e uma torre minúscula no horizonte. O dono abriu, achou "MUITO ruim" e
mandou uma referência do GPT. Nada no fluxo obrigava a IA a olhar a própria tela com olhos de jogador
antes de fechar a tarefa. Esta skill é esse olhar, com régua.

A inteligência mora em **`rubric.md`** (a checklist que cresce a cada uso). Leia-a inteira antes de
julgar e acrescente o que aprendeu no fim.

## Quando rodar (obrigatório, não opcional)
- Mexeu em qualquer coisa visível: cena, menu, HUD, prop, material, luz, shader, pós-processo, fonte.
- Vai dizer "ficou pronto", "ficou bom", "melhorei o visual". Primeiro a nota, depois a frase.
- O usuário mandou uma imagem de referência ("faça parecido com isso").
- Um hook `PostToolUse` (`scripts/game-visual-reminder.sh`) lembra disso ao gravar arquivo visual de
  jogo. O lembrete não substitui a revisão: a revisão é tirar a captura e pontuar.

## Passo 1: capturar a tela REAL (nunca julgar pelo código)
- **Unity (MCP for Unity rodando)**: entrar em Play e `ScreenCapture.CaptureScreenshot("Assets/Screenshots/<nome>.png")`
  via `execute_code`, uma captura por estado (menu, jogo, telas secundárias, estados de destaque,
  zoom/lean). O Game view precisa estar em 1920x1080 ou 16:9 "Full HD"; confira a resolução no retorno.
  Capturas de câmera (`manage_camera screenshot`) NÃO mostram a UI em overlay: use ScreenCapture.
- **Build web**: abrir no Chrome (claude-in-chrome ou chrome-devtools), janela 1920x1080, screenshot.
- **Godot/Unreal/outro**: usar a tecla de screenshot da engine ou a ferramenta de janela do sistema.
- Sempre capturar **o mesmo conjunto de estados** antes e depois de uma mudança, com o mesmo nome de
  arquivo, para comparar.

## Passo 2: folha de contato e métricas
```bash
python -I "$SKILL_DIR/scripts/contact_sheet.py" --out <dir>/review.png \
  --shot <captura.png> [--ref <referencia.png>] [--before <captura_anterior.png>] [--label "menu"]
```
O script escreve `review.png` (captura, referência e versão anterior lado a lado, mesma altura) e
imprime métricas por imagem: luminância média e desvio, saturação média, contraste (p5 a p95),
**variedade de matiz** (quantos matizes distintos pesam mais que 1%), **área plana** (fração da
imagem em blocos 32x32 com desvio quase zero: chapado, placeholder), densidade de bordas (detalhe) e,
se `--ref` foi dado, a distância de histograma de cor e a diferença de luminância média. Os números
não dão nota sozinhos; são evidência para a rubric. Área plana acima de 0,45 ou variedade de matiz
abaixo de 4 quase sempre é "placeholder".

## Passo 3: pontuar contra a rubric
Abra `review.png` com a ferramenta Read e pontue cada item da `rubric.md` de 1 a 5 com uma frase de
evidência ("o céu ocupa 55% da tela com uma cor só", "o texto do botão tem contraste 2,1:1 sobre o
amarelo"). Regras:
- Item com nota **2 ou menos bloqueia** a entrega. Corrija e capture de novo. Não existe "limite
  conhecido" para item visual que o usuário pediu.
- Se houver referência, o item "fidelidade à referência" pontua posição e proporção dos elementos,
  paleta, horário do dia, direção da luz e clima. Estilo (realista versus low-poly) NÃO é cobrado,
  salvo pedido explícito.
- Compare antes e depois: regressão em qualquer item é bloqueio.

## Passo 4: relatório curto e correções
Relate em até 10 linhas: nota por item, os 3 piores com a causa provável no código e o que foi
corrigido. Repita o ciclo até nenhum item ficar em 2 ou menos. Só então diga que ficou pronto, com
o `review.png` final nomeado.

## Passo 5: fazer a rubric crescer
Se o usuário apontou algo que a rubric não pegou, acrescente o item (com a data e o caso) em
`rubric.md`. Se uma métrica do script teria pego, ajuste o limiar e anote.

## Ferramentas externas úteis (pesquisadas em 23/10/2026)
- Não há skill ou MCP pronto que critique qualidade visual de jogo; o que existe são servidores MCP
  de captura (MCP for Unity `manage_camera`, `screen-capture-mcp` para janela no Windows) que apenas
  entregam a imagem. A crítica continua sendo esta rubric aplicada por quem olha a imagem.
