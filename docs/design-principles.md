# Design principles

G-Flow's UI (`core/ui`) follows the same design language as its reference sibling
project, `G-Stride` (`c:\Users\703393028\G-Stride` — visual/UX inspiration only,
never modified). This document states the principles as G-Flow's own, and
records what's actually implemented in `core/ui/src/styles/tokens.css` and
`base.css` versus what's aspirational.

## The nine principles

1. **Operational truth over decoration** — never style sample, stale, or
   unverified data as if it were live. A Module that hasn't been scanned, a
   TestCase that hasn't been run, a connection that isn't actually reachable —
   these must never borrow the visual weight of real state.
2. **Calm hierarchy** — one page title, one primary action (`.btn-primary`) per
   screen, progressive disclosure (`<details class="details-advanced">`) for
   anything secondary.
3. **Business first, technical second** — a field's caption ("Order Type")
   leads; its technical name (`VBAK-AUART`) is secondary/monospace detail, not
   the primary label.
4. **Status is text plus shape, never colour alone** — `.status-badge` always
   carries a text label (PASS/FAIL), not just a color swatch. Applies to any
   new status/health indicator.
5. **Keyboard is a first-class input** — every interactive element gets a
   visible `:focus-visible` ring (`--focus-ring` token), not just a mouse hover
   state.
6. **Responsive means task-complete, not merely scrollable** — a lower
   priority for this internal, desktop-only tool than it would be for a public
   product, but wide content (tables, chains) must scroll in its own container
   (`.table-frame`), never force the whole page to scroll horizontally.
7. **Density is controlled** — comfortable default padding/spacing from the
   `--space-*` scale; don't invent one-off spacing values in new components.
8. **Small composable primitives** — no new dependency for something a few
   lines of CSS/TSX already solve. `lucide-react` is the one icon library; no
   component-library dependency exists or should be added without cause.
9. **Preserve SAP-GUI familiarity without cloning SAP screens** — captions,
   technical names, and window titles come straight from the live SAP session;
   the chrome around them (buttons, tables, dialogs) is G-Flow's own, not a SAP
   GUI skin.

## What's actually implemented (`tokens.css` / `base.css`)

- **Token layer**: semantic CSS custom properties (`--bg`, `--panel`, `--text`,
  `--border`, `--accent`, `--selected-bg`) remapped per theme via
  `[data-theme]` + `prefers-color-scheme`, exactly like G-Stride's mechanism.
  One solid neutral (`--selected-bg`) marks "this is selected/active" (nav
  item, table row); `--accent` is reserved for destructive actions and the
  page's one primary CTA — the same anti-pattern fix G-Stride made after
  finding "five different reds and a blue" in its own history.
- **Typography**: composite shorthand tokens (`--text-body`, `--text-label`,
  etc. — weight/size/line-height bundled together) so a heading can't drift to
  body weight by accident. Self-hosted IBM Plex Sans/Mono via `@fontsource`.
- **Motion**: `--transition-fast` (0.15s ease-in-out) for hover/color/background
  micro-interactions, `--transition-panel` (0.25s cubic-bezier) for
  slower panel motion; buttons/nav items lift or nudge on hover
  (`translateY(-1px)` / `translateX(2px)`), reverting on `:active`. Dialogs
  fade+pop in (`fade-in` / `pop-dialog-in` keyframes). All of it is disabled
  under `prefers-reduced-motion: reduce`.
- **Focus ring**: `--focus-ring`, a soft glow drawn from `--selected-bg` via
  `color-mix()`, applied globally via `:focus-visible { box-shadow: ... }`
  instead of a hard outline.
- **Buttons**: `.btn` (neutral default) / `.btn-secondary` / `.btn-outline` /
  `.btn-ghost` / `.btn-primary` / `.btn-danger` — one shape (`--radius-md`),
  one height, a deliberate scale of visual weight for dense toolbars vs. the
  one primary action per screen.
- **Tables**: `.data-table tbody tr:hover` tints with `--row-hover` — a neutral
  color, explicitly distinct from `.selected`'s `--selected-bg` fill, so a
  hovered row is never mistaken for a selected one.
- **Badges/chips**: `--radius-full` (pill/stadium shape) reserved for
  `.chip`/`.status-badge` only — never for buttons, which stay rectangular.
- **Z-index**: `--z-drawer` (60) / `--z-dialog` (100) tokens, so any new
  overlay references one of these instead of a hand-picked number.

## What's intentionally not ported

- G-Stride's tab/segmented-control components — G-Flow has no tabbed UI yet;
  add them from G-Stride's pattern (underline-style tabs, background-filled
  segmented toggle) if/when a screen needs one, rather than pre-building an
  unused component.
- A formal breakpoint scale — this is a desktop-only internal tool; revisit if
  that changes.
- A CSS icon-size scale — `lucide-react`'s `size={N}` prop is used ad hoc
  (12/14/16/28px cluster in practice), matching G-Stride's own approach, which
  never formalized one either.
