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

### States (look for all, not just the happy path)
- [ ] Empty state (no data) is designed, not a blank gap.
- [ ] Loading state (skeleton/spinner) exists for async content.
- [ ] Error state is styled and actionable (matches the app's error pattern, not a raw browser alert).
- [ ] Success/confirmation feedback for actions.

---

## Pillar 2 — Front-end code

- [ ] Spacing/sizing use **design tokens / CSS variables**, not scattered magic px (flag repeated literals that should be a token).
- [ ] Responsive units where appropriate (rem/%, `clamp()`, `min/max`); avoid fixed px widths that cause overflow.
- [ ] Breakpoints are consistent (a shared set), not ad-hoc per component.
- [ ] **Verify responsiveness in the code, not only screenshots.** Grep every `display:flex` / `display:grid`
  row that holds multiple inline items and confirm it can reflow (`flex-wrap`, `min-width:0`, or a mobile
  media query) — a no-wrap flex row with intrinsic/fixed-width children **will** overflow on narrow screens
  even when today's data happens to fit. Flag fixed `width`/`min-width` px on content that must fit a phone.
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
