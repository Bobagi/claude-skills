# frontend-review - rubric (the growing checklist)

This file IS the skill's expertise. It is **project-agnostic**: never put a specific
project's facts here. Each run applies it; the self-improvement step appends *general*
lessons to the **Learnings log** at the bottom so the reviewer gets sharper over time.

## Severity scale (tag every finding)
- **P0 Blocker** - broken/unusable: content cut off, horizontal scroll on mobile, overlap, illegible.
- **P1 High** - clearly wrong, most users notice: misaligned blocks, inconsistent padding on a key surface, target too small to tap.
- **P2 Medium** - off but tolerable: slightly uneven spacing, weak hierarchy, minor responsive awkwardness.
- **P3 Low / Nit** - polish: 1-2px nudges, optional contrast bump, wording.

Every finding must carry: **what** (the problem), **where** (route + viewport + screenshot file, and/or `file:line`), **why it reads wrong**, **fix** (concrete, in tokens not pixels when the project has a scale).

---

## Pillar 1 - Visual (judged from the screenshots)

### Spacing & padding
- [ ] Padding inside cards/buttons/inputs is **consistent** across like components (same component → same insets).
- [ ] Outer gaps between sections follow one rhythm (multiples of the spacing unit), not arbitrary values.
- [ ] No element is **glued** to a container edge (text/controls touching the border) or to the viewport edge.
- [ ] Symmetric padding where symmetry is implied (left≈right, top≈bottom) unless intentionally directional.
- [ ] Whitespace is **balanced** - not one cramped region next to one empty region.
- [ ] Gap between a label and its field, and between stacked fields, is uniform.
- [ ] **Vertical rhythm between stacked blocks is even** - header→first child, child→child, and
  button→list should read as one consistent step, not alternating big/tiny. The usual culprit is
  **margin stacking/collapse between a component and its neighbor**, not a single wrong value: a child
  that carries its own `margin-top` placed right after a header with `margin-bottom` yields an oversized
  (collapsed-to-the-larger) gap; an element with `margin:0` (e.g. a reset `<p>`) right after another reads
  as *glued* (zero gap). Own the gap in ONE place and match one rhythm - don't let two margins fight.

### Alignment & rhythm
- [ ] Shared left edge: labels, inputs, headings, and body in a column line up to one grid.
- [ ] Related items align to each other; numbers/currency right-align in tables.
- [ ] Icon + text pairs are vertically centered on the same baseline/optical center.
- [ ] Equal-height cards in a row; buttons in a row share height and baseline.

### Responsiveness (compare across viewports)
- [ ] **No horizontal scroll** at any width (the `H-OVERFLOW` / `offcanvas` signals are P0/P1).
- [ ] **Flex/inline rows wrap or reflow on mobile** - a `display:flex` row of chips/badges/labels with no
  `flex-wrap` and fixed/intrinsic-width children **overflows its container instead of growing vertically**
  (the classic "row shoots past its card" on phones). Each such row must `flex-wrap:wrap` (grow down a
  line) or restructure; a `flex:1` spacer that pushes items apart on desktop should be hidden on mobile so
  wrapped items don't leave a dead gap.
- [ ] **A reflowed row is distributed, not just un-broken.** Stopping the overflow is the floor, not the
  goal: when a row wraps onto 2 lines on mobile, judge the *distribution* - left-bunched items with dead
  space on the right read as unfinished. Prefer a deliberate layout (e.g. a 3-zone `grid` start/center/end:
  badge left, title centered, meta right; secondary line left/right) so it stays balanced and attractive.
- [ ] Multi-column layouts collapse cleanly to one column on mobile (no squished columns).
- [ ] Tables: scroll inside their own container or reflow - never push the page wide.
- [ ] Touch targets ≥ 24px (ideally 44px) on mobile; controls don't crowd.
- [ ] Nothing overlaps after reflow; sticky headers don't cover content.
- [ ] Type and spacing scale down sensibly - desktop spacing shouldn't look huge on mobile, or mobile spacing cramped on desktop.
- [ ] Images/media keep aspect ratio; no stretch/squash; avatars stay circular.

### Typography
- [ ] Clear hierarchy (size/weight/color distinguish H1 > H2 > body > caption).
- [ ] Line length ≈ 45-90 chars on desktop; line-height comfortable (~1.4-1.6 body).
- [ ] No clipped/truncated text without an ellipsis; no orphaned single words where it matters.
- [ ] Consistent font family/weights; numerals align in tabular contexts.

### Color, contrast & theme
- [ ] Body text vs background ≥ 4.5:1; large text/UI ≥ 3:1 (judge the dim/muted text especially).
- [ ] Brand palette applied consistently; no stray off-palette colors.
- [ ] Disabled/placeholder states are distinguishable but still legible.
- [ ] Focus states visible (not removed); hover/active states present on interactive elements.
- [ ] **Text and controls over a DECORATIVE ANIMATED background stay readable.** A background element
  that spins/pulses/drifts (rotating rings, glow discs, particle systems, hero card art) behind the
  title, body copy or the CTAs creates motion noise that fights the reading. Contain the decoration
  (smaller than the content area, soft glow, real breathing space between it and the text) and/or give
  the overlaid controls a semi-opaque fill + `backdrop-filter: blur()` (never leave a near-transparent
  "ghost" button sitting over moving art). Judge it with the background IN MOTION, not from a frozen
  frame; verify by watching the animation and reading the copy over it.

- [ ] **Antes de tratar um pixel-diff como regressão, meça o piso de ruído**: capture o mesmo build
  duas vezes e diffe. Animação (emoji, badge flutuante, marquee, carrossel) produz diferença
  não-zero por si só; só o que passa desse piso é mudança real.

### Imagery, icons, motion
- [ ] Icons share a family/stroke weight and optical size; consistent corner radii across cards/buttons/inputs.
- [ ] Shadows/borders consistent (one elevation system).
- [ ] No layout shift or jank on load; loading states present for async areas.

### Product effectiveness (for landing / marketing / entry screens)
- [ ] **Does a stranger see the PRODUCT, or a form?** On an entry screen, the heaviest object should be
  what the product IS (the art, the board, a demo), not a credentials field.
- [ ] **CTA hierarchy matches WHO ARRIVES.** A first-time visitor has no account: "Log in" as the loud
  primary with "Create account" as a faint ghost is inverted. Primary = the action a newcomer can take.
- [ ] **Is there a reason to believe below the fold?** Hero straight into footer = nothing sells the
  product. Look for: how it works, real proof/content, a closing call.

### States (look for all, not just the happy path)
- [ ] Empty state (no data) is designed, not a blank gap.
- [ ] Loading state (skeleton/spinner) exists for async content.
- [ ] Error state is styled and actionable (matches the app's error pattern, not a raw browser alert).
- [ ] Success/confirmation feedback for actions.

### Information design (redundancy & space)
- [ ] **When a surface repeats N items of the same type** (clocks, status pills, "balance" cards, metric
  tiles, list rows), check the **semantic relationship** between them, not just that they render. Two items
  that **always carry the same information** are redundant → **merge them into one** (and reclaim the space).
  Do NOT clear this by observing that "right now they show different values" - values can coincide or diverge
  by chance; ask whether they are the *same underlying thing by design*. (Real case: two day/night clocks,
  "Cetus" and "Earth", that the game syncs 1:1 - obvious once merged, invisible while a data bug made them
  show different states.) Conversely, don't merge items that only *happen* to match now but are distinct
  concepts (e.g. a "Fass/Vome" clock that shares a duration but not the same cycle).
- [ ] **A surface with few items shouldn't bunch to one side** - distribute across the width
  (`justify-content: space-between/around`) or center, so freed space is used, not left as a dead gap.

---

## Pillar 2 - Front-end code

- [ ] Spacing/sizing use **design tokens / CSS variables**, not scattered magic px (flag repeated literals that should be a token).
- [ ] Responsive units where appropriate (rem/%, `clamp()`, `min/max`); avoid fixed px widths that cause overflow.
- [ ] Breakpoints are consistent (a shared set), not ad-hoc per component.
- [ ] **Verify responsiveness in the code, not only screenshots.** Grep every `display:flex` / `display:grid`
  row that holds multiple inline items and confirm it can reflow (`flex-wrap`, `min-width:0`, or a mobile
  media query) - a no-wrap flex row with intrinsic/fixed-width children **will** overflow on narrow screens
  even when today's data happens to fit. Flag fixed `width`/`min-width` px on content that must fit a phone.
- [ ] **A horizontal scroller inflates its ancestors unless they are capped.** `overflow-x:auto` on a
  rail does NOT stop its min-content propagating up through an `overflow:visible` parent - the
  grandparent's implicit `auto` grid track grows to the rail's full content width and the WHOLE page
  goes wider than the viewport. Give stacking containers `grid-template-columns: minmax(0, 1fr)` and
  the scroller's wrapper `min-width: 0`. Prefer `justify-content: safe center` over `center` on any
  row that can overflow (plain `center` puts the first item where scrolling cannot reach it).
- [ ] **No undefined CSS custom properties.** Grep every `var(--x)` reference and diff against the
  tokens defined in `:root`. An undefined token **with no fallback** renders the wrong value silently
  (e.g. `var(--text-muted)` when the token is `--muted` → text shows full-bright, not muted - a real
  bug screenshots barely reveal); one **with a fallback** still bypasses the design system (off-palette).
  Exception: runtime-set vars (e.g. a `--topbar-h` set via JS with a sensible fallback) are legitimate.
- [ ] **Variant styles on a self-nestable component use a scoped/direct-child combinator, not a bare
  descendant.** A reusable component with variants (e.g. `<Collapsible variant="section|help">`) that can
  contain **another instance of itself** will leak: a rule like `.section .cl-title{font-size:lg}` matches
  the title of a nested *help* instance too (same component scope, descendant combinator), silently
  mis-sizing it - so "the same element" looks different in one place than another. Same trap whenever two
  variants share a child class name. Grep every descendant-combinator selector (`.a .b`) whose right-hand
  class also appears on a nested child; prefer `.a > summary > .b` / `:scope >` / a variant-specific class
  so the rule can't cascade into a nested instance. This is a top cause of "this element isn't configured
  like its twin" inconsistencies - verify suspect twins by rendering them adjacent (a faithful mock if auth-gated).
- [ ] No duplicated style blocks that should be a shared class/component; component reuse over copy-paste.
- [ ] **A reusable component meant to look identical everywhere actually renders identically.** Give it
  ONE clean dimension anchor (explicit width OR height) and derive the rest from `aspect-ratio`; a
  `container-type:size` / `contain:size` element cannot size from its content, so `aspect-ratio` alone in
  the wrapper leaves it ambiguous and slightly stretched between call sites. Never `scale()` one instance
  vs its siblings (use lift/z-index/shadow for emphasis). Verify with `offsetWidth/offsetHeight` (NOT
  `getBoundingClientRect`, which includes `rotate()` and lies) plus a pixel-diff of the same item in two contexts.
- [ ] No dead CSS / unused classes; no `!important` wars.
- [ ] Layout uses fl/grid intentionally; avoid absolute positioning for flow content.
- [ ] Conditional rendering covers loading/empty/error, not just data-present.
- [ ] Strings are in the i18n layer, not hardcoded (when the project is localized) - check **every** language dict has the key.
- [ ] Images have width/height or aspect-ratio to avoid CLS; lazy-load below the fold.

## Pillar 3 - UX / a11y / consistency

- [ ] Semantic HTML (`button` for actions, `a` for navigation, headings in order, `nav/main/header`).
- [ ] Every control has an accessible name (the `unnamed`/`unlabeledInputs` signals); inputs have associated labels.
- [ ] Keyboard: everything reachable and operable; visible focus ring; logical tab order; Esc closes modals; focus trapped in modals.
- [ ] Images informative→`alt`, decorative→empty alt/`aria-hidden` (the `alt` signal).
- [ ] **Don't put `tabindex="0"` on a non-interactive element** (a scroll container, a plain `<div>`
  text region). It fails the lint (`a11y-no-noninteractive-tabindex`) and adds a confusing tab stop -
  the content is already in the accessibility tree for screen readers, and the real controls
  (buttons/inputs) remain focusable. For a long scrollable text region (e.g. a Terms block in a
  fixed-height scroller) use `role="region"` + `aria-label` to name it as a landmark, **without** tabindex.
- [ ] Color is not the only signal (icons/text accompany color for status).
- [ ] Forms: labels, helpful errors tied to fields, no destructive action without confirm/undo.
- [ ] Consistency: the same concept looks/behaves the same everywhere (sub-tab placement, button styles, card widths, table patterns).
- [ ] Internationalization renders correctly per locale (flags/text), no untranslated fallbacks leaking.
- [ ] Reduced-motion respected; no essential info conveyed only by animation.

