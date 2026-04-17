# Fix Plan: Complete Implementation Roadmap

Date created: `2026-04-17`

## Phases and Execution Order

### Phase 0: API Connectivity & Health Check
**Objective:** Fix "Failed to fetch" and provide connection status visibility
**Effort:** 2 hours

- [ ] Add `/health` endpoint to backend
- [ ] Add CORS middleware for cross-origin dev
- [ ] Implement connection status pill in UI
- [ ] Enhanced error message display
- [ ] Test all connectivity scenarios

### Phase 1: Validation Resolution Paths (Complete)
**Objective:** Ensure Jump-to-any flows are fully wired
**Effort:** 3 hours

- [ ] Verify jump-to-diagnoses navigation
- [ ] Verify jump-to-line-items with highlights
- [ ] Verify jump-to-attachments with upload
- [ ] Ensure re-run validation after fix
- [ ] Add loading states on jump buttons

### Phase 2: PMB Evidence Rules
**Objective:** Implement PMB_EVIDENCE_REQUIRED and ATTACHMENT_REQUIRED
**Effort:** 4 hours

- [ ] Add PMB_EVIDENCE_REQUIRED rule in platform_core.py
- [ ] Add ATTACHMENT_REQUIRED rule in platform_core.py
- [ ] Both emit action metadata with NAVIGATE target=ATTACHMENTS
- [ ] PMB NOT_DETECTED includes explainability fields
- [ ] Update backend tests

### Phase 3: Attachments Module (Complete Infrastructure)
**Objective:** Ensure attachments can be uploaded and linked
**Effort:** 2 hours

- [ ] Verify GET /claims/{id}/attachments endpoint
- [ ] Verify POST /claims/{id}/attachments (upload/stub)
- [ ] Verify DELETE /claims/{id}/attachments/{document_id}
- [ ] Test document persistence to Postgres
- [ ] Add attachment UI upload form

### Phase 4A: Realistic Seed Data (Complete)
**Objective:** Create believable test data with SA schemes
**Effort:** 3 hours

- [x] Created docs/seed_manifest.md
- [ ] Update demo_seed.py to include:
  - Discovery Health, GEMS, Bonitas, Momentum, Fedhealth, Polmed schemes
  - 8+ providers with SA contact formats
  - 30+ patients with membership numbers
  - 15+ claims with realistic scenarios
- [ ] Run seed scripts and verify in Postgres
- [ ] Document counts and sample IDs

### Phase 4B: UI Redesign Tasks (Complete)
**Objective:** Modernize UI from alerts to cards and dashboards
**Effort:** 8 hours

**Phase 4B-1: Evidence Pack Redesign**
- [ ] Replace alert with drawer/page layout
- [ ] Create card sections:
  - Snapshot & versions
  - Decision bundles (expandable list)
  - PMB decision & routing
  - Costing preview
  - Payloads (canonical + EDI)
  - Submission history & responses
  - Remittance & reconciliation
- [ ] Add "Download JSON" per artefact
- [ ] Add "Download full pack (zip)" button
- [ ] Add data completeness chip

**Phase 4B-2: Remittance Review Redesign**
- [ ] Create remittance summary card
- [ ] Line-level breakdown table
- [ ] Reconciliation status card
- [ ] Exception reasons list
- [ ] "Open exceptions" and "Download JSON" actions

**Phase 4B-3: Submission Tool Redesign**
- [ ] Add stepper header (Generate → Validate → Submit → Response)
- [ ] Add spinners on action buttons
- [ ] Success toast after each step
- [ ] Transport timeline as event list with filters
- [ ] Idempotency key input with suggestion

**Phase 4B-4: Audit Trail Redesign**
- [ ] Add filter bar (action type, claim ID, date range)
- [ ] Make Details column expandable (drawer)
- [ ] Add event type badges
- [ ] Add "Open Evidence Pack" shortcut
- [ ] Remove raw JSON wall-of-text

**Phase 4B-5: Retention Schema UI**
- [ ] Render as cards instead of code block
- [ ] Include: artefact name, retention period, storage type
- [ ] Add "Copy JSON" button
- [ ] Add "Last changed" + audited message

**Phase 4B-6: Patient Registry Enhancement**
- [ ] Make patient rows clickable
- [ ] Create patient detail page with:
  - Claim-ready profile card
  - Membership + scheme/option
  - Provider & last visit
  - Diagnoses & attachments status
  - Claim status & next action
  - "Open claim" button
- [ ] Link missing indicators to relevant panels

### Phase 5: Toast & UX Feedback
**Objective:** Replace remaining alert() with modern notifications
**Effort:** 2 hours

- [ ] Replace all evidence packet alerts with toasts
- [ ] Replace all remittance alerts with toasts
- [ ] Replace failed fetch alerts with detailed error toasts
- [ ] Add loading state components to buttons
- [ ] Success toast on save actions (diagnosis, attachment, link)
- [ ] Auto re-run validation after save

### Phase 6: Testing & Documentation
**Objective:** Add tests and proof documentation
**Effort:** 4 hours

