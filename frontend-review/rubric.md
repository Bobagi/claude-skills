# frontend-review — rubric (the growing checklist)

This file IS the skill's expertise. It is **project-agnostic**: never put a specific
project's facts here. Each run applies it; the self-improvement step appends *general*
lessons to the **Learnings log** at the bottom so the reviewer gets sharper over time.

## Severity scale (tag every finding)
- **P0 Blocker** — broken/unusable: content cut off, horizontal scroll on mobile, overlap, illegible.
- **P1 High** — clearly wrong, most users notice: misaligned blocks, inconsistent padding on a key surface, target too small to tap.
- **P2 Medium** — off but tolerable: slightly uneven spacing, weak hierarchy, minor responsive awkwardness.
- **P3 Low / Nit** — polish: 1–2px nudges, optional contrast bump, wording.

Every finding must carry: **what** (the problem), **where** (route + viewport + screenshot file, and/or `file:line`), **why it reads wrong**, **fix** (concrete, in tokens not pixels when the project has a scale).

---

## Pillar 1 — Visual (judged from the screenshots)

### Spacing & padding
- [ ] Padding inside cards/buttons/inputs is **consistent** across like components (same component → same insets).
- [ ] Outer gaps between sections follow one rhythm (multiples of the spacing unit), not arbitrary values.
- [ ] No element is **glued** to a container edge (text/controls touching the border) or to the viewport edge.
- [ ] Symmetric padding where symmetry is implied (left≈right, top≈bottom) unless intentionally directional.
- [ ] Whitespace is **balanced** — not one cramped region next to one empty region.
- [ ] Gap between a label and its field, and between stacked fields, is uniform.
- [ ] **Vertical rhythm between stacked blocks is even** — header→first child, child→child, and
  button→list should read as one consistent step, not alternating big/tiny. The usual culprit is
  **margin stacking/collapse between a component and its neighbor**, not a single wrong value: a child
  that carries its own `margin-top` placed right after a header with `margin-bottom` yields an oversized
  (collapsed-to-the-larger) gap; an element with `margin:0` (e.g. a reset `<p>`) right after another reads
  as *glued* (zero gap). Own the gap in ONE place and match one rhythm — don't let two margins fight.

### Alignment & rhythm
- [ ] Shared left edge: labels, inputs, headings, and body in a column line up to one grid.
- [ ] Related items align to each other; numbers/currency right-align in tables.
- [ ] Icon + text pairs are vertically centered on the same baseline/optical center.
- [ ] Equal-height cards in a row; buttons in a row share height and baseline.

### Responsiveness (compare across viewports)
- [ ] **No horizontal scroll** at any width (the `H-OVERFLOW` / `offcanvas` signals are P0/P1).
- [ ] **Flex/inline rows wrap or reflow on mobile** — a `display:flex` row of chips/badges/labels with no
  `flex-wrap` and fixed/intrinsic-width children **overflows its container instead of growing vertically**
  (the classic "row shoots past its card" on phones). Each such row must `flex-wrap:wrap` (grow down a
  line) or restructure; a `flex:1` spacer that pushes items apart on desktop should be hidden on mobile so
  wrapped items don't leave a dead gap.
- [ ] **A reflowed row is distributed, not just un-broken.** Stopping the overflow is the floor, not the
  goal: when a row wraps onto 2 lines on mobile, judge the *distribution* — left-bunched items with dead
  space on the right read as unfinished. Prefer a deliberate layout (e.g. a 3-zone `grid` start/center/end:
  badge left, title centered, meta right; secondary line left/right) so it stays balanced and attractive.
- [ ] Multi-column layouts collapse cleanly to one column on mobile (no squished columns).
- [ ] Tables: scroll inside their own container or reflow — never push the page wide.
- [ ] Touch targets ≥ 24px (ideally 44px) on mobile; controls don't crowd.
- [ ] Nothing overlaps after reflow; sticky headers don't cover content.
- [ ] Type and spacing scale down sensibly — desktop spacing shouldn't look huge on mobile, or mobile spacing cramped on desktop.
- [ ] Images/media keep aspect ratio; no stretch/squash; avatars stay circular.

### Typography
- [ ] Clear hierarchy (size/weight/color distinguish H1 > H2 > body > caption).
- [ ] Line length ≈ 45–90 chars on desktop; line-height comfortable (~1.4–1.6 body).
- [ ] No clipped/truncated text without an ellipsis; no orphaned single words where it matters.
- [ ] Consistent font family/weights; numerals align in tabular contexts.

### Color, contrast & theme
- [ ] Body text vs background ≥ 4.5:1; large text/UI ≥ 3:1 (judge the dim/muted text especially).
- [ ] Brand palette applied consistently; no stray off-palette colors.
- [ ] Disabled/placeholder states are distinguishable but still legible.
- [ ] Focus states visible (not removed); hover/active states present on interactive elements.

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
  Do NOT clear this by observing that "right now they show different values" — values can coincide or diverge
  by chance; ask whether they are the *same underlying thing by design*. (Real case: two day/night clocks,
  "Cetus" and "Earth", that the game syncs 1:1 — obvious once merged, invisible while a data bug made them
  show different states.) Conversely, don't merge items that only *happen* to match now but are distinct
  concepts (e.g. a "Fass/Vome" clock that shares a duration but not the same cycle).
- [ ] **A surface with few items shouldn't bunch to one side** — distribute across the width
  (`justify-content: space-between/around`) or center, so freed space is used, not left as a dead gap.

---

## Pillar 2 — Front-end code

- [ ] Spacing/sizing use **design tokens / CSS variables**, not scattered magic px (flag repeated literals that should be a token).
- [ ] Responsive units where appropriate (rem/%, `clamp()`, `min/max`); avoid fixed px widths that cause overflow.
- [ ] Breakpoints are consistent (a shared set), not ad-hoc per component.
- [ ] **Verify responsiveness in the code, not only screenshots.** Grep every `display:flex` / `display:grid`
  row that holds multiple inline items and confirm it can reflow (`flex-wrap`, `min-width:0`, or a mobile
  media query) — a no-wrap flex row with intrinsic/fixed-width children **will** overflow on narrow screens
  even when today's data happens to fit. Flag fixed `width`/`min-width` px on content that must fit a phone.
- [ ] **A horizontal scroller inflates its ancestors unless they are capped.** `overflow-x:auto` on a
  rail does NOT stop its min-content propagating up through an `overflow:visible` parent — the
  grandparent's implicit `auto` grid track grows to the rail's full content width and the WHOLE page
  goes wider than the viewport. Give stacking containers `grid-template-columns: minmax(0, 1fr)` and
  the scroller's wrapper `min-width: 0`. Prefer `justify-content: safe center` over `center` on any
  row that can overflow (plain `center` puts the first item where scrolling cannot reach it).
- [ ] **No undefined CSS custom properties.** Grep every `var(--x)` reference and diff against the
  tokens defined in `:root`. An undefined token **with no fallback** renders the wrong value silently
  (e.g. `var(--text-muted)` when the token is `--muted` → text shows full-bright, not muted — a real
  bug screenshots barely reveal); one **with a fallback** still bypasses the design system (off-palette).
  Exception: runtime-set vars (e.g. a `--topbar-h` set via JS with a sensible fallback) are legitimate.
- [ ] **Variant styles on a self-nestable component use a scoped/direct-child combinator, not a bare
  descendant.** A reusable component with variants (e.g. `<Collapsible variant="section|help">`) that can
  contain **another instance of itself** will leak: a rule like `.section .cl-title{font-size:lg}` matches
  the title of a nested *help* instance too (same component scope, descendant combinator), silently
  mis-sizing it — so "the same element" looks different in one place than another. Same trap whenever two
  variants share a child class name. Grep every descendant-combinator selector (`.a .b`) whose right-hand
  class also appears on a nested child; prefer `.a > summary > .b` / `:scope >` / a variant-specific class
  so the rule can't cascade into a nested instance. This is a top cause of "this element isn't configured
  like its twin" inconsistencies — verify suspect twins by rendering them adjacent (a faithful mock if auth-gated).
- [ ] No duplicated style blocks that should be a shared class/component; component reuse over copy-paste.
- [ ] No dead CSS / unused classes; no `!important` wars.
- [ ] Layout uses fl/grid intentionally; avoid absolute positioning for flow content.
- [ ] Conditional rendering covers loading/empty/error, not just data-present.
- [ ] Strings are in the i18n layer, not hardcoded (when the project is localized) — check **every** language dict has the key.
- [ ] Images have width/height or aspect-ratio to avoid CLS; lazy-load below the fold.

## Pillar 3 — UX / a11y / consistency

- [ ] Semantic HTML (`button` for actions, `a` for navigation, headings in order, `nav/main/header`).
- [ ] Every control has an accessible name (the `unnamed`/`unlabeledInputs` signals); inputs have associated labels.
- [ ] Keyboard: everything reachable and operable; visible focus ring; logical tab order; Esc closes modals; focus trapped in modals.
- [ ] Images informative→`alt`, decorative→empty alt/`aria-hidden` (the `alt` signal).
- [ ] **Don't put `tabindex="0"` on a non-interactive element** (a scroll container, a plain `<div>`
  text region). It fails the lint (`a11y-no-noninteractive-tabindex`) and adds a confusing tab stop —
  the content is already in the accessibility tree for screen readers, and the real controls
  (buttons/inputs) remain focusable. For a long scrollable text region (e.g. a Terms block in a
  fixed-height scroller) use `role="region"` + `aria-label` to name it as a landmark, **without** tabindex.
