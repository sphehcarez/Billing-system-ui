# Submission Tool UI Specification

## Overview

The submission tool (card `#submission_tool`) provides a four-step stepper workflow with action buttons, a status card, an idempotency key input, transport timeline, and secondary raw EDI view.

## Stepper: Generate → Validate → Submit → Response

```html
<div class="submission-stepper" id="submission-stepper">
  <div class="stepper-step" data-step="generate">
    <div class="stepper-indicator"><span class="stepper-num">1</span></div>
    <span class="stepper-label">Generate</span>
  </div>
  <div class="stepper-connector"></div>
  <!-- Validate, Submit, Response similarly -->
</div>
```

Steps use data-state: `idle | active | complete | error`

CSS: `stepper-step[data-state="complete"]` fills circle green, `active` fills brand-blue, `error` fills red.

## Action Buttons (`.btn` with loading states)

```
[Generate EDI]   [Validate EDI]   [Download EDI]   [Submit via Switch] (disabled until validated)
```

Submit via Switch disabled until `state.ediStepperState.validate === "complete"`.

## Status Card (`#edi-status-card`)

- `#edi-feedback` — short human description of current state
- `#edi-artifact-info` — hidden until artifact exists: shows artifact_id, validation chip
- `#edi-idempotency-key` — input, pre-filled with suggested default on generate
- `#edi-error-banner` — `.inline-banner` error/warning, hidden by default

## Transport Timeline (`#transport-log-timeline`)

Filter select: All / Generated / Validated / Queued / Sent / Response

Each event rendered as `.transport-event`:

```html
<div class="transport-event">
  <div class="transport-event-main">
    <span class="audit-badge {class}">{event}</span>
    <span class="muted">{timestamp}</span>
  </div>
  <div class="transport-event-detail muted">{one-line summary from details}</div>
  <button class="chip info" data-action="view-transport-detail" data-id="{log_id}">Detail</button>
</div>
```

Row click → `handleViewTransportDetail(logId)` → Drawer with formatted JSON + Copy button.

## Raw EDI (secondary)

Collapsed `<details>` below timeline. Contains `<pre id="edi-preview">` and Copy button. Default collapsed.

## CSS Classes (new in Run B)

`.submission-stepper`, `.stepper-step`, `.stepper-connector`, `.stepper-indicator`, `.stepper-num`, `.stepper-label`

`.transport-event`, `.transport-event-main`, `.transport-event-detail`

`.inline-banner`, `.inline-banner.error`, `.inline-banner.warn`, `.inline-banner.success`

`.payload-tile` and variants (see canonical_payload_ui.md)

`.cockpit-header`, `.cockpit-body`, `.cockpit-left`, `.cockpit-right`, `.cockpit-id`, `.cockpit-actions`

`.lifecycle-card`, `.lifecycle-card-header`

## Shared Helpers Available to Run C

The following new helpers are defined in js/app.js after Run B:

- `canonicalToStages(payload)` — transformer from canonical JSON to tile array
- `handleViewTransportDetail(logId)` — opens a formatted JSON drawer for a transport log entry
- `renderSubmissionStepper(stepStates)` — updates stepper DOM from `state.ediStepperState`
- `renderTransportTimeline()` — now has category filter and drawer-linked rows
- `setInlineBanner(id, message, tone)` / `clearInlineBanner(id)` — show/hide `.inline-banner` elements
- CSS: `.inline-banner`, `.transport-event`, `.payload-tile`, `.submission-stepper`, stepper step states

Run C (Evidence, Remittance, Audit, Retention) can use `handleViewTransportDetail` as a pattern for any "view JSON in drawer" action, and `setInlineBanner` for contextual error display.
