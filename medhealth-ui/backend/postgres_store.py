from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from db_runtime import create_session
from db_schema import (
    TRUNCATE_TABLES,
    app_settings,
    audit_events,
    benefit_route_rules,
    benefit_routing_decisions,
    billing_snapshots,
    claim_diagnoses,
    claim_documents,
    claim_line_diagnosis_links,
    claim_line_items,
    claim_drafts,
    claim_versions,
    claims,
    copay_items,
    costing_previews,
    decision_bundles,
    financial_bundles,
    icd10_pmb_mappings,
    icd10_reference,
    edi_artifacts,
    invoices,
    ledger_entries,
    patient_balances,
    patients,
    payloads,
    payments,
    pmb_conditions,
    pmb_decisions,
    pmb_payment_policies,
    policy_profiles,
    providers,
    readiness_runs,
    reconciliation_exceptions,
    reconciliations,
    reference_versions,
    remittances,
    reports,
    responses,
    rule_definitions,
    submissions,
    tariff_rates,
    transport_logs,
    users,
)
from platform_core import (
    AttachmentRecord,
    AuditEvent,
    BenefitRouteDecision,
    BenefitRouteRule,
    BillingSnapshot,
    ClaimClosureRequest,
    ClaimDiagnosis,
    ClaimLineItem,
    ClaimRecord,
    ClaimSubmissionRequest,
    ClaimVersion,
    CostingPreview,
    DecisionBundle,
    Diagnosis,
    EDIArtifact,
    FinancialBundle,
    FinancialLineOutcome,
    ICD10Code,
    ICD10ValidationService,
    PMBCondition,
    PMBDecision,
    PMBDetectionService,
    PMBMappingRule,
    PMBPaymentPolicy,
    Patient,
    PayloadArtifact,
    PaymentRecord,
    PolicyProfile,
    PolicyProfilePatch,
    Provider,
    ReadinessItem,
    ReadinessRun,
    ReferenceVersion,
    RemittanceAdvice,
    RemittanceLine,
    Report,
    ResponseReason,
    ResponseRecord,
    RuleDefinition,
    RuleHit,
    RulePatch,
    Submission,
    TariffRate,
    TransportLog,
    User,
    PlatformStore as LegacyPlatformStore,
    BenefitRoutingService,
    CostingPreviewService,
    ReconciliationRecord,
    new_ref,
    utc_now,
)


def _as_float(value: Decimal | float | int | None) -> float | None:
    if value is None:
        return None
    return float(value)