## Reading the automated signals (`manifest.json`)
Each shot carries `signals`: `overflowX` (document wider than viewport - the **real** page-overflow
flag) and `offCanvas` (elements past the right edge, now filtered to exclude children of an
`overflow-x:auto/scroll` ancestor so wide tables/carousels don't false-positive) → responsiveness;
`missingAlt`, `unnamedControls`, `unlabeledInputs` → a11y; `tinyTargets` → mobile tap size;
`consoleErrors` → runtime/code issue. **`overflowX:false` with a high `offCanvas` count = an
in-container horizontal scroller** (e.g. a wide data table that side-scrolls inside its card): not a
layout break, but flag as a *mobile UX* issue if it hides key info/actions. Treat all signals as
**leads to verify on the screenshot**, not auto-verdicts.

Capture tips baked into `scripts/capture.mjs`: pass `--fold true` (default) for an above-the-fold
viewport shot (`*__fold.png`) - full-page mobile shots downscale too far to judge tight padding; pass
`--scale 2` for a crisp 2× shot when eyeballing spacing. For tabs/modals/empty states that need a
click, drive them separately for now (interaction steps are a planned engine feature - see log).

---

## Learnings log (append-only; this is how the reviewer improves)
- **2026-08-11 (via um site institucional) - dois componentes que renderizam "o mesmo rodapé/cabeçalho"
  divergem nos EFEITOS COLATERAIS, não no visual.** Um layout compartilhado copiado em dois componentes
  (uma home stand-alone + um `PageShell` para as sub-páginas) tende a ficar pixel-idêntico, porque a
  divergência visual salta aos olhos na primeira olhada. O que apodrece em silêncio é o que cada cópia
  escreve FORA da própria árvore: `document.documentElement.lang`, `data-theme`, `<title>`, meta tags,
  chaves de `localStorage`, listeners de scroll. Caso real: a home escrevia `lang="pt"` e as sub-páginas
  `lang="pt-BR"` - o mesmo site anunciando dois idiomas conforme a rota, invisível em qualquer screenshot.
  Regra de review: ao revisar QUALQUER bloco duplicado entre componentes, não pare no diff do template e
  do CSS - dê grep nos side effects (`documentElement`, `setAttribute`, `localStorage`, `document.title`)
  de cada cópia e compare os VALORES, e depois meça o atributo no DOM ao vivo em cada rota, não só numa.
  Corolário: um atributo de idioma tem que concordar com a formatação que a página realmente exibe
  (se a data sai `dd/mm/aaaa`, o tag não pode ser um `pt` genérico).

- **2026-08-11 (via um portfolio) - um pixel-diff sem RODADA DE CONTROLE não prova regressão, e
  um token de acento tem DOIS papéis.** Duas lições de uma revisão de tema. (1) Ao validar que um
  refactor de CSS não mexeu no tema que não era o alvo, o diff antes/depois acusou 0.78% de pixels
  diferentes - parecia regressão. Capturar o MESMO build duas vezes deu 0.79% nas mesmas faixas:
  era animação (emoji, badges flutuantes, marquee). **Regra: antes de chamar um diff visual de
  regressão, tire duas capturas do mesmo build e subtraia esse piso.** Qualquer página com
  `@keyframes`, vídeo, carrossel ou emoji animado tem um ruído de base não-zero; sem medir esse
  piso você persegue bug inexistente ou, pior, aceita uma regressão real que ficou abaixo dele.
  (2) **Um token de cor de acento quase sempre tem dois papéis: PREENCHIMENTO e TINTA**, e eles têm
  requisitos opostos. Um amarelo/verde-limão/ciano vibrante funciona como fundo (com texto escuro
  em cima) sobre QUALQUER tema, mas como texto/borda/anel de foco só funciona sobre fundo escuro -
  amarelo #ffd21a sobre branco dá 1.45:1. Enquanto o produto tem um tema só, o mesmo token serve
  aos dois usos e ninguém percebe; no dia em que entra um tema claro (ou um modo de acessibilidade),
  metade dos usos desaparece. Regra ao revisar QUALQUER tema novo: classifique cada uso do acento
  em fill vs ink (`background:` vs `color:`/`border-color:`/`outline:`), separe em dois tokens com o
  token de tinta apontando para o de fill no tema original (mudança visual zero), e confira caso a
  caso - um botão cujo fundo é a cor ESCURA legitimamente mantém o acento vibrante como texto.

- **2026-08-01 (via a web game) - a new rule that CAPS a collection at one item turns the list that
  renders it into a duplicate.** When a backend invariant lands ("only one active X per user", "one
  draft at a time", "a single default card"), the UI usually already has (a) a prominent surface for
  the current item and (b) a generic LIST of that collection built when N could be many. After the
  cap, the list can only ever hold the same single item the prominent surface names, so the screen
  shows the same thing twice, often with two buttons doing the identical action - and the list adds
  raw plumbing (an id/UUID) that the hero surface deliberately hides. Review rule: whenever a change
  bounds cardinality, go find every list/table/counter over that collection and decide, per surface,
  merge or drop; fold the list's genuinely useful metadata (status, last activity) into the item
  surface so nothing is lost. Corollary for reviewing: capture the state where the collection is
  NON-empty - the redundancy is invisible in the empty state, which is what a fresh test account
  shows by default.
- **2026-08-01 (via a canvas game app) - a bottom sheet capped by the FRAMEWORK, not by your own
  constraint.** A sheet whose content asks for `maxHeight: 0.78 * screen` can still render clipped
  because the host API imposes a smaller cap first (Flutter's `showModalBottomSheet` caps at 9/16 of
  the screen unless `isScrollControlled: true`; other stacks have analogous defaults). The symptom is
  a list **sliced mid-item at the bottom edge on every viewport**, and it reads as a layout bug rather
  than an invitation to scroll. Two-part rule when reviewing any scrollable panel/drawer/sheet: (1)
  check whether the container's own height constraint is actually being honoured, not just whether it
  was written; (2) a scrollable region that fills its container needs an explicit **affordance** -
  a bottom fade mask (a gradient with a `dstIn`-style blend over the last ~8%) is the cheap fix and
  beats a scrollbar on touch. A cut-off item with a hard edge is a P2 on its own, independent of
  whether scrolling technically works.
- **2026-08-01 (via a canvas game app) - to review a state-driven UI, SEED the state, don't grind to
  it.** Screens whose whole point is accumulated progress (levels, achievements, streaks, badges,
  history) look empty and untestable on a fresh install, so the interesting states - partially
  unlocked, near a threshold, many badges at once - never get reviewed. Seed the persistence layer
  directly (localStorage/IndexedDB/a fixtures endpoint), reload, then capture. Two traps: (a) match
  the storage layer's **exact encoding** - a wrapper that JSON-encodes values means an object must be
  double-encoded, and getting it wrong can throw inside app bootstrap and leave the app stuck on the
  splash with only a minified stack trace (if the app hangs at boot right after you seeded, suspect
  your seed format before suspecting the code); (b) deliberately seed the **worst case for layout**
  (the most badges/chips that can appear at once) and check it at the SMALLEST viewport - that is
  where a wrapping row pushes the primary buttons out of a height-capped container.
- **2026-08-01 (via a canvas game app) - clicks past the end of a flow silently dismiss modals.**
  When driving a canvas/game UI blind with coordinate clicks, a scripted "click every cell" loop runs
  past the moment the flow completes, and those extra clicks land on the **modal barrier** and close
  the very dialog you meant to capture - producing screenshots of the screen *behind* it and a false
  "the modal never appeared". Fix: screenshot after **each** step and pick the frame, rather than
  acting N times and capturing once at the end.

- **2026-07-23 (via todo - emoji de bandeira quebra no Windows; e valide a classe QUE O APP EMITE):**
  Duas lições. (1) **Nunca use emoji de bandeira (🇧🇷) em UI que precisa funcionar cross-OS.** A fonte
  do Windows (**Segoe UI Emoji) não tem glyphs de bandeira** por decisão da Microsoft - ela renderiza
  as duas letras do "regional indicator" (BR, ES, DE…) no lugar. macOS/iOS (Apple Color Emoji) e muitos
  Android/Linux (Noto Color Emoji) desenham; então o bug **não aparece no Mac do dev** e passa fácil.
  Fix agnóstico: **bandeiras em SVG inline** (data-URI no CSS `background-image`, ou `<svg>`), que
  renderizam idênticas em todo SO e independem de fonte de emoji. Headless Linux costuma TER Noto e
  mostrar a bandeira - então o screenshot do CI/skill esconde o bug do Windows; trate "emoji flag" como
  defeito por construção, não confie no screenshot. (2) **Ao trocar um símbolo por classe/asset keyed
  por um "código", a chave da classe tem que casar com o código que o COMPONENTE realmente emite.**
  Nomeei `.flag--br`/`.flag--us` (país) mas o código gera `flag--<lang>` = `flag--pt`/`flag--en`
  (idioma) → só as 4 em que idioma==país (es/fr/de/it) funcionaram; pt/en ficaram sem background. Pior:
  ao depurar, consultei `getComputedStyle(.flag--br)` (que EXISTIA no CSS) em vez de `.flag--pt` (o que
  o app renderiza) - e o "computed style OK" me mandou pro lado errado por duas rodadas. **Regra: quando
  um estilo não aparece, INSPECIONE a classe/atributo que o DOM VIVO realmente tem no elemento
  (`el.className` no browser), não a classe que você ASSUME que existe.** A distância entre "a regra CSS
  existe" e "o elemento tem essa classe" é onde o bug se esconde.
- **2026-07-23 (via todo - CRITIQUE O ESTADO OCIOSO, e não esconda ícone com opacity:0):** Duas
  lições que se reforçam. (1) **Capture e critique o estado DEFAULT/ocioso de todo componente novo,
  não só o happy path.** Uma rodada anterior validou um checkbox e um dropdown só em cenários que já
  forçavam seleção/abertura - e deixou passar (a) um ✓ que aparecia SEM seleção e (b) um gatilho de
  dropdown com borda quase invisível. Ambos os defeitos só existem no estado ocioso (nada
  selecionado / fechado). Ao revisar um controle com estados, capture SEMPRE: vazio/ocioso, hover,
  aberto, ativo/selecionado - o primeiro é o mais fácil de esquecer e o que o usuário vê primeiro.
  (2) **Não esconda um ícone/glyph com `opacity:0` e revele com uma classe - RENDERIZE-O
  condicionalmente.** Um `<i>` de ícone-fonte (Phosphor/FontAwesome) com `opacity:0` **ainda é
  pintado por alguns browsers mobile** (visto no Chrome do Galaxy S24): o check "escondido" aparecia
  fraco em toda linha. Fix robusto: só inserir o elemento no DOM quando ativo
  (`selected ? e("i",{className:"check"}) : null`), de modo que o estado inativo não tenha glyph
  algum - imune a qualquer diferença de repaint/opacity entre engines. Vale para qualquer overlay de
  estado (badge, check, spinner) sobre um controle. (3) Consistência: um controle novo colocado ao
  lado de uma família existente (aqui um dropdown ao lado de 4 `.iconbtn`) deve REUSAR a mesma
  linguagem visual (mesma borda/raio/altura) - uma pílula de borda fraca ao lado de quadrados de
  borda clara lê como "quebrado", mesmo tecnicamente tendo borda.
- **2026-07-23 (via todo - o controle que gerencia uma faixa rolável NÃO pode morar dentro dela):**
  Quando uma coleção é exibida numa **faixa com `overflow-x:auto`** (abas, chips de filtro, pills de
  categoria), o botão que **gerencia** essa coleção (⚙ "Gerenciar", "+ Novo", "Editar") não pode ser o
  último item da faixa: ele sai do campo de visão **exatamente quando a coleção fica grande**, que é
  quando o usuário precisa dele - e se aquela for a ÚNICA porta para criar/renomear/apagar, a
  funcionalidade vira inalcançável sem que nada pareça quebrado (screenshot sem overflow, sinal
  `overflowX:false`, zero erro de console). Regra: **o controle de gestão fica FORA do container que
  rola** (barra de ferramentas, header, ou canto fixo). Checar sempre: para cada faixa rolável, onde
  está a ação que a administra? Corolário de a11y/descoberta: um item cortado na borda direita sem
  gradiente/fade não comunica "há mais" - se a faixa precisa rolar, dê a affordance.
- **2026-07-23 (via todo - dois pegadinhas de método):** (1) **`.btn { width: 100% }` como regra
  BASE** (comum em apps mobile-first) transforma qualquer botão colocado numa linha flex em um item
  que estica e **espreme os irmãos** - no caso, um "Clear" empurrou o contador "3 selected" para duas
  linhas. Antes de compor uma toolbar/linha flex, **leia a regra base de `button`/`.btn` do projeto** e
  neutralize com `width:auto; flex:0 0 auto` no modificador. (2) **App servida de dentro de uma imagem
  Docker (`COPY . .`) NÃO reflete edições do fonte até o rebuild** - rodei uma rodada inteira de
  captura contra o container velho e "corrigi" achados que continuavam na tela. Antes de confiar nos
  screenshots, **prove que o asset servido contém sua mudança** (`curl -s <base>/js/app/x.js | grep
  <trecho novo>`); se o projeto tem bind-mount de dev, use-o. Vale para qualquer front atrás de
  build/bundle/CDN com cache.
- **2026-07-23 (via cartomania - o landing que é um FORMULÁRIO de login, e 3 armadilhas de layout):**
  **(a) Julgamento de PRODUTO antes do visual.** Numa landing de produto/jogo, a primeira pergunta
  não é "o padding está certo?" e sim **"o visitante vê o PRODUTO ou vê um formulário?"**. Caso real:
  a home de um card game passava em todos os checks visuais (0 overflow, contraste ok, foco ok) e
  ainda assim falhava no objetivo do dono ("quero que dê vontade de jogar") - o objeto mais pesado da
  tela era um campo de senha, a melhor arte do projeto (o tabuleiro de duelo) não aparecia em lugar
  nenhum, e a página acabava no fold. Checklist novo para qualquer landing: (1) o que a tela mostra do
  produto EM SI? (2) a **hierarquia de CTA está certa PARA QUEM CHEGA** - um visitante novo não tem
  conta, então "Log in" gigante dourado + "Criar conta" fantasma minúsculo é hierarquia INVERTIDA;
  (3) existe conteúdo ABAIXO do fold que dá motivo para acreditar (como funciona, prova, coleção), ou
  a página é só herói + rodapé? Um site pode passar em todo o Pilar 1 e falhar como produto.
  **(b) BUG CLASS - a faixa rolável INFLA o container que a contém.** Um `overflow-x:auto` no rail
  **não** impede que o min-content dele suba pela árvore quando há um pai intermediário
  `overflow:visible`: o track implícito `auto` do grid avô cresce até a largura TOTAL do conteúdo do
  rail (medido: 1318px dentro de uma caixa de 1120px) e **TODAS as seções da página** passam a ser
  mais largas que a viewport - scrollbar horizontal no documento inteiro, em todos os viewports.
  Regra: todo container que empilha seções precisa de **`grid-template-columns: minmax(0, 1fr)`** e o
  wrapper de qualquer scroller horizontal precisa de **`min-width: 0`**. Isso NÃO aparece como
  "elemento X estourou" - aparece como a página inteira larga demais, o que confunde o diagnóstico.
  **(c) `justify-content: center` numa flex row que ESTOURA torna o primeiro item inalcançável** -
  o conteúdo transborda para os DOIS lados e não há scroll negativo. Use **`justify-content: safe
  center`** (centraliza quando cabe, cai para flex-start quando não cabe). Sintoma: "o primeiro card
  aparece cortado pela metade e não dá para rolar até ele".
  **(d) Porcentagem em elemento `position:absolute` pode resolver contra caixa inesperada** -
  `width: min(430px, 92%)` renderizou **424px dentro de uma caixa de 350px** só no mobile (17px de
  overflow de página). Não confie na conta mental do containing block: **meça**, e blinde com
  `max-width: 100%` + `overflow-x: clip` no pai (`clip`, não `hidden`: não cria scroll container e
  não corta a sombra/brilho vertical).
  **MÉTODO que pegou os três (e que a screenshot NÃO pegaria):** um probe puppeteer que imprime
  `getBoundingClientRect()` + `scrollWidth`/`clientWidth` de cada ancestral suspeito e compara
  `documentElement.scrollWidth` com `clientWidth`. Depois de CADA correção, re-meça - não olhe o PNG.
- **2026-07-23b (via cartomania - barra fixa inferior precisa RESERVAR o próprio espaço):** uma barra
  `position:fixed` no rodapé (consentimento, notificação, "instale o app") **cobre permanentemente** o
  que estiver no fim da página se a página não tiver altura sobrando - no caso real ela escondia o
  card de login INTEIRO no mobile e nenhuma rolagem liberava. Padrão correto: renderizar um **spacer
  no fluxo** junto com a barra, com altura **medida** (`bind:clientHeight` / ResizeObserver) e
  fallback em CSS responsivo para SSR/primeiro paint (a barra quebra em mais linhas conforme estreita,
  então uma altura fixa única erra). **Teste objetivo, não visual:** rolar até o fim
  (`scrollTo(0, scrollHeight)`) e afirmar que `últimoConteúdo.getBoundingClientRect().bottom <=
  barra.getBoundingClientRect().top` em cada viewport. NÃO teste com `scrollIntoView({block:'center'})`
  - centralizar o elemento na viewport faz qualquer barra inferior "sobrepor" e dá falso positivo
  (errei isso primeiro). Vale para qualquer overlay fixo em borda.
- **2026-07-23c (via cartomania - imagem `loading="lazy"` mente no screenshot full-page):** cards/
  imagens abaixo do fold com `loading="lazy"` saem **em branco** no screenshot `fullPage` do puppeteer
  (o viewport nunca "passa" por elas de verdade) - parece feature quebrada, não é. É primo da lição de
  2026-07-19 (scroll-reveal por IntersectionObserver), mas aqui o culpado é o atributo nativo. Antes de
  reportar "a seção X não renderiza", **prove por estado**: `el.scrollIntoView()` + wait + asserção
  `[...imgs].filter(i=>i.naturalWidth>0).length`. Só chame de bug se `naturalWidth===0` com o elemento
  visível. E cheque `consoleErrors` do manifest (0 erros + vazio visual = artefato de carregamento).

- **2026-07-26 (via cartomania, three landing lessons):** (a) **Decorative animated background vs
  legibility.** A hero had a rotating gold "arena ring" + glow behind the card fan; its rim and glow
  bled up into the promise text and down into the CTAs, so both read worse. Fix that lands: shrink the
  decoration and soften its glow so it stays behind the cards (not under the text), add breathing space
  (gap) between the animated centre and the copy/buttons, and give any control that sits over it a
  semi-opaque fill + `backdrop-filter: blur()`. A "ghost" button with `background: rgba(255,255,255,.03)`
  over moving art is effectively invisible; a dark ~0.6 alpha + blur makes it legible. ALWAYS review a
  hero with the animation running, not a still. Promoted to a Pillar-1 contrast check. (b) **Landing
  copy is design material, verify it against the real content.** The copy claimed "two dragons" and
  "hand-painted dragons" while the actual set is 32 cards of which only 10 are dragons (the rest are
  warriors, mages, mythic creatures). Before shipping hero copy, read the real catalog/seed/DB and make
  the words true; a beautiful but false headline is a bug the owner will catch. (c) **Never use the em
  dash (Unicode U+2014) in UI copy** (this owner's standing rule; use commas, colons, parentheses, or a
  plain hyphen). When reviewing copy, grep the strings for U+2014 (`grep -rnP "\x{2014}" <dir>`) and flag
  any hit. Watch the fold cost of longer, truer copy: a 2-line promise that grows to 3 lines can push the
  primary CTA behind a fixed consent bar, so re-measure `ctaBottom` vs the cookie bar's `top` after a copy change.
- **2026-07-26 (via cartomania, "the same component renders subtly differently in two places"):**
  When one reusable component (a card, a tile, an avatar) is expected to look IDENTICAL everywhere and
  the owner says one instance is "slightly off", do NOT eyeball it and do NOT trust
  `getBoundingClientRect`. Two hard lessons: (1) **Measure the intrinsic aspect with
  `offsetWidth/offsetHeight`, never `getBoundingClientRect`** - the latter returns the axis-aligned
  bounding box AFTER transforms, so any `rotate()` (a fanned hand of cards, a tilted thumbnail) makes an
  UNDISTORTED element report a false, stretched aspect. I chased a "stretched card in the arena" for a
  whole pass; offsetWidth showed every card was actually the correct ratio and the real culprit was the
  fan rotation in my measurement. Then **prove sameness with a pixel-diff of the SAME item cropped from
  two contexts** (normalise to one size, ImageChops.difference, mean diff near 0 = identical). (2) **A
  CSS-containment element (`container-type:size` / `contain:size`) cannot size itself from its content**,
  so a wrapper that gives it only `aspect-ratio` and no width/height leaves the size ambiguous and it
  renders slightly stretched/inconsistent between call sites. Fix: anchor ONE real dimension (an explicit
  width or height) and let the ratio supply the other. Corollary for "make them all identical": also
  check nobody `scale()`s one instance relative to its siblings (a hero fan's centre card was
  `scale(1.07)`, 7% bigger); use lift/z-index/shadow for emphasis, never a size change. Promoted a
  Pillar-2 check. (3) **Transparency test for content inside a framed/masked container:** when an image
  sits inside a PNG frame (or any mask) with a transparent window and the owner reports "gaps on the
  sides showing what is behind", put a BRIGHT SOLID plane (pure red) directly behind the element and
  screenshot: any red bleeding through is a real transparent gap. The usual cause is the inner content
  padded to end EXACTLY at the frame window edge, so sub-pixel rounding leaves a see-through sliver
  (invisible on a dark page, glaring when elements overlap and the thing behind is another card). Fix:
  make the content overlap UNDER the opaque frame border (smaller padding) AND give the container an
  opaque background so residual sub-pixels show the backing, never the layer behind. This kind of gap is
  invisible in a normal screenshot and in a pixel-diff of two matching contexts; only the solid-colour
  backdrop reveals it.
- **2026-07-26 (via bobagi-blocks, capturar página de JOGO/canvas):** duas armadilhas de engine e uma
  de CSS. (1) **`networkidle` pode NUNCA assentar numa página de jogo/canvas** (Phaser etc.): o Chrome
  emite `networkIdle` para os about:blank mas nunca `networkAlmostIdle` para o loader da página real,
  mesmo com ZERO requests pendentes (diagnóstico via `DEBUG='puppeteer:*'` contando
  `Page.lifecycleEvent` por loaderId), e o init de WebGL/SwiftShader pode travar o `load` inteiro em
  VPS pequena. O engine ganhou: `--wait-until load|domcontentloaded|networkidle0|networkidle2`
  (use `load` + `--wait` maior para apps canvas), `--chrome-args="--disable-gpu"` (o parser agora
  aceita `--chave=valor`, obrigatório quando o VALOR começa com `--`), `--scenarios` aceita JSON
  inline além de arquivo, e timeout de navegação agora lista os requests pendentes. Regra prática:
  se uma rota canvas/jogo dá Navigation timeout enquanto as rotas estáticas passam, troque para
  `--wait-until load` antes de caçar fantasmas. (2) **`place-items:center` numa grid com vários
  filhos NÃO agrupa o conteúdo**, cada filho centraliza NA SUA track e eles se espalham na altura;
  para agrupar o bloco todo no centro use `place-content:center` (items vs content). Sintoma:
  "ring no topo, label no meio, legenda embaixo" num botão-overlay que deveria ler como um grupo.
  (3) Reforço da lição de estado ocioso: decoração adicionada ao estado idle (blocos fake atrás de
  um play button) sobrepôs a legenda; todo retoque "cosmético" num estado precisa de screenshot
  próprio ANTES de ir pro ar, e quando a decoração compete com o texto, remova a decoração.
- **2026-07-29 (via bobagi-blocks, o overlay que so quebra COM dados + botao de container aninhado):**
  tres licoes de uma regressao real que chegou ao aparelho do dono. (1) **Todo overlay/card tem estados
  DEPENDENTES DE DADOS: capture cada um com dados representativos, nao so o vazio.** O game over tinha
  uma linha extra ("+N moedas/tijolos") que so renderiza quando a sessao rendeu recurso; todos os meus
  screenshots usavam estado zerado -> a linha nunca apareceu -> o botao colidia com ela em producao.
  Checklist: para cada linha condicional de um card (bonus, recompensa, badge), force o dado via
  localStorage/estado de debug e screenshote COM ela. E capture tambem em dpr>1 (o layout px*dpr muda
  as proporcoes). (2) **Em engine canvas (Phaser e afins), botao = textura em Image direto na cena; nao
  monte botao como Graphics dentro de container DENTRO de outro container com hit-rect manual.** No
  aparelho real o visual e a area de toque divergiram; com Image interativa o hit e o proprio bounds da
  textura e a classe de bug morre. (3) **Nunca deixe uma linha informativa CLICAVEL encostada num botao
  primario**: a linha de tijolos era tambem atalho para outra tela e roubava toques do "jogar de novo"
  (o usuario descreveu como "clique nao funciona direito"). Acao secundaria sobreposta a primaria =
  toque ambiguo; separe espacialmente ou remova a interatividade da linha.

- **2026-08-10 (via um comparador web) - tres licoes que screenshots quase nao revelam.**
  (1) **Um fallback SPA no 404 torna asset quebrado INVISIVEL:** quando toda rota desconhecida devolve
  o index.html com 200, um `url()` de fonte/imagem com caminho errado "carrega" HTML sem erro de rede,
  sem erro de console, e a pagina cai no font-fallback do sistema em silencio. Ao copiar um
  `faces.css`/asset compartilhado entre projetos, os caminhos root-relative (`/fonts/...`) quebram se o
  novo app monta static em outro prefixo. Check barato: `curl -o /dev/null -w '%{content_type}'` em CADA
  asset critico e conferir que NAO veio text/html; e registrar o MIME de .woff2 quando o server e minimo.
  (2) **Verifique o asset servido ATRAVES DA BORDA, nao so da origem:** com CDN/proxy na frente
  (Cloudflare cacheia .js/.css/.zip por 4h por extensao), rebuild + recreate do container continua
  servindo codigo velho (`cf-cache-status: HIT`) - o grep de "o asset contem minha mudanca" tem que rodar
  na URL publica. Fix estrutural quando o HTML e renderizado pelo backend: carimbar as URLs de asset com
  hash de conteudo no boot; a pagina (html nao cacheado) passa a apontar para URL nova a cada deploy.
  (3) **Feedback de acao nasce COLADO no controle que o disparou:** uma mensagem de aviso appendada no
  fim do `<main>` fica fora do fold no mobile exatamente quando mais importa; e um indicador de progresso
  ("coletando...") nao pode afirmar atividade quando a pre-condicao (extensao/agente conectado) nao
  existe - rotule o estado pela CAUSA ("aguardando coletor"), nao pela esperanca.
- **2026-08-11 (via um comparador web - pagina de politica de privacidade exigida por app store):**
  Ao adicionar a pagina legal que uma loja (Chrome Web Store, Play, App Store) exige antes de publicar
  uma extensao/app, o check de "a politica bate com o que o site carrega" (2026-06-26) se ESTENDE ao
  ARTEFATO distribuido, nao so ao site: a copy tem que descrever o que a EXTENSAO/APP realmente faz
  (o que ela busca, quando age, que id/credencial guarda, o que NAO le), verificado contra o codigo do
  coletor/cliente, porque e exatamente isso que o revisor da loja compara com as permissoes declaradas
  no manifest. Uma politica que promete "nao le sua navegacao" com uma permissao `<all_urls>` no manifest
  e uma reprovacao. Reuso barato de UI aqui e o certo: uma pagina legal nova deve REUSAR o componente de
  painel/tokens existentes (nada de identidade nova) - o unico defeito recorrente e o tap target: links
  de RODAPE (`.foot a`, `font-size` pequeno) nascem com ~17px de altura, abaixo do piso de 24px; fixe com
  `display:inline-block;min-height:24px` no seletor do rodape (pega o link legal novo e o "voltar" de
  brinde). Confirme pelo sinal `tinyTargets` antes/depois.
- **2026-08-11 (via um comparador web - capturar um LOADER transiente que so existe sob pre-condicao
  viva):** Para revisar/screenshotar um indicador de carregamento (spinner, skeleton, mascote
  "farejando") que aparece so ENQUANTO uma acao assincrona roda e some no instante em que ela termina,
  NAO basta disparar a acao e tirar o screenshot: se a acao completa rapido (ex.: resposta CACHEADA,
  mock instantaneo, rota local), o loader **pisca e ja foi** antes do frame, e voce conclui falsamente
  "o loader nao aparece / esta quebrado". Precisa das DUAS coisas: (a) satisfazer a pre-condicao REAL
  que dispara o loader (ex.: a extensao/agente conectado, o estado de auth certo) e (b) garantir que a
  acao **realmente demore** - use uma entrada FRESCA/nao-cacheada (query nova, id inedito, `force`) para
  que o backend faca o trabalho e o loader permaneca visivel por segundos. Confirme no proprio DOM que o
  elemento ainda esta `!hidden` no instante do screenshot (`$eval('#loader', e => !e.hidden)`), nao so
  que ele apareceu em algum momento. Capture o loader em desktop E mobile (o mascote/spinner pode
  estourar o ritmo do bloco no estreito). E cheque a a11y do loader: `role="img"`+`aria-label` no
  SVG/icone, container `aria-live="polite"`, e a animacao atras de `@media (prefers-reduced-motion)`.

- **2026-08-11 (via um comparador web - ao "casar com um design system existente", INSPECIONE a marca
  de perto contra a referencia, e confirme que o logo aparece NA PAGINA):** Uma rodada minha passou
  por dois defeitos GROSSEIROS de header que a screenshot full-page mostrava mas eu nao escrutinei: (1)
  a marca "B bobagi" era uma LETRA amarela solta (`<span>B</span> bobagi`) em vez do TILE arredondado
  do design system (quadrado amarelo com "B" em cor on-yellow) - a versao solta lia como "Bbobagi",
  claramente fora do padrao, e o dono pegou na hora; (2) o icone/mascote novo da marca (que o dono
  PEDIU explicitamente) existia so no `<link rel=icon>` (aba do browser), **nunca renderizado na
  pagina**. Licoes durables: **(a)** quando a tarefa e "deixar parecido com o site X / seguir o design
  system", ABRA o componente real da referencia (o markup+CSS da `.brand`/`.mark` do site-mae) e
  reproduza o COMPONENTE (tile+wordmark, tamanhos, radius, tokens `--on-yellow`), nao uma aproximacao
  a olho; um wordmark/logo-tile e o primeiro lugar que um dono compara. **(b)** se o pedido inclui um
  ICONE/logo/mascote, verifique que ele aparece num elemento visivel do DOM (`querySelector` de um
  `<svg>`/`<img>` no header/hero), nao so no favicon - "coloquei o icone" via `rel=icon` NAO cumpre
  "coloque o icone no site". **(c)** metodo: recorte a FAIXA DO HEADER (top ~140px) e leia-a isolada em
  desktop E mobile - defeitos de marca somem no meio de uma screenshot full-page e passam batido. Um
  rebrand nao esta revisado sem um close-up do header comparado lado a lado com a referencia.

> Add a dated, **general** lesson whenever a review surfaces a check worth keeping. Keep it
> project-agnostic. Promote recurring lessons into the checklists above.

- 2026-06-20 - v1 baseline rubric created.
- 2026-06-20 - Engine: `offCanvas` must ignore children inside an `overflow-x:auto/scroll` ancestor;
  otherwise wide data tables/carousels (a legit in-container scroller) spam false positives. Pair the
  signal with `overflowX` to tell a real page-overflow (P0/P1) from an in-container side-scroll (mobile UX).
- 2026-06-20 - A wide multi-column data table that side-scrolls inside its card on phones is usable but
  poor - key columns/actions hide off-screen. Prefer a stacked card-per-row layout below ~600px. Always
  check tables specifically at the narrowest viewport.
- 2026-06-20 - Capture: full-page shots on tall mobile pages downscale too far to judge fine spacing.
  Added `--fold` (above-the-fold viewport shot) and `--scale` (deviceScaleFactor) - use them for padding/
  spacing critique; keep full-page for layout/responsiveness.
- 2026-06-20 - Consistency check to keep: a global `button{}` that paints every button as the primary
  style forces resets on every non-primary button (brand/menu/icon) and breeds regressions. Flag it;
  recommend a neutral default + explicit `.btn-primary`.
- 2026-06-20 - Check breakpoint values are a **shared, small set** (tokens/consts). Ad-hoc per-component
  breakpoints (e.g. 560/600/760px in one app) cause inconsistent reflow; grep `@media` and list distinct widths.
- 2026-06-20 - An avatar/icon control whose text label is hidden at small widths still needs an
  accessible name there (`alt`/`aria-label`); `alt=""` (decorative) is wrong when it's the only account cue on mobile.
- 2026-06-20 - DONE (engine): added `--scenarios <json>` - `[{label,url?,viewport?,actions?,full?}]`
  with actions `{clickText|click|fill|press|wait}`. Drives tabs, sub-tabs, modals and filled forms so a
  SPA's whole surface is captured, not just the default route. (`--scenarios-only` skips the route grid.)
- 2026-06-20 - High-value cheap code check: **grep for undefined CSS tokens** (every `var(--x)` vs the
  `:root` set). Caught real wrong-color bugs (`--text-muted`/`--danger`/`--success` that were never
  defined). Promoted into the Pillar-2 checklist above.
- 2026-06-20 - Capture artifact to ignore: `position:sticky` headers **duplicate down the page** in
  Puppeteer full-page screenshots (the sticky element repaints at each scroll band). It's a screenshot
  artifact, not a UI bug - judge sticky elements from the viewport/fold shot, not the full-page one.
- 2026-06-20 - Layout: a `max-width` form/content card should be **centered** (`margin-inline:auto`),
  not left-aligned - left-align leaves a big empty right half on wide screens that reads as broken. Match
  the app's existing centered-card pattern.
- 2026-06-20 - Consistency: when you reflow one data table to stacked cards on mobile, **reflow its
  siblings too** (Positions vs History) - half-migrated tables are themselves an inconsistency.
- 2026-06-20 - a11y: a disabled/read-only input still needs a programmatic label (`<label for>` /
  `aria-label`); a visual-only `<span class="field-label">` does not associate. And give text link-buttons
  a `min-height:24px` so they meet the tap-target floor.
- 2026-06-21 - Spacing: uneven vertical rhythm usually comes from **margin stacking/collapse between a
  component and its neighbor**, not a single wrong value. A child with its own `margin-top` after a header's
  `margin-bottom` oversizes the gap (siblings collapse to the larger margin); a `margin:0` reset `<p>` right
  after an element glues them (zero gap). Fix by owning the gap in one place and matching one rhythm.
  Promoted into Pillar-1 Spacing. **Always trace adjacent-sibling margins, don't just eyeball one value.**
- 2026-06-21 - Responsiveness (code-level): a `display:flex` row without `flex-wrap` whose children have
  intrinsic/fixed widths **overflows its container on mobile** instead of growing vertically - a frequent
  phone bug that's invisible on desktop. Always grep flex rows and confirm they reflow; hide any `flex:1`
  desktop spacer at the mobile breakpoint so wrapped items don't leave a gap. Promoted into Pillar-1
  Responsiveness + a Pillar-2 code check. **Every review must include a mobile viewport AND this code pass.**
- 2026-06-21 - Aesthetics: fixing overflow is only half the job - once a row wraps on mobile, **judge how the
  items are distributed**, not just that they fit. Left-bunched content with empty space on the right looks
  unfinished; a 3-zone grid (start/center/end: badge left, name centered, pair right; secondary line
  left/right) reads as intentional. Don't ship "it no longer overflows" - ship "it looks balanced." Promoted
  into Pillar-1 Responsiveness. Verify isolated/auth-gated components by screenshotting a faithful mock.
- 2026-06-21 - **Element-configuration failure (style leak via descendant combinator).** When "the same
  element" looks different in two places, suspect a variant rule on a **self-nestable** reusable component
  leaking through a bare descendant selector. Real case: one `<Collapsible>` had `.section .cl-title{font-size:lg}`;
  a `variant="help"` Collapsible nested *inside* a `variant="section"` one inherited that rule (same component
  scope), rendering its "How it works" title at section size while the un-nested twins stayed small. Fix:
  direct-child scope (`.section > summary > .cl-title`). General method that nailed it fast: build a faithful
  **mock** placing the suspected-different instances **adjacent** (real tokens + component CSS inline), screenshot,
  and read it - the size jump was obvious side-by-side though invisible in isolation. Promoted a Pillar-2 check.
  **When asked to make element X "match" element Y, render X and Y adjacent first - don't eyeball them apart.**
- 2026-06-21 - a11y: a **scrollable text region** (long Terms/legal block in a fixed-height scroller)
  should NOT get `tabindex="0"` - it trips `a11y-no-noninteractive-tabindex` and adds a dead tab stop.
  Content is already exposed to screen readers; the checkbox/buttons stay focusable. Use `role="region"`
  + `aria-label` to name it, no tabindex. Promoted into Pillar-3 a11y.
- 2026-06-21 - Method (auth-gated flows): to screenshot a blocking gate / logged-in page when there's no
  shared test login, **create a throwaway account via the signup API, scrape its session cookie from the
  cookie jar, inject it with `--cookie`, capture, then DELETE the account** (and clean up). Confirmed
  end-to-end here (consent gate + account page). Cheaper and more faithful than a static mock when the
  real page is reachable; pair with the mock approach only when no account can be created.
- 2026-06-21 - Bug class (inline link as `<button>` + global button rule): using a `<button>` for an
  **inline text link** breaks when the app has a global `button{}` that sets `height`/`display:inline-flex`
  (a common pattern). The button keeps the ~control height (e.g. 40px) inside running text, so the line box
  of *that* row balloons while sibling rows stay ~1 line tall → **lopsided gaps between stacked checkbox/
  text rows** (looks like a spacing bug, is actually a line-height bug) and the link sits off the text
  baseline. Fix: use a semantic `<a>` for navigation links - it's immune to the button rule and correct
  a11y (`a` for navigation, `button` for actions). When you must keep a button, fully neutralize
  `display`/`height`/`padding`/`line-height`, not just `min-height`. Always cross-check stacked-row spacing
  against whether a row contains an inline `<button>`.
- 2026-06-21 - UX (SPA hash router): `navigate()` to a new **top-level page** (terms/privacy/account…)
  should `window.scrollTo(0,0)` so the page starts at the top instead of inheriting the previous page's
  scroll; do it in the shared navigate() AND on `hashchange` (covers back/forward and direct hash edits).
  A link that "goes to the right page but mid-scroll" reads as broken to users.
- 2026-06-25 - Method (verify a 2-col→1-col reflow): always capture a viewport **just above** the
  collapse breakpoint, not only one well below it. Below the breakpoint tells you the stack works; the
  real risk is the *cramped two-column* band right above it (e.g. breakpoint 860 → shoot 900), where the
  narrower column can squeeze a panel/table before it's allowed to stack. A clean 768 + 1280 pair can
  hide a broken 900. Add the breakpoint+~40px width to the viewport list for any split-hero/2-col layout.
- 2026-06-25 - a11y (decorative product-demo panel): when a hero's signature is a faux UI that **restates
  the copy's claims** (a fake console/dashboard/log, no real controls), mark the **whole panel
  `aria-hidden="true"`** so screen-reader users don't hear a confusing duplicate of the headline/subtitle.
  The textual claim already lives in the real copy beside it; SVG/icons inside then need no alt. (Only do
  this when the panel carries no information that's *absent* from the surrounding text.)
- 2026-06-26 - a11y (cheap, high-value code check): **grep whether the app has a global
  `:focus-visible` for its shared button class** (`.button:focus-visible` / `button:focus-visible`). A
  missing keyboard focus ring is **invisible in screenshots** (hover/mouse look fine) but fails every
  keyboard user, and it's common for a design system to style `input:focus` yet forget buttons. If absent,
  the fix is one global rule using the existing focus-ring token - it lifts the whole app, not one screen.
  Pair it with: links/buttons on a **dark** surface need an explicit focus style (the UA default outline is
  often near-invisible on dark). Added as a recurring Pillar-3 grep.
- 2026-06-26 - a11y (consent/cookie/notification bars): a **non-blocking** bottom bar that traps no focus
  should be `role="region"` + `aria-label`, **not** `role="dialog" aria-modal="false"` - `dialog` implies a
  focus-managed widget it isn't. Reserve `role="dialog"`+`aria-modal="true"`+focus-trap+initial-focus for a
  bar that actually blocks the page. General rule: match the ARIA role to whether the thing blocks/traps,
  not to the word "banner/popup".
- 2026-06-26 - Method (verify a consent-gated third-party script end-to-end): when the task is "load
  script X only after cookie consent", a screenshot can't prove it - **drive it with the browser**: assert
  the gated `<script src*="...">` is **absent before any choice**, **present only after Accept-all**,
  **never after Essential-only**, and **present on a return visit** (cookie already set). Click the bar's
  buttons with `getByRole('button',{name})`, **not** `getByText` - `getByText` can match a wrapping
  text/whitespace node or trip strict-mode and silently click the wrong thing (cost me two false test
  failures until I switched). Read the persisted cookie via the browser context, not `document.cookie` string-matching.
- 2026-06-26 - Consistency/correctness worth a grep on any privacy-touching change: **does the privacy
  policy match what the site actually loads?** A real case here - the policy claimed "no third-party
  analytics" while an analytics `<script>` loaded unconditionally in `app.html`. When reviewing a
  cookie/consent/analytics change, diff the *claims* in the legal copy against the *actual* network/script
  tags; a stale honest-looking policy is a compliance bug, not just a wording nit.
- 2026-06-28 - **`overflowX:false` does NOT mean mobile is fine - confirm the PRIMARY pane survives.**
  A `flex` layout with a `flex-1` content pane + a fixed-width sidebar (`w-[26rem]`) that lacks
  `shrink-0` will, at phone widths, shrink the sidebar *and* starve the primary pane to ~0px instead
  of overflowing - so `overflowX` stays false and `offCanvas` stays empty while the main content has
  effectively **vanished**. The automated overflow signals miss this class entirely. On every mobile
  shot, positively verify the *primary* content is still visible (not just "nothing overflows"); fix by
  stacking panes (`flex-col`) below a breakpoint or giving the main pane a `min-width`/`min-height`.
  **New rule: a mobile shot must be judged for "is the main thing still here?", not only overflow.**
- 2026-06-28 - a11y nuance: an emoji/icon-only `<button>` with a **`title`** attribute does NOT trip the
  `unnamedControls` signal (title provides an accessible name), so the engine reports it clean - but
  `title` is weaker than `aria-label` (no reliable SR exposure on some setups, mouse-only tooltip). When
  the signal says 0 unnamed controls but the UI is full of emoji buttons, spot-check that the name source
  is a real label, and prefer `aria-label` over `title` for icon-only controls.
- 2026-07-02 - Responsiveness (adding children to re-laid-out rows): when a mobile media query re-lays a
  flex row as a **grid with explicit per-child placements** (each existing child has `grid-row/column`),
  any NEW child added later gets **auto-placed into an unintended cell** (its own orphan row/column) -
  desktop looks fine, only the breakpoint breaks. Caught live: a status icon added next to a badge landed
  alone on a third grid row at <600px. Fix pattern: group the new element with its logical partner in one
  wrapper (one wrapper = one grid cell) or give it explicit placement. **Whenever a diff adds a child to a
  row that any media query restructures, re-screenshot that breakpoint** - the auto-placement bug is
  invisible in the unchanged desktop layout.
- 2026-07-03 - Gamified/themed dashboard cards: a card header using `display:flex; justify-content:space-between`
  with a **wrappable title** on the left and a small **tag/badge** on the right (e.g. "Workshop ↗") breaks when
  the title wraps to 2 lines - the tag's own text (esp. a trailing glyph/arrow) wraps onto its own line and the
  tag drifts to vertical-center. Fixes: `align-items:flex-start` (tag pins to the title's first line),
  `white-space:nowrap; flex:none` on the tag, and `min-width:0` on the title so it (not the tag) absorbs the wrap.
  General: any space-between header with one flexible + one fixed child needs nowrap+flex:none on the fixed one.
- 2026-07-03 - Status chips/badges with **semi-transparent backgrounds** break when the layout lets them
  float over a bright decorative layer (fixed-position moon/sun/blob art): at some viewport the chip lands
  on the bright art and its text contrast collapses. If a chip conveys state (ONLINE/OFFLINE), give it a
  **solid** background; save translucency for chips that always sit on a known surface. Check every fixed
  decorative element against reflowed positions of overlaying content at each viewport.
- 2026-07-03 - **CRITICAL bug class: `[hidden]` is defeated by any author `display` rule.** An element
  toggled via the `hidden` attribute/property but styled with `display:flex|grid|block` in a class
  (`.modal-backdrop{display:flex}`, `.stale-warn{display:flex}`) STAYS VISIBLE when hidden - the UA
  `[hidden]{display:none}` is the weakest rule and loses to any author `display`. Two nasty symptoms:
  (1) a "hidden" full-screen modal/overlay with `opacity:0` still covers the page with `pointer-events`
  on, **swallowing every click** (page looks dead); (2) a "hidden" warning/badge shows permanently.
  Fix once, globally: `[hidden]{display:none!important}`. Always add this reset in any page that toggles
  flex/grid elements via `hidden`. Verdict method that caught it: a headless click test where the modal
  never opened + the warning showed in the wrong state - screenshot a toggled-off overlay element and
  confirm it's truly gone, not just transparent. Promote: every review must check that `hidden`-toggled
  elements have no competing `display` rule.
- 2026-07-05 - Apps canvas (Flutter web, jogos): os signals de DOM ficam cegos e cliques por seletor não funcionam - use as actions `clickXY` (clique por coordenada, derivada de um screenshot anterior) e `evalJs` (semear estado via localStorage/reload) adicionadas ao capture.mjs; e ao revisar builds web de apps móveis, cheque primeiro se plugins nativos sem implementação web (ads/consent) travam o boot no splash - guarda kIsWeb no main é o fix padrão. (via tictacverse)
- 2026-07-05 - Method (verify a **consent-gated** element deterministically): don't `clickText` the
  accept button as the first action - it races the banner render (the banner mounts a tick after load,
  so the click finds nothing and the "consented" shot is silently unconsented). Seed consent with
  `evalJs: "localStorage.setItem('<consent-key>','accepted')"` then a second `evalJs: "location.reload()"`
  + a generous trailing `wait`; the reload's context-destroyed error is caught, and the reloaded page
  boots already-consented. Read the app's actual consent localStorage key from the source (it may be
  versioned, e.g. bumped when a new script category is added). (via CoinHub ad rails)
- 2026-07-05 - Method (verify a **width-gated** element, e.g. desktop-only side rails shown only above a
  wide breakpoint): capture a viewport **above** the show-breakpoint to prove it renders in the intended
  slot (gutter), AND the band **just below** it to prove it's cleanly hidden (not squished/overlapping) -
  plus a true mobile width to prove the base layout is untouched. Expect a `position:fixed` element to
  paint in the FIRST viewport band of a full-page screenshot (vertically centred if `top:50%`); that's
  correct fixed behaviour, not a bug - judge its horizontal placement (inside the empty gutter, not over
  content) and confirm `overflowX:false`. Gutter-centred rails should use a token-relative offset
  (`calc((100vw - page-max)/4 - halfwidth)`), never a magic px. (via CoinHub ad rails)
- **2026-07-06 (via CoinHub):** A native control element repurposed as a NON-control (e.g. a `<button>`
  used as an image frame/card wrapper for a lightbox) inherits the app's global control styles - the
  killer is a global `button { height: var(--control-h) }`: the wrapper stays ~40px tall and the
  image visually overflows onto the content below (vertical OVERLAP with zero horizontal overflow, so
  scrollWidth-based checks pass). Rule: when wrapping media/content in `button`/`a`, explicitly
  neutralize the global control rules (`height:auto; padding:0; border:0; background:none` + hover
  filter) - and judge full-page screenshots by EYE for vertical overlap; automated signals only catch
  horizontal overflow. Script-only verification (naturalWidth>0, scrollWidth) is NOT a visual review.
- **2026-07-07 (via CoinHub):** Ao inserir CTA promocional/afiliado/monetização numa UI de produto,
  verifique que ele **não compete com a ação primária** da tela: coloque-o DENTRO da seção auxiliar
  relevante (ex.: um "não tem conta? crie aqui" dentro do guia de conexão), não como banner no topo
  roubando atenção do fluxo principal, e sem dark pattern (deixe a ação primária mais proeminente).
  Links externos de afiliado/apoio: sempre `target="_blank" rel="noopener"` e cheque o contraste do
  link sobre a caixa tingida (callout âmbar/tinta de marca).
- **2026-07-08 (via CoinHub):** Bug class - **stale state badges via helper-closure in compiler-tracked
  templates (Svelte & co.)**: a template that reads state through a plain `const` arrow helper
  (`isActive(x)` closing over `credentials`) hides the dependency from the compiler - the block never
  re-renders when the state object is reassigned, so status tags ("Active/not configured") go STALE
  after the user switches, while sibling expressions that reference tracked vars directly DO update
  (half-fresh UI, worse than fully stale). Fix: reference the state var directly in the markup or via
  a `$:`/derived mirror. **Method that caught it: screenshot AFTER a state-changing interaction
  (click → wait → shot), never only the initial render** - first-paint screenshots cannot reveal
  stale-render bugs; every review of a stateful control (tabs/switch/selector) must include a
  post-interaction shot and check ALL views of that state (card badge + header pill + panel title)
  agree. Bonus check the same run reconfirmed: when a selection highlight and an "active" status are
  distinct concepts, the DEFAULT selection on load must equal the active one, or the two visuals
  contradict each other.
  - **2026-07-13 reinforcement (via CoinHub):** the SAME class bites **`$:` reactive/derived statements**,
    not only markup expressions - and one helper can hide **several** dependencies at once. A derived
    `$: cost = foldByQuote(execFilter(e => e.by==='USER'), e => e.total)` stayed **R$0** after data loaded
    because BOTH `execFilter` (reads `summary`) and `foldByQuote` (reads `quoteBySymbol`) hid their state
    reads from the compiler, so the block was never re-run; a sibling `$: x = fold(summary.operations,…)`
    that named `summary` directly updated fine (again: half-fresh, worse). Fix: inline the state reads so
    every tracked var appears **textually** in the `$:` (`summary.executions.filter(…)`, pass
    `quoteBySymbol` as an arg), or use an explicit `$:`-mirror. Rule of thumb: a `$:` that computes from
    state must MENTION that state by name - if a helper is the only thing that touches it, the compiler is
    blind to it.
- **2026-07-10 (via CoinHub):** Ao adicionar um painel novo com tabelas de dado denso (7+ colunas) num
  app que JÁ tem padrão de reflow stacked-card < 600px para outras tabelas, decida conscientemente:
  ou reflowa igual (consistência) ou aceite o scroll-x contido - mas nesse caso **garanta que os
  números-chave (os que respondem à pergunta do usuário) vivam em CARDS responsivos acima das tabelas**,
  não só dentro delas, senão o mobile esconde o essencial no scroll. Um scroll-x contido é aceitável
  para DETALHE denso; nunca para a métrica principal. (Método de captura de painel auth+chave-gated:
  extrair o `<style>` verbatim do .svelte + os tokens do :root do app.css num mock HTML servido por
  http.server - file:// quebra o route-append do capture.mjs; sirva por http.)
- **2026-07-11 (via CoinHub):** Barra de ação "copy + botão" (título/descrição à esquerda, CTA à direita):
  no desktop use `justify-content:space-between` com a copy `flex:1 1 <base>` e o botão `flex:none`; no
  mobile o `flex-wrap:wrap` empilha (copy acima, botão abaixo) sem overflow. Sempre teste os 2 estados -
  a copy longa é o que empurra o botão pra fora se o botão não for `flex:none`. Para categorias novas num
  split de métricas (ex.: "Você/Robôs/Externo"), renderize a nova parte condicional (`{#if hasX}`) para não
  mostrar "· Externo: R$ 0,00" quando não há dado - e confirme que o total do card SOMA a nova parte
  (headline e split têm que bater).
- **2026-07-11 (via CoinHub):** Para revisar AO VIVO uma feature atrás de login+dado (ex.: posições que só
  existem com estado no banco), o caminho fiel é: signup via API → promover a conta no DB (verificação/
  termos) → **semear as linhas de dado direto no banco** (as posições/registros que a feature exibe) →
  injetar o cookie de sessão no capture.mjs → dirigir as sub-abas com `--scenarios` (arquivo JSON, NÃO
  inline - o script lê `existsSync(path)`) usando `clickText`. Isso prova a feature de ponta a ponta muito
  melhor que um mock. Cuidado: um estado que depende de OUTRA credencial (ex.: "conectado à exchange") vai
  cair no ramo "não conectado" com a conta de teste - verifique esse estado por código e reporte que o
  ramo conectado precisa da credencial real, não finja tê-lo capturado.
- **2026-07-11 (via CoinHub):** Quando uma view depende de estado que SÓ existe com credencial externa
  real (ex.: saldo de exchange), a review viva de conta descartável só alcança o estado VAZIO - capture-o
  (prova que o código novo não quebra: sem crash/console-error/overflow) e valide a view POPULADA por (a)
  teste da lógica pura de valuation num script e (b) conferência dos números derivados contra os DADOS
  REAIS no banco (ex.: preço médio por par = SUM(total)/SUM(qty) bate com o esperado). Diga no relatório
  que o populado foi verificado por lógica+dados, não por screenshot, e peça a conferência visual final ao
  dono da credencial. Não finja screenshot do que exige a credencial real.
- **2026-07-12 (via CoinHub):** Ao ADICIONAR colunas a uma tabela grid com `min-width` fixo, recalcule o
  min-width contra a largura REAL do card que a contém (container `page-max` − paddings), não contra o
  viewport. Uma tabela que cabia com N colunas passa a estourar com N+2 e - como a coluna de AÇÕES
  (botões) costuma ser a última - ela é a primeira a sumir no scroll horizontal do desktop, escondendo a
  ação mais importante. Sempre re-capture a tabela após adicionar colunas e confirme que a última coluna
  (ações) aparece sem scroll no viewport alvo; aperte frações + min-width até caber.
- **2026-07-15 (via CoinHub - ícone-botão num flex encolhe abaixo do tap-target):** Um botão pequeno
  quadrado (ex.: um ✕ de "limpar", com `width/height` fixos) colocado num container **flex** (`inline-flex`/
  `flex`) pode ser **encolhido pelo flex-shrink abaixo do piso de 24px** mesmo com `width` setado - o sinal
  `tinyTargets` pegou um ✕ renderizado a **12×24** apesar de `width:1.5rem`. Regra: todo ícone-botão dentro
  de um flex precisa de **`flex: none`** (+ `min-width`/`min-height` explícitos) senão vira alvo minúsculo
  em algum viewport. Cheque no código: grep botões quadrados de ícone dentro de `display:flex` e confirme
  `flex:none`/`min-width`. Barato de corrigir, e o sinal automático já aponta - mas o fix é `flex:none`, não
  só aumentar `width` (que o shrink ignora).
- **2026-07-15 (via CoinHub - dirigir `<input type=date>` e o formato do date picker nativo):** Para semear
  um `<input type="date">` via `evalJs` no capture, set `el.value='YYYY-MM-DD'` (SEMPRE ISO, independente do
  locale) e dispare **`input` E `change`** (Svelte/bind escuta os dois). E não reporte como bug que o campo
  mostre `mm/dd/yyyy` vs `dd/mm/aaaa`: o formato exibido do date picker nativo vem do **locale do
  navegador**, não da app (o Chrome headless costuma ser en-US) - só o `value` (ISO) importa para a lógica.
- **2026-07-15 (via CoinHub):** Dois pontos de MÉTODO ao capturar uma SPA atrás de nginx com filtros
  `<select>`. (1) **Aponte a base para o host do SPA (nginx), não para a porta da API** - bater direto no
  backend (`:5020`) devolve "404 page not found" para `/` (a API só serve rotas de API; o `dist/` é servido
  pelo nginx). O token de sessão é válido em qualquer host (lookup por hash), então injete o mesmo cookie com
  `--cookie-domain <host-publico>` e capture a URL pública (cookie `Secure` ⇒ precisa de HTTPS). (2) Para
  **dirigir um `<select>` nativo** via `evalJs`, o valor tem que ser **UMA expressão** - `page.evaluate(str)`
  do Puppeteer avalia a string como expressão, então `const s=…; s.dispatchEvent(…)` (múltiplas instruções)
  lança SyntaxError e a ação falha silenciosa (o "action failed" aparece, mas o shot ainda é escrito no
  estado ERRADO). Embrulhe numa IIFE: `(function(){var s=document.querySelectorAll('.x select')[0]; s.value='sold'; s.dispatchEvent(new Event('change',{bubbles:true}));})()`.
  Setar `.value` + disparar `change` é o caminho (opções de `<select>` não são "texto clicável" p/ `clickText`).
  Sempre confira no screenshot que o filtro REALMENTE trocou (conte linhas/leia o cabeçalho), não confie no
  "✓" da cena.
- **2026-07-12 (via CoinHub):** Para uma tabela larga que estoura o card em telas grandes, a correção
  "alargar o container" tem que ser CIENTE de elementos fixed nas calhas (ad-rails/sidebars): esses se
  posicionam via a largura ANTIGA do container (ex.: `--page-max`), então alargar o conteúdo além dela no
  breakpoint onde eles aparecem causa COLISÃO. Padrão: alargue o container só na faixa SEM os fixed
  (ex.: 1280-1519px) e volte ao valor base no breakpoint onde eles surgem (≥1520px); e reduza o min-width
  da tabela para caber também no valor base (com os fixed presentes). Verifique nos 3 regimes: faixa
  alargada, breakpoint dos fixed, e confirme que a última coluna (ações) aparece sem scroll em todos.
- **2026-07-16 (via todo - redesign de app 100% inline-style):** Num app React `createElement`
  **sem build**, com a UI toda em `style={{}}` inline: um redesign por CSS **não "pega"** enquanto os
  inline styles existirem (inline vence qualquer folha). Ordem certa: **primeiro** converta os
  elementos estruturais/barulhentos para `className` (deixando inline SÓ o dinâmico de verdade -
  transform de drag, posição computada de menu), **depois** o CSS de tokens aplica. Ao trocar
  `alert/prompt/confirm` nativos por toast/modal temáticos, cuide da **corrida save-on-blur**: o
  `onBlur` do input de edição (que cancela) dispara ANTES do `onClick` do botão Salvar → salva com o
  id já zerado; blinde o Salvar com `onMouseDown: e=>e.preventDefault()` pra o foco não sair do input
  antes do clique resolver. E hierarquia de botão que presta = **cor com significado**: primário
  sólido, secundário ghost, e uma cor (coral/vermelho) RESERVADA só pro destrutivo - se "tudo é da cor
  da marca", deletar grita igual à ação principal.
- **2026-07-15 (via todo):** Método - revisar app que autentica por **token em `localStorage` (não
  cookie)**: `--cookie` NÃO loga. Registre uma conta descartável pela API, e no scenario semeie o token
  com `evalJs: "localStorage.setItem('token', <json-do-token>)"` seguido de um SEGUNDO `evalJs:
  "location.reload()"` + um `wait` generoso - a SPA remonta já autenticada (mesmo padrão do consent-seed;
  o erro de context-destroyed do reload é engolido). Para ver o estado POPULADO de um app de listas cujo
  tier grátis limita linhas/abas, **semeie várias linhas direto no banco** (conta descartável) em vez de
  esbarrar no limite - e **apague a conta ao final** (cascade). Check barato de alto valor que este
  review reforçou: grep por `box-sizing` (sem `*{box-sizing:border-box}` global, qualquer
  `width:100% + padding` vira overflow de poucos px no mobile - invisível no desktop), por `:focus-visible`
  (ausência total = zero anel de foco de teclado, invisível em screenshot) e por `prefers-reduced-motion`
  (animações decorativas sem guarda). Os três faltando juntos é o padrão "projeto quase pronto".
- **2026-07-16 (via warframe-farm-helper - CSP vs redirect de CDN de imagem):** Quando as imagens vêm de um
  CDN que **301/302-redireciona** para outro host (comum: `cdn.foo.us/img/x.png` → `raw.githubusercontent.com/...`),
  a CSP `img-src` precisa liberar **os DOIS hosts** - o navegador checa o destino do redirect contra a
  política, então liberar só o host inicial faz a imagem **falhar silenciosamente** (aparece o alt/ícone
  quebrado). Sintoma no capture: `consoleErrors` cheio de "Loading the image '<host-do-redirect>' violates
  ... Content Security Policy" e o sinal `missingAlt`/imagem quebrada na tela. Método que pegou: ler o
  `.consoleErrors` do manifest (não só os sinais visuais) - erro de CSP de imagem só aparece no console, e um
  `curl -I` na URL do CDN revela o `location:` do redirect. Fix: adicionar o host de destino ao `img-src`.
  LIÇÃO META: sempre leia `consoleErrors` do manifest numa página com imagens de 3º - CSP de imagem quebrada
  não dispara overflow nem layout-shift, só o console denuncia. E o piso de tap-target (24px) num link de
  tabela densa se resolve com `display:inline-block; padding:Ypx 0; min-height:24px` no `<a>` (a célula já
  tem padding, mas o sinal mede o bounding-box do link, não da célula).
- **2026-07-16 (via warframe-farm-helper - ENGINE fix `missingAlt` + review atrás de CDN/proxy com cache):**
  (1) O check de alt usava `!img.alt`, que acusa **`alt=""` - a marcação CORRETA de imagem decorativa**
  (WAI): false-positive em todo site bem feito. Corrigido para `!img.hasAttribute('alt')`; regra geral:
  `alt` vazio ≠ `alt` ausente - só o segundo é bug. (2) Ao re-capturar um site atrás de **CDN/proxy com
  cache de estáticos** (Cloudflare & co.) logo após um deploy, os shots podem vir com **JS/CSS VELHOS**
  (o fix "não aparece" - sintoma: comportamento antigo num arquivo que você acabou de mudar). Verifique
  contra a ORIGEM (`http://127.0.0.1:<porta>`) para validar o fix agora, e deixe o edge expirar (ou
  purge) para o público. Nunca conclua "fix não funcionou" a partir de um shot atrás de cache. (3) Uma
  **faixa/barra horizontal de status com scrollbar oculta**: no MOBILE o chip cortado na borda é
  affordance suficiente, mas no DESKTOP (mouse, sem swipe) conteúdo cortado fica inalcançável na
  prática - dimensione para caber TUDO no viewport desktop comum (compacte: segundos só quando faltam
  <10min, letter-spacing, divisores) e verifique na banda mais justa (viewport = max-width do wrap
  +20px), nos DOIS idiomas (PT costuma ser mais largo que EN).
- **2026-07-16 (via warframe-farm-helper - toggle de idioma i18n + default por locale):** Ao revisar um
  **toggle de idioma** (PT/EN) cujo default segue `navigator.language`: o **headless Chrome roda em en-US**,
  então as páginas em "idioma default" renderizam no idioma do NAVEGADOR (EN), não no que você imagina -
  rotular a cena "pt-mobile" NÃO força PT. Para capturar um idioma específico, **semeie
  `localStorage['<lang-key>']` + reload** (mesmo padrão do consent-seed) OU lance o browser com locale
  fingido. Sempre capture os DOIS idiomas e confirme visualmente que TUDO trocou (nav, chips, placeholders,
  seções, e conteúdo gerado no servidor como passo-a-passo/prosa) - um toggle costuma cobrir a UI estática e
  esquecer a prosa gerada (steps, mensagens), que fica no idioma antigo. Padrão de header responsivo que
  funcionou (busca fixa + toggle): mobile-first com `flex-wrap` e `order` - marca+toggle na linha 1 (toggle
  `margin-left:auto`), busca `flex-basis:100%` na linha 2, nav rolável na linha 3; num breakpoint (~760px)
  vira `flex-nowrap` uma linha só (marca·nav·busca que cresce·toggle). Verifique que a busca compacta do
  header e a busca-hero da home não brigam (duas caixas) - redundância aceitável se intencional.
- **2026-07-16 (via warframe-farm-helper - redundância semântica que só emerge após fix de dados):** Uma
  review NÃO deve tratar "dois itens do mesmo tipo mostram valores diferentes agora" como prova de que não
  são redundantes. Caso real: dois relógios dia/noite ("Cetus" e "Terra") que o jogo sincroniza 1:1 por
  design (U38.5) apareciam com estados DIFERENTES na 1ª review - porque uma das fontes de dado estava bugada
  (Terra vinha de uma API legada mostrando "noite" enquanto Cetus mostrava "dia"). A duplicação (dois chips
  carregando sempre a mesma info) só ficou óbvia DEPOIS de corrigir o dado. Lição: ao ver N itens do mesmo
  tipo, pergunte se são **a mesma coisa subjacente por design** (→ fundir e reaproveitar o espaço), não se
  os valores atuais coincidem - valores coincidem/divergem por acaso, inclusive por BUG. Método barato:
  para cada par de itens repetidos, cheque na fonte/no código se derivam do mesmo dado; se sim, é candidato
  a fusão mesmo que na tela de agora estejam diferentes. E o inverso: não funda itens que só coincidem no
  momento mas são conceitos distintos (ex.: um relógio "Fass/Vome" que compartilha a duração mas não é o
  mesmo ciclo). Promovido a um item de checklist (Pillar 1 · Information design). Também: superfície com
  poucos itens deve distribuir pela largura (`space-between`/center), não amontoar num canto deixando buraco.
- **2026-07-16 (via warframe-farm-helper - duas caixas de busca ATIVAS na mesma tela):** Uma rubric antiga
  minha dizia "confira que a busca do header e a busca-hero não brigam - redundância **aceitável se
  intencional**"; foi tratada como intencional e o operador reclamou (duas barras na home). Lição: **duas
  entradas de busca ATIVAS na mesma tela são redundância a CONFIRMAR com o dono, não a assumir intencional.**
  O default de produto é **uma entrada de busca por tela**; a secundária vira dica/atalho (ex.: chips de
  exemplo que levam aos resultados) ou é removida. Exceção legítima: uma página **dedicada a busca**
  (resultados) pode ter a barra grande "da página" + a global do header - ali a grande é o campo ATIVO com o
  termo (padrão tipo Google SERP), não redundância. Regra ao FLAGAR: numa tela que NÃO é de resultados de
  busca, se há 2+ campos de busca que fazem a mesma coisa, reporte como redundância (P2) e proponha manter
  só um. (Reforça o item Pillar 1 · Information design: vale para busca, não só para tiles/relógios.)
- **2026-07-17 (via warframe-farm-helper - lista longa com itens "ativos" vs "históricos/inativos"):**
  Quando uma lista mistura itens **acionáveis agora** com itens **inativos/históricos** (disponível vs
  vaulted, ativo vs arquivado/expirado, em estoque vs esgotado), e os inativos são a MAIORIA (aqui: 37 de
  39 relíquias vaulted por componente), despejar tudo afoga a informação que o usuário precisa e empurra o
  resto da página para longe. Padrão: **mostrar os ATIVOS inline + colapsar os inativos num `<details>`**
  ("▸ Ver N vaulted"), com um estado vazio ("nenhum disponível - todos vaulted") quando não há ativos.
  `<details>/<summary>` nativo é a ferramenta certa (acessível por teclado de graça); estilizar com
  `summary{list-style:none}` + `::-webkit-details-marker{display:none}` + um chevron `::before` que rotaciona
  em `[open]`, e **`summary:focus-visible`** explícito (o foco default some ao remover o marker). Checagem
  ao revisar QUALQUER lista longa: os itens estão ORDENADOS com o acionável primeiro (o backend já ordenava
  disponível→vaulted) E o inativo em massa está colapsado? Se a lista tem >~10 itens e a maioria é ruído
  inativo, é candidato a collapse. NOTA de método: para capturar o estado ABERTO de um `<details>`, dispare
  `document.querySelector('.x > summary').click()` via `evalJs` + `wait` antes do shot (o fold-shot padrão
  pega só o estado fechado no topo). Promovido ao item Pillar 1 · Information design.
- **2026-07-17 (via warframe-farm-helper - badge de estado BINÁRIO aplicado a tipo que não tem esse eixo):**
  Um badge de status de duas faces (Disponível/Vaulted, Ativo/Inativo, Em estoque/Esgotado) derivado de um
  booleano `available` mostra o rótulo ERRADO quando renderizado num tipo de item que **não possui esse
  eixo de estado**. Caso real: um recurso bruto (Orokin Cell) caía em `available=false` (não tinha relíquia
  nem fonte no dataset) e exibia **"VAULTED"** - mas recurso não vaulta, está sempre disponível. O default
  `false` de um flag de disponibilidade vira uma AFIRMAÇÃO FALSA de estado. Checagem ao revisar qualquer
  badge de status: confirme que TODO tipo que chega ali realmente tem os dois estados possíveis; para os
  tipos sem esse eixo (recursos, itens sempre-disponíveis, categorias "N/A"), ou force o estado correto na
  origem, ou não renderize o badge. Method: abra a página de um item de CADA tipo que compartilha o
  componente de badge (não só o tipo "normal") e leia o rótulo - um badge "errado mas plausível" passa
  despercebido se você só olha o caso feliz. (Cruza com Pillar 1 · Information design.)
- **2026-07-17 (via tictacverse - review de LOCALE NOVO num app canvas):** ao revisar a adição de um
  idioma cujo script a fonte bundled NÃO cobre (ex.: Devanagari com fonte latina como Fredoka), a
  pergunta não é "a fonte tem os glifos?" (o fallback do sistema resolve) e sim: (a) o fallback
  renderiza em TODAS as telas com peso/altura de linha aceitáveis? (b) strings do idioma novo, muitas
  vezes mais LARGAS, estouram botões/cards/HUD apertados? Method p/ Flutter web e afins: em vez de
  clicar até o seletor de idioma, FORCE o locale persistido antes do boot - shared_preferences web
  grava em localStorage com prefixo `flutter.` e valor JSON-encodado (`localStorage.setItem(
  'flutter.settings.locale', JSON.stringify('hi'))` + reload + wait) - e então percorra home, sheets,
  seleção e telas de jogo. Cobre também: tile do idioma novo no seletor com bandeira/check, e a
  auto-detecção (supportedLocales gerado) sem precisar de aparelho real. (Cruza com Pillar 3 · i18n.)
- **2026-07-18 (via warframe-farm-helper - deep-link gerado por slug 404 para CLASSES inteiras):** Ao
  gerar links para uma referência externa (wiki/docs/catálogo) a partir do NOME do item por um padrão de
  slug (`/w/<Nome_com_underscores>`), NÃO assuma que o padrão resolve para todos os tipos. Caso real: itens
  "de topo" (armas, warframes, recursos: `/w/Jade`, `/w/Plastids`, `/w/Orokin_Cell`) resolvem 200, mas
  **peças de conjunto** ("Braton Prime Barrel") e **cosméticos** ("Alone Portrait", "Stalker's Lair Scene")
  dão **404** - eles vivem como SEÇÃO da página do set/quest, não como página própria. Um link 404 é pior
  que nenhum. Fix por CLASSE: alvos que têm página → `/w/`; alvos que são subitens → a **URL de BUSCA** do
  destino (`/index.php?search=<termo>`, que sempre resolve e cai na página-mãe). Método barato que pegou:
  `curl -o /dev/null -w "%{http_code}" -L` numa AMOSTRA de CADA classe de link (item, peça, cosmético,
  recurso) antes de enviar - não teste só o caso feliz (um item real), teste um representante de cada tipo
  que passa pelo gerador. LIÇÃO META: sempre que um diff introduz links gerados por padrão, enumere as
  CLASSES de entrada e verifique o status HTTP de uma de cada; roteie as que 404 para busca/fallback.
- **2026-07-18 (via warframe-farm-helper - painel/section colapsável com `<details>`: controle interativo NÃO vai no `<summary>`):** Ao tornar um card/section inteiro colapsável com `<details class="panel"><summary>…</summary>`, qualquer controle interativo (botão de filtro, toggle de aba, link "Ver mais/See more") colocado DENTRO do `<summary>` **dispara o toggle do details ao ser clicado** (o summary captura o clique) - o filtro "não funciona" ou abre/fecha o painel sem querer. Padrão certo: o `<summary>` guarda SÓ o título (+ um chevron via `::after` que gira em `[open]`); todo o resto (toggles, listas, "Ver mais") vai num `.panel-body` IRMÃO, fora do summary. Exceção tolerável: um link de NAVEGAÇÃO real (`<a href>` que troca de página) pode ficar no summary - o toggle acontece mas a página descarrega, então é inócuo. Sempre dê `summary { list-style:none; cursor:pointer }` + `::-webkit-details-marker{display:none}` + `summary:focus-visible` explícito (o marker default some ao ocultar). Método de review: capturar o estado COLAPSADO (clicar o summary via `clickText` do título + wait) e o estado com o filtro/ordenação aplicado, provando que o controle age no conteúdo e NÃO no toggle. (Cruza com o item de `<details>` do Pillar 1 · Information design.)
- **2026-07-18 (via warframe-farm-helper - texto que vira link precisa de afordância em REPOUSO):** Ao
  transformar rótulos de texto (nomes de item, recompensas) em `<a>`, decida a afordância de REPOUSO
  conscientemente: `color:inherit` + sublinhado só no hover fica limpo mas é quase indescoberto (o usuário
  não sabe que dá pra clicar sem passar o mouse - e no mobile não há hover). Se os links são o ponto da
  feature (o dono PEDIU pra poder clicar), dê um cue sutil em repouso (sublinhado pontilhado/opacidade baixa)
  ou uma cor de link discreta - sem cair no extremo de N links berrantes competindo com os CTAs. Regra:
  hover-only affordance é aclitável para link secundário/raro, insuficiente para o valor principal da tela.
  transformar server-side dados que vêm de um **cache compartilhado** (um TTL-cache em memória, um objeto
  reaproveitado entre requests), **CLONE antes de transformar** (`map(x => ({...x, campo: tr(x.campo)}))`),
  nunca mute em lugar. Caso real: o handler traduzia `location` mutando os objetos retornados por um cache
  de drops → o cache ficava em PT e o **request EN seguinte vinha traduzido** (um idioma vazando pro outro,
  de forma dependente-de-ordem e intermitente). Método de review que PEGA isso (o teste de "capturar os 2
  idiomas" não basta se rodar sempre na mesma ordem): carregue PT primeiro, DEPOIS bata no MESMO recurso em
  EN e confirme que voltou ao inglês - a contaminação só aparece na 2ª língua após a 1ª ter tocado o cache.
  Vale para qualquer transform (formatar moeda/data, mascarar, reordenar) sobre dado cacheado: transform =
  cópia. (Cruza com a checagem de i18n: teste os dois idiomas E a ordem entre eles.)
- **2026-07-18 (via warframe-farm-helper - adicionar um 3º/4º idioma a um i18n binário PT/EN):** Ao
  expandir um i18n que só tinha 2 idiomas, o bug nº1 é o **ternário binário** espalhado pelo código:
  `lang === 'en' ? EN : PT` (ou `=== 'pt' ? PT : EN`). Ele parte o mundo em "um idioma vs. TODO o
  resto" - então CADA idioma novo (es, ru…) cai no ramo do idioma ERRADO (aqui es/ru vazavam
  **português** na descrição/passo-a-passo/raridade do servidor, porque tudo ≠ 'en' virava PT). Fix
  em duas frentes: (a) normalize no BOUNDARY (o handler que recebe `?lang=`) para os idiomas que a
  prosa do servidor realmente tem - `pt`→pt, qualquer outro→`en` (fallback internacional), nunca
  deixe um idioma desconhecido herdar o ramo pt; (b) torne os ternários internos "idioma-base
  positivo" (só `=== 'pt'` → PT; resto → EN) como defesa em profundidade. E o fallback de chave
  faltante do `t()` deve cair em **en** (padrão internacional), não no 1º idioma do dict. Método de
  review que PEGA o vazamento: bata no MESMO recurso do servidor com `?lang=es` e `?lang=ru` e
  confirme que voltou INGLÊS (não o outro idioma pré-existente) - capturar só a UI estática não pega
  prosa gerada no servidor. Decisão de produto que vale reusar: em apps de nicho com jargão/entidades
  em inglês (games: nomes de item no market/wiki/trade; libs; APIs), **traduza o CHROME e deixe os
  NOMES/dados em inglês** nos idiomas novos - localizar os nomes pioraria a busca. Cross-check de
  ícone: uma **bandeira em opacidade baixa (estado não-selecionado)** pode perder a identidade
  (Espanha vermelho-amarelo-vermelho dimmed ≈ Alemanha escuro-ouro-escuro) - confira a
  reconhecibilidade no estado dim, não só no selecionado. (Cruza com Pillar 3 · i18n.)
- **2026-07-18 (via CoinHub - capturar feature atrás de MÚLTIPLOS gates em sequência):** Para revisar ao
  vivo uma feature de dashboard atrás de login, o cookie de sessão sozinho NÃO basta se a app tem gates
  ENCADEADOS antes do dashboard - aqui a conta descartável (signup + `email_verified_at=NOW()` no DB + login)
  ainda caía na **página de aceite de Termos+Privacidade** (o `clickText` da aba "não encontrado" era o
  sintoma: a aba nem existia porque o dashboard não montou). Cada gate server-side (verificação de e-mail,
  aceite de termos versionado, step-up) tem que ser satisfeito ANTES de capturar: aceitei via
  `POST /account/agreement/accept {version}` (leia a `current_version` do próprio endpoint - ela é
  versionada). Método geral: quando o `clickText`/seletor de uma aba "não é encontrado" mas a base carrega,
  **leia o 1º screenshot** - quase sempre é um gate (consent/terms/verify/paywall) interceptando, não um bug
  de seletor; satisfaça o gate e recapture. E o **rótulo de aba com ícone colado** (`🔒B3 / Investidor10`
  sem espaço, para não-admin) ainda casa por `clickText` com o texto ("B3 / Investidor10" é substring) - o
  que quebrou foi o gate, não o match. (Cruza com o método de auth-gated de 2026-06-21 e 2026-07-11:
  signup→promover no DB→**satisfazer TODOS os gates**→injetar cookie→dirigir com `--scenarios`.) Bônus: num
  painel de dado denso (tabela 8 col) o combo certo é métricas-em-chips (`flex-wrap`) ACIMA + tabela em
  `overflow-x:auto` - `overflowX=false` com a métrica principal nos chips é o padrão aprovado, não achado.
- **2026-07-18 (via warframe-farm-helper - portar um bloco de ADS/3º-party de um app para outro):** Ao
  reusar o padrão de anúncio de outro projeto (iframe A-ads em rails laterais + bloco mobile), os pontos
  que realmente quebram são: (1) o **breakpoint dos rails deriva do page-max DESTE app**, não do original -
  recalcule (`breakpoint ≈ page-max + 2×(rail+folga)`; aqui 1060px → 1420px, no original 1160px → 1520px)
  e capture a faixa logo ACIMA do novo breakpoint; (2) **CSP**: iframe de ad exige `frame-src <host>` no
  app destino (sem frame-src, default-src 'self' bloqueia SILENCIOSO - só o console denuncia; ler
  consoleErrors do manifest); (3) **rótulo "Anúncio" entra no i18n** do app destino em TODAS as línguas
  (teste de paridade de dicionário pega); (4) caixa com width/height explícitos → sem CLS quando o
  criativo chega; iframe `loading=lazy` no fim da página não pinta em full-page shot - não é bug. E um
  check de PRODUTO: units compartilhados entre sites compartilham também o filtro de categoria do painel -
  inventário cripto/apostas pode destoar num site de outro nicho; units novos por site se o dono quiser
  filtros independentes.
- **2026-07-18 (via tictacverse - provar ESTADOS TRANSIENTES de animação/timing):** o capture.mjs tem
  ~0,5-1s de overhead por shot full-page (CDP + página canvas pesada) - janelas de sub-segundo (ex.:
  "a CPU só joga após 550ms", "o modal só sobe após 1,65s") NÃO são prováveis com a cadeia de actions
  dele; o shot "instantâneo" chega tarde e mente. Método que funciona: script puppeteer dedicado com
  (a) screenshots **viewport-only** (rápidos), (b) o **elapsed REAL desde o evento gravado no nome do
  arquivo** (`_t244.png`) para julgar com honestidade o instante capturado, e (c) além do timing, uma
  prova por ESTADO INDIRETO que não depende de relógio (ex.: um toque disparado durante a janela de
  bloqueio deve ser ENGOLIDO - a célula continuar vazia prova a guarda sem medir ms). Bônus de método:
  o 1º clique após uma transição de tela de SPA/canvas pode ser engolido pela animação de rota - dê
  settle ≥1,5s antes do primeiro clique de cada tela, e desconfie quando a partida "seguiu outro rumo"
  (o rumo errado é sintoma de clique perdido, não de bug do app). E `tinyTargets` em Flutter web acusa
  sempre o `flt-semantics-placeholder` 1×1 - artefato do framework, não é achado.
- **2026-07-19 (via bobagi.space portfólio - full-page shot × scroll-reveal):** página com reveal por
  IntersectionObserver (conteúdo nasce `opacity:0` e só aparece ao entrar na viewport) rende um
  full-page screenshot quase todo PRETO abaixo do fold - parece runtime error, mas não é: o
  `fullPage:true` do puppeteer não dispara os observers das seções nunca intersectadas. Antes de
  diagnosticar "página quebrada", cheque consoleErrors no manifest (0 erros + vazio visual = reveal).
  Método que funciona: cenário com N× `{"press":"PageDown"}` + waits curtos até o fim da página e SÓ
  ENTÃO o shot full-page (jump direto com End pode pular seções sem intersectar; PageDown passo a
  passo revela todas). Alternativa: emular `prefers-reduced-motion` se o site tiver o bypass. E ao
  adicionar cards novos numa grade existente, o check mais barato de consistência é diff visual card
  novo × card antigo na MESMA captura (insets, chips, foot) - herdar o padrão é o critério, não a
  estética absoluta do card.
- **2026-07-19b (via bobagi.space - classe de estado × classe base):** um botão que ganha uma classe
  utilitária de visibilidade (`.burger{display:none}`) mas TAMBÉM carrega a classe base do design
  system (`.toggle{display:...}`) fica visível se a regra base vier DEPOIS no CSS - especificidade
  igual, ordem decide. Sempre escope a classe de estado à base (`.toggle.burger`) ou verifique a ordem;
  e o teste barato é capturar o viewport ONDE o elemento deveria sumir (desktop para um hambúrguer),
  não só onde ele aparece. Checklist novo de portfólio/efetividade: além do visual, julgue POSICIONAMENTO
  (o hero vende a senioridade real? CTA primário = objetivo do site?), PROVA (números reais vs enfeite),
  e PRÓXIMO PASSO do visitante convencido (CV baixável / contato) - um site pode passar em todos os
  checks visuais e falhar como produto.
- **2026-07-22 (via Coin Hub - tabela com coluna de texto livre):** numa tabela de dados, a PRIMEIRA
  coluna costuma ser a única com texto livre (nome/título vindo de fonte externa) - e é sempre a que
  quebra. Linha `flex` com `white-space:nowrap` + `min-width` NÃO contém texto longo: ele pinta POR CIMA
  das colunas vizinhas (não empurra, não corta, não gera overflow no manifest - o `overflowX:false`
  mente). Padrão correto: `display:grid` com `minmax(<piso>, Nfr)` na coluna de texto +
  `white-space:normal; overflow-wrap:anywhere; align-items:start`, para o texto quebrar em mais linhas
  DENTRO da própria célula e a linha crescer em altura. Teste com o **pior dado real** (consulte o banco
  por `ORDER BY length(campo) DESC`, não pelo que está na tela). Segunda lição, sobre o breakpoint do
  reflow em cards: escolha-o pela **largura MEDIDA** que a tabela recebe (`el.clientWidth` no browser
  headless, por viewport), não pelo default 600px herdado de outra tabela - se o piso do grid é maior
  que o espaço disponível, a faixa entre 600px e o piso vira scroll horizontal INTERNO e some com as
  últimas colunas sem nenhum affordance. Prova objetiva de que ficou certo: `scrollWidth-clientWidth==0`
  do menor ao maior viewport, mais um par de medidas em volta do breakpoint (939 vs 941).
- **2026-07-23 (via cartomania - a legal "last updated" date is a CONTENT bug when it lags the acceptance
  version):** When an app has a versioned Terms/Privacy re-acceptance gate, the "Last updated: <date>"
  shown on the /terms and /privacy pages must MATCH the version the gate forces users to accept. A stale
  date (page says "June 26" while the gate demands version "2026-07-23") is a real contradiction a user
  will notice, not a nit - flag it P2 and fix by tying the displayed date to the same version constant.
  Also re-validated: a strict CSP (`script-src 'self' 'nonce-…'`, no unsafe-inline) can ship on a
  canvas-heavy SPA with 0 console violations IF inline `style=""` attrs are covered by
  `style-src-attr 'unsafe-inline'` and external font/img hosts are allow-listed - verify by loading every
  key route (incl. a live game screen) headless and counting CSP violations, don't assume.
- **2026-07-26 (via a ranked decision table added to a finance dashboard):** When a NEW multi-column
  table lands next to an EXISTING one that reflows to cards at a different breakpoint, judge the
  in-between window deliberately (one in table mode, one in cards): acceptable only if neither
  overflows there. Prefer reflowing a decision table to cards BEFORE its grid would enter a
  "barely scrolls" zone - hidden columns behind a tiny internal scroll are worse for a comparison
  surface than a longer page of cards. And in label/value card reflow, a status cell that can carry
  TWO chips (state + warning) must be `flex-wrap` so the second chip drops to its own line instead
  of colliding with the `::before` label - verify with a row that actually has both chips, not just
  the common single-chip case.
- **2026-07-28 (via assumption fields in a finance panel that stepped up/down across a row):** When
  items in a flex/grid row are misaligned by a CONSISTENT offset and only the first (or last) item is
  in the "right" place, suspect a **global class-name collision**, not a wrapping/height issue. A
  component that reuses a common utility class name (`.field`, `.card`, `.row`, `.col`, `.item`) silently
  inherits the global design-system rule for that class - classically a vertical-stacking `margin-top`
  with a `:first-child { margin-top: 0 }` reset, which pushes every item BUT the first down by one
  spacing unit. Diagnose by measuring each item's `getBoundingClientRect().top` (labels AND inputs) and
  grepping the global stylesheet for `.<class>` and `.<class>:first-child` / `label { margin }`. Fix with
  a higher-specificity scoped reset (e.g. `.wrapper label { margin: 0 }`) or a unique class name, then
  re-measure at several widths (the collision hides at the width where everything is one line). Lesson
  for the reviewer itself: judging a per-item step from a screenshot alone is unreliable - a 1-spacing-unit
  offset reads as intentional breathing room; always measure box tops when a row "looks slightly off".
- **2026-07-30 (via an icon added to one tab of an existing text-only tab bar):** Putting an icon
  inside a control that until then held ONLY text (tab, button, chip, menu item) is a layout change,
  not a content change. Two things break quietly: (1) the control usually has no `display:flex`, so the
  inline `<svg>` sits on the text baseline and reads a hair low - convert the control to
  `inline-flex; align-items:center; gap:<token>`; (2) sibling children that already carried their own
  spacing (a status glyph with `margin-right`, a badge with `margin-left`) now get **margin + gap
  stacked**, so the controls WITH the legacy child end up spaced differently from the one with the new
  icon. Own the spacing in ONE place: add the `gap` and delete the children's margins. Verify BOTH
  states of the conditional child (e.g. the lock glyph only present when locked) - the un-equal spacing
  only shows in the state you didn't screenshot. Also re-check the narrowest viewport: the longest label
  just got wider, so a bar that used to fit on one line may now wrap (fine if the container already has
  `flex-wrap`, a P0 overflow if it doesn't). And when a signal like `H-OVERFLOW` fires at an extreme
  width, read the `offCanvas` element list before blaming the change - it is often a pre-existing
  unrelated element (header/account menu), and reporting it as a regression burns the reviewer's credibility.
- **2026-07-30 (via adding one list item to a landing's changelog section):** A stylesheet rule that
  sets rhythm on an ELEMENT selector (`section { padding: 46px 0 }`) is silently dead when every one of
  those elements also carries a layout class that sets the same property (`.wrap { padding: 0 20px }`) -
  class (0,1,0) beats element (0,0,1) on the same node, so the page's whole vertical rhythm is actually
  coming from heading margins, and the author's intent in the CSS is a lie. It hides well: the middle
  sections still look spaced (their headings have margins), and only the LAST block before the footer
  reads glued, because there is no heading after it to donate margin. Two lessons: (1) never certify
  spacing from the stylesheet's *intent* - measure `getBoundingClientRect()` for the last child, the
  section box and the next landmark, and compare the transition gaps to the page's other transitions;
  (2) when a section-padding rule turns out to be dead, prefer a LOCAL fix on the block you touched
  (`#that-section { padding-bottom: … }`) and report the global rule as its own finding - raising the
  specificity globally re-spaces every section at once, which is a redesign, not a review fix.
  Corollary: a full-page screenshot scaled down to fit is useless for judging a ~20px gap - it compresses
  the very difference you are judging, so take the measurement (or a 1:1 crop) before calling it.
- **2026-07-30 (via landing estatica - reusar uma classe de layout DENTRO de um container mais
  estreito herda a media query dela):** ao colocar uma lista/grade existente (`.steps`, `.cards`,
  `.grid`) dentro de um **container novo e mais estreito** (um card lado a lado, uma coluna de
  2-col), ela **carrega junto a media query que a torna multi-coluna na largura da PAGINA** - e
  `@media (min-width:760px){.steps{grid-template-columns:repeat(3,1fr)}}` dispara pela largura do
  VIEWPORT, nao pela do container. Resultado: 3 colunas de ~130px dentro de um card de 500px, com
  o texto picado em 6 caracteres por linha - um defeito que **so aparece no desktop** (no mobile a
  media query nem dispara, entao a captura de celular passa limpa e da falsa confianca). Regra:
  toda vez que aninhar uma classe de layout num contexto mais estreito, **anule explicitamente o
  eixo de colunas dela** no escopo novo (`.card .steps{grid-template-columns:none}`) e **capture o
  desktop**, nao so o mobile. Container queries (`container-type:inline-size`) sao a cura de raiz
  quando o projeto pode adota-las. Corolario de metodo: quando a mudanca e "mesmo componente, novo
  container", a passada de revisao que importa e a LARGA, invertendo o instinto mobile-first.
- **2026-08-01 (via rename de marca - o wordmark bicolor escapa de TODA varredura textual):** num
  rename de produto, a verificacao instintiva e `grep -ri "<nome antigo>"` no source e no bundle. Ela
  **mente**, porque o logo textual costuma ser **partido em dois elementos** justamente para pintar as
  metades de cores diferentes (`Coin<span>Hub</span>`, `<b>Air</b>bnb`, `Data<em>Dog</em>`) - a string
  completa nao existe em lugar nenhum, entao o grep volta limpo enquanto o elemento MAIS VISIVEL da
  pagina ainda mostra o nome velho, em todas as telas. Regra: apos qualquer rename, (1) grepe tambem
  as metades e o padrao `>{sufixo}<`/`<span>`, (2) grepe a classe do logo (`.brand`, `.logo`,
  `.wordmark`) em vez do texto, e (3) **confirme no screenshot do above-the-fold** - um shot da dobra
  em um viewport ja teria pego isto em segundos. Corolario mais geral: **quando a mudanca e textual e
  global, o pixel e a autoridade, nao o grep** - inverta a ordem habitual e olhe a imagem primeiro.
  Segundo corolario, de risco: chaves de **estado persistido** (cookie de sessao, `localStorage` de
  idioma/moeda/**consentimento de cookies**, chaves de advisory lock) NAO devem ser renomeadas junto -
  renomear desloga usuarios, zera preferencias e **faz o banner de LGPD reaparecer derrubando o
  consentimento ja dado**. Deixe-as com o nome antigo e DOCUMENTE o porque, senao a proxima sessao
  "termina o rename" e quebra estado de producao.
- **2026-08-01 (adicionar UM elemento a um flex container existente: tres armadilhas, todas
  invisiveis no código e óbvias no pixel):** ao inserir um icone/badge ao lado de um texto que ja
  existia, (1) **`gap` no pai separa TEXT NODES SOLTOS**: `<Icone />Pork<span>folio</span>` sao tres
  itens flex (o text node "Pork" vira item anonimo), entao um `gap` no container parte a palavra ao
  meio - ponha o espacamento como `margin` do proprio icone, nunca como `gap` do pai; (2) **um
  `gap: 0` que ja estava la costuma ser LOAD-BEARING**, neutralizando um `gap` global de
  `button`/`.btn` do design system - apagar por parecer ruido reintroduz o defeito **so em algumas
  telas** (as que usam `<button>`), e a assimetria faz voce declarar vitoria cedo depois de conferir
  a tela errada; deixe-o com comentario dizendo por que fica. (3) **Antes de "consertar" um overflow
  que apareceu, MEÇA quanto dele e seu**: remova seu elemento em runtime (`evalJs`) no mesmo
  carregamento e compare `scrollWidth`. Se o baseline ja estourava, seu dever e **voltar ao baseline**
  (ex.: esconder so o seu elemento no breakpoint apertado), nao redesenhar o header inteiro - e
  documente o residual como pre-existente em vez de assumi-lo silenciosamente. Corolario: teste as
  correcoes candidatas por medicao, nao por intuicao (aqui, "esconder o nome do usuario" nao mudou
  1px porque outra media query ja o escondia, e encolher a fonte nunca chegava a caber).
- **2026-08-01 (revisar uma tela atras de login cujo estado real e caro/perigoso de produzir):** duas
  licoes gerais. **(a) Sirva o BUNDLE PUBLICADO com uma API de fixtures, nao um mock de HTML/CSS.**
  Copiar os tokens para uma pagina de mock parece rapido e envelhece: voce acaba revisando um CSS que
  nao esta no ar. Um servidor local de ~100 linhas que serve o `dist/` real e responde as rotas da API
  com fixtures da o estado que voce precisa (erro, carteira cheia, lista vazia) revisando o codigo que
  o usuario ve. **ARMADILHA que custa uma hora:** a fixture tem que casar com o **formato exato da
  resposta**, chave por chave (`{items, next_cursor}` vs `{rows, has_more}`); com a chave errada o app
  quebra num `TypeError: reading 'filter'` **silencioso** e renderiza o estado VAZIO, que parece
  "os dados nao chegaram" e manda voce depurar rede/auth por muito tempo. Antes de qualquer captura,
  **registre `page.on('pageerror')`** - uma excecao nao capturada e o primeiro sinal, e ela nao aparece
  no console de erros normal. Leia os tipos do cliente (`api.ts`/similar) para montar a fixture, nao
  o handler do servidor. **(b) Identificador que o usuario precisa TRANSCREVER nunca pode quebrar
  linha.** Codigo de incidente/pedido/cupom embutido em prosa quebra no hifen (`PF-` / `K7Q2XM`) e vira
  transcricao errada. Regra: tire-o da frase, de a ele linha propria com rotulo ("Codigo para citar:"),
  `white-space: nowrap` e `user-select: all`. Vale para qualquer string que va parar num e-mail de
  suporte. **▶ Testar:** renderize no viewport mais estreito suportado e confirme que o codigo esta
  numa linha so.
- **2026-08-01 (2ª rodada: confirmacao em varios passos para acao irreversivel):** tres checagens que
  faltavam na rubric. **(a) NUNCA use dois `window.confirm()` seguidos como "confirmacao dupla".**
  Depois do primeiro dialogo nativo o navegador oferece "impedir esta pagina de criar mais dialogos";
  marcado, o SEGUNDO confirm e suprimido e respondido automaticamente, degradando a dupla checagem para
  uma so, justamente na acao mais perigosa. Use um modal do proprio app, que o navegador nao pode
  silenciar. **(b) Verifique QUAL botao recebe o foco no passo final:** o foco padrao tem que estar na
  opcao SEGURA (cancelar/manter), nao na destrutiva; assim quem martela Enter avanca os passos e
  **cancela**, em vez de executar. Meça com `document.activeElement`, nao pelo codigo, porque `autofocus`
  em componente re-renderizado nem sempre pega. **(c) O botao de MAIOR consequencia nao pode ter o
  contraste mais fraco.** E comum o gatilho ganhar um estilo caprichado e o botao final herdar a variante
  `.danger` generica do design system, que costuma ser um vermelho claro (~3:1 com branco) que so passa
  AA como "texto grande" - e botoes de dialogo costumam usar o tamanho pequeno. Meça os DOIS com
  `getComputedStyle` e iguale o tratamento. Corolario geral: ao revisar fluxo destrutivo, **bloqueie o
  endpoint na camada de rede** (`setRequestInterception` + abort) durante toda a review e **conte** os
  requests bloqueados: e a prova de que a review nao disparou nada, e pega o caso em que um passo
  executa a acao antes da hora.
- **2026-08-02 (um numero numa confirmacao destrutiva estava MENTINDO):** um dialogo dizia "isso vende
  1 posicao" para quem tinha 35, porque a lista que alimentava a contagem tem **uma linha por
  GRUPO** (um par/categoria/pasta), nao por item. `lista.length` respondia "quantos grupos", que para
  um grupo so e sempre 1. **Regra durável:** todo numero que aparece numa confirmacao (quantos itens,
  quanto dinheiro, quantos arquivos) tem que ser rastreado ate a fonte e a pergunta que ele responde
  precisa ser dita em voz alta - "isto conta LINHAS DA VIEW ou ITENS DE VERDADE?". Views agregadas
  (uma linha por par/categoria/dia) sao a armadilha classica, e o sintoma e o numero **1 grudado** no
  caso de um grupo so, que passa despercebido porque parece plausivel. Se o backend nao expoe a
  contagem real, ela **nao e derivavel** de somas/quantidades: peca o campo (`COUNT(*) FILTER (...)`),
  nao invente. **▶ Testar:** rode a review com fixtures que tenham **N > 1 por grupo e N = 1 em outro
  grupo** (nunca so 1 em tudo, que e o que esconde o bug) e confira o numero contra a fonte real.
  Corolario de copy: em confirmacao destrutiva, "N itens" sozinho e pouco - diga tambem **quanto** (a
  quantidade/valor) e **o que volta** (o resultado), que sao as perguntas que a pessoa esta realmente
  se fazendo; e elimine `item(s)` / `posicao(oes)`: use frases singular/plural proprias por idioma
  inseridas como sintagma nominal, senao a concordancia quebra em pt/es.
- **2026-08-02 (via um site estático) - `overflowX:true` com `offCanvas` VAZIO aponta para um
  elemento POSICIONADO e invisível, não para o layout.** O sinal de página mais larga que a viewport
  costuma ser lido como "algum bloco estourou", mas quando a varredura de bordas não acha ninguém
  além da margem direita, o culpado quase sempre é um filho `position:absolute` **dentro de um
  scroller horizontal que não é posicionado**. Um absoluto se ancora no ancestral posicionado mais
  próximo; se esse ancestral está FORA do `overflow-x:auto`, o scroller **não o recorta**, e o
  elemento fica na coordenada x rolada (centenas de px) esticando a página inteira. O caso clássico
  é o texto só para leitor de tela (`.sr-only`, que é absoluto por definição) colocado dentro de uma
  célula de tabela larga com rolagem própria: some da tela, não aparece em `offCanvas` (tem 1px) e
  ainda assim é o dono do overflow. **Regra:** todo `overflow-x:auto` que possa conter conteúdo
  absoluto precisa de `position:relative`. **Como achar em 30s:** esconda `section` a `section`
  medindo `document.documentElement.scrollWidth` - a seção que zera o excesso é a sua; dentro dela,
  procure absolutos antes de procurar larguras. Corolário do mesmo caso: no mobile, uma trilha de
  grid escrita como `1fr` é `minmax(AUTO,1fr)`, e o mínimo automático sobe até o **min-content** do
  filho (o `min-width` da tabela dentro do scroller) - use sempre `minmax(0,1fr)` em contêiner que
  empilha, e `min-width:0` no scroller.
- **2026-08-02 (via um site atrás de CDN) - confirme que você está revisando O BUILD QUE ACABOU DE
  SUBIR.** Uma primeira rodada mostrou a página inteira abaixo da dobra em opacidade baixa e parecia
  um bug de CSS grave; era o CDN servindo o JS anterior (`cf-cache-status: HIT`, `age: 152`) porque o
  vhost manda cachear js/css por horas. Revisar um build velho gera achado fantasma e, pior, some com
  o achado real. **Antes de julgar qualquer screenshot de um alvo atrás de CDN/proxy:** compare o
  arquivo servido com o da origem (`curl` na origem com `Host:` contra `curl` na URL pública) ou
  cheque `cf-cache-status`/`age`. **Correção durável, não paliativa:** o deploy deve carimbar as URLs
  dos assets com o **hash do conteúdo** (`/app.js?v=<sha>`), assim a URL muda quando o arquivo muda e
  nunca quando não muda - purgar cache à mão não escala e some com a memória do próximo.
- **2026-08-05 (via um site de projeto) - "ficou com cara de IA" quase nunca se resolve com
  mais capricho; resolve-se com PROCEDÊNCIA.** Um design pode estar bem executado (paleta
  coerente, tipografia pareada, contraste ok) e ainda assim ser rejeitado pelo dono, porque o
  problema não é qualidade, é **origem**: a paleta e as fontes foram inventadas para aquela
  página e não existem em nenhum outro lugar do mundo dele. Regra ao construir qualquer
  superfície nova para alguém que JÁ TEM produto no ar: **antes de escolher uma cor, vá ler os
  tokens do que ele já publicou** (o `:root`/tema do site principal) e reuse-os literalmente,
  incluindo a família tipográfica e a marca do topo. Distinção que vale: inventar identidade é
  o trabalho quando não existe nenhuma; quando existe, inventar é apagar a dele. Corolário de
  revisão: incluir no checklist "esta tela poderia ser de outra pessoa?" e, se puder, apontar
  qual token do produto existente deveria estar ali.
- **2026-08-05 (via um site de projeto) - um tema pedido pelo cliente para de parecer skin
  quando ele pousa numa ESTRUTURA VERDADEIRA do conteúdo.** Pediram temática grega para um
  produto que não tem nada de grego. O que salvou não foi colar colunas e louros: foi notar
  que a lista de tarefas tinha **exatamente doze** itens e virá-la "os doze trabalhos",
  numerada com letras gregas. O ornamento (a grega/meander) entrou como a **régua que separa
  as seções**, ocupando o lugar de um filete que já era necessário, e o tema entrou na
  tipografia (capitais inscricionais) em vez de entrar por imagem. Método: antes de aplicar um
  tema, procure no conteúdo real uma contagem, uma ordem, uma sequência ou uma hierarquia que
  já case com ele; use ornamento apenas onde a página já precisava de um elemento estrutural.
  Se o tema não encontra ancoragem nenhuma no conteúdo, ele vai ler como fantasia por cima.
  Alerta de execução: **ornamento geométrico repetido tem tamanho mínimo de legibilidade** - a
  grega em unidade de 24px lia como pontilhado; só em 40px virou grega. Conferir padrão
  repetido num recorte AMPLIADO, porque no screenshot inteiro ele passa por "uma linha".
- **2026-08-06 (via um site estático com CSP estrita) - `style-src 'self'` bloqueia o ATRIBUTO
  `style=`, não só o bloco `<style>`, e o sintoma é "mal desenhado", não "quebrado".** Um
  gráfico cuja PROPORÇÃO vinha de `style="flex:26"` no HTML renderizou achatado: sem o
  `flex-grow`, os elementos ficaram em `flex: 0 1 auto` e altura `0px`, então a peça apareceu
  como se fosse um erro de altura/alinhamento. Não falta elemento, não há erro de layout, e o
  instinto errado é ir mexer em `height` e `align-items`. Vale para qualquer coisa dirigida
  por estilo inline: largura de barra, `--var` setada por elemento, `background-image` de
  thumbnail, `transform` de posicionamento. **Como diagnosticar em segundos:** meça o elemento
  VIVO (`getComputedStyle(el).flex` / `.height`) e compare com o que o HTML pede - um
  `0 1 auto` num elemento que tem `style="flex:26"` só pode ser CSP. O browser também registra
  a violação no console, então trate `consoleErrors` como pista de LAYOUT, não só de runtime.
  **Correção certa:** mover os valores para o stylesheet (classe por variante, ou uma custom
  property definida em regra); **não** adicionar `'unsafe-inline'` em `style-src` por causa de
  um punhado de números fixos, porque isso troca uma proteção real por conveniência. Regra
  preventiva ao construir sob CSP estrita: **zero atributo `style=` no HTML**, e conferir com
  um grep antes de publicar.
- **2026-08-08 (via um hub de dados de jogo) - `replaceChildren(null)` NÃO ignora o null: vira o
  TEXTO "null" na página; e a faixa de chips "cheia" não avisa quando o novo chip nasce cortado.**
  Dois aprendizados de uma rodada. (a) Codebases com um helper `el()` que filtra filhos nulos
  criam o hábito de escrever `cond ? el(...) : null` - seguro DENTRO do helper, mas passado
  DIRETO a `replaceChildren`/`append` o null é stringificado como "null" (a spec converte não-Node
  em DOMString). O bug só aparece no estado de dado que zera o opcional, então capture também o
  estado em que cada bloco condicional está VAZIO; grep rápido: `replaceChildren(` com argumento
  ternário terminando em `: null`. (b) Ao ADICIONAR um item a uma linha/faixa que já existia
  (chips, ticker, toolbar), meça `scrollWidth - clientWidth` do container ANTES e DEPOIS nos
  breakpoints de desktop: uma faixa `overflow-x:auto` com scrollbar oculta engole o item novo
  sem nenhum sinal visual (nem overflow de página, nem offCanvas - o corte fica DENTRO do
  scroller), e no desktop não há swipe para descobrir o resto. Se o item novo é interativo,
  confira também a ALTURA do alvo: numa faixa fina de texto (~20px), o primeiro elemento
  clicável da faixa nasce abaixo do mínimo de 24px - `padding` vertical + `margin` negativa
  dão área de toque sem mudar o layout.
- **2026-08-08 (consertar overflow horizontal sem criar outro):** tres licoes. **(a) Controles nativos
  com mascara (`input[type=date]`, `time`, `color`, `number` com spinner) tem largura intrinseca que
  NAO encolhe.** Uma linha com rotulo + dois deles vira um bloco rigido de ~330px que empurra a pagina
  inteira no telefone, e o sintoma engana: a largura medida do bloco e IDENTICA em 320px e em 1280px.
  Se ao medir um elemento a largura nao muda entre viewports, ele nao esta participando do layout
  responsivo - e um bloco rigido, nao um bloco que "por acaso coube". **(b) Ligar reflow
  (`flex-wrap`, `flex-grow`) em TODAS as larguras conserta a estreita e quebra a larga:** aqui o
  `flex-wrap` sem media query fez o botao de limpar cair sozinho numa segunda linha no desktop, porque
  o container passou a assentar numa largura onde ele nao cabia mais. Reflow de emergencia mora dentro
  do `@media`, e depois de aplicar **re-meça a larga**, nao so a estreita. **(c) Para empilhar dois
  controles com larguras IGUAIS, flex-wrap nao serve** (ele distribui pelo flex-basis e deixa o
  separador orfao no fim da primeira linha, com os campos de tamanhos diferentes); um grid de duas
  colunas (`1fr auto`) com o rotulo em `grid-column: 1 / -1` da larguras identicas e uma coluna
  reservada para o botao acessorio. Ao esconder um separador visual ("-", "/", "ate") no empilhado,
  confirme que cada campo ja tem `aria-label` proprio, senao o sentido de intervalo some para leitor
  de tela. **▶ Metodo que fecha:** antes de atribuir QUALQUER overflow a sua mudanca, builde o commit
  anterior e rode **a mesma sonda** - aqui, dois dos tres "achados" (header a 320px, rodape rigido a
  601-767px, ritmo vertical desigual) eram identicos no baseline, e so a comparacao provou isso.

- **2026-08-09 (via jogo canvas):** (a) **Lista rolável dentro de painel/modal precisa de
  affordance nas DUAS pontas** - fade de borda + chevron que somem no extremo alcançado; o teste que
  pega é perguntar "o último item visível parece o último item que existe?" quando o viewport corta
  exatamente num limite de linha, o estado mais enganoso (o corte no MEIO de uma linha é o acaso
  avisando; o corte limpo é silêncio total). Em engine canvas (Phaser), gradient de Graphics não
  renderiza no renderer Canvas: o fade portável é pilha de retângulos com alpha decrescente.
  (b) **WheelEvent sintético sem clientX/clientY não rola app canvas** - o hit-test da engine usa a
  posição do pointer, e o default (0,0) cai fora do alvo; dispatch de mousemove + wheel com coords
  centradas no elemento. Vale para qualquer sonda headless de scroll em canvas.
  (c) **Captura de jogo/canvas: navegar com `networkidle` trava** (o loop de render mantém a página
  "ocupada" ou simplesmente nunca há idle): usar `--wait-until load` + wait fixo.

- **2026-08-11 (via um portfolio SPA) - remover um CSS framework remove tambem o RESET dele; e o
  grep de seletor que engana.** (a) **Ao retirar um framework de UI (Vuetify/Bootstrap/preflight do
  Tailwind e afins), o base reset que ele injetava (body{margin:0}, box-sizing, background) sai
  junto** - o browser volta ao default `body{margin:8px}` + fundo branco e o app "dark" ganha uma
  moldura branca em TODA pagina, visivel em qualquer viewport. O defeito nasce no commit da remocao
  e sobrevive semanas porque as reviews olham componentes, nao a moldura do documento. Check barato
  pos-remocao (e em qualquer review): confirmar no CSS BUILDADO que existe um reset de `body` (grep
  por `[^.\w-]body\{` deve achar margin/background), e provar por computed style
  (`getComputedStyle(document.body).margin === '0px'`, `bodyRect.width === innerWidth`), nao so pelo
  PNG - margem de body NAO dispara overflowX/scrollWidth, os sinais automaticos ficam limpos.
  (b) **Armadilha de diagnostico: `grep -oE '(html|body)[^{]*\{'` casa o RABO de seletores de
  classe** - `.bp .card .body{...}` "vira" `body{...}` no output e induz a corrigir um vazamento de
  seletor que nao existe. Ancore o padrao a um nao-word (`[^.\w-]body\{`) ou cheque o contexto antes
  de concluir; a distancia entre "o grep mostrou body{" e "existe uma regra bare body" derruba um
  diagnostico inteiro.

- **2026-08-11 (via um site de dados de jogo) - UNIDADE AUSENTE num card de número é bug de
  CONTEÚDO que nenhum sinal automático pega; e plural de unidade de tempo precisa da regra do
  idioma, não de uma string só.** (a) Numa grade de cards de valor (preço, custo, duração), basta
  UM card omitir a unidade para o leitor herdar a do vizinho: "225 **platina**" ao lado de
  "15.000" faz o segundo ser lido como platina também. O defeito é invisível para overflow/contraste/
  tap-target e sobrevive à review visual porque o card "parece certo" - o check que pega é **ler a
  grade inteira em voz alta e perguntar "unidade de quê?" em cada célula**, e desconfiar sempre que
  cards irmãos tiverem formatos diferentes (um com sufixo, outro sem). Vale também para o inverso:
  reusar um rótulo de card (MAIÚSCULA, `letter-spacing`) dentro de uma frase inline traz a
  capitalização junto e denuncia o reuso ("15.000 Créditos" no meio de uma linha). Tenha, no
  dicionário, a forma **rótulo** e a forma **inline** de cada moeda/unidade. (b) Ao formatar
  duração/contagem, `${n} ${t('unit.days')}` produz "1 dias" em qualquer língua latina e erra feio
  em línguas com mais de duas formas (russo: 1 день / 2-4 дня / 5+ дней, com as exceções de 11-14).
  Se o produto suporta idioma eslavo, a chave tem que ser **one/few/many** com a regra por idioma -
  e o caso de teste que revela é o valor **1** (que quase nunca aparece nos dados de exemplo) e um
  valor terminado em 2-4. Sintoma para grep numa review: template literal com número seguido de uma
  única chave de unidade.

- **2026-08-14 (via um site multi-idioma) - IDIOMA NOVO COM OUTRA ESCRITA (CJK, árabe, devanágari)
  não é "trocar as strings": é revisar TIPOGRAFIA, e o defeito que sobra é PÁGINA MEIO TRADUZIDA.**
  Checklist que passou a valer sempre que entrar uma escrita não-latina: **(a) `letter-spacing` da
  identidade vira lixo** - rótulo com 0.15-0.25em é elegante em caixa alta latina e em CJK espalha
  ideogramas que já são palavras inteiras (override para ~0.04em); **(b) entrelinha** - o ideograma
  preenche a caixa toda, sem ascendente/descendente, então a entrelinha do latino faz as linhas
  encostarem (1.7-1.9); **(c) piso de tamanho** - 11px é legível em latino e vira borrão num glifo de
  20+ traços (mínimo ~13px); **(d) peso** - fonte CJK de sistema costuma não ter 700 real e o
  navegador SINTETIZA o negrito, empastelando os traços (teto 600); **(e) `lang` correto no `<html>`**
  - `zh-CN` vs `ja` mudam o GLIFO desenhado (mesma faixa Unicode, formas diferentes), então lang errado
  não é detalhe de a11y, é texto com cara errada; **(f) a webfont própria não tem os glifos** - a
  pilha precisa do fallback de SISTEMA por plataforma (webfont CJK tem megabytes), e o fallback é por
  CARACTERE, então latino continua na fonte da marca. **(g) O achado que só a review pega:** com o
  layout inteiro certo, o que fica errado é **meia tradução** - nome do item traduzido e a lista de
  ingredientes, o selo de tipo e as unidades ainda no idioma original, **muitas vezes com a tradução
  disponível no próprio dado**, só não usada. Método: leia a tela inteira como se não soubesse o
  idioma de origem e marque TODA palavra que ficou nele; depois cheque, uma a uma, se o dado já tem
  a versão traduzida. **(h) Ao revisar num servidor Linux, confira antes `fc-list :lang=<x>`**: sem
  fonte da escrita instalada o headless mostra caixas vazias ou cai numa fonte bitmap, e você
  julga acabamento de uma coisa que o usuário nunca vai ver (o layout ainda vale; o acabamento não).

- **2026-08-14 (via um site multi-idioma, complemento da lição do mesmo dia) - antes de aceitar
  "isso não tem tradução", PROVE com uma 2ª fonte; e a prova certa quase nunca é o dataset que você
  já está usando.** Ao revisar a página no idioma novo, sobraram palavras na língua original e eu
  concluí, olhando SÓ o dataset que alimenta o site, que "não existe tradução para isso". O dono
  desconfiou. A checagem correta foi: **(1) medir por CATEGORIA, não no total** - o agregado dizia
  "98% traduzido" e escondia que uma categoria inteira estava 98% NÃO traduzida; **(2) buscar uma
  fonte independente que reflita o uso REAL** - aqui foi o marketplace onde os usuários daquele país
  negociam, que expõe nome por locale e cruza pelo id do jogo. As duas fontes concordaram, então a
  ausência era legítima (nome próprio) e não buraco. **Mas a mesma checagem revelou um buraco de
  verdade que a leitura da tela não tinha achado**: outra camada (os nomes de LUGAR) estava 100% na
  língua original porque a tabela de tradução só tinha a coluna do idioma antigo. **Checklist:** ao
  julgar cobertura de tradução, (a) meça por categoria e ordene pela pior; (b) confirme "não tem
  tradução" numa fonte de USO, não só na fonte de dados; (c) liste as CAMADAS de texto separadamente
  (rótulo de UI, nome de entidade, nome de lugar, prosa gerada, conteúdo escrito à mão) - cada uma
  costuma ter dono e cobertura diferentes, e a que ninguém lembra é a de LUGAR/UNIDADE.
- **2026-08-14 (via um comparador web - revisar o POPUP/action de uma extensao de navegador):** O
  motor de captura por grade de rotas NAO alcanca a UI de uma extensao (popup, options): ela mora em
  `chrome-extension://<id>/popup.html`, e o `<id>` so existe com a extensao carregada. Para revisar:
  suba um puppeteer com `--disable-extensions-except=<dir> --load-extension=<dir>`, pegue o `<id>` pelo
  **target do service worker** (`browser.waitForTarget(t => t.type()==='service_worker')`, o host da URL
  e o id), e navegue para `chrome-extension://<id>/popup.html` no **tamanho real do popup** (tipicamente
  ~300px de largura; nao um viewport de pagina). Criterios especificos de popup: largura fixa pequena
  sem overflow, hierarquia acao-primaria vs secundaria (o botao que faz o trabalho e o pesado; "so
  abrir" e outline), tap targets >= 24px mesmo no espaco apertado, `autofocus` no campo, e - armadilha
  de MV3 - o CSP de pagina de extensao **bloqueia script inline**: o JS TEM que ser arquivo externo
  (`<script type="module" src>`), handler inline (`onclick=`) nao roda; confirme 0 erro de console (um
  CSP violation aparece la). Estilo num `<style>`/atributo e permitido. Capture com a extensao carregada
  de verdade, nunca so o HTML solto num file://, senao os `chrome.*` e o CSP real nao valem.

- **2026-08-14 (via um site multi-idioma, 3ª rodada do mesmo caso) - ★ AUDITORIA DE TRADUÇÃO SE FAZ
  POR SCRIPT, NÃO PELO OLHO. Cole isto no console da página no idioma novo:**
  ```js
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode())
    if (/[A-Za-z]{2,}/.test(n.textContent)) console.log(n.textContent.trim());
  ```
  (troque a classe de caracteres pelo alfabeto de ORIGEM; some as ocorrências por palavra e ordene
  por frequência). Eu revisei a mesma página por screenshot **duas vezes**, declarei "0 P0/P1", e o
  dono ainda achou coisa em inglês nos prints. Na terceira rodada o script achou em 5 segundos tudo
  que o olho perdeu: selo de tipo vindo cru do dataset, um cabeçalho de tabela **escrito na mão** no
  código (aparecia em inglês nos 5 idiomas, mesmo com a chave existindo no dicionário), o tier de uma
  entidade, nomes de peça, dois rótulos **concatenados direto na string** (`${x} · Steel Path`) e uma
  abreviação de unidade. Por que o olho falha: numa tela cheia de escrita não-latina, as palavras
  latinas parecem "nome próprio" e o cérebro as aceita. **Regras que saem disso:** (1) a saída do
  script é uma lista de PALAVRAS - classifique cada uma em `nome próprio / marca / URL / BUG`, e o
  que sobrar em BUG é a lista de trabalho; (2) o padrão mais escondido é **literal concatenado em
  template string** (`${a} · Steel Path`), que nenhum grep por `text: '...'` acha - procure também
  por texto solto dentro de crase; (3) rode o script DE NOVO depois de corrigir, e pare quando só
  restar nome próprio/marca/URL; (4) **confirme a tradução dos termos de domínio contra a fonte
  oficial, não de memória** - duas das minhas estavam erradas (usei um sinônimo plausível para um
  termo que o produto nomeia oficialmente de outro jeito), e um teste que proíbe o termo errado no
  código impede a volta.
- **2026-08-14 (via um comparador web - tornar um BADGE/PILL/CHIP clicavel: o tap target e a caixa do
  `<a>`, nao a do pill):** Ao transformar um chip/badge/pill de status em link (ex.: o chip
  "nao instalado" que passa a linkar a loja da extensao), o sinal `tinyTargets` mede a caixa do
  **`<a>` interno**, nao a do pill que o envolve. Dar `min-height:24px` so ao `.chip`/pill NAO
  resolve - o link fica ~16-19px (a altura da linha de texto) dentro de um pill de 24px. Fix: o
  **proprio `<a>`** precisa de `display:inline-flex; align-items:center; min-height:24px` para
  preencher; de o pill uns 2px a mais (`min-height:26px`) para o link caber com folga. Verifique
  re-medindo o `tinyTargets` depois - o instinto de "aumentei o container, ta resolvido" e falso.
- **2026-08-15 (via um site de guias) - `white-space:nowrap` em `th` quebra primeiro no CABEÇALHO,
  e o scroller esconde o corte:** ao estilizar tabela gerada de markdown (sem wrapper possível,
  padrão `table{display:block;overflow-x:auto}`), o rótulo de cabeçalho é quase sempre mais longo
  que o dado da coluna ("Meta de pontos" vs "50") - com `nowrap` no `th`, a última coluna sai do
  campo de visão no viewport estreito lendo cortada no meio da palavra, SEM sinal de overflow de
  página (o scroll é in-container, `overflowX:false`, zero offCanvas). Regra: quando o DADO já cabe
  no mobile, o cabeçalho não pode ser o motivo do scroll - deixe o `th` quebrar linha
  (`vertical-align:bottom` para alinhar as linhas de baixo) e/ou encurte o rótulo, deixando a
  explicação para a prosa ao redor. Teste toda tabela nova no viewport mais estreito olhando o
  CABEÇALHO, não só as células.

- **2026-08-15 (via um comparador - botao pequeno que HERDA o tamanho de um "chip" informativo):**
  ao adicionar um CONTROLE (botao/link clicavel) ao lado de um elemento so-informativo (chip de
  status, badge, pill) e reusar a mesma classe/altura por consistencia visual, cuidado: o chip pode
  ter 24-26px de altura (ok, ninguem clica), mas um botao real precisa de alvo de toque >=44px no
  mobile. A solucao que preserva o visual: manter a altura do chip no DESKTOP (onde ficam lado a
  lado e o alinhamento importa) e so BUMPAR o botao no mobile via media query (onde o header quebra e
  o botao cai em linha propria, entao um alvo maior nao desalinha nada). Checar: todo novo `<button>`/
  `<a>` clicavel que copia o estilo de um chip/badge tem `min-height>=40px` no viewport de telefone.
