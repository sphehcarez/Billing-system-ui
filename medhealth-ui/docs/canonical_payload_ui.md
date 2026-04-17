# Canonical Payload UI Specification

## Overview

The canonical payload preview replaces raw inline-styled article elements with properly classed `.payload-tile` cards. Six stage tiles are rendered from either the backend's `structured_tiles` array or, as fallback, the UI-only `canonicalToStages(payload)` transformer.

## Tile Structure

Each tile is a `.payload-tile` element:

```html
<article class="payload-tile">
  <header class="payload-tile-header" data-toggle>
    <div class="payload-tile-title">
      <span class="payload-tile-name">Parties</span>
      <span class="muted payload-tile-summary">scheme / member / patient / provider</span>
    </div>
    <span class="chip [pass|warn|fail]">COMPLETE</span>
    <button class="payload-tile-toggle" aria-label="Toggle" aria-expanded="true">▾</button>
  </header>
  <div class="payload-tile-body">
    <dl class="ep-dl">…</dl>
    <!-- missing field prompts with jump-to links -->
    <div class="payload-missing-item">
      <span>…missing field message…</span>
      <button data-jump-target="diagnoses">Go to Diagnoses</button>
    </div>
  </div>
</article>
```

## Six Standard Tiles

| # | Title | Key backend fields checked | Jump-to target |
|---|---|---|---|
| 1 | Parties | scheme_id, member_number, patient_id, provider_id, practice_number | — |
| 2 | Visit | service_date, preauth_number, visit_type | — |
| 3 | Diagnoses | primary_icd10, secondary list, linkage_complete | diagnoses |
| 4 | Line items | tariff_code, quantity, claimed_amount, diagnosis_links | line_items |
| 5 | Totals & Routing | pmb_status, route, claimed_total, allowed_total | — |
| 6 | Submission metadata | channel, idempotency_key, correlation_id | submission_tool |

## canonicalToStages(payload) — Transformer Contract

**File**: js/app.js (UI-only, no business rules)

**Inputs**: raw canonical payload object (from structured payload API response or claim detail)

**Output**: array of tile objects compatible with `structured_tiles` format

```
{ title, summary, status, fields: [{label, value}], missing_fields: [{message, action?}] }
```

**Rules**:

- `status = "complete"` if all required fields for that stage are present and non-null
- `status = "warn"` if optional fields missing
- `status = "incomplete"` if required fields missing
- UI only checks field presence/emptiness — never applies business rules
- If backend returns `structured_tiles`, use those directly (they have richer context)

## View JSON Toggle

Below all tiles: `<details><summary class="chip">View JSON</summary>…</details>` with Copy button and `<pre>` block. Default closed.

## CSS Classes

`.payload-tile`, `.payload-tile-header`, `.payload-tile-title`, `.payload-tile-name`, `.payload-tile-summary`, `.payload-tile-body`, `.payload-tile-toggle`, `.payload-missing-item`
