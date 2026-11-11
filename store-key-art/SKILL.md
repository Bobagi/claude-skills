---
name: store-key-art
description: Cria, refaz ou ajusta arte de loja e divulgacao de jogo (capsulas da Steam, header, small, main, vertical, library, hero, capa de itch.io/Play, banner, thumbnail, key art, poster) com pesquisa e comparacao obrigatorias com capas de sucesso do genero, usando o mundo e os modelos REAIS do jogo, e audita o resultado (scripts/audit_capsules.py) antes de mostrar. Use SEMPRE que o pedido envolver arte de loja/capa/banner/capsula/key art, quando o dono pedir "muda a arte", "ficou ruim", "nao chama atencao", "pesquise antes", e antes de subir qualquer imagem para Steam/itch/Play.
allowed-tools: Bash, Read, Edit, Write, Grep, Glob, WebSearch, WebFetch
---

# store-key-art: capa que o jogador clica, sem o dono precisar brigar 4 vezes

Por que existe (11/11/2026, Beneath the Shroud): a capa da Steam precisou de **4 versoes** e o dono se frustrou em
todas. v1 tinha rosto gerado por IA que nem era o personagem; v2 mostrava o modelo 3D cru e um tentaculo cobrindo as
letras; v3 trocou o layout que ele tinha gostado e deixou o ceu liso e as janelas apagadas; so a v4 passou. Cada erro
virou uma regra abaixo. Historico com imagens em `examples/beneath-the-shroud/historico_v1_a_v4.jpg` e `log.md`.

## Regras duras (cada uma custou uma rodada)
1. **Pesquisar ANTES de gerar.** `WebSearch` sobre o que faz capa converter no genero + baixar 20 a 40 capas de
   sucesso (CDN publica: `https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/<appid>/header.jpg`) e
   montar a grade. Nunca mostrar arte sem a grade comparativa junto.
2. **Mundo e personagem REAIS do jogo.** Nada de rosto/personagem gerado por IA (nota 1 automatica). A base vem da
   engine: renderizar os modelos do jogo (Unity via MCP: `scripts/unity_mcp_client.py`).
3. **Nunca mostrar o modelo 3D cru.** Render direto da cena entrega textura pobre. Renderizar em PASSES (ceu, casa,
   mascara colorida por criatura, vidros, completo) e compor em 2D: silhueta contra ceu iluminado, contorno de luz,
   nevoa por profundidade (exemplo completo em `examples/beneath-the-shroud/`).
4. **Ceu e luz sao metade da atmosfera.** Ceu liso = recusado. Usar foto CC0 de tempestade/nuvens (ex.:
   goodfreephotos.com, dominio publico) recolorida para a paleta do jogo + relampago; brilho forte atras das
   silhuetas (sem ele criatura escura some no ceu escuro).
5. **Luz que chama atencao.** Janelas/lamparinas com nucleo quente, caixilho, halo grande e luz vazando na nevoa; uma
   cor quente contra a paleta fria. Luz fraca "nao chama atencao nenhuma".
6. **Letreiro sempre por cima.** Nada atravessa as letras (nem a criatura, nem efeito). Logo grande (header >= ~55% da
   largura), em area de contraste: no teste em cinza borrado o nome tem que ler (escurecer o fundo atras se preciso).
7. **Mudar SO o que o dono apontou.** Se ele disse "o layout estava bom", o layout fica. Anotar o que ele aprovou
   (`log.md` do projeto) antes de cada rodada e conferir que continua igual.
8. **Small capsule**: logo quase enchendo a imagem; "linha fina" do logo (ex.: BENEATH THE) ampliada so nessa versao.
9. **Regras da Steam**: so arte + nome do jogo (nada de "demo", "wishlist", nota, premio); hero sem texto; tamanhos
   exatos (o script confere). A janela "Graphical Asset Rules" e uma declaracao do dono: ele marca, nao o agente.
10. **Abrir as imagens na tela dele** (Start-Process do jpg) e dizer onde estao; nada de so caminho no texto.

## Fluxo
1. Ler `log.md` do projeto (o que ja foi aprovado/recusado) e as regras acima.
2. Pesquisa + grade de referencias (regra 1). Escrever em 3 linhas o padrao do genero que vai seguir.
3. Passes da engine -> composicao 2D -> capsulas (exemplo: `render_passes.py` + `render_passes.cs.template`,
   `compose_keyart_v4.py`, `capsules_v4.py`).
4. **Auditoria obrigatoria**: `python -I scripts/audit_capsules.py <pasta> --genre horror --prev <versao anterior>`.
   Com BLOQUEIO, corrigir antes de mostrar. Ler `vitrine.jpg`, `vitrine_cinza.jpg`, `tamanhos.jpg` com Read.
5. Responder por escrito o **checklist** (cada item com evidencia da imagem):
   - [ ] o nome le em 120x45 e na vitrine em cinza borrado?
   - [ ] a ameaca/gancho do jogo le em 1 segundo (silhueta)?
   - [ ] algo atravessa o letreiro? (tem que ser NAO)
   - [ ] aparece modelo 3D cru, textura pobre, rosto de IA? (NAO)
   - [ ] o ceu tem tempestade/textura/relampago ou e liso? (liso = refazer)
   - [ ] a luz quente chama atencao a 292x136?
   - [ ] o layout aprovado antes continua igual? so mudou o que foi pedido?
   - [ ] ao lado das 20+ capas de sucesso, a nossa se destaca ou some?
6. Mostrar ao dono: abrir folha de tamanhos + vitrine na tela, resumo curto do que mudou e por que (com fontes).
7. Depois da aprovacao: subir (Steam: drop zone so aceita arrastar; ver `log.md` "upload"), e registrar a versao
   aprovada no `log.md` do projeto e um caso novo aqui.

## Arquivos
- `scripts/audit_capsules.py`: tamanhos, metricas relativas as referencias do genero, separacao do logo na small,
  vitrine colorida/cinza, report.md com BLOQUEIOS/AVISOS (sai com codigo 1 se bloquear).
- `scripts/unity_mcp_client.py`: cliente HTTP do MCP for Unity (`tools`, `code <arquivo.cs>`, `tool <nome> <json>`).
- `examples/beneath-the-shroud/`: pipeline completo da v4 aprovada (passes, composicao, capsulas) e o historico.
- `log.md`: casos, o que foi recusado e por que, e o que passou.
