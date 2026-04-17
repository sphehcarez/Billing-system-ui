# Phase 4: Realistic Seed Data Manifest

Date created: `2026-04-17`

## Seed Pack Overview

This manifest documents the realistic mock data seeded for demo and UAT.

### SA Scheme Names (Realistic Market Players)

Seed includes realistic scheme names commonly recognised in South African medical scheme market:
- **Discovery Health** (DISCOVERY_HEALTH)
- **GEMS** (GEMS_SCHEME)
- **Bonitas** (BONITAS)
- **Momentum Medical Scheme** (MOMENTUM)
- **Fedhealth** (FEDHEALTH)
- **Polmed** (POLMED)

**Note:** All seed data is clearly labelled as DEMO. Scheme configurations use placeholder benefit buckets and tariffs for demonstration only. Business-owned scheme and benefit rules must replace these before production use.

### Providers (8+)

Seeded with realistic South African formats:

| ID | Name | NPI | Practice Number | Specialty | Discipline | DSP | Email | Phone | Status |
|----|------|-----|-----------------|-----------|-----------|-----|-------|-------|--------|
| 1 | Dr. Thabo Mthembu | NPI-ZA-001 | PRAC-GP-JNB-001 | General Practice | GP | Yes | dr.thabo@mthembu-practice.co.za | +27-11-555-0001 | active |
| 2 | Dr. Lindiwe Khumalo | NPI-ZA-002 | PRAC-FM-CT-001 | Family Medicine | FM | Yes | dr.lindiwe@medi-care.co.za | +27-21-555-0002 | active |
| 3 | Dr. Sipho Ndlela | NPI-ZA-003 | PRAC-INT-DBN-001 | Internal Medicine | IM | Yes | dr.sipho@hospital-group.co.za | +27-31-555-0003 | active |
| 4 | Dr. Patricia van der Merwe | NPI-ZA-004 | PRAC-OB-PE-001 | Obstetrics | OB | No | dr.patricia@womens-health.co.za | +27-41-555-0004 | active |
| 5 | Dr. James Kumalo | NPI-ZA-005 | PRAC-CARD-JNB-002 | Cardiology | CARD | Yes | dr.james@heart-care.co.za | +27-11-555-0005 | active |
| 6 | Dr. Naledi Leblanc | NPI-ZA-006 | PRAC-ORTHO-CT-002 | Orthopaedics | ORTHO | Yes | dr.naledi@ortho-centre.co.za | +27-21-555-0006 | active |
| 7 | Dr. Mandla Njoko | NPI-ZA-007 | PRAC-GP-JNB-002 | General Practice | GP | Yes | dr.mandla@njoko-clinic.co.za | +27-11-555-0007 | active |
| 8 | Dr. Asha Patel | NPI-ZA-008 | PRAC-PEDS-DBN-002 | Paediatrics | PEDS | No | dr.asha@children-clinic.co.za | +27-31-555-0008 | active |
| 9 | Dr. Emma Schmidt | NPI-ZA-009 | PRAC-DERM-CT-003 | Dermatology | DERM | Yes | dr.emma@skin-care.co.za | +27-21-555-0009 | active |
| 10 | Dr. Kwezi Mkhize | NPI-ZA-010 | PRAC-PSY-JNB-003 | Psychiatry | PSY | No | dr.kwezi@mental-health.co.za | +27-11-555-0010 | active |

### Patients (30+)

Each patient seeded with:
- Realistic name (South African population diversity)
- Member number linked to scheme + option
- Dependant code where applicable
- DOB, sex, contact details
- Last encounter data
- Registration status

Sample patients (representative of full 30+ set):
- **Anele Tshabalala** (MEM-DISC-001-DEP001) - Discovery Health Classic, F, DOB 1988-05-15
- **Sipho Nkomo** (MEM-GEMS-002) - GEMS Standard, M, DOB 1975-03-22
- **Nomsa Dlamini** (MEM-BON-003-DEP002) - Bonitas Premier, F, DOB 1992-07-30
- **Thabo Khumalo** (MEM-MOM-004) - Momentum Medical Scheme, M, DOB 1968-11-08
- **Lerato Molefe** (MEM-FED-005) - Fedhealth Plus, F, DOB 1985-01-12
- ... (24 more patients across all schemes)

