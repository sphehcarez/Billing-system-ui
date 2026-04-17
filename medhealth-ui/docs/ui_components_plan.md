# UI Components Plan — Primitive Catalogue

Run A delivers the token layer and primitives documented here.
Runs B and C may rely on everything in the "Available to Runs B and C" section at the bottom.

---

## Primitive 1 — Toast

**Import / usage**: global functions in `js/app.js` (IIFE scope); exposed as `window.showToast`, `window.toastSuccess`, etc. via the global action handler pattern.

### Functions
| Function | Signature | Notes |
|---|---|---|
| `showToast(msg, tone, opts)` | `(string, "success"\|"error"\|"info"\|"warning", {title?, duration?})` | Returns the toast DOM element |
| `toastSuccess(msg, opts?)` | `(string, opts?)` | title defaults to "Saved" |
| `toastError(msg, opts?)` | `(string, opts?)` | title defaults to "Action failed"; role="alert" assertive |
| `toastInfo(msg, opts?)` | `(string, opts?)` | title defaults to "Heads up" |
| `toastWarning(msg, opts?)` | `(string, opts?)` | title defaults to "Heads up" |

### Options object
```js
{
  title: string,       // override default title
  duration: number     // ms before auto-dismiss (default 4200; 0 = persistent)
}
```

### States
- **Idle**: animates in from right (`toast-in`)
- **Dismiss**: `.hide` class triggers `toast-out` animation, then DOM removal after 220 ms
- **Manual close**: `×` button calls same dismiss path
- **Error**: `role="alert"` + `aria-live="assertive"` for screen readers
- **Others**: `role="status"` + `aria-live="polite"`

### CSS classes
`.toast`, `.toast.{success|error|info|warning}`, `.toast-body`, `.toast-title`, `.toast-message`, `.toast-close`, `.toast.hide`
Host: `#toast-host` / `.toast-host` (position: fixed top-right)

### Where alert() was
Evidence pack, remittance review, and all fetch-error paths route through the global `handleAction` error handler at `app.js:779`, which calls `showToast(formatErrorMessage(error), "error", { title: "Action failed" })`. No `alert()` calls remain.

---

## Primitive 2 — Drawer

**Function**: `showDrawer({ title, subtitle, content, actions })` — `js/app.js`

### Props
| Prop | Type | Notes |
|---|---|---|
| `title` | string | Escaped, rendered as `<h2>` |
| `subtitle` | string | Escaped, rendered as `<p>` |
| `content` | string | Raw HTML injected into `.drawer-body` — caller responsible for escaping |
| `actions` | Array<{label, onClick?, href?, className?}> | Rendered as chips in `.drawer-actions` bar |

### Returns
`{ drawer: HTMLElement, close: () => void }`

### States & behaviours (Run A additions)
- **Open**: slide-in animation (`drawer-in` keyframes), overlay fade-in
- **ESC key**: closes drawer, restores focus to previously focused element
- **Backdrop click**: closes drawer
- **Close button**: `[data-drawer-close]` icon-btn, focused automatically on open
- **Focus restore**: `previouslyFocused.focus()` on close

### CSS classes
`.drawer-overlay`, `.drawer`, `.drawer-header`, `.drawer-actions`, `.drawer-body`, `.icon-btn`
Sub-components: `.drawer-grid`, `.mini-card`

### Stub pattern for Run B/C panels
```js
// Use this until the real panel is wired:
showDrawer({
  title: "Evidence Pack · Claim 42",
  subtitle: "Stub — Run B will replace with tabbed view",
  content: `<pre>${escapeHtml(JSON.stringify(payload, null, 2))}</pre>`,
  actions: [{ label: "Close", onClick: () => {} }],
});
```

---

## Primitive 3 — Modal (Confirm + Input)

**Functions**: `showConfirmDialog(opts)`, `showInputDialog(opts)` — `js/app.js`

### showConfirmDialog props
| Prop | Default | Notes |
|---|---|---|
| `title` | required | |
| `message` | required | |
| `confirmLabel` | `"Confirm"` | |
| `tone` | `"warn"` | `"warn"` → `.btn.warn` (red); anything else → `.btn` |

Returns `Promise<boolean>` — true on confirm, false on cancel/ESC/backdrop.

### showInputDialog props
| Prop | Default | Notes |
|---|---|---|
| `title` | required | |
| `label` | required | |
| `value` | `""` | Pre-filled value |
| `submitLabel` | `"Save"` | |

Returns `Promise<string|null>` — string on submit (including empty string), null on cancel/ESC.

### Run A additions
- ESC closes both dialogs
- `Enter` in input field submits `showInputDialog`
- Focus lands on confirm button / input field automatically
- Styled via `.modal-overlay`, `.modal-card`, `.modal-actions` (added in Run A)

---

## Primitive 4 — Button

**CSS class**: `.btn` (primary), `.btn.secondary`, `.btn.warn`