- [ ] Color is not the only signal (icons/text accompany color for status).
- [ ] Forms: labels, helpful errors tied to fields, no destructive action without confirm/undo.
- [ ] Consistency: the same concept looks/behaves the same everywhere (sub-tab placement, button styles, card widths, table patterns).
- [ ] Internationalization renders correctly per locale (flags/text), no untranslated fallbacks leaking.
- [ ] Reduced-motion respected; no essential info conveyed only by animation.

## Reading the automated signals (`manifest.json`)
Each shot carries `signals`: `overflowX` (document wider than viewport — the **real** page-overflow
flag) and `offCanvas` (elements past the right edge, now filtered to exclude children of an
`overflow-x:auto/scroll` ancestor so wide tables/carousels don't false-positive) → responsiveness;
`missingAlt`, `unnamedControls`, `unlabeledInputs` → a11y; `tinyTargets` → mobile tap size;
`consoleErrors` → runtime/code issue. **`overflowX:false` with a high `offCanvas` count = an
in-container horizontal scroller** (e.g. a wide data table that side-scrolls inside its card): not a
layout break, but flag as a *mobile UX* issue if it hides key info/actions. Treat all signals as
**leads to verify on the screenshot**, not auto-verdicts.

Capture tips baked into `scripts/capture.mjs`: pass `--fold true` (default) for an above-the-fold
viewport shot (`*__fold.png`) — full-page mobile shots downscale too far to judge tight padding; pass
`--scale 2` for a crisp 2× shot when eyeballing spacing. For tabs/modals/empty states that need a
click, drive them separately for now (interaction steps are a planned engine feature — see log).

---

## Learnings log (append-only; this is how the reviewer improves)

- **2026-07-23 (via todo — CRITIQUE O ESTADO OCIOSO, e não esconda ícone com opacity:0):** Duas
  lições que se reforçam. (1) **Capture e critique o estado DEFAULT/ocioso de todo componente novo,
  não só o happy path.** Uma rodada anterior validou um checkbox e um dropdown só em cenários que já
  forçavam seleção/abertura — e deixou passar (a) um ✓ que aparecia SEM seleção e (b) um gatilho de
  dropdown com borda quase invisível. Ambos os defeitos só existem no estado ocioso (nada
  selecionado / fechado). Ao revisar um controle com estados, capture SEMPRE: vazio/ocioso, hover,
  aberto, ativo/selecionado — o primeiro é o mais fácil de esquecer e o que o usuário vê primeiro.
  (2) **Não esconda um ícone/glyph com `opacity:0` e revele com uma classe — RENDERIZE-O
  condicionalmente.** Um `<i>` de ícone-fonte (Phosphor/FontAwesome) com `opacity:0` **ainda é
  pintado por alguns browsers mobile** (visto no Chrome do Galaxy S24): o check "escondido" aparecia
  fraco em toda linha. Fix robusto: só inserir o elemento no DOM quando ativo
  (`selected ? e("i",{className:"check"}) : null`), de modo que o estado inativo não tenha glyph
  algum — imune a qualquer diferença de repaint/opacity entre engines. Vale para qualquer overlay de
  estado (badge, check, spinner) sobre um controle. (3) Consistência: um controle novo colocado ao
  lado de uma família existente (aqui um dropdown ao lado de 4 `.iconbtn`) deve REUSAR a mesma
  linguagem visual (mesma borda/raio/altura) — uma pílula de borda fraca ao lado de quadrados de
  borda clara lê como "quebrado", mesmo tecnicamente tendo borda.
- **2026-07-23 (via todo — o controle que gerencia uma faixa rolável NÃO pode morar dentro dela):**
  Quando uma coleção é exibida numa **faixa com `overflow-x:auto`** (abas, chips de filtro, pills de
  categoria), o botão que **gerencia** essa coleção (⚙ "Gerenciar", "+ Novo", "Editar") não pode ser o
  último item da faixa: ele sai do campo de visão **exatamente quando a coleção fica grande**, que é
  quando o usuário precisa dele — e se aquela for a ÚNICA porta para criar/renomear/apagar, a
  funcionalidade vira inalcançável sem que nada pareça quebrado (screenshot sem overflow, sinal
  `overflowX:false`, zero erro de console). Regra: **o controle de gestão fica FORA do container que
  rola** (barra de ferramentas, header, ou canto fixo). Checar sempre: para cada faixa rolável, onde
  está a ação que a administra? Corolário de a11y/descoberta: um item cortado na borda direita sem
  gradiente/fade não comunica "há mais" — se a faixa precisa rolar, dê a affordance.
- **2026-07-23 (via todo — dois pegadinhas de método):** (1) **`.btn { width: 100% }` como regra
  BASE** (comum em apps mobile-first) transforma qualquer botão colocado numa linha flex em um item
  que estica e **espreme os irmãos** — no caso, um "Clear" empurrou o contador "3 selected" para duas
  linhas. Antes de compor uma toolbar/linha flex, **leia a regra base de `button`/`.btn` do projeto** e
  neutralize com `width:auto; flex:0 0 auto` no modificador. (2) **App servida de dentro de uma imagem
  Docker (`COPY . .`) NÃO reflete edições do fonte até o rebuild** — rodei uma rodada inteira de
  captura contra o container velho e "corrigi" achados que continuavam na tela. Antes de confiar nos
  screenshots, **prove que o asset servido contém sua mudança** (`curl -s <base>/js/app/x.js | grep
  <trecho novo>`); se o projeto tem bind-mount de dev, use-o. Vale para qualquer front atrás de
  build/bundle/CDN com cache.
- **2026-07-23 (via cartomania — o landing que é um FORMULÁRIO de login, e 3 armadilhas de layout):**
  **(a) Julgamento de PRODUTO antes do visual.** Numa landing de produto/jogo, a primeira pergunta
  não é "o padding está certo?" e sim **"o visitante vê o PRODUTO ou vê um formulário?"**. Caso real:
  a home de um card game passava em todos os checks visuais (0 overflow, contraste ok, foco ok) e
  ainda assim falhava no objetivo do dono ("quero que dê vontade de jogar") — o objeto mais pesado da
  tela era um campo de senha, a melhor arte do projeto (o tabuleiro de duelo) não aparecia em lugar
  nenhum, e a página acabava no fold. Checklist novo para qualquer landing: (1) o que a tela mostra do
  produto EM SI? (2) a **hierarquia de CTA está certa PARA QUEM CHEGA** — um visitante novo não tem
  conta, então "Log in" gigante dourado + "Criar conta" fantasma minúsculo é hierarquia INVERTIDA;
  (3) existe conteúdo ABAIXO do fold que dá motivo para acreditar (como funciona, prova, coleção), ou
  a página é só herói + rodapé? Um site pode passar em todo o Pilar 1 e falhar como produto.
  **(b) BUG CLASS — a faixa rolável INFLA o container que a contém.** Um `overflow-x:auto` no rail
  **não** impede que o min-content dele suba pela árvore quando há um pai intermediário
  `overflow:visible`: o track implícito `auto` do grid avô cresce até a largura TOTAL do conteúdo do
  rail (medido: 1318px dentro de uma caixa de 1120px) e **TODAS as seções da página** passam a ser
  mais largas que a viewport — scrollbar horizontal no documento inteiro, em todos os viewports.
  Regra: todo container que empilha seções precisa de **`grid-template-columns: minmax(0, 1fr)`** e o
  wrapper de qualquer scroller horizontal precisa de **`min-width: 0`**. Isso NÃO aparece como
  "elemento X estourou" — aparece como a página inteira larga demais, o que confunde o diagnóstico.
  **(c) `justify-content: center` numa flex row que ESTOURA torna o primeiro item inalcançável** —
  o conteúdo transborda para os DOIS lados e não há scroll negativo. Use **`justify-content: safe
  center`** (centraliza quando cabe, cai para flex-start quando não cabe). Sintoma: "o primeiro card
  aparece cortado pela metade e não dá para rolar até ele".
  **(d) Porcentagem em elemento `position:absolute` pode resolver contra caixa inesperada** —
  `width: min(430px, 92%)` renderizou **424px dentro de uma caixa de 350px** só no mobile (17px de
  overflow de página). Não confie na conta mental do containing block: **meça**, e blinde com
  `max-width: 100%` + `overflow-x: clip` no pai (`clip`, não `hidden`: não cria scroll container e
  não corta a sombra/brilho vertical).
  **MÉTODO que pegou os três (e que a screenshot NÃO pegaria):** um probe puppeteer que imprime
  `getBoundingClientRect()` + `scrollWidth`/`clientWidth` de cada ancestral suspeito e compara
  `documentElement.scrollWidth` com `clientWidth`. Depois de CADA correção, re-meça — não olhe o PNG.
- **2026-07-23b (via cartomania — barra fixa inferior precisa RESERVAR o próprio espaço):** uma barra
  `position:fixed` no rodapé (consentimento, notificação, "instale o app") **cobre permanentemente** o
  que estiver no fim da página se a página não tiver altura sobrando — no caso real ela escondia o
  card de login INTEIRO no mobile e nenhuma rolagem liberava. Padrão correto: renderizar um **spacer
  no fluxo** junto com a barra, com altura **medida** (`bind:clientHeight` / ResizeObserver) e
  fallback em CSS responsivo para SSR/primeiro paint (a barra quebra em mais linhas conforme estreita,
  então uma altura fixa única erra). **Teste objetivo, não visual:** rolar até o fim
  (`scrollTo(0, scrollHeight)`) e afirmar que `últimoConteúdo.getBoundingClientRect().bottom <=
  barra.getBoundingClientRect().top` em cada viewport. NÃO teste com `scrollIntoView({block:'center'})`
  — centralizar o elemento na viewport faz qualquer barra inferior "sobrepor" e dá falso positivo
  (errei isso primeiro). Vale para qualquer overlay fixo em borda.
- **2026-07-23c (via cartomania — imagem `loading="lazy"` mente no screenshot full-page):** cards/
  imagens abaixo do fold com `loading="lazy"` saem **em branco** no screenshot `fullPage` do puppeteer
  (o viewport nunca "passa" por elas de verdade) — parece feature quebrada, não é. É primo da lição de
  2026-07-19 (scroll-reveal por IntersectionObserver), mas aqui o culpado é o atributo nativo. Antes de
  reportar "a seção X não renderiza", **prove por estado**: `el.scrollIntoView()` + wait + asserção
  `[...imgs].filter(i=>i.naturalWidth>0).length`. Só chame de bug se `naturalWidth===0` com o elemento
  visível. E cheque `consoleErrors` do manifest (0 erros + vazio visual = artefato de carregamento).

> Add a dated, **general** lesson whenever a review surfaces a check worth keeping. Keep it
> project-agnostic. Promote recurring lessons into the checklists above.

- 2026-06-20 — v1 baseline rubric created.
- 2026-06-20 — Engine: `offCanvas` must ignore children inside an `overflow-x:auto/scroll` ancestor;
  otherwise wide data tables/carousels (a legit in-container scroller) spam false positives. Pair the
  signal with `overflowX` to tell a real page-overflow (P0/P1) from an in-container side-scroll (mobile UX).
- 2026-06-20 — A wide multi-column data table that side-scrolls inside its card on phones is usable but
  poor — key columns/actions hide off-screen. Prefer a stacked card-per-row layout below ~600px. Always
  check tables specifically at the narrowest viewport.
- 2026-06-20 — Capture: full-page shots on tall mobile pages downscale too far to judge fine spacing.
  Added `--fold` (above-the-fold viewport shot) and `--scale` (deviceScaleFactor) — use them for padding/
  spacing critique; keep full-page for layout/responsiveness.
- 2026-06-20 — Consistency check to keep: a global `button{}` that paints every button as the primary
  style forces resets on every non-primary button (brand/menu/icon) and breeds regressions. Flag it;
  recommend a neutral default + explicit `.btn-primary`.
- 2026-06-20 — Check breakpoint values are a **shared, small set** (tokens/consts). Ad-hoc per-component
  breakpoints (e.g. 560/600/760px in one app) cause inconsistent reflow; grep `@media` and list distinct widths.
- 2026-06-20 — An avatar/icon control whose text label is hidden at small widths still needs an
  accessible name there (`alt`/`aria-label`); `alt=""` (decorative) is wrong when it's the only account cue on mobile.
- 2026-06-20 — DONE (engine): added `--scenarios <json>` — `[{label,url?,viewport?,actions?,full?}]`
  with actions `{clickText|click|fill|press|wait}`. Drives tabs, sub-tabs, modals and filled forms so a
  SPA's whole surface is captured, not just the default route. (`--scenarios-only` skips the route grid.)
- 2026-06-20 — High-value cheap code check: **grep for undefined CSS tokens** (every `var(--x)` vs the
  `:root` set). Caught real wrong-color bugs (`--text-muted`/`--danger`/`--success` that were never
  defined). Promoted into the Pillar-2 checklist above.
- 2026-06-20 — Capture artifact to ignore: `position:sticky` headers **duplicate down the page** in
  Puppeteer full-page screenshots (the sticky element repaints at each scroll band). It's a screenshot
  artifact, not a UI bug — judge sticky elements from the viewport/fold shot, not the full-page one.
- 2026-06-20 — Layout: a `max-width` form/content card should be **centered** (`margin-inline:auto`),
  not left-aligned — left-align leaves a big empty right half on wide screens that reads as broken. Match
  the app's existing centered-card pattern.
- 2026-06-20 — Consistency: when you reflow one data table to stacked cards on mobile, **reflow its
  siblings too** (Positions vs History) — half-migrated tables are themselves an inconsistency.
- 2026-06-20 — a11y: a disabled/read-only input still needs a programmatic label (`<label for>` /
  `aria-label`); a visual-only `<span class="field-label">` does not associate. And give text link-buttons
  a `min-height:24px` so they meet the tap-target floor.
- 2026-06-21 — Spacing: uneven vertical rhythm usually comes from **margin stacking/collapse between a
  component and its neighbor**, not a single wrong value. A child with its own `margin-top` after a header's
  `margin-bottom` oversizes the gap (siblings collapse to the larger margin); a `margin:0` reset `<p>` right
  after an element glues them (zero gap). Fix by owning the gap in one place and matching one rhythm.
  Promoted into Pillar-1 Spacing. **Always trace adjacent-sibling margins, don't just eyeball one value.**
- 2026-06-21 — Responsiveness (code-level): a `display:flex` row without `flex-wrap` whose children have
  intrinsic/fixed widths **overflows its container on mobile** instead of growing vertically — a frequent
  phone bug that's invisible on desktop. Always grep flex rows and confirm they reflow; hide any `flex:1`
  desktop spacer at the mobile breakpoint so wrapped items don't leave a gap. Promoted into Pillar-1
  Responsiveness + a Pillar-2 code check. **Every review must include a mobile viewport AND this code pass.**
- 2026-06-21 — Aesthetics: fixing overflow is only half the job — once a row wraps on mobile, **judge how the
  items are distributed**, not just that they fit. Left-bunched content with empty space on the right looks
  unfinished; a 3-zone grid (start/center/end: badge left, name centered, pair right; secondary line
  left/right) reads as intentional. Don't ship "it no longer overflows" — ship "it looks balanced." Promoted
  into Pillar-1 Responsiveness. Verify isolated/auth-gated components by screenshotting a faithful mock.
- 2026-06-21 — **Element-configuration failure (style leak via descendant combinator).** When "the same
  element" looks different in two places, suspect a variant rule on a **self-nestable** reusable component
  leaking through a bare descendant selector. Real case: one `<Collapsible>` had `.section .cl-title{font-size:lg}`;
  a `variant="help"` Collapsible nested *inside* a `variant="section"` one inherited that rule (same component
  scope), rendering its "How it works" title at section size while the un-nested twins stayed small. Fix:
  direct-child scope (`.section > summary > .cl-title`). General method that nailed it fast: build a faithful
  **mock** placing the suspected-different instances **adjacent** (real tokens + component CSS inline), screenshot,
  and read it — the size jump was obvious side-by-side though invisible in isolation. Promoted a Pillar-2 check.
  **When asked to make element X "match" element Y, render X and Y adjacent first — don't eyeball them apart.**
- 2026-06-21 — a11y: a **scrollable text region** (long Terms/legal block in a fixed-height scroller)
  should NOT get `tabindex="0"` — it trips `a11y-no-noninteractive-tabindex` and adds a dead tab stop.
  Content is already exposed to screen readers; the checkbox/buttons stay focusable. Use `role="region"`
  + `aria-label` to name it, no tabindex. Promoted into Pillar-3 a11y.
- 2026-06-21 — Method (auth-gated flows): to screenshot a blocking gate / logged-in page when there's no
  shared test login, **create a throwaway account via the signup API, scrape its session cookie from the
  cookie jar, inject it with `--cookie`, capture, then DELETE the account** (and clean up). Confirmed
  end-to-end here (consent gate + account page). Cheaper and more faithful than a static mock when the
  real page is reachable; pair with the mock approach only when no account can be created.
- 2026-06-21 — Bug class (inline link as `<button>` + global button rule): using a `<button>` for an
  **inline text link** breaks when the app has a global `button{}` that sets `height`/`display:inline-flex`
  (a common pattern). The button keeps the ~control height (e.g. 40px) inside running text, so the line box
  of *that* row balloons while sibling rows stay ~1 line tall → **lopsided gaps between stacked checkbox/
  text rows** (looks like a spacing bug, is actually a line-height bug) and the link sits off the text
  baseline. Fix: use a semantic `<a>` for navigation links — it's immune to the button rule and correct
  a11y (`a` for navigation, `button` for actions). When you must keep a button, fully neutralize
  `display`/`height`/`padding`/`line-height`, not just `min-height`. Always cross-check stacked-row spacing
  against whether a row contains an inline `<button>`.
- 2026-06-21 — UX (SPA hash router): `navigate()` to a new **top-level page** (terms/privacy/account…)
  should `window.scrollTo(0,0)` so the page starts at the top instead of inheriting the previous page's
  scroll; do it in the shared navigate() AND on `hashchange` (covers back/forward and direct hash edits).
  A link that "goes to the right page but mid-scroll" reads as broken to users.
- 2026-06-25 — Method (verify a 2-col→1-col reflow): always capture a viewport **just above** the
  collapse breakpoint, not only one well below it. Below the breakpoint tells you the stack works; the
  real risk is the *cramped two-column* band right above it (e.g. breakpoint 860 → shoot 900), where the
  narrower column can squeeze a panel/table before it's allowed to stack. A clean 768 + 1280 pair can
  hide a broken 900. Add the breakpoint+~40px width to the viewport list for any split-hero/2-col layout.
- 2026-06-25 — a11y (decorative product-demo panel): when a hero's signature is a faux UI that **restates
  the copy's claims** (a fake console/dashboard/log, no real controls), mark the **whole panel
  `aria-hidden="true"`** so screen-reader users don't hear a confusing duplicate of the headline/subtitle.
  The textual claim already lives in the real copy beside it; SVG/icons inside then need no alt. (Only do
  this when the panel carries no information that's *absent* from the surrounding text.)
- 2026-06-26 — a11y (cheap, high-value code check): **grep whether the app has a global
  `:focus-visible` for its shared button class** (`.button:focus-visible` / `button:focus-visible`). A
  missing keyboard focus ring is **invisible in screenshots** (hover/mouse look fine) but fails every
  keyboard user, and it's common for a design system to style `input:focus` yet forget buttons. If absent,
  the fix is one global rule using the existing focus-ring token — it lifts the whole app, not one screen.
  Pair it with: links/buttons on a **dark** surface need an explicit focus style (the UA default outline is
  often near-invisible on dark). Added as a recurring Pillar-3 grep.
- 2026-06-26 — a11y (consent/cookie/notification bars): a **non-blocking** bottom bar that traps no focus
  should be `role="region"` + `aria-label`, **not** `role="dialog" aria-modal="false"` — `dialog` implies a
  focus-managed widget it isn't. Reserve `role="dialog"`+`aria-modal="true"`+focus-trap+initial-focus for a
  bar that actually blocks the page. General rule: match the ARIA role to whether the thing blocks/traps,
  not to the word "banner/popup".
- 2026-06-26 — Method (verify a consent-gated third-party script end-to-end): when the task is "load
  script X only after cookie consent", a screenshot can't prove it — **drive it with the browser**: assert
  the gated `<script src*="...">` is **absent before any choice**, **present only after Accept-all**,
  **never after Essential-only**, and **present on a return visit** (cookie already set). Click the bar's
  buttons with `getByRole('button',{name})`, **not** `getByText` — `getByText` can match a wrapping
  text/whitespace node or trip strict-mode and silently click the wrong thing (cost me two false test
  failures until I switched). Read the persisted cookie via the browser context, not `document.cookie` string-matching.
- 2026-06-26 — Consistency/correctness worth a grep on any privacy-touching change: **does the privacy
  policy match what the site actually loads?** A real case here — the policy claimed "no third-party
  analytics" while an analytics `<script>` loaded unconditionally in `app.html`. When reviewing a
  cookie/consent/analytics change, diff the *claims* in the legal copy against the *actual* network/script
  tags; a stale honest-looking policy is a compliance bug, not just a wording nit.
- 2026-06-28 — **`overflowX:false` does NOT mean mobile is fine — confirm the PRIMARY pane survives.**
  A `flex` layout with a `flex-1` content pane + a fixed-width sidebar (`w-[26rem]`) that lacks
  `shrink-0` will, at phone widths, shrink the sidebar *and* starve the primary pane to ~0px instead
  of overflowing — so `overflowX` stays false and `offCanvas` stays empty while the main content has
  effectively **vanished**. The automated overflow signals miss this class entirely. On every mobile
  shot, positively verify the *primary* content is still visible (not just "nothing overflows"); fix by
  stacking panes (`flex-col`) below a breakpoint or giving the main pane a `min-width`/`min-height`.
  **New rule: a mobile shot must be judged for "is the main thing still here?", not only overflow.**
- 2026-06-28 — a11y nuance: an emoji/icon-only `<button>` with a **`title`** attribute does NOT trip the
  `unnamedControls` signal (title provides an accessible name), so the engine reports it clean — but
  `title` is weaker than `aria-label` (no reliable SR exposure on some setups, mouse-only tooltip). When
  the signal says 0 unnamed controls but the UI is full of emoji buttons, spot-check that the name source
  is a real label, and prefer `aria-label` over `title` for icon-only controls.
- 2026-07-02 — Responsiveness (adding children to re-laid-out rows): when a mobile media query re-lays a
  flex row as a **grid with explicit per-child placements** (each existing child has `grid-row/column`),
  any NEW child added later gets **auto-placed into an unintended cell** (its own orphan row/column) —
  desktop looks fine, only the breakpoint breaks. Caught live: a status icon added next to a badge landed
  alone on a third grid row at <600px. Fix pattern: group the new element with its logical partner in one
  wrapper (one wrapper = one grid cell) or give it explicit placement. **Whenever a diff adds a child to a
  row that any media query restructures, re-screenshot that breakpoint** — the auto-placement bug is
  invisible in the unchanged desktop layout.
- 2026-07-03 — Gamified/themed dashboard cards: a card header using `display:flex; justify-content:space-between`
  with a **wrappable title** on the left and a small **tag/badge** on the right (e.g. "Workshop ↗") breaks when
  the title wraps to 2 lines — the tag's own text (esp. a trailing glyph/arrow) wraps onto its own line and the
  tag drifts to vertical-center. Fixes: `align-items:flex-start` (tag pins to the title's first line),
  `white-space:nowrap; flex:none` on the tag, and `min-width:0` on the title so it (not the tag) absorbs the wrap.
  General: any space-between header with one flexible + one fixed child needs nowrap+flex:none on the fixed one.
- 2026-07-03 — Status chips/badges with **semi-transparent backgrounds** break when the layout lets them
  float over a bright decorative layer (fixed-position moon/sun/blob art): at some viewport the chip lands
  on the bright art and its text contrast collapses. If a chip conveys state (ONLINE/OFFLINE), give it a
  **solid** background; save translucency for chips that always sit on a known surface. Check every fixed
  decorative element against reflowed positions of overlaying content at each viewport.
- 2026-07-03 — **CRITICAL bug class: `[hidden]` is defeated by any author `display` rule.** An element
  toggled via the `hidden` attribute/property but styled with `display:flex|grid|block` in a class
  (`.modal-backdrop{display:flex}`, `.stale-warn{display:flex}`) STAYS VISIBLE when hidden — the UA
  `[hidden]{display:none}` is the weakest rule and loses to any author `display`. Two nasty symptoms:
  (1) a "hidden" full-screen modal/overlay with `opacity:0` still covers the page with `pointer-events`
  on, **swallowing every click** (page looks dead); (2) a "hidden" warning/badge shows permanently.
  Fix once, globally: `[hidden]{display:none!important}`. Always add this reset in any page that toggles
  flex/grid elements via `hidden`. Verdict method that caught it: a headless click test where the modal
  never opened + the warning showed in the wrong state — screenshot a toggled-off overlay element and
  confirm it's truly gone, not just transparent. Promote: every review must check that `hidden`-toggled
  elements have no competing `display` rule.
- 2026-07-05 — Apps canvas (Flutter web, jogos): os signals de DOM ficam cegos e cliques por seletor não funcionam — use as actions `clickXY` (clique por coordenada, derivada de um screenshot anterior) e `evalJs` (semear estado via localStorage/reload) adicionadas ao capture.mjs; e ao revisar builds web de apps móveis, cheque primeiro se plugins nativos sem implementação web (ads/consent) travam o boot no splash — guarda kIsWeb no main é o fix padrão. (via tictacverse)
- 2026-07-05 — Method (verify a **consent-gated** element deterministically): don't `clickText` the
  accept button as the first action — it races the banner render (the banner mounts a tick after load,
  so the click finds nothing and the "consented" shot is silently unconsented). Seed consent with
  `evalJs: "localStorage.setItem('<consent-key>','accepted')"` then a second `evalJs: "location.reload()"`
  + a generous trailing `wait`; the reload's context-destroyed error is caught, and the reloaded page
  boots already-consented. Read the app's actual consent localStorage key from the source (it may be
  versioned, e.g. bumped when a new script category is added). (via CoinHub ad rails)
- 2026-07-05 — Method (verify a **width-gated** element, e.g. desktop-only side rails shown only above a
  wide breakpoint): capture a viewport **above** the show-breakpoint to prove it renders in the intended
  slot (gutter), AND the band **just below** it to prove it's cleanly hidden (not squished/overlapping) —
  plus a true mobile width to prove the base layout is untouched. Expect a `position:fixed` element to
  paint in the FIRST viewport band of a full-page screenshot (vertically centred if `top:50%`); that's
  correct fixed behaviour, not a bug — judge its horizontal placement (inside the empty gutter, not over
  content) and confirm `overflowX:false`. Gutter-centred rails should use a token-relative offset
  (`calc((100vw - page-max)/4 - halfwidth)`), never a magic px. (via CoinHub ad rails)
- **2026-07-06 (via CoinHub):** A native control element repurposed as a NON-control (e.g. a `<button>`
  used as an image frame/card wrapper for a lightbox) inherits the app's global control styles — the
  killer is a global `button { height: var(--control-h) }`: the wrapper stays ~40px tall and the
  image visually overflows onto the content below (vertical OVERLAP with zero horizontal overflow, so
  scrollWidth-based checks pass). Rule: when wrapping media/content in `button`/`a`, explicitly
  neutralize the global control rules (`height:auto; padding:0; border:0; background:none` + hover
  filter) — and judge full-page screenshots by EYE for vertical overlap; automated signals only catch
  horizontal overflow. Script-only verification (naturalWidth>0, scrollWidth) is NOT a visual review.
- **2026-07-07 (via CoinHub):** Ao inserir CTA promocional/afiliado/monetização numa UI de produto,
  verifique que ele **não compete com a ação primária** da tela: coloque-o DENTRO da seção auxiliar
  relevante (ex.: um "não tem conta? crie aqui" dentro do guia de conexão), não como banner no topo
  roubando atenção do fluxo principal, e sem dark pattern (deixe a ação primária mais proeminente).
  Links externos de afiliado/apoio: sempre `target="_blank" rel="noopener"` e cheque o contraste do
  link sobre a caixa tingida (callout âmbar/tinta de marca).
- **2026-07-08 (via CoinHub):** Bug class — **stale state badges via helper-closure in compiler-tracked
  templates (Svelte & co.)**: a template that reads state through a plain `const` arrow helper
  (`isActive(x)` closing over `credentials`) hides the dependency from the compiler — the block never
  re-renders when the state object is reassigned, so status tags ("Active/not configured") go STALE
  after the user switches, while sibling expressions that reference tracked vars directly DO update
  (half-fresh UI, worse than fully stale). Fix: reference the state var directly in the markup or via
  a `$:`/derived mirror. **Method that caught it: screenshot AFTER a state-changing interaction
  (click → wait → shot), never only the initial render** — first-paint screenshots cannot reveal
  stale-render bugs; every review of a stateful control (tabs/switch/selector) must include a
  post-interaction shot and check ALL views of that state (card badge + header pill + panel title)
  agree. Bonus check the same run reconfirmed: when a selection highlight and an "active" status are
  distinct concepts, the DEFAULT selection on load must equal the active one, or the two visuals
  contradict each other.
  - **2026-07-13 reinforcement (via CoinHub):** the SAME class bites **`$:` reactive/derived statements**,
    not only markup expressions — and one helper can hide **several** dependencies at once. A derived
    `$: cost = foldByQuote(execFilter(e => e.by==='USER'), e => e.total)` stayed **R$0** after data loaded
    because BOTH `execFilter` (reads `summary`) and `foldByQuote` (reads `quoteBySymbol`) hid their state
    reads from the compiler, so the block was never re-run; a sibling `$: x = fold(summary.operations,…)`
    that named `summary` directly updated fine (again: half-fresh, worse). Fix: inline the state reads so
    every tracked var appears **textually** in the `$:` (`summary.executions.filter(…)`, pass
    `quoteBySymbol` as an arg), or use an explicit `$:`-mirror. Rule of thumb: a `$:` that computes from
    state must MENTION that state by name — if a helper is the only thing that touches it, the compiler is
    blind to it.
- **2026-07-10 (via CoinHub):** Ao adicionar um painel novo com tabelas de dado denso (7+ colunas) num
  app que JÁ tem padrão de reflow stacked-card < 600px para outras tabelas, decida conscientemente:
  ou reflowa igual (consistência) ou aceite o scroll-x contido — mas nesse caso **garanta que os
  números-chave (os que respondem à pergunta do usuário) vivam em CARDS responsivos acima das tabelas**,
  não só dentro delas, senão o mobile esconde o essencial no scroll. Um scroll-x contido é aceitável
  para DETALHE denso; nunca para a métrica principal. (Método de captura de painel auth+chave-gated:
  extrair o `<style>` verbatim do .svelte + os tokens do :root do app.css num mock HTML servido por
  http.server — file:// quebra o route-append do capture.mjs; sirva por http.)
- **2026-07-11 (via CoinHub):** Barra de ação "copy + botão" (título/descrição à esquerda, CTA à direita):
  no desktop use `justify-content:space-between` com a copy `flex:1 1 <base>` e o botão `flex:none`; no
  mobile o `flex-wrap:wrap` empilha (copy acima, botão abaixo) sem overflow. Sempre teste os 2 estados —
  a copy longa é o que empurra o botão pra fora se o botão não for `flex:none`. Para categorias novas num
  split de métricas (ex.: "Você/Robôs/Externo"), renderize a nova parte condicional (`{#if hasX}`) para não
  mostrar "· Externo: R$ 0,00" quando não há dado — e confirme que o total do card SOMA a nova parte
  (headline e split têm que bater).
- **2026-07-11 (via CoinHub):** Para revisar AO VIVO uma feature atrás de login+dado (ex.: posições que só
  existem com estado no banco), o caminho fiel é: signup via API → promover a conta no DB (verificação/
  termos) → **semear as linhas de dado direto no banco** (as posições/registros que a feature exibe) →
  injetar o cookie de sessão no capture.mjs → dirigir as sub-abas com `--scenarios` (arquivo JSON, NÃO
  inline — o script lê `existsSync(path)`) usando `clickText`. Isso prova a feature de ponta a ponta muito
  melhor que um mock. Cuidado: um estado que depende de OUTRA credencial (ex.: "conectado à exchange") vai
  cair no ramo "não conectado" com a conta de teste — verifique esse estado por código e reporte que o
  ramo conectado precisa da credencial real, não finja tê-lo capturado.
- **2026-07-11 (via CoinHub):** Quando uma view depende de estado que SÓ existe com credencial externa
  real (ex.: saldo de exchange), a review viva de conta descartável só alcança o estado VAZIO — capture-o
  (prova que o código novo não quebra: sem crash/console-error/overflow) e valide a view POPULADA por (a)
  teste da lógica pura de valuation num script e (b) conferência dos números derivados contra os DADOS
  REAIS no banco (ex.: preço médio por par = SUM(total)/SUM(qty) bate com o esperado). Diga no relatório
  que o populado foi verificado por lógica+dados, não por screenshot, e peça a conferência visual final ao
  dono da credencial. Não finja screenshot do que exige a credencial real.
- **2026-07-12 (via CoinHub):** Ao ADICIONAR colunas a uma tabela grid com `min-width` fixo, recalcule o
  min-width contra a largura REAL do card que a contém (container `page-max` − paddings), não contra o
  viewport. Uma tabela que cabia com N colunas passa a estourar com N+2 e — como a coluna de AÇÕES
  (botões) costuma ser a última — ela é a primeira a sumir no scroll horizontal do desktop, escondendo a
  ação mais importante. Sempre re-capture a tabela após adicionar colunas e confirme que a última coluna
  (ações) aparece sem scroll no viewport alvo; aperte frações + min-width até caber.
- **2026-07-15 (via CoinHub — ícone-botão num flex encolhe abaixo do tap-target):** Um botão pequeno
  quadrado (ex.: um ✕ de "limpar", com `width/height` fixos) colocado num container **flex** (`inline-flex`/
  `flex`) pode ser **encolhido pelo flex-shrink abaixo do piso de 24px** mesmo com `width` setado — o sinal
  `tinyTargets` pegou um ✕ renderizado a **12×24** apesar de `width:1.5rem`. Regra: todo ícone-botão dentro
  de um flex precisa de **`flex: none`** (+ `min-width`/`min-height` explícitos) senão vira alvo minúsculo
  em algum viewport. Cheque no código: grep botões quadrados de ícone dentro de `display:flex` e confirme
  `flex:none`/`min-width`. Barato de corrigir, e o sinal automático já aponta — mas o fix é `flex:none`, não
  só aumentar `width` (que o shrink ignora).
- **2026-07-15 (via CoinHub — dirigir `<input type=date>` e o formato do date picker nativo):** Para semear
  um `<input type="date">` via `evalJs` no capture, set `el.value='YYYY-MM-DD'` (SEMPRE ISO, independente do
  locale) e dispare **`input` E `change`** (Svelte/bind escuta os dois). E não reporte como bug que o campo
  mostre `mm/dd/yyyy` vs `dd/mm/aaaa`: o formato exibido do date picker nativo vem do **locale do
  navegador**, não da app (o Chrome headless costuma ser en-US) — só o `value` (ISO) importa para a lógica.
- **2026-07-15 (via CoinHub):** Dois pontos de MÉTODO ao capturar uma SPA atrás de nginx com filtros
  `<select>`. (1) **Aponte a base para o host do SPA (nginx), não para a porta da API** — bater direto no
  backend (`:5020`) devolve "404 page not found" para `/` (a API só serve rotas de API; o `dist/` é servido
  pelo nginx). O token de sessão é válido em qualquer host (lookup por hash), então injete o mesmo cookie com
  `--cookie-domain <host-publico>` e capture a URL pública (cookie `Secure` ⇒ precisa de HTTPS). (2) Para
  **dirigir um `<select>` nativo** via `evalJs`, o valor tem que ser **UMA expressão** — `page.evaluate(str)`
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
  (ex.: 1280–1519px) e volte ao valor base no breakpoint onde eles surgem (≥1520px); e reduza o min-width
  da tabela para caber também no valor base (com os fixed presentes). Verifique nos 3 regimes: faixa
  alargada, breakpoint dos fixed, e confirme que a última coluna (ações) aparece sem scroll em todos.
- **2026-07-16 (via todo — redesign de app 100% inline-style):** Num app React `createElement`
  **sem build**, com a UI toda em `style={{}}` inline: um redesign por CSS **não "pega"** enquanto os
  inline styles existirem (inline vence qualquer folha). Ordem certa: **primeiro** converta os
  elementos estruturais/barulhentos para `className` (deixando inline SÓ o dinâmico de verdade —
  transform de drag, posição computada de menu), **depois** o CSS de tokens aplica. Ao trocar
  `alert/prompt/confirm` nativos por toast/modal temáticos, cuide da **corrida save-on-blur**: o
  `onBlur` do input de edição (que cancela) dispara ANTES do `onClick` do botão Salvar → salva com o
  id já zerado; blinde o Salvar com `onMouseDown: e=>e.preventDefault()` pra o foco não sair do input
  antes do clique resolver. E hierarquia de botão que presta = **cor com significado**: primário
  sólido, secundário ghost, e uma cor (coral/vermelho) RESERVADA só pro destrutivo — se "tudo é da cor
  da marca", deletar grita igual à ação principal.
- **2026-07-15 (via todo):** Método — revisar app que autentica por **token em `localStorage` (não
  cookie)**: `--cookie` NÃO loga. Registre uma conta descartável pela API, e no scenario semeie o token
  com `evalJs: "localStorage.setItem('token', <json-do-token>)"` seguido de um SEGUNDO `evalJs:
  "location.reload()"` + um `wait` generoso — a SPA remonta já autenticada (mesmo padrão do consent-seed;
  o erro de context-destroyed do reload é engolido). Para ver o estado POPULADO de um app de listas cujo
  tier grátis limita linhas/abas, **semeie várias linhas direto no banco** (conta descartável) em vez de
  esbarrar no limite — e **apague a conta ao final** (cascade). Check barato de alto valor que este
  review reforçou: grep por `box-sizing` (sem `*{box-sizing:border-box}` global, qualquer
  `width:100% + padding` vira overflow de poucos px no mobile — invisível no desktop), por `:focus-visible`
  (ausência total = zero anel de foco de teclado, invisível em screenshot) e por `prefers-reduced-motion`
  (animações decorativas sem guarda). Os três faltando juntos é o padrão "projeto quase pronto".
- **2026-07-16 (via warframe-farm-helper — CSP vs redirect de CDN de imagem):** Quando as imagens vêm de um
  CDN que **301/302-redireciona** para outro host (comum: `cdn.foo.us/img/x.png` → `raw.githubusercontent.com/...`),
  a CSP `img-src` precisa liberar **os DOIS hosts** — o navegador checa o destino do redirect contra a
  política, então liberar só o host inicial faz a imagem **falhar silenciosamente** (aparece o alt/ícone
  quebrado). Sintoma no capture: `consoleErrors` cheio de "Loading the image '<host-do-redirect>' violates
  ... Content Security Policy" e o sinal `missingAlt`/imagem quebrada na tela. Método que pegou: ler o
  `.consoleErrors` do manifest (não só os sinais visuais) — erro de CSP de imagem só aparece no console, e um
  `curl -I` na URL do CDN revela o `location:` do redirect. Fix: adicionar o host de destino ao `img-src`.
  LIÇÃO META: sempre leia `consoleErrors` do manifest numa página com imagens de 3º — CSP de imagem quebrada
  não dispara overflow nem layout-shift, só o console denuncia. E o piso de tap-target (24px) num link de
  tabela densa se resolve com `display:inline-block; padding:Ypx 0; min-height:24px` no `<a>` (a célula já
  tem padding, mas o sinal mede o bounding-box do link, não da célula).
- **2026-07-16 (via warframe-farm-helper — ENGINE fix `missingAlt` + review atrás de CDN/proxy com cache):**
  (1) O check de alt usava `!img.alt`, que acusa **`alt=""` — a marcação CORRETA de imagem decorativa**
  (WAI): false-positive em todo site bem feito. Corrigido para `!img.hasAttribute('alt')`; regra geral:
  `alt` vazio ≠ `alt` ausente — só o segundo é bug. (2) Ao re-capturar um site atrás de **CDN/proxy com
  cache de estáticos** (Cloudflare & co.) logo após um deploy, os shots podem vir com **JS/CSS VELHOS**
  (o fix "não aparece" — sintoma: comportamento antigo num arquivo que você acabou de mudar). Verifique
  contra a ORIGEM (`http://127.0.0.1:<porta>`) para validar o fix agora, e deixe o edge expirar (ou
  purge) para o público. Nunca conclua "fix não funcionou" a partir de um shot atrás de cache. (3) Uma
  **faixa/barra horizontal de status com scrollbar oculta**: no MOBILE o chip cortado na borda é
  affordance suficiente, mas no DESKTOP (mouse, sem swipe) conteúdo cortado fica inalcançável na
  prática — dimensione para caber TUDO no viewport desktop comum (compacte: segundos só quando faltam
  <10min, letter-spacing, divisores) e verifique na banda mais justa (viewport = max-width do wrap
  +20px), nos DOIS idiomas (PT costuma ser mais largo que EN).
- **2026-07-16 (via warframe-farm-helper — toggle de idioma i18n + default por locale):** Ao revisar um
  **toggle de idioma** (PT/EN) cujo default segue `navigator.language`: o **headless Chrome roda em en-US**,
  então as páginas em "idioma default" renderizam no idioma do NAVEGADOR (EN), não no que você imagina —
  rotular a cena "pt-mobile" NÃO força PT. Para capturar um idioma específico, **semeie
  `localStorage['<lang-key>']` + reload** (mesmo padrão do consent-seed) OU lance o browser com locale
  fingido. Sempre capture os DOIS idiomas e confirme visualmente que TUDO trocou (nav, chips, placeholders,
  seções, e conteúdo gerado no servidor como passo-a-passo/prosa) — um toggle costuma cobrir a UI estática e
  esquecer a prosa gerada (steps, mensagens), que fica no idioma antigo. Padrão de header responsivo que
  funcionou (busca fixa + toggle): mobile-first com `flex-wrap` e `order` — marca+toggle na linha 1 (toggle
  `margin-left:auto`), busca `flex-basis:100%` na linha 2, nav rolável na linha 3; num breakpoint (~760px)
  vira `flex-nowrap` uma linha só (marca·nav·busca que cresce·toggle). Verifique que a busca compacta do
  header e a busca-hero da home não brigam (duas caixas) — redundância aceitável se intencional.
- **2026-07-16 (via warframe-farm-helper — redundância semântica que só emerge após fix de dados):** Uma
  review NÃO deve tratar "dois itens do mesmo tipo mostram valores diferentes agora" como prova de que não
  são redundantes. Caso real: dois relógios dia/noite ("Cetus" e "Terra") que o jogo sincroniza 1:1 por
  design (U38.5) apareciam com estados DIFERENTES na 1ª review — porque uma das fontes de dado estava bugada
  (Terra vinha de uma API legada mostrando "noite" enquanto Cetus mostrava "dia"). A duplicação (dois chips
  carregando sempre a mesma info) só ficou óbvia DEPOIS de corrigir o dado. Lição: ao ver N itens do mesmo
  tipo, pergunte se são **a mesma coisa subjacente por design** (→ fundir e reaproveitar o espaço), não se
  os valores atuais coincidem — valores coincidem/divergem por acaso, inclusive por BUG. Método barato:
  para cada par de itens repetidos, cheque na fonte/no código se derivam do mesmo dado; se sim, é candidato
  a fusão mesmo que na tela de agora estejam diferentes. E o inverso: não funda itens que só coincidem no
  momento mas são conceitos distintos (ex.: um relógio "Fass/Vome" que compartilha a duração mas não é o
  mesmo ciclo). Promovido a um item de checklist (Pillar 1 · Information design). Também: superfície com
  poucos itens deve distribuir pela largura (`space-between`/center), não amontoar num canto deixando buraco.
- **2026-07-16 (via warframe-farm-helper — duas caixas de busca ATIVAS na mesma tela):** Uma rubric antiga
  minha dizia "confira que a busca do header e a busca-hero não brigam — redundância **aceitável se
  intencional**"; foi tratada como intencional e o operador reclamou (duas barras na home). Lição: **duas
  entradas de busca ATIVAS na mesma tela são redundância a CONFIRMAR com o dono, não a assumir intencional.**
  O default de produto é **uma entrada de busca por tela**; a secundária vira dica/atalho (ex.: chips de
  exemplo que levam aos resultados) ou é removida. Exceção legítima: uma página **dedicada a busca**
  (resultados) pode ter a barra grande "da página" + a global do header — ali a grande é o campo ATIVO com o
  termo (padrão tipo Google SERP), não redundância. Regra ao FLAGAR: numa tela que NÃO é de resultados de
  busca, se há 2+ campos de busca que fazem a mesma coisa, reporte como redundância (P2) e proponha manter
  só um. (Reforça o item Pillar 1 · Information design: vale para busca, não só para tiles/relógios.)
- **2026-07-17 (via warframe-farm-helper — lista longa com itens "ativos" vs "históricos/inativos"):**
  Quando uma lista mistura itens **acionáveis agora** com itens **inativos/históricos** (disponível vs
  vaulted, ativo vs arquivado/expirado, em estoque vs esgotado), e os inativos são a MAIORIA (aqui: 37 de
  39 relíquias vaulted por componente), despejar tudo afoga a informação que o usuário precisa e empurra o
  resto da página para longe. Padrão: **mostrar os ATIVOS inline + colapsar os inativos num `<details>`**
  ("▸ Ver N vaulted"), com um estado vazio ("nenhum disponível — todos vaulted") quando não há ativos.
  `<details>/<summary>` nativo é a ferramenta certa (acessível por teclado de graça); estilizar com
  `summary{list-style:none}` + `::-webkit-details-marker{display:none}` + um chevron `::before` que rotaciona
  em `[open]`, e **`summary:focus-visible`** explícito (o foco default some ao remover o marker). Checagem
  ao revisar QUALQUER lista longa: os itens estão ORDENADOS com o acionável primeiro (o backend já ordenava
  disponível→vaulted) E o inativo em massa está colapsado? Se a lista tem >~10 itens e a maioria é ruído
  inativo, é candidato a collapse. NOTA de método: para capturar o estado ABERTO de um `<details>`, dispare
  `document.querySelector('.x > summary').click()` via `evalJs` + `wait` antes do shot (o fold-shot padrão
  pega só o estado fechado no topo). Promovido ao item Pillar 1 · Information design.
- **2026-07-17 (via warframe-farm-helper — badge de estado BINÁRIO aplicado a tipo que não tem esse eixo):**
  Um badge de status de duas faces (Disponível/Vaulted, Ativo/Inativo, Em estoque/Esgotado) derivado de um
  booleano `available` mostra o rótulo ERRADO quando renderizado num tipo de item que **não possui esse
  eixo de estado**. Caso real: um recurso bruto (Orokin Cell) caía em `available=false` (não tinha relíquia
  nem fonte no dataset) e exibia **"VAULTED"** — mas recurso não vaulta, está sempre disponível. O default
  `false` de um flag de disponibilidade vira uma AFIRMAÇÃO FALSA de estado. Checagem ao revisar qualquer
  badge de status: confirme que TODO tipo que chega ali realmente tem os dois estados possíveis; para os
  tipos sem esse eixo (recursos, itens sempre-disponíveis, categorias "N/A"), ou force o estado correto na
  origem, ou não renderize o badge. Method: abra a página de um item de CADA tipo que compartilha o
  componente de badge (não só o tipo "normal") e leia o rótulo — um badge "errado mas plausível" passa
  despercebido se você só olha o caso feliz. (Cruza com Pillar 1 · Information design.)
- **2026-07-17 (via tictacverse — review de LOCALE NOVO num app canvas):** ao revisar a adição de um
  idioma cujo script a fonte bundled NÃO cobre (ex.: Devanagari com fonte latina como Fredoka), a
  pergunta não é "a fonte tem os glifos?" (o fallback do sistema resolve) e sim: (a) o fallback
  renderiza em TODAS as telas com peso/altura de linha aceitáveis? (b) strings do idioma novo, muitas
  vezes mais LARGAS, estouram botões/cards/HUD apertados? Method p/ Flutter web e afins: em vez de
  clicar até o seletor de idioma, FORCE o locale persistido antes do boot — shared_preferences web
  grava em localStorage com prefixo `flutter.` e valor JSON-encodado (`localStorage.setItem(
  'flutter.settings.locale', JSON.stringify('hi'))` + reload + wait) — e então percorra home, sheets,
  seleção e telas de jogo. Cobre também: tile do idioma novo no seletor com bandeira/check, e a
  auto-detecção (supportedLocales gerado) sem precisar de aparelho real. (Cruza com Pillar 3 · i18n.)
- **2026-07-18 (via warframe-farm-helper — deep-link gerado por slug 404 para CLASSES inteiras):** Ao
  gerar links para uma referência externa (wiki/docs/catálogo) a partir do NOME do item por um padrão de
  slug (`/w/<Nome_com_underscores>`), NÃO assuma que o padrão resolve para todos os tipos. Caso real: itens
  "de topo" (armas, warframes, recursos: `/w/Jade`, `/w/Plastids`, `/w/Orokin_Cell`) resolvem 200, mas
  **peças de conjunto** ("Braton Prime Barrel") e **cosméticos** ("Alone Portrait", "Stalker's Lair Scene")
  dão **404** — eles vivem como SEÇÃO da página do set/quest, não como página própria. Um link 404 é pior
  que nenhum. Fix por CLASSE: alvos que têm página → `/w/`; alvos que são subitens → a **URL de BUSCA** do
  destino (`/index.php?search=<termo>`, que sempre resolve e cai na página-mãe). Método barato que pegou:
  `curl -o /dev/null -w "%{http_code}" -L` numa AMOSTRA de CADA classe de link (item, peça, cosmético,
  recurso) antes de enviar — não teste só o caso feliz (um item real), teste um representante de cada tipo
  que passa pelo gerador. LIÇÃO META: sempre que um diff introduz links gerados por padrão, enumere as
  CLASSES de entrada e verifique o status HTTP de uma de cada; roteie as que 404 para busca/fallback.
- **2026-07-18 (via warframe-farm-helper — painel/section colapsável com `<details>`: controle interativo NÃO vai no `<summary>`):** Ao tornar um card/section inteiro colapsável com `<details class="panel"><summary>…</summary>`, qualquer controle interativo (botão de filtro, toggle de aba, link "Ver mais/See more") colocado DENTRO do `<summary>` **dispara o toggle do details ao ser clicado** (o summary captura o clique) — o filtro "não funciona" ou abre/fecha o painel sem querer. Padrão certo: o `<summary>` guarda SÓ o título (+ um chevron via `::after` que gira em `[open]`); todo o resto (toggles, listas, "Ver mais") vai num `.panel-body` IRMÃO, fora do summary. Exceção tolerável: um link de NAVEGAÇÃO real (`<a href>` que troca de página) pode ficar no summary — o toggle acontece mas a página descarrega, então é inócuo. Sempre dê `summary { list-style:none; cursor:pointer }` + `::-webkit-details-marker{display:none}` + `summary:focus-visible` explícito (o marker default some ao ocultar). Método de review: capturar o estado COLAPSADO (clicar o summary via `clickText` do título + wait) e o estado com o filtro/ordenação aplicado, provando que o controle age no conteúdo e NÃO no toggle. (Cruza com o item de `<details>` do Pillar 1 · Information design.)
- **2026-07-18 (via warframe-farm-helper — texto que vira link precisa de afordância em REPOUSO):** Ao
  transformar rótulos de texto (nomes de item, recompensas) em `<a>`, decida a afordância de REPOUSO
  conscientemente: `color:inherit` + sublinhado só no hover fica limpo mas é quase indescoberto (o usuário
  não sabe que dá pra clicar sem passar o mouse — e no mobile não há hover). Se os links são o ponto da
  feature (o dono PEDIU pra poder clicar), dê um cue sutil em repouso (sublinhado pontilhado/opacidade baixa)
  ou uma cor de link discreta — sem cair no extremo de N links berrantes competindo com os CTAs. Regra:
  hover-only affordance é aclitável para link secundário/raro, insuficiente para o valor principal da tela.
  transformar server-side dados que vêm de um **cache compartilhado** (um TTL-cache em memória, um objeto
  reaproveitado entre requests), **CLONE antes de transformar** (`map(x => ({...x, campo: tr(x.campo)}))`),
  nunca mute em lugar. Caso real: o handler traduzia `location` mutando os objetos retornados por um cache
  de drops → o cache ficava em PT e o **request EN seguinte vinha traduzido** (um idioma vazando pro outro,
  de forma dependente-de-ordem e intermitente). Método de review que PEGA isso (o teste de "capturar os 2
  idiomas" não basta se rodar sempre na mesma ordem): carregue PT primeiro, DEPOIS bata no MESMO recurso em
  EN e confirme que voltou ao inglês — a contaminação só aparece na 2ª língua após a 1ª ter tocado o cache.
  Vale para qualquer transform (formatar moeda/data, mascarar, reordenar) sobre dado cacheado: transform =
  cópia. (Cruza com a checagem de i18n: teste os dois idiomas E a ordem entre eles.)
- **2026-07-18 (via warframe-farm-helper — adicionar um 3º/4º idioma a um i18n binário PT/EN):** Ao
  expandir um i18n que só tinha 2 idiomas, o bug nº1 é o **ternário binário** espalhado pelo código:
  `lang === 'en' ? EN : PT` (ou `=== 'pt' ? PT : EN`). Ele parte o mundo em "um idioma vs. TODO o
  resto" — então CADA idioma novo (es, ru…) cai no ramo do idioma ERRADO (aqui es/ru vazavam
  **português** na descrição/passo-a-passo/raridade do servidor, porque tudo ≠ 'en' virava PT). Fix
  em duas frentes: (a) normalize no BOUNDARY (o handler que recebe `?lang=`) para os idiomas que a
  prosa do servidor realmente tem — `pt`→pt, qualquer outro→`en` (fallback internacional), nunca
  deixe um idioma desconhecido herdar o ramo pt; (b) torne os ternários internos "idioma-base
  positivo" (só `=== 'pt'` → PT; resto → EN) como defesa em profundidade. E o fallback de chave
  faltante do `t()` deve cair em **en** (padrão internacional), não no 1º idioma do dict. Método de
  review que PEGA o vazamento: bata no MESMO recurso do servidor com `?lang=es` e `?lang=ru` e
  confirme que voltou INGLÊS (não o outro idioma pré-existente) — capturar só a UI estática não pega
  prosa gerada no servidor. Decisão de produto que vale reusar: em apps de nicho com jargão/entidades
  em inglês (games: nomes de item no market/wiki/trade; libs; APIs), **traduza o CHROME e deixe os
  NOMES/dados em inglês** nos idiomas novos — localizar os nomes pioraria a busca. Cross-check de
  ícone: uma **bandeira em opacidade baixa (estado não-selecionado)** pode perder a identidade
  (Espanha vermelho-amarelo-vermelho dimmed ≈ Alemanha escuro-ouro-escuro) — confira a
  reconhecibilidade no estado dim, não só no selecionado. (Cruza com Pillar 3 · i18n.)
- **2026-07-18 (via CoinHub — capturar feature atrás de MÚLTIPLOS gates em sequência):** Para revisar ao
  vivo uma feature de dashboard atrás de login, o cookie de sessão sozinho NÃO basta se a app tem gates
  ENCADEADOS antes do dashboard — aqui a conta descartável (signup + `email_verified_at=NOW()` no DB + login)
  ainda caía na **página de aceite de Termos+Privacidade** (o `clickText` da aba "não encontrado" era o
  sintoma: a aba nem existia porque o dashboard não montou). Cada gate server-side (verificação de e-mail,
  aceite de termos versionado, step-up) tem que ser satisfeito ANTES de capturar: aceitei via
  `POST /account/agreement/accept {version}` (leia a `current_version` do próprio endpoint — ela é
  versionada). Método geral: quando o `clickText`/seletor de uma aba "não é encontrado" mas a base carrega,
  **leia o 1º screenshot** — quase sempre é um gate (consent/terms/verify/paywall) interceptando, não um bug
  de seletor; satisfaça o gate e recapture. E o **rótulo de aba com ícone colado** (`🔒B3 / Investidor10`
  sem espaço, para não-admin) ainda casa por `clickText` com o texto ("B3 / Investidor10" é substring) — o
  que quebrou foi o gate, não o match. (Cruza com o método de auth-gated de 2026-06-21 e 2026-07-11:
  signup→promover no DB→**satisfazer TODOS os gates**→injetar cookie→dirigir com `--scenarios`.) Bônus: num
  painel de dado denso (tabela 8 col) o combo certo é métricas-em-chips (`flex-wrap`) ACIMA + tabela em
  `overflow-x:auto` — `overflowX=false` com a métrica principal nos chips é o padrão aprovado, não achado.
- **2026-07-18 (via warframe-farm-helper — portar um bloco de ADS/3º-party de um app para outro):** Ao
  reusar o padrão de anúncio de outro projeto (iframe A-ads em rails laterais + bloco mobile), os pontos
  que realmente quebram são: (1) o **breakpoint dos rails deriva do page-max DESTE app**, não do original —
  recalcule (`breakpoint ≈ page-max + 2×(rail+folga)`; aqui 1060px → 1420px, no original 1160px → 1520px)
  e capture a faixa logo ACIMA do novo breakpoint; (2) **CSP**: iframe de ad exige `frame-src <host>` no
  app destino (sem frame-src, default-src 'self' bloqueia SILENCIOSO — só o console denuncia; ler
  consoleErrors do manifest); (3) **rótulo "Anúncio" entra no i18n** do app destino em TODAS as línguas
  (teste de paridade de dicionário pega); (4) caixa com width/height explícitos → sem CLS quando o
  criativo chega; iframe `loading=lazy` no fim da página não pinta em full-page shot — não é bug. E um
  check de PRODUTO: units compartilhados entre sites compartilham também o filtro de categoria do painel —
  inventário cripto/apostas pode destoar num site de outro nicho; units novos por site se o dono quiser
  filtros independentes.
- **2026-07-18 (via tictacverse — provar ESTADOS TRANSIENTES de animação/timing):** o capture.mjs tem
  ~0,5–1s de overhead por shot full-page (CDP + página canvas pesada) — janelas de sub-segundo (ex.:
  "a CPU só joga após 550ms", "o modal só sobe após 1,65s") NÃO são prováveis com a cadeia de actions
  dele; o shot "instantâneo" chega tarde e mente. Método que funciona: script puppeteer dedicado com
  (a) screenshots **viewport-only** (rápidos), (b) o **elapsed REAL desde o evento gravado no nome do
  arquivo** (`_t244.png`) para julgar com honestidade o instante capturado, e (c) além do timing, uma
  prova por ESTADO INDIRETO que não depende de relógio (ex.: um toque disparado durante a janela de
  bloqueio deve ser ENGOLIDO — a célula continuar vazia prova a guarda sem medir ms). Bônus de método:
  o 1º clique após uma transição de tela de SPA/canvas pode ser engolido pela animação de rota — dê
  settle ≥1,5s antes do primeiro clique de cada tela, e desconfie quando a partida "seguiu outro rumo"
  (o rumo errado é sintoma de clique perdido, não de bug do app). E `tinyTargets` em Flutter web acusa
  sempre o `flt-semantics-placeholder` 1×1 — artefato do framework, não é achado.
- **2026-07-19 (via bobagi.space portfólio — full-page shot × scroll-reveal):** página com reveal por
  IntersectionObserver (conteúdo nasce `opacity:0` e só aparece ao entrar na viewport) rende um
  full-page screenshot quase todo PRETO abaixo do fold — parece runtime error, mas não é: o
  `fullPage:true` do puppeteer não dispara os observers das seções nunca intersectadas. Antes de
  diagnosticar "página quebrada", cheque consoleErrors no manifest (0 erros + vazio visual = reveal).
  Método que funciona: cenário com N× `{"press":"PageDown"}` + waits curtos até o fim da página e SÓ
  ENTÃO o shot full-page (jump direto com End pode pular seções sem intersectar; PageDown passo a
  passo revela todas). Alternativa: emular `prefers-reduced-motion` se o site tiver o bypass. E ao
  adicionar cards novos numa grade existente, o check mais barato de consistência é diff visual card
  novo × card antigo na MESMA captura (insets, chips, foot) — herdar o padrão é o critério, não a
  estética absoluta do card.
- **2026-07-19b (via bobagi.space — classe de estado × classe base):** um botão que ganha uma classe
  utilitária de visibilidade (`.burger{display:none}`) mas TAMBÉM carrega a classe base do design
  system (`.toggle{display:...}`) fica visível se a regra base vier DEPOIS no CSS — especificidade
  igual, ordem decide. Sempre escope a classe de estado à base (`.toggle.burger`) ou verifique a ordem;
  e o teste barato é capturar o viewport ONDE o elemento deveria sumir (desktop para um hambúrguer),
  não só onde ele aparece. Checklist novo de portfólio/efetividade: além do visual, julgue POSICIONAMENTO
  (o hero vende a senioridade real? CTA primário = objetivo do site?), PROVA (números reais vs enfeite),
  e PRÓXIMO PASSO do visitante convencido (CV baixável / contato) — um site pode passar em todos os
  checks visuais e falhar como produto.
- **2026-07-22 (via Coin Hub — tabela com coluna de texto livre):** numa tabela de dados, a PRIMEIRA
  coluna costuma ser a única com texto livre (nome/título vindo de fonte externa) — e é sempre a que
  quebra. Linha `flex` com `white-space:nowrap` + `min-width` NÃO contém texto longo: ele pinta POR CIMA
  das colunas vizinhas (não empurra, não corta, não gera overflow no manifest — o `overflowX:false`
  mente). Padrão correto: `display:grid` com `minmax(<piso>, Nfr)` na coluna de texto +
  `white-space:normal; overflow-wrap:anywhere; align-items:start`, para o texto quebrar em mais linhas
  DENTRO da própria célula e a linha crescer em altura. Teste com o **pior dado real** (consulte o banco
  por `ORDER BY length(campo) DESC`, não pelo que está na tela). Segunda lição, sobre o breakpoint do
  reflow em cards: escolha-o pela **largura MEDIDA** que a tabela recebe (`el.clientWidth` no browser
  headless, por viewport), não pelo default 600px herdado de outra tabela — se o piso do grid é maior
  que o espaço disponível, a faixa entre 600px e o piso vira scroll horizontal INTERNO e some com as
  últimas colunas sem nenhum affordance. Prova objetiva de que ficou certo: `scrollWidth-clientWidth==0`
  do menor ao maior viewport, mais um par de medidas em volta do breakpoint (939 vs 941).
- **2026-07-23 (via cartomania — a legal "last updated" date is a CONTENT bug when it lags the acceptance
  version):** When an app has a versioned Terms/Privacy re-acceptance gate, the "Last updated: <date>"
  shown on the /terms and /privacy pages must MATCH the version the gate forces users to accept. A stale
  date (page says "June 26" while the gate demands version "2026-07-23") is a real contradiction a user
  will notice, not a nit — flag it P2 and fix by tying the displayed date to the same version constant.
  Also re-validated: a strict CSP (`script-src 'self' 'nonce-…'`, no unsafe-inline) can ship on a
  canvas-heavy SPA with 0 console violations IF inline `style=""` attrs are covered by
  `style-src-attr 'unsafe-inline'` and external font/img hosts are allow-listed — verify by loading every
  key route (incl. a live game screen) headless and counting CSP violations, don't assume.
