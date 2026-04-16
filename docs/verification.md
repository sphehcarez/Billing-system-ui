# Verification Checklist

Date: `2026-04-16`

- PASS: Jump to diagnoses works from the readiness modal via `medhealth-ui/js/app.js:1421-1434` `jumpToClaimTarget` and destination `medhealth-ui/claim_detail.html:95-131`
- PASS: Primary ICD can be captured and set through `GET/POST /api/claims/{id}/diagnoses`, `PUT /api/claims/{id}/diagnoses/{diagnosis_id}/make-primary`, and `POST /api/claims/{id}/diagnoses/auto-fix-primary`
- PASS: PMB mapping becomes visible after ICD capture through `pmb_decision.matched_icd10`, `mapping_id`, `condition_id`, and `explainability`
- PASS: Routing becomes visible after ICD capture through `benefit_routing_decision.route` and `reason_code`
- PASS: Costing preview is visible and explains DSP basis through `costing_preview.pricing_basis`, `allowed_total`, `pmb_allowed_total`, and `member_liability_estimate`
- PASS: Audit trail shows PMB and routing events including `PMB_DETECTED`, `PMB_REVIEW_REQUIRED`, `PMB_PROVIDER_NOT_MARKED`, `BENEFIT_ROUTED_*`, and `COSTING_PREVIEW_COMPUTED`
- PASS: Evidence packet includes PMB and routing decisions plus costing preview through `pmb_decisions`, `benefit_route_decisions`, and `costing_previews`
- PASS: Reference data is configurable and effective-dated through `ICD10Code`, `PMBCondition`, `PMBMappingRule`, `BenefitRouteRule`, `TariffRate`, and `PMBPaymentPolicy`