### Variants
| Class | Background | Use |
|---|---|---|
| `.btn` | `--brand-600` | Primary actions |
| `.btn.secondary` | white + `--line-200` border | Secondary / cancel |
| `.btn.warn` | `--color-error` | Destructive confirm |

### States (Run A additions)
| State | CSS | Notes |
|---|---|---|
| Hover | `filter:brightness(.94)` | |
| Active | `filter:brightness(.88)` + `translateY(1px)` | |
| Focus | `box-shadow: var(--focus-ring)` via `:focus-visible` | |
| Disabled | `opacity:.45; pointer-events:none` | `.btn[disabled]` or `.btn:disabled` |
| Loading | `.btn.loading` → spinner pseudo-element, text transparent | Add/remove class in JS |

### Loading pattern
```js
button.classList.add("loading");
button.disabled = true;
try { await doWork(); } finally {
  button.classList.remove("loading");
  button.disabled = false;
}
```

---

## Primitive 5 — Chip / Badge

**CSS class**: `.chip` + tone modifier

### Variants
| Class | Colour | Use |
|---|---|---|
| `.chip` | neutral | Default label |
| `.chip.pass` | green | PASS / READY |
| `.chip.fail` | red | FAIL / BLOCK |
| `.chip.warn` | amber | WARN / INCOMPLETE |
| `.chip.info` | brand-blue | INFO / action chip |

### Run A additions
- `button.chip` and `a.chip` get `cursor:pointer`, hover lift, `:focus-visible` ring
- Non-interactive `.chip` spans keep `cursor:default`

---

## Primitive 6 — Card

**CSS class**: `.card`

Sub-slots: `.card h3` (heading), `.card .muted` (helper text), `.panel` (inset dashed panel for metadata)

No changes in Run A. Run B can extend with `.card.flat` (no shadow) if needed.

---

## Primitive 7 — Table

**CSS class**: `.table`

### Run A additions
- `tbody tr:hover td` — subtle brand tint (`rgba(10,134,189,.04)`)
- `tbody tr[tabindex]:focus-visible td` — stronger tint + no outline (ring on cell instead)
- Sticky header: not yet — add `position:sticky; top:0` to `thead th` when needed in Run B

---

## Design Token File

**Path**: `css/tokens.css`
**Import**: `@import "./tokens.css"` at top of `css/styles.css` (all pages pick it up automatically)

Key tokens for Runs B and C:
| Token | Value | Notes |
|---|---|---|
| `--focus-ring` | `0 0 0 3px rgba(10,134,189,.35)` | All `:focus-visible` states |
| `--transition` | `150ms ease` | Hover colour changes |
| `--transition-slow` | `220ms ease` | Drawer slide, toast animations |
| `--radius-xs` | `8px` | Small badges, modals |
| `--color-success/warn/error/info` | see tokens.css | Semantic status colours |
| `--shadow-sm` | `0 2px 8px rgba(11,18,32,.06)` | Chip hover elevation |

---

## Available to Runs B and C

The following are stable and ready to use after Run A lands:

### Functions (js/app.js IIFE)
- `showToast(message, tone, options)` — toast with title, close button, auto-dismiss, aria
- `toastSuccess / toastError / toastInfo / toastWarning` — shortcuts
- `showDrawer({ title, subtitle, content, actions })` — slide-in drawer with ESC, focus restore
- `showConfirmDialog({ title, message, confirmLabel, tone })` → `Promise<boolean>`
- `showInputDialog({ title, label, value, submitLabel })` → `Promise<string|null>`
- `escapeHtml(str)` — XSS-safe HTML escaping
- `formatErrorMessage(error, attemptedAction)` — human-readable error strings

### CSS tokens (css/tokens.css via styles.css @import)
- All `--brand-*`, `--ink-*`, `--color-{success|warn|error|info}*` variables
- `--focus-ring`, `--transition`, `--transition-slow`
- `--radius`, `--radius-sm`, `--radius-xs`
- `--space-{1..8}`

### CSS classes (css/styles.css)
- `.btn`, `.btn.secondary`, `.btn.warn` + all states
- `.chip`, `.chip.{pass|fail|warn|info}` + interactive states
- `.drawer-overlay / .drawer / .drawer-header / .drawer-actions / .drawer-body / .icon-btn`
- `.drawer-grid / .mini-card`
- `.modal-overlay / .modal-card / .modal-actions`
- `.toast / .toast-body / .toast-title / .toast-message / .toast-close / .toast.hide`
- `.ep-tabs / .ep-tab / .ep-pane / .ep-section / .ep-dl`
- `.audit-badge.{create|update|delete|submit|validate|system}`
- `.retention-grid / .retention-card`
- `.table` with row hover
- `.input` with `:focus` ring

### What Runs B and C should NOT do
- Do not duplicate `showToast` or define another `showDrawer`
- Do not inline hex values — use token variables
- Do not use `alert()`, `confirm()`, or `prompt()` — use the modal/toast primitives above
- Do not add `alert()` in stub handlers — use `toastInfo("Opening X…")` pattern
