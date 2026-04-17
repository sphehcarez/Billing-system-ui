# UI Inventory — MedHealth Billing Platform

## Framework
- Static HTML + vanilla JS IIFE (no React/Vite/Next/webpack)
- Entry: DOMContentLoaded listener in js/app.js (3419 lines) inside a single IIFE
- API client: js/api-client.js (542 lines), exposes window.api = new BillingAPI()
- Styles: css/styles.css (379 lines) — single stylesheet, all pages import it
- No build step; pages served directly

## Pages (HTML entry points)
| File | Title | Module |
|---|---|---|
| index.html | Login | auth |
| dashboard.html | Dashboard | dashboard |
| patients.html | Patients | patients |
| providers.html | Providers | providers |
| claims.html | Claims | claims |
| claim_detail.html | Claim detail | claim-detail |
| payments.html | Payments | payments |
| reports.html | Reports | reports |
| audit.html | Audit | audit |
| users.html | Users | users |
| settings.html | Settings | settings |
| manual.html | Manual | static-doc |

## Components (all in js/app.js)

### Utility primitives (lines approx.)
| Function | Type | Line range | Notes |
|---|---|---|---|
| showToast(msg, tone, opts) | Toast | 388–401 | CANONICAL — second definition; first definition (lines 3–21) is dead code |
| dismissToast(toast) | Toast helper | 22–25 | dead code (inside dead first definition) |
| toastSuccess/Error/Info/Warning | Toast shortcuts | 26–29 | call the dead first showToast; need remapping |
| showDrawer({title,subtitle,content,actions}) | Drawer | 416–455 | right-anchored; missing ESC key handler |
| showConfirmDialog({title,msg,label,tone}) | Modal | 457–484 | backdrop click, no ESC |
| showInputDialog({title,label,value,submitLabel}) | Modal | 486–518 | backdrop click, no ESC |
| showFormModal({title,fields,onSubmit,...}) | Modal | not found in scan; implied by CREATE_CONFIG |
| ensureToastHost() | Dom util | 377–386 | creates #toast-host |
| formatErrorMessage(error, action) | Error format | 403–414 | handles NETWORK_ERROR + HTTP status |
| escapeHtml(str) | XSS safety | elsewhere | used throughout for output |
| formatCurrency(val) | Format | elsewhere | formatCurrency(cents/100) |
| formatDateTime(iso) | Format | elsewhere | |

### Page-level loaders
| Function | Page | Notes |
|---|---|---|
| loadPatients() | patients.html | calls _loadPatientBalances() |
| openPatientProfile(id) | patients.html | fetches balance+invoices, renders drawer |
| renderPatientProfileDrawer(...) | patients.html | membership, billing summary, pay now |
| handlePayInvoice(pid, cents, invId) | patients.html | EFT payment with idempotency |
| handleViewEvidence() | claim_detail.html | opens Evidence Pack drawer |
| handleViewRemittance() | claim_detail.html | opens Remittance drawer |
| handleGenerateEdi() | claim_detail.html | toast on complete |
| handleValidateEdi() | claim_detail.html | toast success/error |
| handleSubmitEdiSwitch() | claim_detail.html | idempotency key dialog then submit |
| buildEvidencePackMarkup(evidence) | claim_detail.html | 6-tab markup |
| renderAuditTrail() | audit.html | filter bar + badge rows |
| handleViewAuditDetail(id) | audit.html | drawer with hashes |

## CSS classes (all in css/styles.css)

### Design tokens (:root)
--brand-900/800/700/600/500/200, --ink-900/700/500, --line-200, --bg-50, --card, --warn, --fail, --pass, --shadow, --radius, --radius-sm, --mono, --sans

### Layout
.shell (grid 280px + 1fr), .sidebar, .brand, .nav, .main, .topbar, .h1, .actions, .pill, .grid (12-col), .split (1.2fr 0.8fr), .panel

### Interactive primitives
.btn, .btn.secondary (missing: .btn.warn, .btn[disabled], .btn.loading, :focus-visible)
.chip, .chip.pass/.fail/.warn/.info (missing: cursor, :focus-visible)
.input (missing: :focus state with ring)
.table th/td (missing: tbody tr:hover)

### Component CSS (added in previous sessions)
.drawer-overlay, .drawer, .drawer-header, .drawer-actions, .drawer-body, .icon-btn
.drawer-grid, .mini-card
.ep-tabs, .ep-tab, .ep-tab.active, .ep-pane, .ep-pane.active, .ep-section, .ep-dl
.audit-badge (create/update/delete/submit/validate/system), .audit-filter-bar
.retention-grid, .retention-card

### Toast (MISMATCH — CSS styles .toast-msg/.toast-close but canonical JS renders .toast-title/.toast-message)
#toast-host, .toast, .toast.success/error/info/warning, .toast-close, toast-in/toast-out animations
Missing: .toast-body, .toast-title, .toast-message, .toast.hide

### Modal (MISSING from CSS — JS uses these classes)
.modal-overlay, .modal-card, .modal-actions (not styled)
.btn.warn (used in confirm dialog, not styled)

## Alert() call sites
**None found.** All alert() calls were removed in a previous refactor. Evidence pack, remittance review, and fetch-error paths already use toastError() / showToast(..., "error", ...) via the global action error handler at app.js:779.

## Env / base-URL references
| File | Line | Pattern |
|---|---|---|
| js/api-client.js | 13–20 | resolveApiBaseUrl() — reads meta[name="medhealth-api-base"], localStorage override, port 8001 fallback |
| js/api-client.js | 19 | "http://localhost:8001/api" (final fallback) |
| js/api-client.js | 22–23 | API_BASE_URL, API_ORIGIN |

## Known issues to fix in Run A
1. Duplicate `showToast` — lines 3–30 are dead code; canonical is lines 388–401 but its CSS structure doesn't match styles.css
2. No CSS for .toast-title, .toast-message, .toast.hide
3. No CSS for .modal-overlay, .modal-card, .modal-actions, .btn.warn
4. showDrawer missing ESC key handler and initial focus
5. No explicit :focus-visible rings on buttons, chips, inputs
6. No table row hover
7. No .btn[disabled], .btn.loading states
8. No separate token file — all vars inline in styles.css :root
