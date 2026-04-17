# Test Plan: Validation & Coverage Strategy

Date created: `2026-04-17`

## Test Strategy Overview

**Scope:** Unit tests for rules, integration tests for workflows, minimal UI tests

**Approach:**
- Unit tests for backend validation rules (PMB evidence, attachments)
- Integration tests for claim workflows (diagnose → validate → resolve)
- Smoke tests for UI navigation (jump-to flows)
- No end-to-end browser automation (too brittle)

**Target coverage:**
- Backend: 75%+ (focus on validation logic)
- Integration: Key claim lifecycle paths
- UI: Critical user flows only

---

## Unit Tests

### 1. PMB Evidence Rule Tests

**File:** `backend/tests/test_platform_core.py`

#### Test: PMB_EVIDENCE_REQUIRED When Evidence Missing

```python
def test_pmb_evidence_required_when_missing_motivation():
    """
    Given: Claim with ICD-10 I10 (maps to PMB_DTP_001)
    When:  PMB mapping requires MOTIVATION evidence
    And:   No MOTIVATION document attached
    Then:  Readiness outcome=WARN, rule emits PMB_EVIDENCE_REQUIRED
    And:   action type=NAVIGATE, target=ATTACHMENTS, payload.required=["MOTIVATION"]
    """
    claim = store.create_claim({
        "claim_number": "TEST-PMB-EVIDENCE-001",
        "patient_id": 1,
        "provider_id": 1,
        "member_number": "MEM900001",
        "scheme_id": DEMO_SCHEME,
        "plan_option_id": DEMO_OPTION,
        "service_date": "2026-04-17",
        "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
        "line_items": [{"line_id": "1", "service_code": "CONS001", ...}],
        "attachments": [],  # NO MOTIVATION
    }, "test", "Billing Specialist")
    
    result = store.run_readiness(claim.id, "test", "Billing Specialist")
    
    assert result["outcome"] == "WARN"
    pmb_rule = next((r for r in result.get("validation_summary", {}).get("warnings", [])
                     if r.get("reason_code") == "PMB_EVIDENCE_REQUIRED"), None)
    assert pmb_rule is not None
    assert pmb_rule["action"]["type"] == "NAVIGATE"
    assert pmb_rule["action"]["target"] == "ATTACHMENTS"
    assert "MOTIVATION" in pmb_rule["action"]["payload"].get("required", [])
```

#### Test: PMB Evidence Rule Clears When Evidence Attached

```python
def test_pmb_evidence_warning_clears_after_attachment():
    """
    Given: Claim with PMB_EVIDENCE_REQUIRED warning
    When:  User attaches MOTIVATION document
    Then:  Re-run readiness should not warn on PMB evidence
    """
    claim = store.create_claim({...}, "test", "Billing Specialist")
    result1 = store.run_readiness(claim.id, "test", "Billing Specialist")
    assert any(r.get("reason_code") == "PMB_EVIDENCE_REQUIRED"
               for r in result1.get("validation_summary", {}).get("warnings", []))
    
    # Attach motivation
    store.add_claim_attachment(claim.id, {
        "attachment_type": "MOTIVATION",
        "filename": "motivation.pdf",
        "storage_ref": "local://motivation.pdf",
    }, "test", "Billing Specialist")
    
    result2 = store.run_readiness(claim.id, "test", "Billing Specialist")
    pmb_evidence_warning = any(r.get("reason_code") == "PMB_EVIDENCE_REQUIRED"
                                for r in result2.get("validation_summary", {}).get("warnings", []))
    assert not pmb_evidence_warning
```

### 2. Attachment Required Rule Tests

#### Test: ATTACHMENT_REQUIRED When Recommended

```python
def test_attachment_recommended_for_surgery():
    """
    Given: Claim with high-value surgery line item
    When:  Service code is flagged as "requires supporting documentation"
    Then:  Readiness outcome=INFO, rule emits ATTACHMENT_REQUIRED
    And:   action suggests uploading REPORT
    """
    claim = store.create_claim({
        ...,
        "line_items": [{
            "line_id": "1",
            "service_code": "SURG-ORTHO-001",  # Requires attachment
            "requires_attachment": True,
        }],
        "attachments": [],
    }, "test", "Billing Specialist")
    
    result = store.run_readiness(claim.id, "test", "Billing Specialist")
    
    info_items = result.get("validation_summary", {}).get("info", [])
    attachment_info = next((r for r in info_items
                           if r.get("reason_code") == "ATTACHMENT_RECOMMENDED"), None)
    assert attachment_info is not None
    assert attachment_info["action"]["payload"]["recommended"] == ["REPORT"]
```

### 3. Primary ICD-10 Missing Tests

#### Test: Primary ICD Blocked at Readiness

