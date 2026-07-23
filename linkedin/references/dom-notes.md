# Mapa do DOM e armadilhas provadas

Tudo aqui foi pago com sessão de debug. Antes de "consertar" um seletor, leia a
armadilha correspondente — várias falhas são silenciosas e destrutivas.

## Estrutura

- As classes são ofuscadas e trocam a cada deploy (`d37602e6 b8a6c64d ...`).
  **Nunca selecione por classe.** Use `role`, `aria-label` ou texto.
- As listas de `/details/<seção>/` **não usam mais `<ul>/<li>`** — são `div` anônimas.
  O único handle estável por item, no próprio perfil, é o **lápis de edição**:
  `main [aria-label]` com label começando em `Editar`. É assim que `entries()` conta.
- `aria-label` de lápis **não é único**: toda linha de idioma é literalmente
  `"Editar idioma"`. Chaveie por label + trecho do texto.
- `"Editar idioma do perfil"` aparece na página de experiência e **não é uma entrada** —
  filtre.
- O LinkedIn renderiza cada rótulo duas vezes (visível + leitor de tela). `dedupeLines()`
  descarta a linha igual à anterior: metade dos tokens, zero perda.

## Scroll e virtualização

- Em várias páginas de detalhes **a janela não rola**: `<main>` é o container de scroll
  (`document.scrollHeight` fica do tamanho da viewport). `window.scrollBy` é no-op
  silencioso e você lê uma lista truncada — foi assim que Competências contava 10 em vez
  de 67.
- A lista é virtualizada: itens fora da tela **saem do DOM**. Contar no fim erra tanto
  quanto não rolar. Colha a cada passo e acumule.

## Formulários

- **Campos de texto longo não são `textarea`** — são `div[role="textbox"][contenteditable]`
  (Sobre, headline, descrição de experiência). Localize por
  `dialog[open] [role="textbox"]`. Em **Projetos**, a Descrição é `textarea` de verdade.
- **`Ctrl+A` + Delete para limpar é instável**: falha em silêncio e o texto novo é
  **concatenado** no antigo → estoura o limite e o save se perde. Use `locator.fill('')`,
  **assere que o campo ficou vazio** e aborte se não ficou. Depois `keyboard.insertText()`
  (preserva quebras de linha; `fill()` não).
- **Nunca navegue direto para `/details/experience/edit/forms/<id>`**: o form renderiza
  **vazio** (cargo, empresa, datas em branco) e salvar assim **apaga a vaga**. Sempre
  abra clicando no lápis e espere hidratar de verdade — o critério é um `<select>` de
  data já com ano `20xx`.
- **Typeahead que exige seleção** (idioma, competência): digitar não basta, dá
  "Selecione entre as sugestões". `pressSequentially` + clicar no `role="option"`.
  As sugestões vêm **no idioma da UI**: "Inglês", não "English".
- **Typeahead que aceita texto livre** (cargo, Diploma, Área): `click()`/`fill()` falham
  porque o listbox intercepta o ponteiro. `focus()` → Ctrl+A → Delete → `keyboard.type()`
  → **Escape** para fechar o dropdown.
- No form de experiência, **localize o campo de cargo pelo valor atual, não por posição**:
  o mesmo form contém o campo da headline do perfil, e mexer no errado troca a headline.
- Formulário de **Projetos não tem `aria-label`** — os campos são ligados por `<label>`:
  `getByLabel('Nome do projeto*')`.
- Selects nativos: `selectOption(value)`. Proficiência de idioma:
  `LanguageProficiency_ELEMENTARY|LIMITED_WORKING|PROFESSIONAL_WORKING|FULL_PROFESSIONAL|NATIVE_OR_BILINGUAL`.

## Fluxos de duas etapas

- **Em destaque / mídia de projeto**: `…`/`+` → menuitem "Adicionar link" → colar URL →
  **"Adicionar"** → o LinkedIn busca o preview de forma assíncrona (~9-12s) e só então
  preenche o **"Título*" obrigatório** e habilita o Salvar. Espere o botão deixar de
  estar `disabled` — timeout fixo falha em silêncio. O fetcher é **instável**: às vezes
  diz "Insira um link válido" sem motivo; **repetir resolve**, e subdomínio funciona
  melhor com barra final (`https://x.bobagi.space/`).
- **Adicionar competência**: link `<a>` "Adicionar seção" no perfil — clique via
  `evaluate(el.click())`, porque um banner "Experimente o Premium" intercepta o ponteiro
  → no modal, "Principal/Recomendado/Adicionais" são **acordeões `div[role=button]`
  fechados** → "Principal" → "Adicionar competências".
  (Competências ficam em Principal; Em destaque/Projetos/Certificações em Recomendado.)
- **Confirmação de save de competência**: a página `/details/skills/` é virtualizada, o
  readback dá falso-negativo. O sinal confiável é o toast do próprio LinkedIn —
  **"Esta competência já está no seu perfil"** = já existe. Espere ≥2,5s pelo toast.

## Dados de contato

Perfil → link "Dados de contato" → lápis dentro do overlay. Campo é `input` com
aria-label "URL do site". A URL `/edit/contact-info/` **não existe** (404).

## Idioma da UI

Todos os `aria-label` mudam se o perfil for para inglês. Os regex em `lib.mjs` (`RX`)
já casam PT e EN — mantenha assim ao adicionar seletores novos.
