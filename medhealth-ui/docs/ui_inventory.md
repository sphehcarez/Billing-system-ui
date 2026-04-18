# UI Inventory — MedHealth Billing Platform
_Last updated: 2026-04-17_

---

## 1. Stack Reality

| Attribute | Value |
|---|---|
| Framework | Zero-build static HTML + vanilla JS IIFE |
| Entry point | `DOMContentLoaded` listener inside a single IIFE in `js/app.js` (~3 800 lines) |
| API client | `js/api-client.js` (~560 lines) — `window.api = new BillingAPI()` |
| Styles | `css/styles.css` (single stylesheet, all pages import it) |
| Build step | **None** — `python -m http.server` or nginx serves files directly |
| Package manager | None |
| CI | None at this time |

---

## 2. HTML Surface Map (12 pages)

| File | Title / Module | Primary content |
|---|---|---|
| `index.html` | Login / auth | Username + password form |
| `dashboard.html` | Dashboard | Summary KPI tiles |
| `patients.html` | Patients | Patient list, search, profile drawer |
| `providers.html` | Providers | Provider list |
| `claims.html` | Claims | Claim list with filter bar |
| `claim_detail.html` | Claim detail / cockpit | Two-column cockpit: lifecycle + payload left; summary + attachments right |
| `payments.html` | Payments | Payment list |
| `reports.html` | Reports + Insights badge | Report views |
| `audit.html` | Audit | Event log with filter bar + detail drawer |
| `users.html` | Users | User management |
| `settings.html` | Settings | Config |
| `manual.html` | Manual | Static documentation |

---

## 3. Component Inventory

### 3a. Utility primitives (in `js/app.js` IIFE)

| Function | Type | Status | Notes |
|---|---|---|---|
| `showToast(msg, tone, opts)` | Toast | ✅ Canonical | Renders `.toast-title` + `.toast-message`; auto-dismiss 4 200 ms |
| `toastSuccess/Error/Info/Warning` | Shortcuts | ✅ | Call canonical `showToast` |
| `dismissToast(toast)` | Helper | ✅ | `.hide` class → 220 ms → DOM removal |
| `ensureToastHost()` | DOM util | ✅ | Creates `#toast-host` once |
| `showDrawer({title,subtitle,content,actions})` | Drawer | ✅ | Right-anchored; ESC + backdrop close; focus restore |
| `showConfirmDialog({title,message,confirmLabel,tone})` | Modal | ✅ | Returns `Promise<boolean>`; ESC closes |
| `showInputDialog({title,label,value,submitLabel})` | Modal | ✅ | Returns `Promise<string\|null>`; Enter submits |
| `escapeHtml(str)` | XSS safety | ✅ | Used for all dynamic output |
| `formatErrorMessage(error, action)` | Error format | ✅ | Handles network + HTTP status |
| `formatCurrency(val)` | Format | ✅ | Accepts cents/100 |
| `formatDateTime(iso)` | Format | ✅ | ISO → locale string |
| `setInlineBanner(id, msg, tone)` | Banner | ✅ | Contextual card feedback |
| `clearInlineBanner(id)` | Banner | ✅ | Hides banner element |

### 3b. Page-level features

| Function | Page | Status |
|---|---|---|
| `loadPatients()` | patients.html | ✅ |
| `openPatientProfile(id)` | patients.html | ✅ — uses `getPatientClaimContext()` |
| `renderPatientProfileDrawer(...)` | patients.html | ✅ |
| `handlePayInvoice(pid, cents, invId)` | patients.html | ✅ |
| `loadClaimDetail()` | claim_detail.html | ✅ |
| `canonicalToStages(payload)` | claim_detail.html | ✅ — client-side tile derivation |
| `renderStructuredPayload()` | claim_detail.html | ✅ — `.payload-tile` details/summary |
| `renderSubmissionStepper(stepStates)` | claim_detail.html | ✅ |
| `renderEdiPanel()` | claim_detail.html | ✅ |
| `renderTransportTimeline()` | claim_detail.html | ✅ — with event-type filter |
| `handleViewTransportDetail(logId)` | claim_detail.html | ✅ |
| `renderAttachmentsSummary()` | claim_detail.html | ✅ |
| `renderQuickAudit()` | claim_detail.html | ✅ |
| `handleGenerateEdi()` | claim_detail.html | ✅ — advances stepper |
| `handleValidateEdi()` | claim_detail.html | ✅ — advances stepper |
| `handleSubmitEdiSwitch()` | claim_detail.html | ✅ — advances stepper |
| `renderAuditTrail()` | audit.html | ✅ |
| `handleViewAuditDetail(id)` | audit.html | ✅ |