- [ ] Unit tests for PMB_EVIDENCE_REQUIRED rule
- [ ] Unit tests for ATTACHMENT_REQUIRED rule
- [ ] Integration test: upload attachment → validation clears warning
- [ ] Integration test: set diagnosis primary → PMB re-evaluates
- [ ] UI test: jump-to-attachments navigates and focuses
- [ ] Create docs/test_plan.md with test scenario descriptions
- [ ] Create docs/ui_redesign_checklist.md with before/after notes

### Phase 7: Proof & Final Commit
**Objective:** Verify all changes work end-to-end
**Effort:** 3 hours

- [ ] Start docker compose with all services
- [ ] Seed realistic data
- [ ] Run through jump-to flows in UI
- [ ] Upload attachment and verify persistence
- [ ] Re-run validation and confirm rule clears
- [ ] Check audit events in database
- [ ] Document runtime proof in docs/runtime_proof.md
- [ ] Create commit with all changes

## Detailed Implementation Plan

### Fix Plan Checklist by Component

#### Backend Changes (platform_api.py)

```python
# Add health endpoint
@app.get("/health")
def health():
    db_health = database_healthcheck()
    return {"status": "ok", "db": db_health.get("db", "unknown"), "timestamp": utc_now()}

# Add CORS middleware (for dev cross-origin)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Frontend Changes (js/app.js)

```javascript
// Health check component
let healthCheckInterval = null;
let lastHealthStatus = "unknown";

function startHealthCheck() {
  healthCheckInterval = setInterval(() => {
    fetch("/health") // or API_BASE + "/health"
      .then(r => r.json())
      .then(data => {
        lastHealthStatus = data.status === "ok" ? "ok" : "error";
        updateHealthIndicator(lastHealthStatus);
      })
      .catch(() => {
        lastHealthStatus = "error";
        updateHealthIndicator("error");
      });
  }, 30000);
}

function updateHealthIndicator(status) {
  const pill = document.querySelector("#health-pill");
  if (!pill) return;
  pill.className = `health-pill ${status}`;
  pill.textContent = status === "ok" ? "🟢 API OK" : "🔴 API Down";
}

// Call on page load
window.addEventListener("load", () => startHealthCheck());
```

#### CSS Changes (css/styles.css)

```css
.health-pill {
  padding: 0.4rem 0.8rem;
  border-radius: 9999px;
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: all 0.2s ease;
}

.health-pill.ok {
  background: #ecfdf5;
  color: #065f46;
  border: 1px solid #6ee7b7;
}

.health-pill.error {
  background: #fef2f2;
  color: #7f1d1d;
  border: 1px solid #fca5a5;
}

.health-pill:hover {
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* Evidence pack cards */
.evidence-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  background: #f8fafc;
}

.evidence-card-title {
  font-weight: 600;
  font-size: 1rem;
  color: #1e293b;
  margin-bottom: 0.5rem;
}

.evidence-card-content {
  font-size: 0.9rem;
  color: #475569;
  line-height: 1.6;
}
```

## Risk Mitigation

### Risk 1: API Connectivity Changes Break Existing Flows
**Mitigation:**
- CORS is additive, not breaking
- Health endpoint is GET-only, safe
- Fall back to original hard-coded URL if env var not set

### Risk 2: Seed Data Creates Duplicate Records
**Mitigation:**
- Seeds check for existing records by unique key (claim_number, mrn)
- Purge and recreate if exists
- Scripts are idempotent

### Risk 3: UI Redesign Introduces Visual Regressions
**Mitigation:**
- Keep existing functionality unchanged
- New UI components add to page, don't replace critical flows
- Test on multiple browsers before commit

### Risk 4: Database Performance with 30+ Patients
**Mitigation:**
- Add indexes on frequently queried columns (status, scheme_id, mrn)
- Paginate patient list queries (limit 20 per request)
- Cache scheme lookup results

## Time Estimate

| Phase | Effort | Status |
|-------|--------|--------|
| Phase 0 | 2h | ⏳ TODO |
| Phase 1 | 3h | ⏳ TODO |
| Phase 2 | 4h | ⏳ TODO |
| Phase 3 | 2h | ⏳ TODO |
| Phase 4A | 3h | ⏳ TODO |
| Phase 4B | 8h | ⏳ TODO |
| Phase 5 | 2h | ⏳ TODO |
| Phase 6 | 4h | ⏳ TODO |
| Phase 7 | 3h | ⏳ TODO |
| **Total** | **31h** | |

**Parallel Work:** Phases 0, 1, 2, 3, 4A can be done in parallel with 4B (UI design). Realistic timeline: **12-16 hours serial execution**.

## Success Criteria

- [ ] No "Failed to fetch" errors when backend is running
- [ ] Health pill shows accurate status
- [ ] Jump-to-any navigation works for all scenarios
- [ ] PMB_EVIDENCE_REQUIRED blocks/warns appropriately
- [ ] Attachments upload and persist
- [ ] Evidence Pack shows structured cards instead of alerts
- [ ] Remittance, Submission Tool, Audit Trail modernized
- [ ] Patient Registry shows clickable profiles
- [ ] All tests pass
- [ ] No performance degradation on seed data queries
- [ ] Audit trail shows all material actions