class PersistentPlatformStore(LegacyPlatformStore):
    def __init__(self, session: Session | None = None) -> None:
        self.session = session or create_session()
        self._owns_session = session is None
        self._initialize_empty_state()
        self._load_from_database()
        self._reset_counters()
        self.icd10_validation_service = ICD10ValidationService(self)
        self.pmb_detection_service = PMBDetectionService(self)
        self.benefit_routing_service = BenefitRoutingService(self)
        self.costing_preview_service = CostingPreviewService(self)

    def close(self) -> None:
        if self._owns_session:
            self.session.close()

    def _initialize_empty_state(self) -> None:
        self.patients: Dict[int, Any] = {}
        self.providers: Dict[int, Any] = {}
        self.users: Dict[int, Any] = {}
        self.auth_users: Dict[str, Dict[str, Any]] = {}
        self.claims: Dict[int, Any] = {}
        self.claim_versions: Dict[int, List[Any]] = {}
        self.claim_history: Dict[str, Dict[str, Any]] = {}
        self.billing_snapshots: Dict[str, Any] = {}
        self.reference_versions: Dict[str, Any] = {}
        self.icd10_codes: Dict[str, Any] = {}
        self.claim_diagnoses: Dict[int, List[Any]] = {}
        self.edi_artifacts: Dict[str, Any] = {}
        self.pmb_conditions: Dict[str, Any] = {}
        self.pmb_mapping_rules: Dict[str, Any] = {}
        self.benefit_route_rules: Dict[str, Any] = {}
        self.tariff_rates: Dict[str, Any] = {}
        self.pmb_payment_policies: Dict[str, Any] = {}
        self.pmb_decisions: Dict[str, Any] = {}
        self.benefit_route_decisions: Dict[str, Any] = {}
        self.costing_previews: Dict[str, Any] = {}
        self.rule_definitions: Dict[str, Any] = {}
        self.policy_profiles: Dict[str, List[Any]] = {}
        self.readiness_runs: Dict[str, Any] = {}
        self.readiness_items: Dict[str, Any] = {}
        self.decision_bundles: Dict[str, Any] = {}
        self.payloads: Dict[str, Any] = {}
        self.submissions: Dict[str, Any] = {}
        self.transport_logs: Dict[str, Any] = {}
        self.responses: Dict[str, Any] = {}
        self.financial_bundles: Dict[str, Any] = {}
        self.payments: Dict[int, Any] = {}
        self.remittances: Dict[str, Any] = {}
        self.reconciliations: Dict[str, Any] = {}
        self.audit_events: Dict[str, Any] = {}
        self.reports: Dict[int, Any] = {}
        self.idempotency_index: Dict[str, str] = {}
        self.ledger_entries: Dict[str, Dict[str, Any]] = {}
        self.patient_balances: Dict[int, Any] = {}
        self.invoices: Dict[str, Any] = {}
        self.copay_items: Dict[str, Any] = {}
        self.settings: Dict[str, Any] = {
            "api_version": "2.0.0",
            "database": "postgresql",
            "rbac_enabled": True,
            "audit_logging": True,
            "throughput_target": {
                "claims_per_day": "UNSPECIFIED",
                "peak_claims_per_hour": "UNSPECIFIED",
                "max_payload_size": "UNSPECIFIED",
            },
            "retention": {
                "decision_bundles": "7 years",
                "audit_events": "7 years",
                "claims_and_snapshots": "7 years",
                "remittance_and_reconciliation": "7 years",
            },
            "schema_registry": self._default_schema_registry(),
            "retention_matrix": self._default_retention_matrix(),
        }
        self.counters = {"patient": 1, "provider": 1, "user": 1, "claim": 1, "report": 1, "payment": 1}

    def _reset_counters(self) -> None:
        self.counters = {
            "patient": (max(self.patients.keys()) + 1) if self.patients else 1,
            "provider": (max(self.providers.keys()) + 1) if self.providers else 1,
            "user": (max(self.users.keys()) + 1) if self.users else 1,
            "claim": (max(self.claims.keys()) + 1) if self.claims else 1,
            "report": (max(self.reports.keys()) + 1) if self.reports else 1,
            "payment": (max(self.payments.keys()) + 1) if self.payments else 1,
        }

    def _rows(self, table) -> List[Dict[str, Any]]:
        return [dict(row) for row in self.session.execute(select(table)).mappings().all()]

    def _load_from_database(self) -> None:
        for row in self._rows(reference_versions):
            self.reference_versions[row["reference_key"]] = ReferenceVersion(
                reference_key=row["reference_key"],
                version=row["version"],
                effective_from=row["effective_from"],
            )

        for row in self._rows(app_settings):
            self.settings[row["setting_key"]] = row["value_json"]
        self.settings["database"] = "postgresql"

        for row in self._rows(users):
            user = User(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                role=row["role"],
                status=row["status"],
                created_at=row["created_at"],
            )
            self.users[user.id] = user
            self.auth_users[user.username] = {
                "password": row["password"],
                "role": user.role,
                "user_id": user.id,
                "email": user.email,
            }

        for row in self._rows(patients):
            patient = Patient(
                id=row["id"],
                name=row["name"],
                mrn=row["mrn"],
                dob=row["dob"],
                sex=row["sex"],
                email=row["email"],
                phone=row["phone"],
                status=row["status"],
                created_at=row["created_at"],
            )
            self.patients[patient.id] = patient

        for row in self._rows(providers):
            provider = Provider(
                id=row["id"],
                name=row["name"],
                npi=row["npi"],
                practice_number=row["practice_number"],
                specialty=row["specialty"],
                discipline=row["discipline"],
                is_dsp_provider=row["is_dsp_provider"],
                email=row["email"],
                phone=row["phone"],
                status=row["status"],
                created_at=row["created_at"],
            )
            self.providers[provider.id] = provider

        for row in self._rows(claims):
            claim = ClaimRecord(**row["payload_json"])
            self.claims[claim.id] = claim

        versions_by_claim: dict[int, list[ClaimVersion]] = defaultdict(list)
        for row in self._rows(claim_versions):
            version = ClaimVersion(
                claim_id=row["claim_id"],
                version=row["version"],
                snapshot_id=row["snapshot_id"],
                status=row["status"],
                previous_version=row["previous_version"],
                change_summary=row["change_summary"],
                created_at=row["created_at"],
            )
            versions_by_claim[row["claim_id"]].append(version)
            self.claim_history[f"{row['claim_id']}:{row['version']}"] = row["data_json"]
        self.claim_versions = {key: sorted(value, key=lambda item: item.version) for key, value in versions_by_claim.items()}

        for row in self._rows(billing_snapshots):
            snapshot = BillingSnapshot(
                snapshot_id=row["snapshot_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                data=row["data_json"],
                input_hash=row["input_hash"],
                created_at=row["created_at"],
                created_by=row["created_by"],
            )
            self.billing_snapshots[snapshot.snapshot_id] = snapshot

        for row in self._rows(rule_definitions):
            rule = RuleDefinition(
                rule_id=row["rule_id"],
                name=row["name"],
                category=row["category"],
                severity=row["severity"],
                reason_code=row["reason_code"],
                message=row["message"],
                remediation_hint=row["remediation_hint"],
                affected_fields=row["affected_fields_json"],
                stage_scope=row["stage_scope_json"],
                enabled=row["enabled"],
                decision_table=row["decision_table_json"],
            )
            self.rule_definitions[rule.rule_id] = rule

        policies_by_key: dict[str, list[PolicyProfile]] = defaultdict(list)
        for row in self._rows(policy_profiles):
            profile = PolicyProfile(
                policy_profile_id=row["policy_profile_id"],
                scheme_id=row["scheme_id"],
                plan_option_id=row["plan_option_id"],
                version=row["version"],
                effective_from=row["effective_from"],
                effective_to=row["effective_to"],
                status=row["status"],
                approved_by=row["approved_by"],
                approved_at=row["approved_at"],
                runtime_toggles=row["runtime_toggles_json"],
                rule_ids=row["rule_ids_json"],
            )
            policies_by_key[profile.policy_profile_id].append(profile)
        self.policy_profiles = {
            key: sorted(items, key=lambda item: item.version) for key, items in policies_by_key.items()
        }

        for row in self._rows(decision_bundles):
            bundle = DecisionBundle(
                decision_bundle_id=row["decision_bundle_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                snapshot_id=row["snapshot_id"],
                stage=row["stage"],
                policy_profile_id=row["policy_profile_id"],
                policy_version=row["policy_version"],
                outcome=row["outcome"],
                input_hash=row["input_hash"],
                payload_hash=row["payload_hash"],
                reference_versions=row["reference_versions_json"],
                rule_hits=[RuleHit(**item) for item in row["rule_hits_json"]],
                explanations=row["explanations_json"],
                created_at=row["created_at"],
                created_by=row["created_by"],
            )
            self.decision_bundles[bundle.decision_bundle_id] = bundle

        for row in self._rows(readiness_runs):
            items = [ReadinessItem(**item) for item in row["items_json"]]
            for item in items:
                self.readiness_items[item.item_id] = item
            run = ReadinessRun(
                readiness_run_id=row["readiness_run_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                decision_bundle_id=row["decision_bundle_id"],
                outcome=row["outcome"],
                created_at=row["created_at"],
                items=items,
            )
            self.readiness_runs[run.readiness_run_id] = run

        for row in self._rows(icd10_reference):
            code = ICD10Code(
                code=row["code"],
                description=row["description"],
                version=row["version"],
                active=row["active"],
                effective_from=row["effective_from"],
                effective_to=row["effective_to"],
                source=row["source"],
                status=row["status"],
            )
            self.icd10_codes[code.code] = code

        for row in self._rows(pmb_conditions):
            condition = PMBCondition(
                condition_id=row["condition_id"],
                name=row["name"],
                type=row["type"],
                descriptor=row["descriptor"],
                category=row["category"],
                metadata=row["metadata_json"],
                evidence_requirements=row["evidence_requirements_json"],
                confirmation_flags=row["confirmation_flags_json"],
                active=row["active"],
                effective_from=row["effective_from"],
                effective_to=row["effective_to"],
                source=row["source"],
                status=row["status"],
            )
            self.pmb_conditions[condition.condition_id] = condition

        for row in self._rows(icd10_pmb_mappings):
            mapping = PMBMappingRule(
                mapping_id=row["mapping_id"],
                icd10_code=row["icd10_code"],
                pmb_condition_id=row["pmb_condition_id"],
                match_type=row["match_type"],
                version=row["version"],
                effective_from=row["effective_from"],
                effective_to=row["effective_to"],
                confidence=row["confidence"],
                auto_route_allowed=row["auto_route_allowed"],
                required_evidence_types=row["required_evidence_types_json"],
                active=row["active"],
                status=row["status"],
                source=row["source"],
            )
            self.pmb_mapping_rules[mapping.mapping_id] = mapping

        for row in self._rows(benefit_route_rules):
            rule = BenefitRouteRule(
                rule_id=row["rule_id"],
                scheme_id=row["scheme_id"],
                plan_option_id=row["plan_option_id"],
                route_when_confirmed=row["route_when_confirmed"],
                route_when_possible=row["route_when_possible"],
                route_when_missing_evidence=row["route_when_missing_evidence"],
                auto_route_possible_matches=row["auto_route_possible_matches"],
                active=row["active"],
                effective_from=row["effective_from"],
                effective_to=row["effective_to"],
                source=row["source"],
            )
            self.benefit_route_rules[rule.rule_id] = rule

        for row in self._rows(tariff_rates):
            rate = TariffRate(
                rate_id=row["rate_id"],
                scheme_id=row["scheme_id"],
                plan_option_id=row["plan_option_id"],
                tariff_code=row["tariff_code"],
                dsp_flag=row["dsp_flag"],
                rate_amount=_as_float(row["rate_amount"]) or 0.0,
                unit=row["unit"],
                active=row["active"],
                effective_from=row["effective_from"],
                effective_to=row["effective_to"],
                source=row["source"],
            )
            self.tariff_rates[rate.rate_id] = rate

        for row in self._rows(pmb_payment_policies):
            policy = PMBPaymentPolicy(
                policy_id=row["policy_id"],
                scheme_id=row["scheme_id"],
                plan_option_id=row["plan_option_id"],
                pay_in_full_requires_dsp=row["pay_in_full_requires_dsp"],
                voluntary_non_dsp_rate_mode=row["voluntary_non_dsp_rate_mode"],
                involuntary_non_dsp_no_copay=row["involuntary_non_dsp_no_copay"],
                active=row["active"],
                effective_from=row["effective_from"],
                effective_to=row["effective_to"],
                source=row["source"],
            )
            self.pmb_payment_policies[policy.policy_id] = policy

        diagnoses_by_claim: dict[int, list[ClaimDiagnosis]] = defaultdict(list)
        for row in self._rows(claim_diagnoses):
            diagnosis = ClaimDiagnosis(
                diagnosis_id=row["diagnosis_id"],
                claim_id=row["claim_id"],
                seq=row["seq"],
                icd10_code=row["icd10_code"],
                is_primary=row["is_primary"],
                source=row["source"],
                captured_by=row["captured_by"],
                captured_at=row["captured_at"],
            )
            diagnoses_by_claim[diagnosis.claim_id].append(diagnosis)
        self.claim_diagnoses = {
            key: sorted(items, key=lambda item: item.seq) for key, items in diagnoses_by_claim.items()
        }

        line_rows_by_claim: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
        for row in self._rows(claim_line_items):
            line_rows_by_claim[(row["claim_id"], row["claim_version"])].append(row)
        link_rows_by_line: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in self._rows(claim_line_diagnosis_links):
            link_rows_by_line[row["claim_line_item_id"]].append(row)
        for (claim_id, claim_version), rows in line_rows_by_claim.items():
            claim = self.claims.get(claim_id)
            if not claim or claim.version != claim_version:
                continue
            diagnoses_by_id = {
                item.diagnosis_id: item
                for item in self.claim_diagnoses.get(claim_id, [])
            }
            rebuilt_items: list[ClaimLineItem] = []
            for row in sorted(rows, key=lambda item: item["line_id"]):
                links = sorted(link_rows_by_line.get(row["claim_line_item_id"], []), key=lambda item: item["sequence"])
                diagnosis_refs = [
                    diagnoses_by_id[link["diagnosis_id"]].seq
                    for link in links
                    if link["diagnosis_id"] in diagnoses_by_id
                ]
                rebuilt_items.append(
                    ClaimLineItem(
                        claim_line_item_id=row["claim_line_item_id"],
                        line_id=row["line_id"],
                        service_code=row["service_code"],
                        service_description=row["service_description"],
                        quantity=_as_float(row["quantity"]) or 0.0,
                        unit_price=_as_float(row["unit_price"]) or 0.0,
                        claimed_amount=_as_float(row["claimed_amount"]) or 0.0,
                        service_date=row["service_date"],
                        diagnosis_refs=diagnosis_refs,
                        modifiers=row["modifiers_json"],
                        nappi_code=row["nappi_code"],
                        device_id=row["device_id"],
                        rendering_provider_practice_number=row["rendering_provider_practice_number"],
                        requires_preauth=row["requires_preauth"],
                        requires_attachment=row["requires_attachment"],
                    )
                )
            if rebuilt_items:
                claim.line_items = rebuilt_items

        for row in self._rows(pmb_decisions):
            decision = PMBDecision(
                decision_id=row["decision_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                stage=row["stage"],
                pmb_status=row["pmb_status"],
                matched_icd10=row["matched_icd10"],
                mapping_id=row["mapping_id"],
                condition_id=row["condition_id"],
                condition_name=row["condition_name"],
                condition_type=row["condition_type"],
                provider_marked_pmb=row["provider_marked_pmb"],
                auto_flagged=row["auto_flagged"],
                reason_code=row["reason_code"],
                message=row["message"],
                remediation_hint=row["remediation_hint"],
                explainability=row["explainability"],
                descriptor=row["descriptor"],
                confidence=row["confidence"],
                evidence_required=row["evidence_required_json"],
                evidence_missing=row["evidence_missing_json"],
                evaluated_icd10_list=row["evaluated_icd10_list_json"],
                mapping_table_version=row["mapping_table_version"],
                effective_date_used=row["effective_date_used"],
                detection_reason=row["detection_reason"],
                action=row["action_json"],
                line_level_evaluation_limited=row["line_level_evaluation_limited"],
                created_at=row["created_at"],
            )
            self.pmb_decisions[decision.decision_id] = decision

        for row in self._rows(benefit_routing_decisions):
            decision = BenefitRouteDecision(
                decision_id=row["decision_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                stage=row["stage"],
                pmb_decision_id=row["pmb_decision_id"],
                pmb_status=row["pmb_status"],
                trigger_icd10=row["trigger_icd10"],
                mapping_id=row["mapping_id"],
                pmb_condition_id=row["pmb_condition_id"],
                provider_marked_pmb=row["provider_marked_pmb"],
                pmb_detected=row["pmb_detected"],
                route=row["route"],
                action=row["action"],
                confidence=row["confidence"],
                reason_code=row["reason_code"],
                message=row["message"],
                remediation_hint=row["remediation_hint"],
                evidence_required=row["evidence_required_json"],
                evidence_missing=row["evidence_missing_json"],
                created_at=row["created_at"],
            )
            self.benefit_route_decisions[decision.decision_id] = decision

        for row in self._rows(costing_previews):
            preview = CostingPreview(
                preview_id=row["preview_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                stage=row["stage"],
                pmb_decision_id=row["pmb_decision_id"],
                routing_decision_id=row["routing_decision_id"],
                claimed_total=_as_float(row["claimed_total"]) or 0.0,
                allowed_total=_as_float(row["allowed_total"]) or 0.0,
                pmb_allowed_total=_as_float(row["pmb_allowed_total"]),
                member_liability_estimate=_as_float(row["member_liability_estimate"]) or 0.0,
                pricing_basis=row["pricing_basis"],
                pending_pmb_review=row["pending_pmb_review"],
                provisional=row["provisional"],
                reason_code=row["reason_code"],
                explanation=row["explanation"],
                created_at=row["created_at"],
            )
            self.costing_previews[preview.preview_id] = preview

        for row in self._rows(payloads):
            payload = PayloadArtifact(
                payload_id=row["payload_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                snapshot_id=row["snapshot_id"],
                canonical_claim=row["canonical_claim_json"],
                pseudo_edi=row["pseudo_edi"],
                phisc_xml=row["phisc_xml"],
                canonical_hash=row["canonical_hash"],
                payload_hash=row["payload_hash"],
                created_at=row["created_at"],
            )
            self.payloads[payload.payload_id] = payload

        for row in self._rows(edi_artifacts):
            artifact = EDIArtifact(
                artifact_id=row["artifact_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                payload_id=row["payload_id"],
                format=row["format"],
                content=row["content"],
                content_hash=row["content_hash"],
                validation_errors=row["validation_errors_json"],
                created_at=row["created_at"],
                created_by=row["created_by"],
            )
            self.edi_artifacts[artifact.artifact_id] = artifact

        for row in self._rows(submissions):
            submission = Submission(
                submission_id=row["submission_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                channel=row["channel"],
                correlation_id=row["correlation_id"],
                idempotency_key=row["idempotency_key"],
                status=row["status"],
                attempts=row["attempts"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            self.submissions[submission.submission_id] = submission
            self.idempotency_index[submission.idempotency_key] = submission.submission_id

        for row in self._rows(transport_logs):
            log = TransportLog(
                transport_log_id=row["transport_log_id"],
                submission_id=row["submission_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                artifact_id=row["artifact_id"],
                event=row["event"],
                details=row["details_json"],
                created_at=row["created_at"],
            )
            self.transport_logs[log.transport_log_id] = log

        for row in self._rows(responses):
            response = ResponseRecord(
                response_id=row["response_id"],
                submission_id=row["submission_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                status=row["status"],
                reasons=[ResponseReason(**item) for item in row["reasons_json"]],
                received_at=row["received_at"],
            )
            self.responses[response.response_id] = response

        for row in self._rows(financial_bundles):
            bundle = FinancialBundle(
                financial_bundle_id=row["financial_bundle_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                policy_profile_id=row["policy_profile_id"],
                policy_version=row["policy_version"],
                totals=row["totals_json"],
                line_outcomes=[FinancialLineOutcome(**item) for item in row["line_outcomes_json"]],
                created_at=row["created_at"],
            )
            self.financial_bundles[bundle.financial_bundle_id] = bundle

        for row in self._rows(remittances):
            remittance = RemittanceAdvice(
                remittance_id=row["remittance_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                payment_batch_ref=row["payment_batch_ref"],
                claim_reference=row["claim_reference"],
                lines=[RemittanceLine(**item) for item in row["lines_json"]],
                totals=row["totals_json"],
                created_at=row["created_at"],
            )
            self.remittances[remittance.remittance_id] = remittance

        for row in self._rows(reconciliations):
            record = ReconciliationRecord(
                reconciliation_id=row["reconciliation_id"],
                claim_id=row["claim_id"],
                claim_version=row["claim_version"],
                status=row["status"],
                exception_reasons=row["exception_reasons_json"],
                created_at=row["created_at"],
            )
            self.reconciliations[record.reconciliation_id] = record

        for row in self._rows(ledger_entries):
            self.ledger_entries[row["entry_id"]] = {
                "entry_id": row["entry_id"],
                "claim_id": row["claim_id"],
                "claim_version": row["claim_version"],
                "entry_type": row["entry_type"],
                "amount": _as_float(row["amount"]) or 0.0,
                "reference": row["reference"],
                "detail": row["detail_json"],
                "created_at": row["created_at"],
            }

        for row in self._rows(payments):
            payment = PaymentRecord(
                id=row["id"],
                claim_id=row["claim_id"],
                amount=_as_float(row["amount"]) or 0.0,
                payment_date=row["payment_date"],
                method=row["method"],
                status=row["status"],
                created_at=row["created_at"],
            )
            self.payments[payment.id] = payment

        for row in self._rows(patient_balances):
            self.patient_balances[row["patient_id"]] = {
                "balance_cents": row["balance_cents"],
                "credit_cents": row["credit_cents"],
            }

        for row in self._rows(invoices):
            self.invoices[row["id"]] = {
                "id": row["id"],
                "patient_id": row["patient_id"],
                "claim_id": row["claim_id"],
                "total_cents": row["total_cents"],
                "paid_cents": row["paid_cents"],
                "status": row["status"],
                "created_at": str(row["created_at"]) if row["created_at"] else None,
            }

        for row in self._rows(copay_items):
            self.copay_items[row["id"]] = {
                "id": row["id"],
                "invoice_id": row["invoice_id"],
                "reason_code": row["reason_code"],
                "amount_cents": row["amount_cents"],
            }

        for row in self._rows(audit_events):
            event = AuditEvent(
                audit_event_id=row["audit_event_id"],
                event_type=row["event_type"],
                actor=row["actor"],
                role=row["role"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                policy_profile_id=row["policy_profile_id"],
                policy_version=row["policy_version"],
                hashes=row["hashes_json"],
                detail=row["detail_json"],
                timestamp=row["timestamp"],
            )
            self.audit_events[event.audit_event_id] = event

        for row in self._rows(reports):
            report = Report(
                id=row["id"],
                name=row["name"],
                report_type=row["report_type"],
                generated_at=row["generated_at"],
                period=row["period"],
                summary=row["summary_json"],
            )
            self.reports[report.id] = report

    def save(self) -> None:
        truncate_names = ", ".join(table.name for table in TRUNCATE_TABLES)
        try:
            self.session.execute(text(f"TRUNCATE TABLE {truncate_names} RESTART IDENTITY CASCADE"))
            self._insert_rows(reference_versions, self._reference_version_rows())
            self._insert_rows(app_settings, self._settings_rows())
            self._insert_rows(users, self._user_rows())
            self._insert_rows(patients, self._patient_rows())
            self._insert_rows(providers, self._provider_rows())
            self._insert_rows(claims, self._claim_rows())
            self._insert_rows(claim_drafts, self._claim_draft_rows())
            self._insert_rows(claim_versions, self._claim_version_rows())
            self._insert_rows(billing_snapshots, self._snapshot_rows())
            self._insert_rows(rule_definitions, self._rule_rows())
            self._insert_rows(policy_profiles, self._policy_rows())
            self._insert_rows(decision_bundles, self._decision_bundle_rows())
            self._insert_rows(readiness_runs, self._readiness_run_rows())
            self._insert_rows(icd10_reference, self._icd10_rows())
            self._insert_rows(pmb_conditions, self._pmb_condition_rows())
            self._insert_rows(icd10_pmb_mappings, self._pmb_mapping_rows())
            self._insert_rows(benefit_route_rules, self._benefit_route_rule_rows())
            self._insert_rows(tariff_rates, self._tariff_rows())
            self._insert_rows(pmb_payment_policies, self._payment_policy_rows())
            self._insert_rows(claim_diagnoses, self._claim_diagnosis_rows())
            self._insert_rows(claim_line_items, self._claim_line_item_rows())
            self._insert_rows(claim_line_diagnosis_links, self._claim_line_diagnosis_link_rows())
            self._insert_rows(claim_documents, self._claim_document_rows())
            self._insert_rows(pmb_decisions, self._pmb_decision_rows())
            self._insert_rows(benefit_routing_decisions, self._benefit_routing_rows())
            self._insert_rows(costing_previews, self._costing_rows())
            self._insert_rows(payloads, self._payload_rows())
            self._insert_rows(edi_artifacts, self._edi_artifact_rows())
            self._insert_rows(submissions, self._submission_rows())
            self._insert_rows(transport_logs, self._transport_log_rows())
            self._insert_rows(responses, self._response_rows())
            self._insert_rows(financial_bundles, self._financial_bundle_rows())
            self._insert_rows(remittances, self._remittance_rows())
            self._insert_rows(reconciliations, self._reconciliation_rows())
            self._insert_rows(reconciliation_exceptions, self._reconciliation_exception_rows())
            self._insert_rows(ledger_entries, self._ledger_entry_rows())
            self._insert_rows(payments, self._payment_rows())
            self._insert_rows(patient_balances, self._patient_balance_rows())
            self._insert_rows(invoices, self._invoice_rows())
            self._insert_rows(copay_items, self._copay_item_rows())
            self._insert_rows(audit_events, self._audit_rows())
            self._insert_rows(reports, self._report_rows())
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def _insert_rows(self, table, rows: List[Dict[str, Any]]) -> None:
        if rows:
            self.session.execute(table.insert(), rows)

    def _reference_version_rows(self) -> List[Dict[str, Any]]:
        return [item.model_dump(mode="json") for item in self.reference_versions.values()]

    def _settings_rows(self) -> List[Dict[str, Any]]:
        excluded = {"policy_profiles", "rule_definitions"}
        return [{"setting_key": key, "value_json": deepcopy(value)} for key, value in self.settings.items() if key not in excluded]

    def _user_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for user in self.users.values():
            auth = self.auth_users.get(user.username, {})
            rows.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "status": user.status,
                    "password": auth.get("password", ""),
                    "created_at": user.created_at or utc_now(),
                }
            )
        return rows

    def _patient_rows(self) -> List[Dict[str, Any]]:
        return [item.model_dump(mode="json") for item in self.patients.values()]

    def _provider_rows(self) -> List[Dict[str, Any]]:
        return [item.model_dump(mode="json") for item in self.providers.values()]

    def _claim_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for claim in self.claims.values():
            payload = claim.model_dump(mode="json")
            rows.append(
                {
                    "id": claim.id,
                    "version": claim.version,
                    "previous_version": claim.previous_version,
                    "scenario_key": claim.scenario_key,
                    "status": claim.status,
                    "claim_number": claim.claim_number,
                    "claim_reference": claim.claim_reference,
                    "invoice_number": claim.invoice_number,
                    "scheme_id": claim.scheme_id,
                    "plan_option_id": claim.plan_option_id,
                    "member_number": claim.member_number,
                    "patient_id": claim.patient_id,
                    "provider_id": claim.provider_id,
                    "service_date": claim.service_date,
                    "pmb_status": claim.pmb_status,
                    "readiness_status": claim.readiness_status,
                    "validation_status": claim.validation_status,
                    "payload_status": claim.payload_status,
                    "submission_status": claim.submission_status,
                    "submission_channel": claim.submission_channel,
                    "remittance_status": claim.remittance_status,
                    "reconciliation_status": claim.reconciliation_status,
                    "latest_snapshot_id": claim.latest_snapshot_id,
                    "latest_payload_id": claim.latest_payload_id,
                    "latest_submission_id": claim.latest_submission_id,
                    "latest_response_id": claim.latest_response_id,
                    "latest_financial_bundle_id": claim.latest_financial_bundle_id,
                    "latest_remittance_id": claim.latest_remittance_id,
                    "latest_reconciliation_id": claim.latest_reconciliation_id,
                    "latest_pmb_decision_id": claim.latest_pmb_decision_id,
                    "latest_benefit_route_decision_id": claim.latest_benefit_route_decision_id,
                    "latest_costing_preview_id": claim.latest_costing_preview_id,
                    "created_at": claim.created_at or utc_now(),
                    "updated_at": claim.updated_at or utc_now(),
                    "payload_json": payload,
                }
            )
        return rows

    def _claim_draft_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "claim_id": claim.id,
                "claim_version": claim.version,
                "draft_json": claim.model_dump(mode="json"),
                "updated_at": claim.updated_at or utc_now(),
            }
            for claim in self.claims.values()
        ]

    def _claim_version_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for claim_id, versions in self.claim_versions.items():
            for version in versions:
                rows.append(
                    {
                        "claim_id": claim_id,
                        "version": version.version,
                        "snapshot_id": version.snapshot_id,
                        "status": version.status,
                        "previous_version": version.previous_version,
                        "change_summary": version.change_summary,
                        "data_json": self.claim_history.get(f"{claim_id}:{version.version}", {}),
                        "created_at": version.created_at,
                    }
                )
        return rows

    def _snapshot_rows(self) -> List[Dict[str, Any]]:
        deduped: Dict[tuple[int, int], Dict[str, Any]] = {}
        for item in self.billing_snapshots.values():
            row = {
                "snapshot_id": item.snapshot_id,
                "claim_id": item.claim_id,
                "claim_version": item.claim_version,
                "data_json": item.data,
                "input_hash": item.input_hash,
                "created_at": item.created_at,
                "created_by": item.created_by,
            }
            key = (item.claim_id, item.claim_version)
            existing = deduped.get(key)
            if existing is None or (row["created_at"] or "") >= (existing["created_at"] or ""):
                deduped[key] = row
        return [deduped[key] for key in sorted(deduped)]

    def _rule_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "rule_id": item.rule_id,
                "name": item.name,
                "category": item.category,
                "severity": item.severity,
                "reason_code": item.reason_code,
                "message": item.message,
                "remediation_hint": item.remediation_hint,
                "affected_fields_json": item.affected_fields,
                "stage_scope_json": item.stage_scope,
                "enabled": item.enabled,
                "decision_table_json": item.decision_table,
            }
            for item in self.rule_definitions.values()
        ]

    def _policy_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for items in self.policy_profiles.values():
            for item in items:
                rows.append(
                    {
                        "policy_profile_id": item.policy_profile_id,
                        "version": item.version,
                        "scheme_id": item.scheme_id,
                        "plan_option_id": item.plan_option_id,
                        "effective_from": item.effective_from,
                        "effective_to": item.effective_to,
                        "status": item.status,
                        "approved_by": item.approved_by,
                        "approved_at": item.approved_at,
                        "runtime_toggles_json": item.runtime_toggles,
                        "rule_ids_json": item.rule_ids,
                    }
                )
        return rows

    def _decision_bundle_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for item in self.decision_bundles.values():
            rows.append(
                {
                    "decision_bundle_id": item.decision_bundle_id,
                    "claim_id": item.claim_id,
                    "claim_version": item.claim_version,
                    "snapshot_id": item.snapshot_id,
                    "stage": item.stage,
                    "policy_profile_id": item.policy_profile_id,
                    "policy_version": item.policy_version,
                    "outcome": item.outcome,
                    "input_hash": item.input_hash,
                    "payload_hash": item.payload_hash,
                    "reference_versions_json": item.reference_versions,
                    "rule_hits_json": [hit.model_dump(mode="json") for hit in item.rule_hits],
                    "explanations_json": item.explanations,
                    "created_at": item.created_at,
                    "created_by": item.created_by,
                }
            )
        return rows

    def _readiness_run_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "readiness_run_id": item.readiness_run_id,
                "claim_id": item.claim_id,
                "claim_version": item.claim_version,
                "decision_bundle_id": item.decision_bundle_id,
                "outcome": item.outcome,
                "items_json": [row.model_dump(mode="json") for row in item.items],
                "created_at": item.created_at,
            }
            for item in self.readiness_runs.values()
        ]

    def _icd10_rows(self) -> List[Dict[str, Any]]:
        return [item.model_dump(mode="json") for item in self.icd10_codes.values()]

    def _pmb_condition_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "condition_id": item.condition_id,
                "name": item.name,
                "type": item.type,
                "descriptor": item.descriptor,
                "category": item.category,
                "metadata_json": item.metadata,
                "evidence_requirements_json": item.evidence_requirements,
                "confirmation_flags_json": item.confirmation_flags,
                "active": item.active,
                "effective_from": item.effective_from,
                "effective_to": item.effective_to,
                "source": item.source,
                "status": item.status,
            }
            for item in self.pmb_conditions.values()
        ]

    def _pmb_mapping_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "mapping_id": item.mapping_id,
                "icd10_code": item.icd10_code,
                "pmb_condition_id": item.pmb_condition_id,
                "match_type": item.match_type,
                "version": item.version,
                "effective_from": item.effective_from,
                "effective_to": item.effective_to,
                "confidence": item.confidence,
                "auto_route_allowed": item.auto_route_allowed,
                "required_evidence_types_json": item.required_evidence_types,
                "active": item.active,
                "status": item.status,
                "source": item.source,
            }
            for item in self.pmb_mapping_rules.values()
        ]

    def _benefit_route_rule_rows(self) -> List[Dict[str, Any]]:
        return [item.model_dump(mode="json") for item in self.benefit_route_rules.values()]

    def _tariff_rows(self) -> List[Dict[str, Any]]:
        return [item.model_dump(mode="json") for item in self.tariff_rates.values()]

    def _payment_policy_rows(self) -> List[Dict[str, Any]]:
        return [item.model_dump(mode="json") for item in self.pmb_payment_policies.values()]

    def _claim_diagnosis_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for items in self.claim_diagnoses.values():
            rows.extend(item.model_dump(mode="json") for item in items)
        return rows

    def _claim_line_item_rows(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for claim in self.claims.values():
            self._ensure_claim_line_item_ids(claim)
            for item in claim.line_items:
                rows.append(
                    {
                        "claim_line_item_id": item.claim_line_item_id,
                        "claim_id": claim.id,
                        "claim_version": claim.version,
                        "line_id": item.line_id,
                        "service_code": item.service_code,
                        "service_description": item.service_description,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "claimed_amount": item.claimed_amount,
                        "service_date": item.service_date,
                        "modifiers_json": item.modifiers,
                        "nappi_code": item.nappi_code,
                        "device_id": item.device_id,
                        "rendering_provider_practice_number": item.rendering_provider_practice_number,
                        "requires_preauth": item.requires_preauth,
                        "requires_attachment": item.requires_attachment,
                    }
                )
        return rows

    def _claim_line_diagnosis_link_rows(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for claim in self.claims.values():
            self._ensure_claim_line_item_ids(claim)
            diagnoses_by_seq = {item.seq: item for item in self.claim_diagnoses.get(claim.id, [])}
            for item in claim.line_items:
                for sequence, seq in enumerate(item.diagnosis_refs, start=1):
                    diagnosis = diagnoses_by_seq.get(int(seq))
                    if not diagnosis:
                        continue
                    rows.append(
                        {
                            "link_id": f"{item.claim_line_item_id}:{diagnosis.diagnosis_id}",
                            "claim_line_item_id": item.claim_line_item_id,
                            "claim_id": claim.id,
                            "claim_version": claim.version,
                            "line_id": item.line_id,
                            "diagnosis_id": diagnosis.diagnosis_id,
                            "sequence": sequence,
                        }
                    )
        return rows

    def _claim_document_rows(self) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for claim in self.claims.values():
            for item in claim.attachments:
                rows.append(
                    {
                        "document_id": item.attachment_id,
                        "claim_id": claim.id,
                        "claim_version": claim.version,
                        "encounter_id": None,
                        "patient_id": claim.patient_id,
                        "provider_id": claim.provider_id,
                        "doc_type": item.attachment_type,
                        "filename": item.file_name,
                        "storage_ref": item.storage_ref,
                        "file_hash": item.file_hash,
                        "uploaded_at": item.uploaded_at,
                        "uploaded_by": item.uploaded_by,
                        "status": "AVAILABLE" if item.virus_scan_status == "CLEAN" else "PENDING_SCAN",
                    }
                )
        return rows

    def _pmb_decision_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "decision_id": item.decision_id,
                "claim_id": item.claim_id,
                "claim_version": item.claim_version,
                "stage": item.stage,
                "pmb_status": item.pmb_status,
                "matched_icd10": item.matched_icd10,
                "mapping_id": item.mapping_id,
                "condition_id": item.condition_id,
                "condition_name": item.condition_name,
                "condition_type": item.condition_type,
                "provider_marked_pmb": item.provider_marked_pmb,
                "auto_flagged": item.auto_flagged,
                "reason_code": item.reason_code,
                "message": item.message,
                "remediation_hint": item.remediation_hint,
                "explainability": item.explainability,
                "descriptor": item.descriptor,
                "confidence": item.confidence,
                "evidence_required_json": item.evidence_required,
                "evidence_missing_json": item.evidence_missing,
                "evaluated_icd10_list_json": item.evaluated_icd10_list,
                "mapping_table_version": item.mapping_table_version,
                "effective_date_used": item.effective_date_used,
                "detection_reason": item.detection_reason,
                "action_json": item.action,
                "line_level_evaluation_limited": item.line_level_evaluation_limited,
                "created_at": item.created_at,
            }
            for item in self.pmb_decisions.values()
        ]

    def _benefit_routing_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "decision_id": item.decision_id,
                "claim_id": item.claim_id,
                "claim_version": item.claim_version,
                "stage": item.stage,
                "pmb_decision_id": item.pmb_decision_id,
                "pmb_status": item.pmb_status,
                "trigger_icd10": item.trigger_icd10,
                "mapping_id": item.mapping_id,
                "pmb_condition_id": item.pmb_condition_id,
                "provider_marked_pmb": item.provider_marked_pmb,
                "pmb_detected": item.pmb_detected,
                "route": item.route,
                "action": item.action,
                "confidence": item.confidence,
                "reason_code": item.reason_code,
                "message": item.message,
                "remediation_hint": item.remediation_hint,
                "evidence_required_json": item.evidence_required,
                "evidence_missing_json": item.evidence_missing,
                "created_at": item.created_at,
            }
            for item in self.benefit_route_decisions.values()
        ]

    def _costing_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "preview_id": item.preview_id,
                "claim_id": item.claim_id,
                "claim_version": item.claim_version,
                "stage": item.stage,
                "pmb_decision_id": item.pmb_decision_id,
                "routing_decision_id": item.routing_decision_id,
                "claimed_total": item.claimed_total,
                "allowed_total": item.allowed_total,
                "pmb_allowed_total": item.pmb_allowed_total,
                "member_liability_estimate": item.member_liability_estimate,
                "pricing_basis": item.pricing_basis,
                "pending_pmb_review": item.pending_pmb_review,
                "provisional": item.provisional,
                "reason_code": item.reason_code,
                "explanation": item.explanation,
                "created_at": item.created_at,
            }
            for item in self.costing_previews.values()
        ]

    def _payload_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "payload_id": item.payload_id,
                "claim_id": item.claim_id,
                "claim_version": item.claim_version,
                "snapshot_id": item.snapshot_id,
                "canonical_claim_json": item.canonical_claim,
                "pseudo_edi": item.pseudo_edi,
                "phisc_xml": item.phisc_xml,
                "canonical_hash": item.canonical_hash,
                "payload_hash": item.payload_hash,
                "created_at": item.created_at,
            }
            for item in self.payloads.values()
        ]

    def _edi_artifact_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "artifact_id": item.artifact_id,
                "claim_id": item.claim_id,
                "claim_version": item.claim_version,
                "payload_id": item.payload_id,
                "format": item.format,
                "content": item.content,
                "content_hash": item.content_hash,
                "validation_errors_json": item.validation_errors,
                "created_at": item.created_at,
                "created_by": item.created_by,
            }
            for item in self.edi_artifacts.values()
        ]

    def _submission_rows(self) -> List[Dict[str, Any]]:
        return [item.model_dump(mode="json") for item in self.submissions.values()]

    def _transport_log_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "transport_log_id": item.transport_log_id,
                "submission_id": item.submission_id,
                "claim_id": item.claim_id,
                "claim_version": item.claim_version,
                "artifact_id": item.artifact_id,
                "event": item.event,
                "details_json": item.details,
                "created_at": item.created_at,
            }
            for item in self.transport_logs.values()
        ]

    def _response_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "response_id": item.response_id,
                "submission_id": item.submission_id,
                "claim_id": item.claim_id,
                "claim_version": item.claim_version,
                "status": item.status,
                "reasons_json": [reason.model_dump(mode="json") for reason in item.reasons],
                "received_at": item.received_at,
            }
            for item in self.responses.values()
        ]

    def _financial_bundle_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "financial_bundle_id": item.financial_bundle_id,
                "claim_id": item.claim_id,
                "claim_version": item.claim_version,
                "policy_profile_id": item.policy_profile_id,
                "policy_version": item.policy_version,
                "totals_json": item.totals,
                "line_outcomes_json": [line.model_dump(mode="json") for line in item.line_outcomes],
                "created_at": item.created_at,
            }
            for item in self.financial_bundles.values()
        ]

    def _remittance_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "remittance_id": item.remittance_id,
                "claim_id": item.claim_id,
                "claim_version": item.claim_version,
                "payment_batch_ref": item.payment_batch_ref,
                "claim_reference": item.claim_reference,
                "lines_json": [line.model_dump(mode="json") for line in item.lines],
                "totals_json": item.totals,
                "created_at": item.created_at,
            }
            for item in self.remittances.values()
        ]

    def _reconciliation_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "reconciliation_id": item.reconciliation_id,
                "claim_id": item.claim_id,
                "claim_version": item.claim_version,
                "status": item.status,
                "exception_reasons_json": item.exception_reasons,
                "created_at": item.created_at,
            }
            for item in self.reconciliations.values()
        ]

    def _reconciliation_exception_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for record in self.reconciliations.values():
            for reason in record.exception_reasons:
                rows.append(
                    {
                        "exception_id": new_ref("rex"),
                        "reconciliation_id": record.reconciliation_id,
                        "claim_id": record.claim_id,
                        "reason_code": reason[:120].upper().replace(" ", "_"),
                        "message": reason,
                        "created_at": record.created_at,
                    }
                )
        return rows

    def _ledger_entry_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "entry_id": item["entry_id"],
                "claim_id": item["claim_id"],
                "claim_version": item["claim_version"],
                "entry_type": item["entry_type"],
                "amount": item["amount"],
                "reference": item["reference"],
                "detail_json": item["detail"],
                "created_at": item["created_at"],
            }
            for item in self.ledger_entries.values()
        ]

    def _payment_rows(self) -> List[Dict[str, Any]]:
        return [item.model_dump(mode="json") for item in self.payments.values()]

    def _patient_balance_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for patient_id, bal in self.patient_balances.items():
            b = bal if isinstance(bal, dict) else {"balance_cents": getattr(bal, "balance_cents", 0), "credit_cents": getattr(bal, "credit_cents", 0)}
            rows.append({"patient_id": patient_id, "balance_cents": b.get("balance_cents", 0), "credit_cents": b.get("credit_cents", 0)})
        return rows

    def _invoice_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for inv in self.invoices.values():
            d = inv if isinstance(inv, dict) else inv.__dict__
            rows.append({"id": d["id"], "patient_id": d["patient_id"], "claim_id": d["claim_id"],
                         "total_cents": d["total_cents"], "paid_cents": d.get("paid_cents", 0),
                         "status": d.get("status", "OPEN"), "created_at": d.get("created_at")})
        return rows

    def _copay_item_rows(self) -> List[Dict[str, Any]]:
        rows = []
        for item in self.copay_items.values():
            d = item if isinstance(item, dict) else item.__dict__
            rows.append({"id": d["id"], "invoice_id": d["invoice_id"],
                         "reason_code": d["reason_code"], "amount_cents": d["amount_cents"]})
        return rows

    def _audit_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "audit_event_id": item.audit_event_id,
                "event_type": item.event_type,
                "actor": item.actor,
                "role": item.role,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "policy_profile_id": item.policy_profile_id,
                "policy_version": item.policy_version,
                "hashes_json": item.hashes,
                "detail_json": item.detail,
                "timestamp": item.timestamp,
            }
            for item in self.audit_events.values()
        ]

    def _report_rows(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": item.id,
                "name": item.name,
                "report_type": item.report_type,
                "generated_at": item.generated_at,
                "period": item.period,
                "summary_json": item.summary,
            }
            for item in self.reports.values()
        ]

    def _persist_result(self, result: Any) -> Any:
        self.save()
        return result

    def create_patient(self, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().create_patient(data, actor, role))

    def update_patient(self, patient_id: int, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().update_patient(patient_id, data, actor, role))

    def delete_patient(self, patient_id: int, actor: str, role: str) -> None:
        result = super().delete_patient(patient_id, actor, role)
        self.save()
        return result

    def create_provider(self, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().create_provider(data, actor, role))

    def update_provider(self, provider_id: int, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().update_provider(provider_id, data, actor, role))

    def delete_provider(self, provider_id: int, actor: str, role: str) -> None:
        result = super().delete_provider(provider_id, actor, role)
        self.save()
        return result

    def create_user(self, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().create_user(data, actor, role))

    def update_user(self, user_id: int, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().update_user(user_id, data, actor, role))

    def delete_user(self, user_id: int, actor: str, role: str) -> None:
        result = super().delete_user(user_id, actor, role)
        self.save()
        return result

    def create_claim(self, data: Dict[str, Any], actor: str, role: str) -> ClaimRecord:
        return self._persist_result(super().create_claim(data, actor, role))

    def update_claim(
        self,
        claim_id: int,
        data: Dict[str, Any],
        actor: str,
        role: str,
        change_summary: str = "Draft updated",
    ) -> Dict[str, Any]:
        return self._persist_result(super().update_claim(claim_id, data, actor, role, change_summary))

    def add_claim_diagnosis(self, claim_id: int, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().add_claim_diagnosis(claim_id, data, actor, role))

    def make_primary_diagnosis(self, claim_id: int, diagnosis_id: str, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().make_primary_diagnosis(claim_id, diagnosis_id, actor, role))

    def auto_fix_primary_diagnosis(self, claim_id: int, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().auto_fix_primary_diagnosis(claim_id, actor, role))

    def update_claim_line_diagnosis_links(
        self,
        claim_id: int,
        line_id: str,
        diagnosis_ids: List[str],
        actor: str,
        role: str,
    ) -> Dict[str, Any]:
        return self._persist_result(
            super().update_claim_line_diagnosis_links(claim_id, line_id, diagnosis_ids, actor, role)
        )

    def run_readiness(self, claim_id: int, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().run_readiness(claim_id, actor, role))

    def close_claim(self, claim_id: int, request: ClaimClosureRequest, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().close_claim(claim_id, request, actor, role))

    def run_post_closure_validation(self, claim_id: int, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().run_post_closure_validation(claim_id, actor, role))

    def build_payload(self, claim_id: int, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().build_payload(claim_id, actor, role))

    def generate_edi_artifact(self, claim_id: int, version: int, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().generate_edi_artifact(claim_id, version, actor, role))

    def validate_edi_artifact(self, claim_id: int, version: int, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().validate_edi_artifact(claim_id, version, actor, role))

    def submit_edi_artifact(
        self,
        claim_id: int,
        version: int,
        channel: str,
        idempotency_key: str | None,
        actor: str,
        role: str,
    ) -> Dict[str, Any]:
        return self._persist_result(
            super().submit_edi_artifact(claim_id, version, channel, idempotency_key, actor, role)
        )

    def adjudicate(self, claim_id: int, actor: str, role: str) -> FinancialBundle:
        bundle = super().adjudicate(claim_id, actor, role)
        self._capture_financial_ledger(bundle)
        return bundle

    def generate_remittance(self, claim_id: int, actor: str, role: str):
        remittance = super().generate_remittance(claim_id, actor, role)
        payment = max(self.payments.values(), key=lambda item: item.id or 0)
        self.ledger_entries[new_ref("led")] = {
            "entry_id": new_ref("led"),
            "claim_id": remittance.claim_id,
            "claim_version": remittance.claim_version,
            "entry_type": "PAYMENT_RECEIPT",
            "amount": remittance.totals["paid"],
            "reference": payment.method,
            "detail": remittance.model_dump(mode="json"),
            "created_at": remittance.created_at,
        }
        return remittance

    def reconcile(self, claim_id: int, actor: str, role: str) -> ReconciliationRecord:
        record = super().reconcile(claim_id, actor, role)
        if record.exception_reasons:
            self.ledger_entries[new_ref("led")] = {
                "entry_id": new_ref("led"),
                "claim_id": record.claim_id,
                "claim_version": record.claim_version,
                "entry_type": "RECONCILIATION_EXCEPTION",
                "amount": 0.0,
                "reference": record.status,
                "detail": record.model_dump(mode="json"),
                "created_at": record.created_at,
            }
        return record

    def submit_claim(self, claim_id: int, request: ClaimSubmissionRequest, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().submit_claim(claim_id, request, actor, role))

    def create_payment(self, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().create_payment(data, actor, role))

    def update_payment(self, payment_id: int, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().update_payment(payment_id, data, actor, role))

    def create_policy_version(self, policy_profile_id: str, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().create_policy_version(policy_profile_id, actor, role))

    def update_policy_profile(self, policy_profile_id: str, version: int, patch: PolicyProfilePatch, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().update_policy_profile(policy_profile_id, version, patch, actor, role))

    def activate_policy_profile(self, policy_profile_id: str, version: int, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().activate_policy_profile(policy_profile_id, version, actor, role))

    def update_rule(self, rule_id: str, patch: RulePatch, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().update_rule(rule_id, patch, actor, role))

    def create_pmb_mapping(self, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().create_pmb_mapping(data, actor, role))

    def update_pmb_mapping(self, mapping_id: str, data: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().update_pmb_mapping(mapping_id, data, actor, role))

    def delete_pmb_mapping(self, mapping_id: str, actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().delete_pmb_mapping(mapping_id, actor, role))

    def update_settings(self, payload: Dict[str, Any], actor: str, role: str) -> Dict[str, Any]:
        return self._persist_result(super().update_settings(payload, actor, role))

    def generate_report(self, report_type: str, period: str) -> Dict[str, Any]:
        return self._persist_result(super().generate_report(report_type, period))

    def _capture_financial_ledger(self, bundle: FinancialBundle) -> None:
        self.ledger_entries[new_ref("led")] = {
            "entry_id": new_ref("led"),
            "claim_id": bundle.claim_id,
            "claim_version": bundle.claim_version,
            "entry_type": "ADJUDICATED_TOTAL",
            "amount": bundle.totals["paid"],
            "reference": bundle.financial_bundle_id,
            "detail": bundle.model_dump(mode="json"),
            "created_at": bundle.created_at,
        }
