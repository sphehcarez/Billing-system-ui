# Data Realism Map — Phase 0 Scan Results

Generated: 2026-04-17

## 1. Placeholder Strings — File:Line Locations

### backend/demo_seed.py
| Line | String | Action |
|---|---|---|
| 10 | `DEMO_SCHEME = "SCHEMEA"` | Kept as stable internal ID; `display_name = "MedHealth Classic Scheme"` added |
| 11 | `DEMO_OPTION = "OPT1"` | Kept as stable internal ID; `display_name = "Standard Option"` added |
| 481–485 | Patient names: `"Anele Demo"`, `"Mpho Demo"`, etc. | Replaced with realistic SA names |
| 549–550 | `"DEMO-PRACTICE-001"`, `"DSP Demo Provider"` | Replaced with real suburb practices |
| 736–762 | `DEMO_DTP_001`, `DEMO_CDL_001` PMB conditions | PMB IDs stable; names changed to clinical descriptions |
| 805 | `source="DEMO business-owned production data required"` | Replaced with `source="synthetic_reference_data"` |

### backend/app_server.py  
| Line | String | Action |
|---|---|---|
| 142 | `scheme: str = "SCHEMEA"` | Internal ID — kept, UI reads `display_name` |
| 224–225 | `"scheme": "SCHEMEA"`, `"option": "OPT1"` | Internal IDs — kept |
| 903–905 | `demo_credentials` in root response | Replaced with generic credential hints |

### backend/platform_core.py
| Line | String | Action |
|---|---|---|
| 1619/1629 | `"TAR-DEMO-DSP-CONS001"` tariff IDs | Stable IDs; `is_synthetic=True` flag added |
| 1552–1602 | PMB placeholder conditions | Clinical names added; IDs preserved |

### js/app.js
| Line | String | Action |
|---|---|---|
| 1556 | `` `demo/${resolveClaimId(...)` `` | Updated to use real path |

### index.html
| Line | String | Action |
|---|---|---|
| 17 | `<span>Demo mode</span><strong>Enabled</strong>` | Removed |
| 37 | `placeholder="e.g., demo.user"` | Changed to `placeholder="e.g., admin"` |
| 90 | Demo credentials tooltip | Removed |

---

## 2. Alert/Confirm Calls

| File | Line | Call | Action |
|---|---|---|---|
| js/app.js | 2688 | `alert(error.message)` | → `toastError(error.message)` |
| index.html | 61 | `alert("Please enter username and password")` | → inline `showLoginError()` |
| index.html | 78 | `alert("Authentication failed: " + error.message)` | → inline `showLoginError()` |

---

## 3. Money Column Audit (pre-fix)

All columns using `NUMERIC(12,2)` or `float` — **converted to `BIGINT` cents**:

| File | Column | Old Type | New Type |
|---|---|---|---|
| db_schema.py:303 | `rate_amount` | `Numeric(12,2)` | `BigInteger` (cents) |
| db_schema.py:349–351 | `quantity`, `unit_price`, `claimed_amount` | `Numeric(12,2)` | `BigInteger` (cents) |
| db_schema.py:461–464 | `claimed_total`, `allowed_total`, `pmb_allowed_total`, `member_liability_estimate` | `Numeric(12,2)` | `BigInteger` (cents) |
| db_schema.py:599,610 | `amount` (payments, ledger) | `Numeric(12,2)` | `BigInteger` (cents) |
| migrations/002 | All monetary columns | `NUMERIC(12,2)` | `BIGINT` |
| platform_core.py:303 | `member_liability_estimate` | `float` | `int` (cents) |

New tables (`invoices`, `copay_items`, `patient_balances`) use `BIGINT` from creation.

---

## 4. Seed Entry Points

| File | Function | Called From |
|---|---|---|
| demo_seed.py | `seed_reference_data(store)` | conftest.py, platform_api.py startup |
| demo_seed.py | `seed_uat_scenarios(store)` | conftest.py, docker-entrypoint |
| platform_core.py:1437 | `PlatformStore.seed()` | Constructor (in-memory mode) |
| platform_core.py:1533 | `_seed_coding_and_pmb_reference()` | `seed()` |
| platform_core.py:1834 | `_seed_claims()` | `seed()` |

---

## 5. Patient Registry Rendering

| File | Location | Notes |
|---|---|---|
| patients.html | `<tbody>` — table rows rendered by JS | Updated: rows now clickable, Status + Balance chips |
| js/app.js:785 | `renderPatientActions()` | Updated: each row has `role="button"`, keyboard handler |
| js/app.js | `openPatientProfile(id)` | **New** — fetches `/claim-ready-profile` + `/balances`, renders drawer |

---

## 6. Costing / Member Liability

| File | Location | Notes |
|---|---|---|
| platform_core.py:889 | `CostingPreviewService.evaluate()` | Updated to use cents arithmetic |
| platform_core.py:901–902 | `claimed_total`, `allowed_total` sum | Changed: sum of `line.claimed_amount` (int cents), no float |
| platform_core.py:911 | `member_liability` | Changed: `max(0, claimed_cents - allowed_cents)` as int |
| platform_api.py | New: `GET /api/patients/{id}/claim-ready-profile` | Returns `billing_summary` with `*_cents` fields |

---

## 7. Existing DB Tables (38 tables pre-migration)

`reference_versions`, `app_settings`, `users`, `patients`, `providers`, `claims`, `claim_drafts`, `claim_versions`, `billing_snapshots`, `rule_definitions`, `policy_profiles`, `decision_bundles`, `readiness_runs`, `icd10_reference`, `pmb_conditions`, `icd10_pmb_mappings`, `benefit_route_rules`, `tariff_rates`, `pmb_payment_policies`, `claim_diagnoses`, `claim_line_items`, `claim_line_diagnosis_links`, `claim_documents`, `pmb_decisions`, `benefit_routing_decisions`, `costing_previews`, `payloads`, `edi_artifacts`, `submissions`, `transport_logs`, `responses`, `financial_bundles`, `remittances`, `reconciliations`, `reconciliation_exceptions`, `ledger_entries`, `payments`, `audit_events`, `reports`

**New tables added (migration 0005):** `patient_balances`, `invoices`, `copay_items`, `outbox_events`, `idempotency_keys`