### Schemes and Plan Options

| Scheme | Code | Plans | Notes |
|--------|------|-------|-------|
| Discovery Health | DISCOVERY_HEALTH | Classic A, Classic B, Smart Plan | Market leader, used for proof-of-concept |
| GEMS | GEMS_SCHEME | Standard, Enhanced | Government employee scheme replica |
| Bonitas | BONITAS | Basic, Premier | Mid-market player |
| Momentum Medical Scheme | MOMENTUM | Essential, Comprehensive | Employer-focused |
| Fedhealth | FEDHEALTH | Plus, Max | Union-affiliated |
| Polmed | POLMED | Entry, Select, Elite | Traditionally employer scheme |

All schemes use DEMO-labelled tariff rates and PMB mappings.

### Claims Scenarios (15+)

#### 1. CLEAN_SUCCESS (DSP, ACK → Paid)
- Claim: UAT-CLM-CLEAN-SUCCESS-001
- Provider: Dr. Thabo (DSP)
- Patient: Anele Tshabalala
- Scheme: Discovery Health Classic A
- Primary ICD-10: I10 (hypertension)
- Status: PAID
- Evidence: MOTIVATION attached
- Remittance: R 900 paid in full

#### 2. MISSING_PRIMARY_ICD (Non-DSP, BLOCKED)
- Claim: UAT-CLM-MISSING-PRIMARY-001
- Status: BLOCKED at readiness
- Missing primary diagnosis
- Jump-to: diagnoses

#### 3. PMB_EVIDENCE_MISSING (DSP, WARN → PMB_REVIEW)
- Claim: UAT-CLM-PMB-EVIDENCE-001
- ICD-10: E11.9 (diabetes) - maps to PMB condition
- Motivation attachment required
- Status: PEND (evidence pending)
- Jump-to: attachments with "Upload motivation"

#### 4. DIAGNOSIS_LINK_MISSING (WARN)
- Claim: UAT-CLM-DIAG-LINK-001
- Line items present but no diagnosis linkage
- Readiness: WARN
- Jump-to: line_items with "Link diagnosis to service"

#### 5. PARTIAL_PAYMENT (ACK → PARTIAL_PAID)
- Claim: UAT-CLM-PARTIAL-001
- Claimed: R 1200
- Paid: R 900
- Member liability: R 300
- Remittance shows partial payment details

#### 6. RECONCILIATION_EXCEPTION (ACK but amount mismatch)
- Claim: UAT-CLM-RECON-EXC-001
- Claimed: R 1000
- Remitted: R 850
- Reconciliation: EXCEPTION - shortfall not explained
- Remittance reason code: ADJUSTED_BY_SCHEME

#### 7. NON_DSP_VOLUNTARY (Non-DSP, voluntary access)
- Claim: UAT-CLM-NONDSP-VOL-001
- Provider: Dr. Patricia (Non-DSP, obstetrics)
- Access type: VOLUNTARY
- Tariff applies: Non-DSP rate

#### 8. NON_DSP_INVOLUNTARY (Non-DSP, no copay)
- Claim: UAT-CLM-NONDSP-INVOL-001
- Access type: INVOLUNTARY (emergency)
- No member copay
- Full DSP rate applies

#### 9. MULTIPLE_DIAGNOSES (PRIMARY + SECONDARY)
- Claim: UAT-CLM-MULTI-DIAG-001
- Primary: I10 (hypertension)
- Secondary: E11.9 (diabetes)
- Line items linked to both
- Both PMB mappings evaluated

#### 10. HIGH_VALUE_CLAIM (R 5000+)
- Claim: UAT-CLM-HIGH-VALUE-001
- Service: Orthopaedic surgery
- Claimed: R 5200
- Requires advanced authorization flow
- Complex costing breakdown

#### 11. ATTACHMENT_REQUIRED_RECOMMENDED (WARN)
- Claim: UAT-CLM-ATTACH-REC-001
- Document recommended: REPORT (not mandatory)
- Jump-to: attachments with "Upload report to avoid pend"

#### 12. INVALID_ICD_FORMAT (BLOCKED)
- Claim: UAT-CLM-INVALID-ICD-001
- ICD-10 code malformed: "INVALID123"
- Readiness: BLOCKED
- Error: "ICD-10 format invalid"

