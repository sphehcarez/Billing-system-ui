# Enforcement Map

Date verified: `2026-04-17`

## Diagnosis Linkage Resolution

- Backend persistence
  - `backend/db_schema.py`
    - `claim_line_items`
    - `claim_line_diagnosis_links`
  - `backend/alembic/versions/20260416_0003_resolution_paths_payload_edi.py`
    - creates the line-item and diagnosis-link tables and PMB explainability columns
- Backend rules and orchestration
  - `backend/platform_core.py`
    - `get_claim_line_items()`
    - `update_claim_line_diagnosis_links()`
    - `_line_items_with_updated_links()`
    - `_best_pmb_mapping_for_claim()`
  - `backend/postgres_store.py`
    - persists line items and diagnosis links across versioned claims
- API surface
  - `backend/platform_api.py`
    - `GET /api/claims/{claim_id}/line-items`
    - `PUT /api/claims/{claim_id}/line-items/{line_id}/diagnosis-links`
    - `POST /api/claims/{claim_id}/validation/post-closure`
- UI flow
  - `claim_detail.html`
    - `#line_items`
    - diagnosis-link controls and submission tool container
  - `js/app.js`
    - `renderClaimLineItems()`
    - `handleApplyLineDiagnosisLinks()`
    - `jumpToClaimTarget()`

## Patient Registry Claim-Carry

- Backend assembler
  - `backend/platform_core.py`
    - `get_patient_claim_context()`
    - `get_patient_timeline()`
    - `_patient_claim_context_claim()`
- API surface
  - `backend/platform_api.py`
    - `GET /api/patients/{patient_id}/claim-context`
    - `GET /api/patients/{patient_id}/timeline`
- UI flow
  - `patients.html`
    - `#patient-claim-context`
    - `#patient-timeline`
  - `js/app.js`
    - `renderPatientClaimContext()`
    - `renderPatientTimeline()`
    - `handleViewPatientClaimContext()`

## Structured Payload Tiles

- Backend payload composition
  - `backend/platform_core.py`
    - `get_structured_payload()`
    - `_payload_missing_actions()`
    - `get_payload_for_claim_version()`
- API surface
  - `backend/platform_api.py`
    - `GET /api/claims/{claim_id}/payloads/{version}/structured`
- UI flow
  - `claim_detail.html`
    - `#payload-preview`
  - `js/app.js`
    - `renderStructuredPayload()`
    - `handleCopyCanonicalJson()`

## Functional Pseudo-EDI Submission Tool

- Backend persistence
  - `backend/db_schema.py`
    - `edi_artifacts`
  - `backend/platform_core.py`
    - `generate_edi_artifact()`
    - `validate_edi_artifact()`
    - `download_edi_artifact()`
    - `submit_edi_artifact()`
    - `_validate_edi_content()`
  - `backend/postgres_store.py`
    - persists EDI artifacts and transport logs
- API surface
  - `backend/platform_api.py`
    - `POST /api/claims/{claim_id}/payloads/{version}/edi/generate`
    - `POST /api/claims/{claim_id}/payloads/{version}/edi/validate`
    - `GET /api/claims/{claim_id}/payloads/{version}/edi/download`
    - `POST /api/claims/{claim_id}/payloads/{version}/edi/submit`
    - `GET /api/claims/{claim_id}/transport-logs`
- UI flow
  - `claim_detail.html`
    - `#submission_tool`
    - `#edi-preview`
    - `#transport-log-timeline`
  - `js/app.js`
    - `renderEdiPanel()`
    - `renderTransportTimeline()`
    - `handleGenerateEdi()`
    - `handleValidateEdi()`
    - `handleDownloadEdi()`
    - `handleSubmitEdiSwitch()`

## PMB Mapping Match And Explainability

- Backend reference and rule evaluation
  - `backend/platform_core.py`
    - `_best_pmb_mapping_for_claim()`
    - `_diagnoses_for_pmb_evaluation()`
    - `create_pmb_mapping()`
    - `update_pmb_mapping()`
    - `delete_pmb_mapping()`
    - `simulate_pmb_mapping()`
  - `backend/db_schema.py`
    - PMB explainability columns:
      - `evaluated_icd10_list_json`
      - `mapping_table_version`
      - `effective_date_used`
      - `detection_reason`
      - `action_json`
      - `line_level_evaluation_limited`
- API surface
  - `backend/platform_api.py`
    - `GET /api/reference/pmb-mappings`
    - `GET /api/reference/pmb-mappings/simulate`
    - `POST /api/reference/pmb-mappings`
    - `PATCH /api/reference/pmb-mappings/{mapping_id}`
    - `DELETE /api/reference/pmb-mappings/{mapping_id}`
- UI flow
  - `settings.html`
    - PMB Mapping Admin section
  - `js/app.js`
    - `renderClaimPmbSummary()`
    - `handleCreatePmbMapping()`
    - `handleEditPmbMapping()`
    - `handleDeletePmbMapping()`
    - `handleSimulatePmbMapping()`