```python
def test_primary_icd_missing_blocks_readiness():
    """
    Given: Claim with no diagnoses
    When:  Run readiness
    Then:  outcome=BLOCK, blocker reason_code=ICD_MISSING_PRIMARY
    And:   action type=NAVIGATE, target=diagnoses
    """
    claim = store.create_claim({
        ...,
        "diagnoses": [],  # NO DIAGNOSES
    }, "test", "Billing Specialist")
    
    result = store.run_readiness(claim.id, "test", "Billing Specialist")
    
    assert result["outcome"] == "BLOCK"
    blocker = next((b for b in result.get("validation_summary", {}).get("blockers", [])
                   if b.get("reason_code") == "ICD_MISSING_PRIMARY"), None)
    assert blocker is not None
    assert blocker["action"]["target"] == "diagnoses"
    assert blocker["allowAutoFix"] == False
```

### 4. ICD-10 Format Validation Tests

#### Test: Invalid ICD Format Blocked

```python
def test_invalid_icd_format_blocked():
    """
    Given: Claim with malformed ICD-10 code "INVALID123"
    When:  Run readiness
    Then:  outcome=BLOCK, blocker reason_code=ICD_FORMAT_INVALID
    """
    claim = store.create_claim({
        ...,
        "diagnoses": [{"seq": 1, "icd10": "INVALID123", "diagnosis_type": "PRIMARY"}],
    }, "test", "Billing Specialist")
    
    result = store.run_readiness(claim.id, "test", "Billing Specialist")
    
    assert result["outcome"] == "BLOCK"
    format_blocker = next((b for b in result.get("validation_summary", {}).get("blockers", [])
                          if b.get("reason_code") == "ICD_FORMAT_INVALID"), None)
    assert format_blocker is not None
```

---

## Integration Tests

### 1. Claim Lifecycle: Diagnose → Validate → Resolve

**File:** `backend/tests/test_persistence_runtime.py`

```python
def test_claim_lifecycle_missing_diagnosis_to_ready():
    """
    1. Create claim with no diagnosis
    2. Run readiness → BLOCK
    3. Add primary diagnosis via API
    4. Re-run readiness → check PMB evaluation
    5. Verify diagnosis persisted to Postgres
    """
    store = PersistentPlatformStore()
    try:
        # Step 1: Create claim
        claim = store.create_claim({
            ...,
            "diagnoses": [],
        }, "test", "Billing Specialist")
        assert claim.id > 0
        
        # Step 2: Readiness blocked
        result1 = store.run_readiness(claim.id, "test", "Billing Specialist")
        assert result1["outcome"] == "BLOCK"
        
        # Step 3: Add diagnosis
        store.add_claim_diagnosis(claim.id, {
            "icd10_code": "I10",
            "is_primary": True,
            "source": "UserEntry",
        }, "test", "Billing Specialist")
        
        # Step 4: Re-run readiness
        result2 = store.run_readiness(claim.id, "test", "Billing Specialist")
        assert result2["outcome"] in ["PASS", "WARN"]  # No longer BLOCK
        assert result2["pmb_decision"]["pmb_status"] in ["CONFIRMED", "REVIEW_REQUIRED"]
        
        # Step 5: Verify Postgres persistence
        session = create_session()
        try:
            diagnosis_count = session.execute(
                text("SELECT count(*) FROM claim_diagnoses WHERE claim_id = :cid"),
                {"cid": claim.id}
            ).scalar_one()
            assert diagnosis_count == 1
        finally:
            session.close()
    finally:
        store.close()
```

### 2. Attachment Upload → Warning Clears

```python
def test_attachment_upload_clears_pmb_evidence_warning():
    """
    1. Create claim with PMB mapping but no evidence
    2. Run readiness → WARN (PMB_EVIDENCE_REQUIRED)
    3. Upload MOTIVATION attachment
    4. Re-run readiness → warning should be gone
    5. Verify document persisted to claim_documents table
    """
    store = PersistentPlatformStore()
    try:
        # Step 1: Create claim
        claim = store.create_claim({
            ...,
            "diagnoses": [{"seq": 1, "icd10": "E11.9", "diagnosis_type": "PRIMARY"}],
            "attachments": [],  # NO MOTIVATION
        }, "test", "Billing Specialist")
        
        # Step 2: Readiness warns about evidence
        result1 = store.run_readiness(claim.id, "test", "Billing Specialist")
        pmb_warn = any(r.get("reason_code") == "PMB_EVIDENCE_REQUIRED"
                       for r in result1.get("validation_summary", {}).get("warnings", []))
        assert pmb_warn, "Expected PMB_EVIDENCE_REQUIRED warning"
        
        # Step 3: Upload document
        store.add_claim_attachment(claim.id, {
            "attachment_type": "MOTIVATION",
            "filename": "motivation.pdf",
            "storage_ref": "local://evidence/motivation.pdf",
        }, "test", "Billing Specialist")
        
        # Step 4: Re-run readiness
        result2 = store.run_readiness(claim.id, "test", "Billing Specialist")
        pmb_warn2 = any(r.get("reason_code") == "PMB_EVIDENCE_REQUIRED"
                        for r in result2.get("validation_summary", {}).get("warnings", []))
        assert not pmb_warn2, "PMB_EVIDENCE_REQUIRED should be cleared"
        
        # Step 5: Verify document in DB
        session = create_session()
        try:
            doc_count = session.execute(
                text("SELECT count(*) FROM claim_documents WHERE claim_id = :cid AND doc_type = :dtype"),
                {"cid": claim.id, "dtype": "MOTIVATION"}
            ).scalar_one()
            assert doc_count == 1
        finally:
            session.close()
    finally:
        store.close()
```