### 3c. Components NOT YET built (gap list)

| Component | Notes |
|---|---|
| Global nav active-state highlight | Sidebar `<a>` has no `.active` styling wired |
| Skeleton / loading states | All cards show "Loading…" text; no skeleton shimmer |
| Empty-state illustrations | Tables show plain text when empty |
| Responsive / mobile layout | `.shell` grid is fixed 280 px sidebar; no breakpoints |
| Keyboard shortcuts | No `?` help, no `Alt+` nav shortcuts |
| Inline editable fields | All edits go through drawers/modals |
| Data export (CSV) | Reports page has no CSV download |

---

## 4. CSS Class Inventory

### 4a. Design tokens (`:root` in `css/styles.css`)

```
--brand-900/800/700/600/500/200
--ink-900/700/500
--line-200
--bg-50
--card          (white)
--warn          (#e6ac00 amber background)
--fail          (#c0392b red)
--pass          (#1a9c5b green)
--shadow
--radius        (12px)
--radius-sm     (8px)
--mono, --sans
```

**No separate token file** — all vars are inline in `:root`. Run A added `css/tokens.css` with expanded token set; `styles.css` imports it.

### 4b. Layout classes

`.shell`, `.sidebar`, `.brand`, `.nav`, `.main`, `.topbar`, `.h1`, `.actions`, `.pill`, `.grid` (12-col), `.split` (1.2fr 0.8fr), `.panel`, `.field`, `.label`, `.kv`, `.row-actions`, `.muted`, `.code`

### 4c. Cockpit layout (claim_detail.html)

`.cockpit-header`, `.cockpit-body`, `.cockpit-left`, `.cockpit-right`, `.cockpit-id`, `.cockpit-member`, `.cockpit-actions`
`.lifecycle-card`, `.lifecycle-stage`, `.lifecycle-stage-header`, `.lifecycle-stage-name`, `.lifecycle-stage-actions`
`.inline-banner`, `.inline-banner.error/.warn/.success`
`.payload-tile`, `.payload-tile-header`, `.payload-tile-body`, `.payload-tile-row`
`.submission-stepper`, `.stepper-step`, `.stepper-step[data-state=idle/active/complete/error]`, `.stepper-connector`, `.stepper-indicator`, `.stepper-label`
`.edi-status-card`, `.edi-actions`
`.transport-event`, `.transport-event-header`, `.transport-event-type`, `.transport-event-time`, `.transport-event-detail`

### 4d. Interactive primitives

`.btn` (primary), `.btn.secondary`, `.btn.warn`, `.btn[disabled]`, `.btn.loading`
`.chip`, `.chip.pass/.fail/.warn/.info`
`.input`
`.table th/td` with `tbody tr:hover`

### 4e. Component CSS

`.drawer-overlay`, `.drawer`, `.drawer-header`, `.drawer-actions`, `.drawer-body`, `.icon-btn`
`.drawer-grid`, `.mini-card`
`.modal-overlay`, `.modal-card`, `.modal-actions`
`.toast`, `.toast-body`, `.toast-title`, `.toast-message`, `.toast-close`, `.toast.hide`, `.toast.success/.error/.info/.warning`
`#toast-host` / `.toast-host`
`.ep-tabs`, `.ep-tab`, `.ep-tab.active`, `.ep-pane`, `.ep-pane.active`, `.ep-section`, `.ep-dl`
`.audit-badge.{create|update|delete|submit|validate|system}`, `.audit-filter-bar`
`.retention-grid`, `.retention-card`

---

## 5. Contrast Audit (WCAG 2.2 AA)

| Token | Hex | Background | Ratio | Result | Fix |
|---|---|---|---|---|---|
| `--brand-600` (link/action text) | `#0a86bd` | white `#fff` | **4.1 : 1** | **FAIL** (needs 4.5) | Use `--brand-700` `#0872a1` for text; keep `--brand-600` for large UI chrome only |
| `--color-warn` (amber text) | `#b36b00` | `--color-warn-bg` `#fef3cd` | **4.03 : 1** | **FAIL** (needs 4.5) | Darken to `#7c4a00` |
| `--color-error` | `#c0392b` | white | 5.1 : 1 | PASS | — |
| `--color-success` | `#1a9c5b` | white | 4.6 : 1 | PASS | — |
| `--ink-900` | `#0b1220` | white | 18.9 : 1 | PASS | — |
| `--ink-700` | `#3d4a5c` | white | 7.8 : 1 | PASS | — |

