# Claim Cockpit UI Specification

## Overview

The claim cockpit is the primary operator surface for single-claim processing. It wraps all lifecycle actions, data entry (diagnoses, line items), payload preview, and submission in one scrollable view. Run B introduces a sticky header, two-column body layout, Button loading states replacing "Working..." text, and inline error banners inside relevant cards.

## Component Tree

```
claim_detail.html
├── .shell
│   ├── aside.sidebar             (unchanged — shared nav)
│   └── main.main
│       ├── .topbar               (unchanged — search + API Docs + New)
│       ├── #cockpit-header       (sticky: claim ID + status chip + member + action bar)
│       └── #cockpit-body         (CSS grid, 2 columns)
│           ├── #cockpit-left     (1.4fr)
│           │   ├── .lifecycle-card  Readiness
│           │   ├── .lifecycle-card  Closure + Post-closure
│           │   ├── #diagnoses    (ICD-10 data entry card — unchanged)
│           │   ├── #line_items   (Line items + diagnosis linking — unchanged)
│           │   ├── .payload-card (Canonical payload stages)
│           │   └── .submission-card  (Stepper + transport timeline)
│           └── #cockpit-right    (1fr, sticky top)
│               ├── .summary-card   (Patient, provider, dates)
│               ├── .pmb-costing-card  (PMB decision + costing)
│               ├── .attachments-summary-card
│               └── .quick-audit-card   (last 3–5 events)
```

## Sticky Header (#cockpit-header)

- `position: sticky; top: 0; z-index: 100`
- Left: `.cockpit-id` block — Claim number (`.code`), member number, status chip (`#claim-status-chip`)
- Right: `.cockpit-actions` — View Evidence (`.btn.secondary`), View Remittance (`.btn.secondary`), Build Payload (`.btn`)
- On narrow screens: collapses to compact two-row bar

## Lifecycle Cards

Each lifecycle step is its own `.card.lifecycle-card` with:

- Header: stage name (`<h3>`) + status chip
- Action buttons (`.btn.secondary` or `.btn`) using Run A loading state
- `#readiness-banner`, `#closure-banner`, etc. — `.inline-banner` that shows error/warning text inline when the action fails; hidden by default

## Loading State Contract

`handleAction()` now adds `.btn.loading` to the button (CSS spinner, text hidden) instead of setting `textContent = "Working..."`. Non-`.btn` elements (chips) still fall back to text replacement. Button restores state in `finally` regardless of success or failure.

## Two-Column Body

```css
#cockpit-body {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
  align-items: start;
}
#cockpit-right { position: sticky; top: 64px; }
@media (max-width: 980px) {
  #cockpit-body { grid-template-columns: 1fr; }
  #cockpit-right { position: static; }
}
```

## IDs Preserved (backward-compatible)

All existing IDs used by app.js are preserved in new layout: `claim-number`, `claim-member`, `claim-status-chip`, `readiness-status`, `closure-status`, `post-closure-status`, `claim-pmb-summary`, `diagnoses`, `line_items`, `payload-preview`, `submission_tool`, `edi-feedback`, `edi-preview`, `transport-log-timeline`, `diagnosis-*`, `line-items-*`, `icd10-options`.