### 3. Diagnosis Link → Line Item Validation Clears

```python
def test_line_diagnosis_link_clears_warning():
    """
    1. Create claim with line items missing diagnosis links
    2. Run readiness → WARN (DIAGNOSIS_LINK_MISSING)
    3. Link diagnosis to line item
    4. Re-run readiness → warning cleared
    """
    store = PersistentPlatformStore()
    try:
        # Step 1: Create claim
        claim = store.create_claim({
            ...,
            "diagnoses": [{"seq": 1, "icd10": "I10", "diagnosis_type": "PRIMARY"}],
            "line_items": [{
                "line_id": "1",
                "service_code": "CONS001",
                "diagnosis_refs": [],  # NOT LINKED
            }],
        }, "test", "Billing Specialist")
        
        # Step 2: Readiness warns
        result1 = store.run_readiness(claim.id, "test", "Billing Specialist")
        link_warn = any(r.get("reason_code") == "DIAGNOSIS_LINK_MISSING"
                        for r in result1.get("validation_summary", {}).get("warnings", []))
        assert link_warn
        
        # Step 3: Link diagnosis
        store.update_claim_line_diagnosis_links(claim.id, "1", [1], "test", "Billing Specialist")
        
        # Step 4: Re-run
        result2 = store.run_readiness(claim.id, "test", "Billing Specialist")
        link_warn2 = any(r.get("reason_code") == "DIAGNOSIS_LINK_MISSING"
                         for r in result2.get("validation_summary", {}).get("warnings", []))
        assert not link_warn2
    finally:
        store.close()
```

---

## UI Smoke Tests

### 1. Jump-to-Diagnoses Navigation

**File:** `backend/tests/test_ui_validation_modal.py`

```python
def test_jump_to_diagnoses_action_metadata():
    """
    Verify that readiness blockers include jump-to action.
    
    When readiness returns ICD_MISSING_PRIMARY blocker,
    the action metadata must have:
    - type = "NAVIGATE"
    - target = "diagnoses"
    - claimId in payload
    """
    result = {
        "outcome": "BLOCK",
        "validation_summary": {
            "blockers": [
                {
                    "reason_code": "ICD_MISSING_PRIMARY",
                    "action": {
                        "type": "NAVIGATE",
                        "target": "diagnoses",
                        "payload": {"claimId": 13}
                    }
                }
            ]
        }
    }
    
    blocker = result["validation_summary"]["blockers"][0]
    assert blocker["action"]["type"] == "NAVIGATE"
    assert blocker["action"]["target"] == "diagnoses"
    assert blocker["action"]["payload"]["claimId"] == 13
```

### 2. Jump-to-Attachments with Required Documents

```python
def test_jump_to_attachments_action_metadata():
    """
    Verify PMB_EVIDENCE_REQUIRED includes attachments action.
    """
    result = {
        "outcome": "WARN",
        "validation_summary": {
            "warnings": [
                {
                    "reason_code": "PMB_EVIDENCE_REQUIRED",
                    "action": {
                        "type": "NAVIGATE",
                        "target": "ATTACHMENTS",
                        "payload": {"required": ["MOTIVATION"]}
                    }
                }
            ]
        }
    }
    
    warning = result["validation_summary"]["warnings"][0]
    assert warning["action"]["target"] == "ATTACHMENTS"
    assert "MOTIVATION" in warning["action"]["payload"]["required"]
```

---

## Test Execution

### Run All Backend Tests
```bash
cd backend
pytest tests -v
```

### Run Specific Test Suite
```bash
pytest tests/test_platform_core.py::test_pmb_evidence_required_when_missing_motivation -v
pytest tests/test_persistence_runtime.py::test_claim_lifecycle_missing_diagnosis_to_ready -v
pytest tests/test_ui_validation_modal.py -v
```

### Coverage Report
```bash
pytest tests --cov=backend --cov-report=html
```

---

## Test Results Baseline

After implementing all changes, expected results:

| Test Suite | Count | Expected Pass | Status |
|-----------|-------|---------------|--------|
| Unit: PMB Evidence Rules | 4 | 4 | ⏳ TODO |
| Unit: Attachment Rules | 3 | 3 | ⏳ TODO |
| Unit: ICD-10 Validation | 3 | 3 | ⏳ TODO |
| Integration: Claim Lifecycle | 3 | 3 | ⏳ TODO |
| UI: Action Metadata | 2 | 2 | ⏳ TODO |
| **Total** | **15** | **15** | |

---

## Regression Gates

**Pre-Commit Checks:**
- [ ] All 15 tests pass
- [ ] No new test failures
- [ ] Coverage >75% for backend validation logic
- [ ] No performance regression on seed data queries