---

## 6. Palette → Semantic Token Mapping

| Role | Current token | Proposed semantic name | Notes |
|---|---|---|---|
| Primary brand action | `--brand-600` | `--color-action` | Buttons, active chips — switch to `--brand-700` for AA text |
| Brand accent / light | `--brand-200` | `--color-action-subtle` | Highlight backgrounds |
| Body text | `--ink-900` | `--color-text-primary` | |
| Secondary text | `--ink-700` | `--color-text-secondary` | |
| Muted / placeholder | `--ink-500` | `--color-text-muted` | |
| Page background | `--bg-50` | `--color-bg` | |
| Card background | `--card` (white) | `--color-surface` | |
| Border / rule | `--line-200` | `--color-border` | |
| Success / pass | `--pass` / `--color-success` | `--color-status-pass` | |
| Warning / incomplete | `--warn` / `--color-warn` | `--color-status-warn` | Darken text token to `#7c4a00` |
| Error / fail | `--fail` / `--color-error` | `--color-status-fail` | |
| Info / in-progress | `--brand-600` | `--color-status-info` | |

---

## 7. Ambiguities Requiring Input

The modernisation brief asks: stop if **framework choice**, **component library**, or **palette mapping** is unclear. Four decisions remain open:

### A — Build step
**Options:**
1. ✅ _Recommended_ — Stay zero-build. Add `css/tokens.css` + better scoped CSS. Ship with `python -m http.server` as now.
2. Add Vite. Enables CSS imports, TypeScript, tree-shaking. Requires `npm install` and a build step in Docker.
3. Add Vite + Lit Web Components. True component encapsulation but largest migration cost.

**Recommendation:** Option 1. The app is medium complexity (~4 000 JS lines, 12 pages). Zero-build already works; a build step adds toolchain complexity for limited gain at this stage.

### B — Icon library
**Options:**
1. ✅ _Recommended_ — SVG sprite (`assets/icons.svg`) + `<use href="#">` — zero runtime, tree-shakeable, no CDN dependency.
2. Lucide via CDN (`<script src="https://unpkg.com/lucide@latest">`) — easy but CDN dependency and runtime cost.
3. No icons this pass — defer to a later run.

**Recommendation:** Option 1 if icons are in scope; Option 3 if not.

### C — `/preview` endpoint
The current `canonicalToStages()` function derives payload tiles client-side as a fallback because the backend `/structured` endpoint sometimes returns empty tiles.

**Options:**
1. ✅ _Recommended_ — Add `GET /claims/{id}/preview` endpoint that returns pre-computed tiles with completeness flags. Removes client-side derivation logic.
2. Enrich the existing `/structured` endpoint to always return tiles.
3. Keep client-side `canonicalToStages()` as-is indefinitely.

**Recommendation:** Option 2 (enrich `/structured`) is lowest-effort; Option 1 is cleaner long-term.

### D — EDI status polling
EDI `generate`, `validate`, and `submit` are currently synchronous — the UI waits for the HTTP response. For slow Switch connections this blocks the UI.

**Options:**
1. ✅ _Recommended_ — Keep synchronous for now; add loading state to buttons (already in `.btn.loading` CSS).
2. Add `GET /edi/status/{artifactId}` polling endpoint + client-side poll loop.
3. WebSocket for real-time transport events.

**Recommendation:** Option 1 unless the Switch integration adds async behaviour.

---

## 8. Proposed Work Order (post-decision)

| Phase | Scope | Blocker |
|---|---|---|
| **Token expansion** | Expand `css/tokens.css` with semantic aliases; fix two contrast violations | None |
| **Base component refactor** | `.btn`, `.chip`, `.input`, `.card`, `.table` — states, focus rings, loading | Token expansion done |
| **Navigation active state** | Wire `data-module` → `.active` in sidebar `<nav>` | None |
| **Skeleton / empty states** | Add shimmer CSS class + JS helper; empty-state markup | None |
| **`/preview` endpoint** (if chosen) | Backend: enrich `/structured` or add `/preview`; remove `canonicalToStages()` client workaround | Decision C |
| **Icons** (if chosen) | Build `assets/icons.svg` sprite; add `<use>` wrappers in HTML | Decision B |
| **Mobile / responsive** | Add breakpoints to `.shell`; collapsible sidebar | None |
| **Accessibility pass** | ARIA roles, keyboard nav, skip link | Base components done |
| **Keyboard shortcuts** | `?` overlay, `Alt+` nav | Accessibility pass done |
