(() => {
  const ROLE_MODULES = {
    Administrator: [
      "dashboard",
      "patients",
      "providers",
      "claims",
      "payments",
      "reports",
      "audit",
      "users",
      "settings",
    ],
    "Billing Specialist": ["dashboard", "patients", "providers", "claims", "payments"],
    "Healthcare Provider": ["dashboard", "patients", "claims"],
    "Finance Officer": ["dashboard", "payments", "reports"],
    "Compliance Auditor": ["dashboard", "reports", "audit"],
  };

  const ROLE_PERMISSIONS = {
    Administrator: {
      patients: new Set(["read", "write", "delete"]),
      providers: new Set(["read", "write", "delete"]),
      claims: new Set(["read", "write", "process", "submit"]),
      payments: new Set(["read", "write"]),
      reports: new Set(["read", "generate"]),
      audit: new Set(["read"]),
      users: new Set(["read", "write", "delete"]),
      settings: new Set(["read", "write"]),
    },
    "Billing Specialist": {
      patients: new Set(["read", "write"]),
      providers: new Set(["read", "write"]),
      claims: new Set(["read", "write", "process", "submit"]),
      payments: new Set(["read", "write"]),
    },
    "Healthcare Provider": {
      patients: new Set(["read"]),
      providers: new Set(["read"]),
      claims: new Set(["read", "process"]),
    },
    "Finance Officer": {
      claims: new Set(["read"]),
      payments: new Set(["read", "write"]),
      reports: new Set(["read", "generate"]),
    },
    "Compliance Auditor": {
      patients: new Set(["read"]),
      providers: new Set(["read"]),
      claims: new Set(["read"]),
      payments: new Set(["read"]),
      reports: new Set(["read"]),
      audit: new Set(["read"]),
    },
  };

  const CREATE_CONFIG = {
    "patients.html": {
      resource: "patients",
      buildModal: () =>
        showFormModal({
          title: "Create Patient",
          submitLabel: "Create",
          fields: [
            { name: "name", label: "Name" },
            { name: "mrn", label: "Medical Record Number" },
            { name: "dob", label: "Date of Birth", type: "date" },
            { name: "email", label: "Email", type: "email" },
            { name: "phone", label: "Phone" },
          ],
          onSubmit: async (values, close) => {
            await window.api.createPatient(values);
            close();
            await loadPatients();
          },
        }),
    },
    "providers.html": {
      resource: "providers",
      buildModal: () =>
        showFormModal({
          title: "Create Provider",
          submitLabel: "Create",
          fields: [
            { name: "name", label: "Name" },
            { name: "npi", label: "NPI" },
            { name: "specialty", label: "Specialty" },
            { name: "email", label: "Email", type: "email" },
            { name: "phone", label: "Phone" },
          ],
          onSubmit: async (values, close) => {
            await window.api.createProvider(values);
            close();
            await loadProviders();
          },
        }),
    },
    "claims.html": {
      resource: "claims",
      buildModal: () =>
        showFormModal({
          title: "Create Claim",
          submitLabel: "Create",
          fields: [
            { name: "claim_number", label: "Claim Number" },
            { name: "patient_id", label: "Patient ID", type: "number", min: 1 },
            { name: "provider_id", label: "Provider ID", type: "number", min: 1 },
            { name: "amount", label: "Amount", type: "number", min: 0, step: "0.01" },
          ],
          onSubmit: async (values, close) => {
            values.patient_id = Number(values.patient_id);
            values.provider_id = Number(values.provider_id);
            values.amount = Number(values.amount);
            await window.api.createClaim(values);
            close();
            await loadClaims();
          },
        }),
    },
    "payments.html": {
      resource: "payments",
      buildModal: () =>
        showFormModal({
          title: "Create Payment",
          submitLabel: "Create",
          fields: [
            { name: "claim_id", label: "Claim ID", type: "number", min: 1 },
            { name: "amount", label: "Amount", type: "number", min: 0, step: "0.01" },
            { name: "payment_date", label: "Payment Date", type: "date" },
            { name: "method", label: "Method" },
          ],
          onSubmit: async (values, close) => {
            values.claim_id = Number(values.claim_id);
            values.amount = Number(values.amount);
            await window.api.createPayment(values);
            close();
            await loadPayments();
          },
        }),
    },
    "users.html": {
      resource: "users",
      buildModal: () =>
        showFormModal({
          title: "Create User",
          submitLabel: "Create",
          fields: [
            { name: "username", label: "Username" },
            { name: "email", label: "Email", type: "email" },
            {
              name: "role",
              label: "Role",
              type: "select",
              options: Object.keys(ROLE_MODULES).map((role) => ({ value: role, label: role })),
            },
            { name: "password", label: "Temporary Password", type: "password" },
          ],
          onSubmit: async (values, close) => {
            await window.api.createUser(values);
            close();
            await loadUsers();
          },
        }),
    },
    "reports.html": {
      resource: "reports",
      requiredAction: "generate",
      buildModal: () =>
        showFormModal({
          title: "Generate Report",
          submitLabel: "Generate",
          fields: [
            {
              name: "report_type",
              label: "Report Type",
              type: "select",
              options: [
                { value: "summary", label: "Claims Summary" },
                { value: "payment", label: "Payment Analysis" },
                { value: "audit", label: "Audit Trail" },
              ],
            },
            { name: "period", label: "Period", value: "Q2 2026" },
          ],
          onSubmit: async (values, close) => {
            await window.api.generateReport(values.report_type, values.period);
            close();
            await loadReports();
          },
        }),
    },
  };

  const state = {
    page: getCurrentPage(),
    role: getStoredRole(),
    claimId: getClaimIdFromLocation(),
    claimDetail: null,
    claimDiagnoses: [],
    icd10Reference: [],
  };

  document.addEventListener("DOMContentLoaded", () => {
    if (!window.api) {
      return;
    }

    if (state.page !== "index.html" && !window.api.isAuthenticated()) {
      location.href = "index.html";
      return;
    }

    applyRoleToLayout();
    configureTopbar();
    bindGlobalHandlers();
    void initializePage();
  });

  function getCurrentPage() {
    return location.pathname.split("/").pop() || "index.html";
  }

  function getClaimIdFromLocation() {
    const claimId = Number(new URLSearchParams(location.search).get("id"));
    return Number.isInteger(claimId) && claimId > 0 ? claimId : null;
  }

  function getStoredRole() {
    return localStorage.getItem("api_role") || localStorage.getItem("role") || "Billing Specialist";
  }

  function hasPermission(resource, action) {
    const permissions = ROLE_PERMISSIONS[state.role]?.[resource];
    return Boolean(permissions && permissions.has(action));
  }

  function applyRoleToLayout() {
    state.role = getStoredRole();

    document.querySelectorAll("[data-role]").forEach((element) => {
      element.textContent = state.role;
    });

    const allowedModules = new Set(ROLE_MODULES[state.role] || []);
    document.querySelectorAll("[data-module]").forEach((link) => {
      const moduleName = link.getAttribute("data-module");
      link.style.display = allowedModules.has(moduleName) ? "" : "none";
    });

    const pageModule = state.page === "claim_detail.html" ? "claims" : state.page.replace(".html", "");
    if (state.page !== "index.html" && state.page !== "dashboard.html" && !allowedModules.has(pageModule)) {
      location.href = "dashboard.html";
      return;
    }

    document.querySelectorAll(".nav a").forEach((link) => {
      const href = link.getAttribute("href");
      link.classList.toggle("active", href === state.page);
    });
  }

  function configureTopbar() {
    const actionsBar = document.querySelector(".topbar .actions");
    if (actionsBar && !actionsBar.querySelector("[data-manual-link]")) {
      const manualLink = document.createElement("a");
      manualLink.href = "manual.html";
      manualLink.className = "btn secondary";
      manualLink.setAttribute("data-manual-link", "true");
      manualLink.textContent = "User Manual";
      actionsBar.insertBefore(manualLink, actionsBar.firstChild);
    }

    const createButton = document.querySelector('[data-action="create-new"]');
    if (!createButton) {
      return;
    }

    const config = CREATE_CONFIG[state.page];
    if (!config) {
      createButton.style.display = "none";
      return;
    }

    const requiredAction = config.requiredAction || "write";
    if (!hasPermission(config.resource, requiredAction)) {
      createButton.style.display = "none";
    }
  }

  function bindGlobalHandlers() {
    document.addEventListener("click", (event) => {
      const actionButton = event.target.closest("[data-action]");
      if (!actionButton) {
        return;
      }

      event.preventDefault();
      void handleAction(actionButton);
    });

    const logoutLink = document.querySelector("a[href='index.html']");
    if (logoutLink) {
      logoutLink.addEventListener("click", () => {
        window.api.logout();
      });
    }
  }

  async function initializePage() {
    switch (state.page) {
      case "dashboard.html":
        await loadDashboardSummary();
        break;
      case "patients.html":
        await loadPatients();
        break;
      case "providers.html":
        await loadProviders();
        break;
      case "claims.html":
        await loadClaims();
        break;
      case "payments.html":
        await loadPayments();
        break;
      case "reports.html":
        await loadReports();
        break;
      case "audit.html":
        await loadAuditLogs();
        break;
      case "users.html":
        await loadUsers();
        break;
      case "settings.html":
        await loadSettings();
        break;
      case "claim_detail.html":
        await loadClaimDetail();
        break;
      default:
        break;
    }
  }

  async function loadDashboardSummary() {
    const summary = await window.api.getDashboardSummary();
    setTextById("dashboard-ready-to-close", String(summary.ready_to_close || 0));
    setTextById("dashboard-ready-to-submit", String(summary.ready_to_submit || 0));
    setTextById("dashboard-rejected-pended", String(summary.rejected_or_pended || 0));
    setTextById("dashboard-reconciliation-exceptions", String(summary.reconciliation_exceptions || 0));
    setTextById(
      "dashboard-top-rule-hit",
      `Top reasons: ${Object.keys(summary.top_rule_hits || {})
        .slice(0, 2)
        .join(", ") || "None"}`,
    );
    setTextById("dashboard-policy-profile", summary.active_policy?.profile || "SCHEME_A:OPTION_X");
    setTextById("dashboard-policy-version", String(summary.active_policy?.version || 1));
    setTextById(
      "dashboard-policy-rule",
      Object.keys(summary.top_rule_hits || {})[0] || "No hits yet",
    );

    const tbody = document.getElementById("dashboard-worklist-rows");
    if (tbody) {
      const worklist = summary.worklist || [];
      tbody.innerHTML = worklist.length
        ? worklist
            .map(
              (item) => `
                <tr>
                  <td class="code">${escapeHtml(item.claim_number)}</td>
                  <td>${escapeHtml(item.reasons?.[0] || "-")}</td>
                  <td><span class="chip ${statusClass(item.status)}">${escapeHtml(item.status)}</span></td>
                  <td>${escapeHtml(item.next_action || "Review claim")}</td>
                  <td class="row-actions"><a class="chip info" href="claim_detail.html?id=${item.claim_id}">Open</a></td>
                </tr>
              `,
            )
            .join("")
        : '<tr><td colspan="5" style="text-align:center;color:#999;">No worklist items.</td></tr>';
    }
  }

  async function handleAction(button) {
    if (button.disabled) {
      return;
    }

    const action = button.getAttribute("data-action");
    const id = button.getAttribute("data-id");
    const originalLabel = button.textContent;

    button.disabled = true;
    button.textContent = "Working...";

    try {
      switch (action) {
        case "open-api-docs":
          window.open("http://localhost:8001/docs", "_blank", "noopener");
          break;
        case "create-new":
          handleCreateNew();
          break;
        case "run-readiness":
        case "readiness-run":
          await handleRunReadiness(id);
          break;
        case "close-file":
        case "closure-confirm":
          await handleCloseClaim(id);
          break;
        case "post-closure-validate":
        case "post-closure-validation":
          await handlePostClosureValidation(id);
          break;
        case "build-payload":
          await handleBuildPayload(id);
          break;
        case "add-diagnosis":
          await handleAddDiagnosis();
          break;
        case "make-primary-diagnosis":
          await handleMakePrimaryDiagnosis(id);
          break;
        case "auto-fix-primary":
          await handleAutoFixPrimary();
          break;
        case "submit-direct":
          await handleSubmitClaim("direct");
          break;
        case "submit-switch":
          await handleSubmitClaim("switch");
          break;
        case "view-remittance":
          await handleViewRemittance();
          break;
        case "evidence-packet":
          await handleViewEvidence();
          break;
        case "download-report":
          await handleDownloadReport(id);
          break;
        case "edit-patient":
          await handleEditPatient(id);
          break;
        case "delete-patient":
          await handleDeletePatient(id);
          break;
        case "edit-provider":
          await handleEditProvider(id);
          break;
        case "delete-provider":
          await handleDeleteProvider(id);
          break;
        case "edit-payment":
          await handleEditPayment(id);
          break;
        case "edit-user":
          await handleEditUser(id);
          break;
        case "delete-user":
          await handleDeleteUser(id);
          break;
        case "new-policy-version":
          await handleCreatePolicyVersion();
          break;
        case "edit-policy":
          await handleEditPolicy(button);
          break;
        case "activate-policy":
          await handleActivatePolicy(button);
          break;
        case "edit-rule":
          await handleEditRule(button);
          break;
        default:
          throw new Error(`Unsupported action: ${action}`);
      }
    } catch (error) {
      alert(error.message || "Something went wrong.");
    } finally {
      button.disabled = false;
      button.textContent = originalLabel;
    }
  }

  function handleCreateNew() {
    const config = CREATE_CONFIG[state.page];
    if (!config) {
      throw new Error("This page does not support creation.");
    }

    const requiredAction = config.requiredAction || "write";
    if (!hasPermission(config.resource, requiredAction)) {
      throw new Error("You do not have permission to create records on this page.");
    }

    config.buildModal();
  }

  async function loadPatients() {
    const patients = await window.api.getPatients();
    renderTable(
      patients,
      6,
      (patient) => `
        <tr>
          <td class="code">${escapeHtml(patient.mrn)}</td>
          <td>${escapeHtml(patient.name)}</td>
          <td>${escapeHtml(patient.email)}</td>
          <td>${escapeHtml(patient.phone)}</td>
          <td><span class="chip ${statusClass(patient.status)}">${escapeHtml(patient.status)}</span></td>
          <td class="row-actions">${renderPatientActions(patient.id)}</td>
        </tr>
      `,
      "No patients found.",
    );
  }

  async function loadProviders() {
    const providers = await window.api.getProviders();
    renderTable(
      providers,
      6,
      (provider) => `
        <tr>
          <td class="code">${escapeHtml(provider.npi)}</td>
          <td>${escapeHtml(provider.name)}</td>
          <td>${escapeHtml(provider.specialty)}</td>
          <td>${escapeHtml(provider.email)}</td>
          <td><span class="chip ${statusClass(provider.status)}">${escapeHtml(provider.status)}</span></td>
          <td class="row-actions">${renderProviderActions(provider.id)}</td>
        </tr>
      `,
      "No providers found.",
    );
  }

  async function loadClaims() {
    const claims = await window.api.getClaims();
    renderTable(
      claims,
      5,
      (claim) => `
        <tr>
          <td class="code">${escapeHtml(claim.claim_number)}</td>
          <td>${escapeHtml(claim.member_number || `Patient ${claim.patient_id}`)}</td>
          <td>${escapeHtml(claim.scheme || `Provider ${claim.provider_id}`)}</td>
          <td><span class="chip ${claimStatusClass(claim)}">${escapeHtml(claim.status)}</span></td>
          <td class="row-actions">${renderClaimActions(claim.id, claim.status)}</td>
        </tr>
      `,
      "No claims found.",
    );
  }

  async function loadPayments() {
    const payments = await window.api.getPayments();
    renderTable(
      payments,
      6,
      (payment) => `
        <tr>
          <td class="code">PAY-${payment.id}</td>
          <td>Claim ${payment.claim_id}</td>
          <td>${formatCurrency(payment.amount)}</td>
          <td>${escapeHtml(payment.method)}</td>
          <td><span class="chip ${statusClass(payment.status)}">${escapeHtml(payment.status)}</span></td>
          <td class="row-actions">${renderPaymentActions(payment.id)}</td>
        </tr>
      `,
      "No payments found.",
    );
  }

  async function loadReports() {
    const payload = await window.api.getReports();
    const reports = payload.reports || [];
    renderTable(
      reports,
      5,
      (report) => `
        <tr>
          <td class="code">${escapeHtml(report.name)}</td>
          <td>${escapeHtml(report.report_type)}</td>
          <td>${escapeHtml(report.period)}</td>
          <td>${formatDateTime(report.generated_at)}</td>
          <td class="row-actions"><button class="chip info" data-action="download-report" data-id="${report.id}">Download</button></td>
        </tr>
      `,
      "No reports available.",
    );
  }

  async function loadAuditLogs() {
    const logs = await window.api.getAuditLogs();
    renderTable(
      logs,
      5,
      (log) => `
        <tr>
          <td class="code">${escapeHtml(log.action)}</td>
          <td>${escapeHtml(log.resource)}</td>
          <td>${escapeHtml(log.username || `User ${log.user_id}`)}</td>
          <td>${formatDateTime(log.timestamp)}</td>
          <td style="font-size:12px;color:#666;">${escapeHtml(log.details)}</td>
        </tr>
      `,
      "No audit events recorded.",
    );
  }

  async function loadUsers() {
    const users = await window.api.getUsers();
    renderTable(
      users,
      5,
      (user) => `
        <tr>
          <td>${escapeHtml(user.username)}</td>
          <td>${escapeHtml(user.email)}</td>
          <td>${escapeHtml(user.role)}</td>
          <td><span class="chip ${statusClass(user.status)}">${escapeHtml(user.status)}</span></td>
          <td class="row-actions">${renderUserActions(user.id)}</td>
        </tr>
      `,
      "No users found.",
    );
  }

  async function loadSettings() {
    const settings = await window.api.getSettings();
    setTextById("settings-scheme", settings.scheme || "SCHEME_A");
    setTextById("settings-option", settings.option || "OPTION_X");
    setTextById("settings-policy-version", String(settings.policy_version || 1));

    const policyBody = document.getElementById("policy-profile-rows");
    if (policyBody) {
      const policyProfiles = settings.policy_profiles || [];
      policyBody.innerHTML = policyProfiles.length
        ? policyProfiles
            .map(
              (profile) => `
                <tr>
                  <td class="code">${escapeHtml(profile.policy_profile_id)}</td>
                  <td>${escapeHtml(String(profile.version))}</td>
                  <td><span class="chip ${statusClass(profile.status)}">${escapeHtml(profile.status)}</span></td>
                  <td>${escapeHtml(profile.effective_from || "-")}</td>
                  <td>${escapeHtml(profile.runtime_toggles?.defaultSubmissionChannel || "-")}</td>
                  <td class="row-actions">
                    <button class="chip" data-action="edit-policy" data-profile-id="${escapeHtml(
                      profile.policy_profile_id,
                    )}" data-version="${escapeHtml(String(profile.version))}">Edit</button>
                    <button class="chip info" data-action="activate-policy" data-profile-id="${escapeHtml(
                      profile.policy_profile_id,
                    )}" data-version="${escapeHtml(String(profile.version))}">Activate</button>
                  </td>
                </tr>
              `,
            )
            .join("")
        : '<tr><td colspan="6" style="text-align:center;color:#999;">No policy profiles found.</td></tr>';
    }

    const ruleBody = document.getElementById("rule-definition-rows");
    if (ruleBody) {
      const rules = settings.rule_definitions || [];
      ruleBody.innerHTML = rules.length
        ? rules
            .map(
              (rule) => `
                <tr>
                  <td class="code">${escapeHtml(rule.rule_id)}</td>
                  <td>${escapeHtml(rule.category)}</td>
                  <td><span class="chip ${statusClass(rule.severity)}">${escapeHtml(rule.severity)}</span></td>
                  <td>${escapeHtml((rule.stage_scope || []).join(", "))}</td>
                  <td><span class="chip ${rule.enabled ? "pass" : "fail"}">${rule.enabled ? "ENABLED" : "DISABLED"}</span></td>
                  <td class="row-actions">
                    <button class="chip" data-action="edit-rule" data-rule-id="${escapeHtml(rule.rule_id)}">Edit</button>
                  </td>
                </tr>
              `,
            )
            .join("")
        : '<tr><td colspan="6" style="text-align:center;color:#999;">No rules found.</td></tr>';
    }

    setPreById(
      "settings-retention",
      JSON.stringify(
        {
          retention: settings.retention,
          retention_matrix: settings.retention_matrix,
          schema_registry: settings.schema_registry,
        },
        null,
        2,
      ),
    );
  }

  async function loadClaimDetail() {
    const claimId = state.claimId || 1;
    const [claim, diagnoses, icd10Reference] = await Promise.all([
      window.api.getClaim(claimId),
      window.api.getClaimDiagnoses(claimId),
      state.icd10Reference.length ? Promise.resolve(state.icd10Reference) : window.api.getIcd10Reference(),
    ]);
    state.claimId = claim.id;
    state.claimDetail = claim;
    state.claimDiagnoses = diagnoses || [];
    state.icd10Reference = icd10Reference || [];

    setTextById("claim-number", claim.claim_number);
    setTextById("claim-member", claim.member_number || `Patient ${claim.patient_id}`);
    setChipById("claim-status-chip", claim.status, claimStatusClass(claim));
    setTextById("readiness-status", upperCaseValue(claim.readiness_status));
    setTextById("closure-status", claim.latest_snapshot ? "PASS" : "PENDING");
    setTextById("post-closure-status", claim.validation_status ? upperCaseValue(claim.validation_status) : "PENDING");
    setPreById(
      "payload-preview",
      JSON.stringify(claim.latest_payload?.canonical_claim || buildPayloadPreview(claim), null, 2),
    );
    setPreById("edi-preview", claim.latest_payload?.pseudo_edi || buildEdiPreview(claim));
    renderDiagnosisReferenceOptions();
    renderClaimDiagnoses();
    renderClaimPmbSummary(
      claim.latest_pmb_decision,
      claim.latest_benefit_route_decision,
      claim.latest_costing_preview,
    );
  }

  function renderDiagnosisReferenceOptions() {
    const datalist = document.getElementById("icd10-options");
    if (!datalist) {
      return;
    }
    datalist.innerHTML = (state.icd10Reference || [])
      .slice(0, 200)
      .map(
        (item) =>
          `<option value="${escapeHtml(item.code)}">${escapeHtml(`${item.code} - ${item.description || ""}`)}</option>`,
      )
      .join("");
  }

  function renderClaimDiagnoses() {
    const container = document.getElementById("diagnoses-list");
    const autoFixButton = document.getElementById("diagnosis-auto-fix");
    if (!container) {
      return;
    }

    const diagnoses = state.claimDiagnoses || [];
    if (autoFixButton) {
      autoFixButton.style.display = diagnoses.length === 1 && !diagnoses.some((item) => item.is_primary) ? "" : "none";
    }

    if (!diagnoses.length) {
      container.innerHTML =
        '<div class="panel"><strong>No diagnoses captured.</strong><div class="muted" style="margin-top:6px;">Capture a primary ICD-10 to clear the readiness blocker and enable PMB evaluation.</div></div>';
      return;
    }

    container.innerHTML = diagnoses
      .map(
        (diagnosis) => `
          <article style="border:1px solid #e5e7eb;border-radius:14px;padding:12px;display:grid;gap:8px;margin-bottom:10px;">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
              <div>
                <strong class="code">${escapeHtml(diagnosis.icd10_code)}</strong>
                <span class="chip ${diagnosis.is_primary ? "pass" : "info"}" style="margin-left:8px;">${diagnosis.is_primary ? "PRIMARY" : "SECONDARY"}</span>
              </div>
              <div class="row-actions">
                ${diagnosis.is_primary ? "" : `<button class="chip" data-action="make-primary-diagnosis" data-id="${escapeHtml(diagnosis.diagnosis_id)}">Set primary</button>`}
              </div>
            </div>
            <div class="muted">
              Source: ${escapeHtml(diagnosis.source || "UserEntry")} · Captured: ${escapeHtml(diagnosis.captured_at || "-")}
            </div>
          </article>
        `,
      )
      .join("");
  }

  function renderClaimPmbSummary(pmbDecision, routingDecision, costingPreview) {
    const container = document.getElementById("claim-pmb-summary");
    if (!container) {
      return;
    }
    if (!pmbDecision && !routingDecision && !costingPreview) {
      container.textContent = "Run readiness to load PMB identification, routing, and costing preview.";
      return;
    }

    const pmbStatus = pmbDecision?.pmb_status || "UNKNOWN";
    const route = routingDecision?.route || "-";
    const pricingBasis = costingPreview?.pricing_basis || "-";
    const pmbAllowed = costingPreview?.pmb_allowed_total == null ? "-" : formatCurrency(costingPreview.pmb_allowed_total);

    container.innerHTML = `
      <div class="panel" style="display:grid;gap:8px;">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
          <strong>${escapeHtml(pmbStatus)}</strong>
          <span class="chip ${
            pmbStatus === "CONFIRMED" ? "pass" : pmbStatus === "NOT_DETECTED" ? "info" : pmbStatus === "UNKNOWN" ? "fail" : "warn"
          }">${escapeHtml(pmbDecision?.reason_code || routingDecision?.reason_code || "PMB")}</span>
        </div>
        <div class="muted">ICD-10: ${escapeHtml(pmbDecision?.matched_icd10 || "-")} · Mapping: ${escapeHtml(pmbDecision?.mapping_id || "-")} · Condition: ${escapeHtml(pmbDecision?.condition_id || "-")}</div>
        <div class="muted">Route: ${escapeHtml(route)} · Provider marked PMB: ${escapeHtml(pmbDecision?.provider_marked_pmb ? "yes" : "no")}</div>
        <div class="muted">Pricing basis: ${escapeHtml(pricingBasis)} · Scheme allowed: ${formatCurrency(costingPreview?.allowed_total || 0)} · PMB allowed: ${escapeHtml(pmbAllowed)}</div>
        <div class="muted">Member liability estimate: ${formatCurrency(costingPreview?.member_liability_estimate || 0)}</div>
      </div>
    `;
  }

  function normalizeIcd10InputValue(value) {
    return String(value || "")
      .trim()
      .split(/\s|-/)[0]
      .toUpperCase();
  }

  function setDiagnosisFeedback(message, tone = "info") {
    const element = document.getElementById("diagnosis-feedback");
    if (!element) {
      return;
    }
    element.textContent = message || "";
    element.style.color =
      tone === "error" ? "var(--fail)" : tone === "success" ? "var(--pass)" : "var(--ink-500)";
  }

  function focusDiagnosisSearchInput() {
    const searchInput = document.getElementById("diagnosis-search-input");
    if (!searchInput) {
      return;
    }
    setTimeout(() => {
      searchInput.focus();
      searchInput.select?.();
    }, 120);
  }

  async function rerunReadinessFromDiagnosisAction(titlePrefix) {
    const result = await window.api.runReadinessCheck(resolveClaimId(state.claimId));
    await refreshClaimViews();
    showValidationSummaryModal(`${titlePrefix}: ${result.claim_number || `claim ${result.claim_id}`}`, result);
  }

  async function handleAddDiagnosis() {
    const codeInput = document.getElementById("diagnosis-search-input");
    const typeInput = document.getElementById("diagnosis-type-input");
    const sourceInput = document.getElementById("diagnosis-source-input");
    const icd10Code = normalizeIcd10InputValue(codeInput?.value);
    if (!icd10Code) {
      setDiagnosisFeedback("Enter an ICD-10 code before adding a diagnosis.", "error");
      focusDiagnosisSearchInput();
      return;
    }
    await window.api.addClaimDiagnosis(resolveClaimId(state.claimId), {
      icd10_code: icd10Code,
      is_primary: typeInput?.value === "PRIMARY",
      source: sourceInput?.value || "UserEntry",
    });
    setDiagnosisFeedback(`Diagnosis ${icd10Code} captured. Readiness is rerunning.`, "success");
    if (codeInput) {
      codeInput.value = "";
    }
    await rerunReadinessFromDiagnosisAction("Diagnosis captured");
  }

  async function handleMakePrimaryDiagnosis(diagnosisId) {
    await window.api.makePrimaryDiagnosis(resolveClaimId(state.claimId), diagnosisId);
    setDiagnosisFeedback("Primary diagnosis updated. Readiness is rerunning.", "success");
    await rerunReadinessFromDiagnosisAction("Primary diagnosis updated");
  }

  async function handleAutoFixPrimary() {
    const result = await window.api.autoFixPrimaryDiagnosis(resolveClaimId(state.claimId));
    if (!result.fixed) {
      setDiagnosisFeedback(result.message || "Primary diagnosis could not be auto-fixed.", "error");
      focusDiagnosisSearchInput();
      return;
    }
    setDiagnosisFeedback("Primary diagnosis auto-fixed. Readiness is rerunning.", "success");
    await rerunReadinessFromDiagnosisAction("Primary diagnosis auto-fixed");
  }

  async function handleRunReadiness(claimId) {
    const targetId = resolveClaimId(claimId);
    const result = await window.api.runReadinessCheck(targetId);
    showValidationSummaryModal(`Readiness: ${result.claim_number || `claim ${result.claim_id}`}`, result);
    await refreshClaimViews();
  }

  async function handleCloseClaim(claimId) {
    const targetId = resolveClaimId(claimId);
    if (!confirm("Close this claim?")) {
      return;
    }

    const result = await window.api.closeClaim(targetId);
    if (result.status === "blocked" || result.status === "override_required") {
      showValidationSummaryModal(`Closure ${result.status}: ${result.claim_number || result.claim_id}`, result);
      await refreshClaimViews();
      return;
    }
    showValidationSummaryModal(`Claim closed: ${result.claim_number || result.claim_id}`, result);
    await refreshClaimViews();
  }

  async function handlePostClosureValidation(claimId) {
    const targetId = resolveClaimId(claimId);
    const result = await window.api.postClosureValidate(targetId);
    showValidationSummaryModal(`Post-closure validation: ${result.claim_number || result.claim_id}`, result);
    await refreshClaimViews();
  }

  async function handleBuildPayload(claimId) {
    const targetId = resolveClaimId(claimId);
    const result = await window.api.buildClaimPayload(targetId);
    if (result.status === "blocked") {
      showValidationSummaryModal("Payload generation blocked", result);
      return;
    }
    alert(`Payload built for ${result.claim_number || `claim ${result.claim_id}`}.`);
    await refreshClaimViews();
  }

  async function handleSubmitClaim(channel) {
    const targetId = resolveClaimId(state.claimId);
    const result = await window.api.submitClaim(targetId, channel);
    if (result.status === "blocked" || result.error) {
      showValidationSummaryModal("Submission blocked", result);
      return;
    }
    alert(`Claim submitted via ${result.channel}. Status: ${result.submission_status}.`);
    await refreshClaimViews();
  }

  async function handleViewRemittance() {
    const targetId = resolveClaimId(state.claimId);
    const remittance = await window.api.getClaimRemittance(targetId);
    alert(
      `Remittance status: ${remittance.status}\nReference: ${remittance.reference}\n` +
        `${JSON.stringify(remittance.remittance?.totals || {}, null, 2)}`,
    );
  }

  async function handleViewEvidence() {
    const targetId = resolveClaimId(state.claimId);
    const evidence = await window.api.getClaimEvidence(targetId);
    alert(
      `Evidence packet\nDocuments: ${evidence.documents.join(", ")}\n` +
        `Decision bundles: ${(evidence.decision_bundles || []).length}`,
    );
  }

  async function handleCreatePolicyVersion() {
    if (!hasPermission("settings", "write")) {
      throw new Error("You do not have permission to manage policy versions.");
    }
    const activeProfileId = document
      .querySelector('[data-action="activate-policy"]')
      ?.getAttribute("data-profile-id");
    if (!activeProfileId) {
      throw new Error("No policy profile is available.");
    }
    await window.api.createPolicyVersion(activeProfileId);
    await loadSettings();
  }

  async function handleEditPolicy(button) {
    if (!hasPermission("settings", "write")) {
      throw new Error("You do not have permission to edit policy profiles.");
    }
    const profileId = button.getAttribute("data-profile-id");
    const version = Number(button.getAttribute("data-version"));
    const profiles = await window.api.getPolicyProfiles();
    const profile = profiles.find((item) => item.policy_profile_id === profileId && item.version === version);
    if (!profile) {
      throw new Error("Policy profile not found.");
    }
    showFormModal({
      title: `Edit ${profileId} v${version}`,
      submitLabel: "Save",
      fields: [
        {
          name: "icdEnforcementMode",
          label: "ICD Enforcement",
          type: "select",
          value: profile.runtime_toggles?.icdEnforcementMode || "BLOCK",
          options: statusOptions(["warn", "block"]),
        },
        {
          name: "defaultSubmissionChannel",
          label: "Default Submission Channel",
          type: "select",
          value: profile.runtime_toggles?.defaultSubmissionChannel || "DIRECT",
          options: statusOptions(["direct", "switch"]),
        },
        {
          name: "requireSupervisorOverrideOnWarnings",
          label: "Supervisor Override on Warnings",
          value: String(Boolean(profile.runtime_toggles?.requireSupervisorOverrideOnWarnings)),
        },
        {
          name: "memberNumberRegex",
          label: "Member Number Regex",
          value: profile.runtime_toggles?.memberNumberRegex || "^MEM\\\\d{6}$",
        },
      ],
      onSubmit: async (values, close) => {
        await window.api.updatePolicyProfile(profileId, version, {
          runtime_toggles: {
            icdEnforcementMode: String(values.icdEnforcementMode).toUpperCase(),
            defaultSubmissionChannel: String(values.defaultSubmissionChannel).toUpperCase(),
            requireSupervisorOverrideOnWarnings:
              String(values.requireSupervisorOverrideOnWarnings).toLowerCase() === "true",
            memberNumberRegex: values.memberNumberRegex,
          },
        });
        close();
        await loadSettings();
      },
    });
  }

  async function handleActivatePolicy(button) {
    if (!hasPermission("settings", "write")) {
      throw new Error("You do not have permission to activate policy versions.");
    }
    const profileId = button.getAttribute("data-profile-id");
    const version = Number(button.getAttribute("data-version"));
    if (!confirm(`Activate ${profileId} v${version}?`)) {
      return;
    }
    await window.api.activatePolicyProfile(profileId, version);
    await loadSettings();
  }

  async function handleEditRule(button) {
    if (!hasPermission("settings", "write")) {
      throw new Error("You do not have permission to edit rules.");
    }
    const ruleId = button.getAttribute("data-rule-id");
    const rules = await window.api.getRules();
    const rule = rules.find((item) => item.rule_id === ruleId);
    if (!rule) {
      throw new Error("Rule not found.");
    }
    showFormModal({
      title: `Edit ${ruleId}`,
      submitLabel: "Save",
      fields: [
        {
          name: "enabled",
          label: "Enabled",
          type: "select",
          value: rule.enabled ? "true" : "false",
          options: [
            { value: "true", label: "True" },
            { value: "false", label: "False" },
          ],
        },
        {
          name: "severity",
          label: "Severity",
          type: "select",
          value: rule.severity,
          options: statusOptions(["block", "warn", "info"]),
        },
        { name: "message", label: "Message", value: rule.message },
        { name: "remediation_hint", label: "Remediation Hint", type: "textarea", value: rule.remediation_hint },
        {
          name: "decision_table",
          label: "Decision Table JSON",
          type: "textarea",
          value: JSON.stringify(rule.decision_table || {}, null, 2),
        },
      ],
      onSubmit: async (values, close) => {
        let decisionTable = rule.decision_table;
        try {
          decisionTable = JSON.parse(values.decision_table);
        } catch (error) {
          throw new Error("Decision table must be valid JSON.");
        }
        await window.api.updateRule(ruleId, {
          enabled: values.enabled === "true",
          severity: String(values.severity).toUpperCase(),
          message: values.message,
          remediation_hint: values.remediation_hint,
          decision_table: decisionTable,
        });
        close();
        await loadSettings();
      },
    });
  }

  async function handleDownloadReport(reportId) {
    const report = await window.api.getReport(reportId);
    alert(`Report ready: ${report.name}\nGenerated: ${formatDateTime(report.generated_at)}`);
  }

  async function handleEditPatient(patientId) {
    if (!hasPermission("patients", "write")) {
      throw new Error("You do not have permission to edit patients.");
    }

    const patient = await window.api.getPatient(patientId);
    showFormModal({
      title: "Edit Patient",
      submitLabel: "Save",
      fields: [
        { name: "name", label: "Name", value: patient.name },
        { name: "mrn", label: "Medical Record Number", value: patient.mrn },
        { name: "dob", label: "Date of Birth", type: "date", value: patient.dob },
        { name: "email", label: "Email", type: "email", value: patient.email },
        { name: "phone", label: "Phone", value: patient.phone },
        {
          name: "status",
          label: "Status",
          type: "select",
          value: patient.status,
          options: statusOptions(["active", "inactive", "blocked"]),
        },
      ],
      onSubmit: async (values, close) => {
        await window.api.updatePatient(patientId, { ...patient, ...values });
        close();
        await loadPatients();
      },
    });
  }

  async function handleDeletePatient(patientId) {
    if (!hasPermission("patients", "delete")) {
      throw new Error("You do not have permission to delete patients.");
    }

    if (!confirm("Delete this patient?")) {
      return;
    }

    await window.api.deletePatient(patientId);
    await loadPatients();
  }

  async function handleEditProvider(providerId) {
    if (!hasPermission("providers", "write")) {
      throw new Error("You do not have permission to edit providers.");
    }

    const provider = await window.api.getProvider(providerId);
    showFormModal({
      title: "Edit Provider",
      submitLabel: "Save",
      fields: [
        { name: "name", label: "Name", value: provider.name },
        { name: "npi", label: "NPI", value: provider.npi },
        { name: "specialty", label: "Specialty", value: provider.specialty },
        { name: "email", label: "Email", type: "email", value: provider.email },
        { name: "phone", label: "Phone", value: provider.phone },
        {
          name: "status",
          label: "Status",
          type: "select",
          value: provider.status,
          options: statusOptions(["active", "inactive", "suspended"]),
        },
      ],
      onSubmit: async (values, close) => {
        await window.api.updateProvider(providerId, { ...provider, ...values });
        close();
        await loadProviders();
      },
    });
  }

  async function handleDeleteProvider(providerId) {
    if (!hasPermission("providers", "delete")) {
      throw new Error("You do not have permission to delete providers.");
    }

    if (!confirm("Delete this provider?")) {
      return;
    }

    await window.api.deleteProvider(providerId);
    await loadProviders();
  }

  async function handleEditPayment(paymentId) {
    if (!hasPermission("payments", "write")) {
      throw new Error("You do not have permission to edit payments.");
    }

    const payment = await window.api.getPayment(paymentId);
    showFormModal({
      title: "Edit Payment",
      submitLabel: "Save",
      fields: [
        { name: "amount", label: "Amount", type: "number", min: 0, step: "0.01", value: payment.amount },
        { name: "payment_date", label: "Payment Date", type: "date", value: payment.payment_date },
        { name: "method", label: "Method", value: payment.method },
        {
          name: "status",
          label: "Status",
          type: "select",
          value: payment.status,
          options: statusOptions(["pending", "completed", "failed"]),
        },
      ],
      onSubmit: async (values, close) => {
        values.amount = Number(values.amount);
        await window.api.updatePayment(paymentId, { ...payment, ...values });
        close();
        await loadPayments();
      },
    });
  }

  async function handleEditUser(userId) {
    if (!hasPermission("users", "write")) {
      throw new Error("You do not have permission to edit users.");
    }

    const user = await window.api.getUser(userId);
    showFormModal({
      title: "Edit User",
      submitLabel: "Save",
      fields: [
        { name: "username", label: "Username", value: user.username },
        { name: "email", label: "Email", type: "email", value: user.email },
        {
          name: "role",
          label: "Role",
          type: "select",
          value: user.role,
          options: Object.keys(ROLE_MODULES).map((role) => ({ value: role, label: role })),
        },
        {
          name: "status",
          label: "Status",
          type: "select",
          value: user.status,
          options: statusOptions(["active", "inactive", "locked"]),
        },
      ],
      onSubmit: async (values, close) => {
        await window.api.updateUser(userId, { ...user, ...values });
        close();
        await loadUsers();
      },
    });
  }

  async function handleDeleteUser(userId) {
    if (!hasPermission("users", "delete")) {
      throw new Error("You do not have permission to delete users.");
    }

    if (!confirm("Delete this user?")) {
      return;
    }

    await window.api.deleteUser(userId);
    await loadUsers();
  }

  async function refreshClaimViews() {
    if (state.page === "claims.html") {
      await loadClaims();
    }

    if (state.page === "claim_detail.html") {
      await loadClaimDetail();
    }
  }

  function resolveClaimId(claimId) {
    const numericId = Number(claimId || state.claimId);
    if (!Number.isInteger(numericId) || numericId <= 0) {
      throw new Error("A claim id is required for this action.");
    }
    return numericId;
  }

  function renderTable(items, colspan, rowRenderer, emptyMessage) {
    const tbody = document.querySelector("table tbody");
    if (!tbody) {
      return;
    }

    if (!items.length) {
      tbody.innerHTML = `<tr><td colspan="${colspan}" style="text-align:center;color:#999;">${escapeHtml(emptyMessage)}</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(rowRenderer).join("");
  }

  function renderPatientActions(patientId) {
    if (!hasPermission("patients", "write")) {
      return '<span class="muted">Read only</span>';
    }

    const deleteButton = hasPermission("patients", "delete")
      ? `<button class="chip warn" data-action="delete-patient" data-id="${patientId}">Delete</button>`
      : "";

    return `<button class="chip" data-action="edit-patient" data-id="${patientId}">Edit</button>${deleteButton}`;
  }

  function renderProviderActions(providerId) {
    if (!hasPermission("providers", "write")) {
      return '<span class="muted">Read only</span>';
    }

    const deleteButton = hasPermission("providers", "delete")
      ? `<button class="chip warn" data-action="delete-provider" data-id="${providerId}">Delete</button>`
      : "";

    return `<button class="chip" data-action="edit-provider" data-id="${providerId}">Edit</button>${deleteButton}`;
  }

  function renderClaimActions(claimId, status) {
    const actions = [`<a class="chip info" href="claim_detail.html?id=${claimId}">Open</a>`];

    if (hasPermission("claims", "process")) {
      actions.push(`<button class="chip" data-action="run-readiness" data-id="${claimId}">Run readiness</button>`);

      if (status !== "closed") {
        actions.push(`<button class="chip" data-action="close-file" data-id="${claimId}">Close file</button>`);
      } else {
        actions.push(
          `<button class="chip" data-action="post-closure-validate" data-id="${claimId}">Post-closure validate</button>`,
        );
      }
    }

    return actions.join("");
  }

  function renderPaymentActions(paymentId) {
    if (!hasPermission("payments", "write")) {
      return '<span class="muted">Read only</span>';
    }

    return `<button class="chip" data-action="edit-payment" data-id="${paymentId}">Edit</button>`;
  }

  function renderUserActions(userId) {
    if (!hasPermission("users", "write")) {
      return '<span class="muted">Read only</span>';
    }

    const deleteButton = hasPermission("users", "delete")
      ? `<button class="chip warn" data-action="delete-user" data-id="${userId}">Delete</button>`
      : "";

    return `<button class="chip" data-action="edit-user" data-id="${userId}">Edit</button>${deleteButton}`;
  }

  function showValidationSummaryModal(title, result) {
    const summary = result.validation_summary || buildFallbackValidationSummary(result);
    const overlay = document.createElement("div");
    overlay.style.cssText =
      "position:fixed;inset:0;background:rgba(15,23,42,0.6);display:flex;align-items:center;justify-content:center;z-index:2200;padding:24px;";

    const card = document.createElement("div");
    card.style.cssText =
      "background:#fff;border-radius:20px;width:min(760px,100%);max-height:86vh;overflow:auto;box-shadow:0 24px 55px rgba(15,23,42,0.25);";

    card.innerHTML = `
      <div style="padding:22px 24px;border-bottom:1px solid #e5e7eb;display:flex;gap:16px;justify-content:space-between;align-items:flex-start;">
        <div>
          <h2 style="margin:0 0 6px 0;font-size:1.25rem;">${escapeHtml(title)}</h2>
          <p style="margin:0;color:#475569;">${escapeHtml(summary.summary_message || "Validation completed.")}</p>
        </div>
        <span class="chip ${summary.blockers?.length ? "fail" : summary.warnings?.length ? "warn" : "pass"}">
          ${escapeHtml(summary.outcome || result.outcome || result.status || "PASS")}
        </span>
      </div>
      <div style="padding:18px 24px;display:grid;gap:14px;">
        ${validationGroupMarkup("Blockers", summary.blockers || [], "fail")}
        ${validationGroupMarkup("Warnings", summary.warnings || [], "warn")}
        ${validationGroupMarkup("Information", summary.info || [], "info")}
        ${pmbDecisionMarkup(summary, result)}
        <div style="display:flex;justify-content:flex-end;gap:10px;margin-top:4px;">
          <button type="button" class="btn secondary" data-modal-close>Close</button>
        </div>
      </div>
    `;

    overlay.appendChild(card);
    document.body.appendChild(overlay);
    const close = () => overlay.remove();

    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) close();
    });
    card.querySelector("[data-modal-close]").addEventListener("click", close);
    card.querySelectorAll("[data-jump-target]").forEach((button) => {
      button.addEventListener("click", () => {
        const targetName = button.getAttribute("data-jump-target");
        if (jumpToClaimTarget(targetName)) {
          close();
        }
      });
    });
  }

  function jumpToClaimTarget(targetName) {
    const selectorValue = String(targetName || "").replaceAll("\\", "\\\\").replaceAll('"', '\\"');
    const target =
      document.querySelector(`[data-field="${selectorValue}"]`) ||
      document.getElementById(targetName);
    if (!target) {
      return false;
    }
    target.scrollIntoView({ behavior: "smooth", block: "center" });
    if (String(targetName).toLowerCase() === "diagnoses") {
      focusDiagnosisSearchInput();
    }
    return true;
  }

  function validationGroupMarkup(title, items, chipClass) {
    if (!items.length) {
      return "";
    }
    return `
      <section style="display:grid;gap:8px;">
        <h3 style="margin:0;font-size:.95rem;">${escapeHtml(title)}</h3>
        ${items
          .map((item) => {
            const jumpTarget = item.action?.target || item.jump_target || item.affected_fields?.[0] || "";
            const jumpButton = jumpTarget
              ? `<button type="button" class="chip" data-jump-target="${escapeHtml(jumpTarget)}">Jump to ${escapeHtml(jumpTarget)}</button>`
              : "";
            const autoFixButton = item.allowAutoFix
              ? `<button type="button" class="chip info" data-action="auto-fix-primary">Auto-fix primary</button>`
              : "";
            return `
              <article style="border:1px solid #e5e7eb;border-radius:14px;padding:12px;display:grid;gap:7px;">
                <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;">
                  <strong>${escapeHtml(item.title || item.reason_code)}</strong>
                  <span class="chip ${chipClass}">${escapeHtml(item.reason_code)}</span>
                </div>
                <p style="margin:0;color:#334155;">${escapeHtml(item.message)}</p>
                <p style="margin:0;color:#64748b;font-size:.9rem;">${escapeHtml(item.remediation || item.remediation_hint || "")}</p>
                <div style="display:flex;gap:8px;flex-wrap:wrap;">${jumpButton}${autoFixButton}</div>
              </article>
            `;
          })
          .join("")}
      </section>
    `;
  }

  function pmbDecisionMarkup(summary, result) {
    const pmbDecision = summary.pmb_decision || result.pmb_decision || null;
    const routingDecision = summary.benefit_routing_decision || result.benefit_routing_decision || null;
    const costingPreview = summary.costing_preview || result.costing_preview || null;
    const legacyItems = summary.pmb || result.benefit_route_decisions || [];
    if (!pmbDecision && !routingDecision && !costingPreview && !legacyItems.length) {
      return "";
    }
    const reasonCode = pmbDecision?.reason_code || routingDecision?.reason_code || legacyItems[0]?.reason_code || "PMB";
    const statusLabel = pmbDecision?.pmb_status || routingDecision?.route || legacyItems[0]?.route || "UNKNOWN";
    const matchedCode = pmbDecision?.matched_icd10 || routingDecision?.trigger_icd10 || legacyItems[0]?.trigger_icd10 || "-";
    const mappingId = pmbDecision?.mapping_id || routingDecision?.mapping_id || legacyItems[0]?.mapping_id || "-";
    const conditionId = pmbDecision?.condition_id || routingDecision?.pmb_condition_id || legacyItems[0]?.pmb_condition_id || "-";
    const pmbMessage =
      pmbDecision?.message ||
      routingDecision?.message ||
      legacyItems[0]?.message ||
      "No PMB decision returned.";
    const routeLabel = routingDecision?.route || legacyItems[0]?.route || "-";
    const routeReason = routingDecision?.reason_code || legacyItems[0]?.reason_code || "-";
    const providerMarked = pmbDecision?.provider_marked_pmb ?? routingDecision?.provider_marked_pmb ?? legacyItems[0]?.provider_marked_pmb;
    const schemeAllowed = costingPreview ? formatCurrency(costingPreview.allowed_total || 0) : "-";
    const pmbAllowed =
      costingPreview && costingPreview.pmb_allowed_total != null
        ? formatCurrency(costingPreview.pmb_allowed_total)
        : "-";
    const liability = costingPreview ? formatCurrency(costingPreview.member_liability_estimate || 0) : "-";
    const pendingReviewNote =
      pmbDecision?.pmb_status === "UNKNOWN"
        ? "PMB cannot be evaluated until primary diagnosis is captured."
        : costingPreview?.pending_pmb_review
          ? "Costing preview is provisional while PMB review is pending."
          : "";
    return `
      <section style="display:grid;gap:8px;">
        <h3 style="margin:0;font-size:.95rem;">PMB Detection and Benefit Routing</h3>
        <article style="border:1px solid #dbeafe;background:#eff6ff;border-radius:14px;padding:12px;display:grid;gap:9px;">
          <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;">
            <strong>${escapeHtml(statusLabel)}</strong>
            <span class="chip info">${escapeHtml(reasonCode)}</span>
          </div>
          <p style="margin:0;color:#334155;">${escapeHtml(pmbMessage)}</p>
          <p style="margin:0;color:#64748b;font-size:.9rem;">
            ICD-10: ${escapeHtml(matchedCode)} · Mapping: ${escapeHtml(mappingId)} · Condition: ${escapeHtml(conditionId)} ·
            Provider marked PMB: ${escapeHtml(providerMarked ? "yes" : "no")}
          </p>
          <p style="margin:0;color:#64748b;font-size:.9rem;">
            Route: ${escapeHtml(routeLabel)} · Route reason: ${escapeHtml(routeReason)} · Pricing basis:
            ${escapeHtml(costingPreview?.pricing_basis || "-")}
          </p>
          <p style="margin:0;color:#64748b;font-size:.9rem;">
            Scheme allowed: ${escapeHtml(schemeAllowed)} · PMB allowed: ${escapeHtml(pmbAllowed)} · Member liability estimate:
            ${escapeHtml(liability)}
          </p>
          ${pendingReviewNote ? `<p style="margin:0;color:#0f567b;font-size:.9rem;">${escapeHtml(pendingReviewNote)}</p>` : ""}
          <p style="margin:0;color:#64748b;font-size:.9rem;">${escapeHtml(
            pmbDecision?.remediation_hint || routingDecision?.remediation_hint || legacyItems[0]?.remediation || legacyItems[0]?.remediation_hint || "",
          )}</p>
        </article>
      </section>
    `;
  }

  function buildFallbackValidationSummary(result) {
    const hits = result.decision_bundle?.rule_hits || [];
    const summary = {
      outcome: result.outcome || result.status || result.validation_status || "PASS",
      summary_message: result.error || "Validation completed.",
      blockers: [],
      warnings: [],
      info: [],
      pmb: result.benefit_route_decisions || [],
      pmb_decision: result.pmb_decision || null,
      benefit_routing_decision: result.benefit_routing_decision || null,
      costing_preview: result.costing_preview || null,
    };
    hits.forEach((hit) => {
      const item = {
        severity: hit.severity,
        reason_code: hit.reason_code,
        title: hit.name,
        message: hit.message,
        remediation: hit.remediation_hint,
        affected_fields: hit.affected_fields,
        jump_target: hit.affected_fields?.[0],
      };
      if (hit.severity === "BLOCK") summary.blockers.push(item);
      else if (hit.severity === "WARN") summary.warnings.push(item);
      else summary.info.push(item);
    });
    if (!hits.length && result.error) {
      summary.blockers.push({
        severity: "BLOCK",
        reason_code: "ACTION_BLOCKED",
        title: "Action blocked",
        message: result.error,
        remediation: "Resolve the prerequisite step and retry.",
      });
    }
    return summary;
  }

  function showFormModal({ title, submitLabel, fields, onSubmit }) {
    const overlay = document.createElement("div");
    overlay.style.cssText =
      "position:fixed;inset:0;background:rgba(15,23,42,0.55);display:flex;align-items:center;justify-content:center;z-index:2000;padding:24px;";

    const card = document.createElement("div");
    card.style.cssText =
      "background:#fff;border-radius:16px;padding:24px;width:min(560px,100%);box-shadow:0 20px 45px rgba(15,23,42,0.2);";

    card.innerHTML = `
      <h2 style="margin:0 0 16px 0;font-size:1.25rem;">${escapeHtml(title)}</h2>
      <form style="display:grid;gap:12px;">
        ${fields.map(renderFieldMarkup).join("")}
        <div style="display:flex;gap:12px;justify-content:flex-end;margin-top:8px;">
          <button type="button" class="btn secondary" data-modal-close>Cancel</button>
          <button type="submit" class="btn">${escapeHtml(submitLabel)}</button>
        </div>
      </form>
    `;

    overlay.appendChild(card);
    document.body.appendChild(overlay);

    const form = card.querySelector("form");
    const close = () => overlay.remove();

    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) {
        close();
      }
    });

    card.querySelector("[data-modal-close]").addEventListener("click", close);

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const submitButton = form.querySelector('[type="submit"]');
      submitButton.disabled = true;

      try {
        const formData = new FormData(form);
        const values = Object.fromEntries(formData.entries());
        await onSubmit(values, close);
      } catch (error) {
        alert(error.message || "Unable to save your changes.");
      } finally {
        submitButton.disabled = false;
      }
    });

    return close;
  }

  function renderFieldMarkup(field) {
    const commonStyle =
      "width:100%;padding:10px 12px;border:1px solid #d1d5db;border-radius:10px;font:inherit;box-sizing:border-box;";
    const value = field.value ?? "";

    if (field.type === "select") {
      return `
        <label style="display:grid;gap:6px;">
          <span style="font-weight:600;color:#334155;">${escapeHtml(field.label)}</span>
          <select name="${escapeHtml(field.name)}" style="${commonStyle}">
            ${field.options
              .map(
                (option) => `
                  <option value="${escapeHtml(option.value)}" ${option.value === value ? "selected" : ""}>
                    ${escapeHtml(option.label)}
                  </option>
                `,
              )
              .join("")}
          </select>
        </label>
      `;
    }

    if (field.type === "textarea") {
      return `
        <label style="display:grid;gap:6px;">
          <span style="font-weight:600;color:#334155;">${escapeHtml(field.label)}</span>
          <textarea name="${escapeHtml(field.name)}" style="${commonStyle};min-height:120px;">${escapeHtml(
            String(value),
          )}</textarea>
        </label>
      `;
    }

    const attributes = [
      `name="${escapeHtml(field.name)}"`,
      `type="${escapeHtml(field.type || "text")}"`,
      `style="${commonStyle}"`,
      field.required === false ? "" : "required",
      field.min !== undefined ? `min="${field.min}"` : "",
      field.step !== undefined ? `step="${field.step}"` : "",
      value !== "" ? `value="${escapeHtml(String(value))}"` : "",
    ]
      .filter(Boolean)
      .join(" ");

    return `
      <label style="display:grid;gap:6px;">
        <span style="font-weight:600;color:#334155;">${escapeHtml(field.label)}</span>
        <input ${attributes} />
      </label>
    `;
  }

  function buildPayloadPreview(claim) {
    const diagnosisCodes = (claim.diagnoses || [])
      .map((item) => item.icd10 || item.icd10_code)
      .filter(Boolean);
    return {
      header: {
        claim_id: claim.claim_number,
        scheme_id: claim.scheme || claim.scheme_id,
        member_number: claim.member_number || `PAT-${claim.patient_id}`,
      },
      diagnoses: diagnosisCodes,
      lines: (claim.line_items || []).map((item) => ({
        line_id: item.line_id,
        code: item.service_code,
        claimed_amount: item.claimed_amount,
      })),
      totals: { claimed_total: claim.amount || 0 },
      statuses: {
        readiness: claim.readiness_status,
        closure: claim.status,
        submission: claim.submission_status,
      },
    };
  }

  function buildEdiPreview(claim) {
    const primaryDiagnosis =
      (claim.diagnoses || []).find((item) => item.is_primary || item.diagnosis_type === "PRIMARY") || claim.diagnoses?.[0];
    return [
      `UNH+${claim.claim_number}+MEDCLM+0:912:13.4+ZA'`,
      `BGM+CLAIM+${claim.claim_number}'`,
      `DTM+137+${new Date().toISOString().slice(0, 10)}+102'`,
      `NAD+MSN+${claim.member_number || `PAT-${claim.patient_id}`}'`,
      `RFF+SCH+${claim.scheme}'`,
      `RFF+ICD+${primaryDiagnosis?.icd10 || primaryDiagnosis?.icd10_code || "MISSING"}'`,
      "LIN+1+CONS001+Procedure'",
      "QTY+47+1'",
      `MOA+203+${claim.amount}'`,
      "UNT+9'",
    ].join("\n");
  }

  function setStrongText(row, value) {
    const strong = row.querySelector("strong");
    if (strong) {
      strong.textContent = value;
    }
  }

  function setTextById(id, value) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value;
    }
  }

  function setChipById(id, label, chipClass) {
    const element = document.getElementById(id);
    if (element) {
      element.className = `chip ${chipClass}`;
      element.textContent = label;
    }
  }

  function setPreById(id, value) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value;
    }
  }

  function upperCaseValue(value) {
    return value ? String(value).toUpperCase() : "PENDING";
  }

  function claimStatusClass(claim) {
    const status = String(claim.status || "").toLowerCase();
    if (["reconciled", "paid", "acknowledged", "ready_to_submit", "ready_to_close"].includes(status)) {
      return "pass";
    }
    if (["blocked", "validation_exception", "rejected", "exception"].includes(status)) {
      return "fail";
    }
    return "warn";
  }

  function statusClass(status) {
    switch (String(status).toLowerCase()) {
      case "active":
      case "completed":
      case "validated":
      case "valid":
      case "enabled":
      case "approved":
      case "active":
      case "reconciled":
      case "received":
      case "pass":
        return "pass";
      case "pending":
      case "inactive":
      case "warning":
      case "partial":
      case "draft":
      case "warn":
        return "warn";
      default:
        return "fail";
    }
  }

  function formatCurrency(value) {
    const amount = Number(value);
    return new Intl.NumberFormat("en-ZA", {
      style: "currency",
      currency: "ZAR",
      minimumFractionDigits: 2,
    }).format(Number.isFinite(amount) ? amount : 0);
  }

  function formatDateTime(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString();
  }

  function statusOptions(values) {
    return values.map((value) => ({ value, label: upperCaseValue(value) }));
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }
})();