#### 13. MEMBER_NOT_FOUND (REJECTED)
- Claim: UAT-CLM-MEMBER-NOT-FOUND-001
- Member number: MEM-INVALID-999999
- Submission: REJECTED
- Response reason: MEMBER_NOT_ON_PLAN

#### 14. CLOSED_WITH_WARNINGS (CLOSED_FOR_BILLING_WITH_WARNINGS)
- Claim: UAT-CLM-WARNINGS-001
- Readiness: WARN (not BLOCK)
- Closure override: Approved by supervisor
- Proceeds to billing with noted warnings
- Audit: override reason recorded

#### 15. EXPEDITED_PROCESSING (DSP, EXPRESS)
- Claim: UAT-CLM-EXPRESS-001
- Provider: DSP with priority flag
- Processing: Expedited (mock delay: 1 second)
- Status: ACKNOWLEDGED with express handling

### Documents (Evidence Artefacts)

Seeded as placeholder files (locally stored, metadata persisted):
- **MOTIVATION.pdf** - Supporting clinical rationale (linked to PMB evidence scenarios)
- **REPORT.pdf** - Laboratory or imaging report
- **REFERRAL.pdf** - Specialist referral letter
- **PRESCRIPTION.pdf** - Medication or treatment prescription
- **XRAY.png** - Imaging evidence (placeholder image metadata)
- **LAB_RESULT.txt** - Lab test results

Each document linked to:
- Patient ID
- Encounter ID (where applicable)
- Claim ID
- Document type (MOTIVATION, REPORT, REFERRAL, PRESCRIPTION, etc.)
- Uploaded at timestamp
- Uploaded by user/system

### Audit Events

Seeded scenarios produce 50+ audit events tracking:
- User actions: create claim, add diagnosis, attach document, make primary
- Validation events: readiness run, closure gate, post-closure validation
- PMB detection: mapping evaluated, condition auto-flagged, route decision taken
- Submission: payload built, submitted via channel, response received
- Remittance: remittance ingested, reconciliation matched/exception
- Overrides: warning override approved, mapping simulation used

### Idempotency and Repeatability

All seeds are idempotent:
- Checks for existing records by `claim_number` or `mrn`
- Purges and recreates if exists
- Safe to re-run without data duplication

### Seed Script Entry Points

#### Reference Data
```bash
python infra/seed/seed_reference_data.py
```
Output:
```json
{
  "seed": "reference_data",
  "result": {
    "users": 6,
    "patients": 30,
    "providers": 10,
    "icd10_reference": 12,
    "pmb_conditions": 6,
    "pmb_mappings": 15,
    "policy_profiles": 6
  }
}
```

#### UAT Scenarios
```bash
python infra/seed/seed_uat_scenarios.py
```
Output:
```json
{
  "seed": "uat_scenarios",
  "claim_ids": {
    "CLEAN_SUCCESS": 1,
    "MISSING_PRIMARY_ICD": 2,
    "PMB_EVIDENCE_MISSING": 3,
    ... (15 total)
  }
}
```

### Verification Commands

After seeding, verify data presence:

```sql
-- Provider count and distribution
SELECT count(*), specialty FROM providers GROUP BY specialty;

-- Patient registration status
SELECT count(*), status FROM patients GROUP BY status;

-- Claims by scenario
SELECT count(*), scenario_key, status FROM claims GROUP BY scenario_key, status;

-- Audit event types
SELECT event_type, count(*) FROM audit_events GROUP BY event_type;

-- Document types attached
SELECT doc_type, count(*) FROM claim_documents GROUP BY doc_type;
```

### Limitations and Next Steps

**Current limitations (DEMO only):**
- Tariff rates are simplified and may not reflect actual scheme pricing
- PMB mappings are proof-of-concept; production requires CMS or scheme-curated data
- Document storage is local file references; production would use S3 or document vault
- All scheme configurations are synthetic; production requires business-owned policy profiles

**For production transition:**
1. Replace scheme names and plan options with actual contracts
2. Import CMS and scheme-curated ICD-10 to PMB mappings
3. Replace tariff rates with current price lists per scheme
4. Migrate document storage to enterprise vault (S3, Azure Blob, etc.)
5. Implement actual member eligibility checks against scheme admin systems
6. Add real HL7 v2 / EDI submission connectors

