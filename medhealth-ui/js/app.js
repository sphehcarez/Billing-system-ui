(() => {
  // Toast + shortcut functions defined further below (canonical at ensureToastHost / showToast)

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
    connection: { status: "checking", message: "Checking API connection..." },
    patients: [],
    providers: [],
    claims: [],
    auditLogs: [],
    selectedProviderId: null,
    claimDetail: null,
    claimDiagnoses: [],
    claimLineItems: [],
    claimAttachments: [],
    claimTransportLogs: [],
    patientClaimContext: null,
    patientTimeline: null,
    selectedPatientId: null,
    pmbReference: null,
    structuredPayload: null,
    latestEdiArtifact: null,
    highlightedLineIds: [],
    highlightedAttachmentTypes: { required: [], recommended: [] },
    icd10Reference: [],
    ediStepperState: { generate: "idle", validate: "idle", submit: "idle", response: "idle" },
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
    void refreshConnectionStatus();
    scheduleConnectionChecks();
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
      const statusPill = document.createElement("div");
      statusPill.className = "connection-pill";
      statusPill.setAttribute("id", "connection-status-pill");
      statusPill.innerHTML = '<span class="connection-dot"></span><span id="connection-status-label">Checking API…</span>';
      actionsBar.insertBefore(statusPill, actionsBar.firstChild);

      const manualLink = document.createElement("a");
      manualLink.href = "manual.html";
      manualLink.className = "btn secondary";
      manualLink.setAttribute("data-manual-link", "true");
      manualLink.textContent = "User Manual";
      actionsBar.insertBefore(manualLink, statusPill.nextSibling);
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

  async function refreshConnectionStatus() {
    const label = document.getElementById("connection-status-label");
    const pill = document.getElementById("connection-status-pill");
    if (!label || !pill || !window.api?.getHealth) {
      return;
    }
    try {
      const health = await window.api.getHealth();
      state.connection = {
        status: health.db === "ok" ? "up" : "degraded",
        message: health.db === "ok" ? "API connected" : "API degraded",
      };
    } catch (_) {
      state.connection = {
        status: "down",
        message: "API down",
      };
    }
    pill.dataset.status = state.connection.status;
    label.textContent = state.connection.message;
    pill.title = `${state.connection.message} · ${window.api.getHealthUrl()}`;
  }

  function scheduleConnectionChecks() {
    if (state.page === "index.html") {
      return;
    }
    window.setInterval(() => {
      void refreshConnectionStatus();
    }, 30000);
  }

  // ===== TOAST — canonical implementation =====
  function ensureToastHost() {
    let host = document.getElementById("toast-host");
    if (!host) {
      host = document.createElement("div");
      host.id = "toast-host";
      host.className = "toast-host";
      document.body.appendChild(host);
    }
    return host;
  }

  function showToast(message, tone = "info", options = {}) {
    const host = ensureToastHost();
    const toast = document.createElement("div");
    const isError = tone === "error";
    const defaultTitle = isError ? "Action failed" : tone === "success" ? "Saved" : "Heads up";
    toast.className = `toast ${tone}`;
    toast.setAttribute("role", isError ? "alert" : "status");
    toast.setAttribute("aria-live", isError ? "assertive" : "polite");
    toast.innerHTML = `
      <div class="toast-body">
        <div class="toast-title">${escapeHtml(options.title || defaultTitle)}</div>
        <div class="toast-message">${escapeHtml(message)}</div>
      </div>
      <button type="button" class="toast-close" aria-label="Dismiss notification">&times;</button>
    `;
    const dismiss = () => {
      toast.classList.add("hide");
      window.setTimeout(() => toast.remove(), 220);
    };
    toast.querySelector(".toast-close").addEventListener("click", dismiss);
    host.appendChild(toast);
    const duration = typeof options.duration === "number" ? options.duration : 4200;
    if (duration > 0) window.setTimeout(dismiss, duration);
    return toast;
  }

  function toastSuccess(msg, opts) { return showToast(msg, "success", opts || {}); }
  function toastError(msg, opts)   { return showToast(msg, "error",   opts || {}); }
  function toastInfo(msg, opts)    { return showToast(msg, "info",    opts || {}); }
  function toastWarning(msg, opts) { return showToast(msg, "warning", opts || {}); }
  // ===== END TOAST =====

  function formatErrorMessage(error, attemptedAction = "request") {
    if (!error) {
      return `Unable to ${attemptedAction}.`;
    }
    if (error.code === "NETWORK_ERROR") {
      return `${attemptedAction} could not reach the API. Check the backend on :8001 and try again.`;
    }
    if (error.status) {
      return `${attemptedAction} failed with HTTP ${error.status}. ${error.message || "Please retry."}`;
    }
    return error.message || `Unable to ${attemptedAction}.`;
  }

  function showDrawer({ title, subtitle = "", content = "", actions = [] }) {
    const overlay = document.createElement("div");
    overlay.className = "drawer-overlay";
    const drawer = document.createElement("aside");
    drawer.className = "drawer";
    drawer.innerHTML = `
      <div class="drawer-header">
        <div>
          <h2>${escapeHtml(title)}</h2>
          <p>${escapeHtml(subtitle)}</p>
        </div>
        <button type="button" class="icon-btn" data-drawer-close>Close</button>
      </div>
      <div class="drawer-actions"></div>
      <div class="drawer-body">${content}</div>
    `;
    overlay.appendChild(drawer);
    document.body.appendChild(overlay);

    const actionsBar = drawer.querySelector(".drawer-actions");
    actions.forEach((action) => {
      const button = document.createElement(action.href ? "a" : "button");
      if (action.href) {
        button.href = action.href;
      } else {
        button.type = "button";
        button.addEventListener("click", action.onClick);
      }
      button.className = action.className || "chip info";
      button.textContent = action.label;
      actionsBar.appendChild(button);
    });

    const previouslyFocused = document.activeElement;
    const closeBtn = drawer.querySelector("[data-drawer-close]");

    const close = () => {
      document.removeEventListener("keydown", handleEsc);
      overlay.remove();
      if (previouslyFocused && previouslyFocused.focus) {
        previouslyFocused.focus();
      }
    };

    const handleEsc = (e) => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("keydown", handleEsc);

    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) close();
    });
    closeBtn.addEventListener("click", close);

    // Focus the close button so keyboard users can immediately interact
    window.setTimeout(() => closeBtn.focus(), 60);

    return { drawer, close };
  }

  function showConfirmDialog({ title, message, confirmLabel = "Confirm", tone = "warn" }) {
    return new Promise((resolve) => {
      const overlay = document.createElement("div");
      overlay.className = "modal-overlay";
      overlay.innerHTML = `
        <div class="modal-card">
          <h2>${escapeHtml(title)}</h2>
          <p>${escapeHtml(message)}</p>
          <div class="modal-actions">
            <button type="button" class="btn secondary" data-confirm-cancel>Cancel</button>
            <button type="button" class="btn ${tone === "warn" ? "warn" : ""}" data-confirm-ok>${escapeHtml(confirmLabel)}</button>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
      const close = (value) => {
        document.removeEventListener("keydown", onEsc);
        overlay.remove();
        resolve(value);
      };
      const onEsc = (e) => { if (e.key === "Escape") close(false); };
      document.addEventListener("keydown", onEsc);
      overlay.addEventListener("click", (event) => {
        if (event.target === overlay) close(false);
      });
      overlay.querySelector("[data-confirm-cancel]").addEventListener("click", () => close(false));
      overlay.querySelector("[data-confirm-ok]").addEventListener("click", () => close(true));
      // Focus confirm button so keyboard users can hit Enter immediately
      window.setTimeout(() => overlay.querySelector("[data-confirm-ok]")?.focus(), 60);
    });
  }

  function showInputDialog({ title, label, value = "", submitLabel = "Save" }) {
    return new Promise((resolve) => {
      const overlay = document.createElement("div");
      overlay.className = "modal-overlay";
      overlay.innerHTML = `
        <div class="modal-card">
          <h2>${escapeHtml(title)}</h2>
          <label class="field" style="margin:0;">
            <span class="label">${escapeHtml(label)}</span>
            <input class="input" id="modal-input-value" value="${escapeHtml(value)}" />
          </label>
          <div class="modal-actions">
            <button type="button" class="btn secondary" data-input-cancel>Cancel</button>
            <button type="button" class="btn" data-input-submit>${escapeHtml(submitLabel)}</button>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
      const input = overlay.querySelector("#modal-input-value");
      const close = (result) => {
        document.removeEventListener("keydown", onEsc);
        overlay.remove();
        resolve(result);
      };
      const onEsc = (e) => { if (e.key === "Escape") close(null); };
      document.addEventListener("keydown", onEsc);
      overlay.querySelector("[data-input-cancel]").addEventListener("click", () => close(null));
      overlay.querySelector("[data-input-submit]").addEventListener("click", () => close(input.value));
      input.addEventListener("keydown", (e) => { if (e.key === "Enter") close(input.value); });
      overlay.addEventListener("click", (event) => {
        if (event.target === overlay) close(null);
      });
      window.setTimeout(() => input.focus(), 60);
    });
  }

  function bindGlobalHandlers() {
    document.addEventListener("click", (event) => {
      const jumpButton = event.target.closest("[data-jump-target]");
      if (jumpButton) {
        event.preventDefault();
        const targetName = jumpButton.getAttribute("data-jump-target");
        let payload = {};
        try {
          payload = JSON.parse(jumpButton.getAttribute("data-jump-payload") || "{}");
        } catch (_) {
          payload = {};
        }
        const lineIds = String(jumpButton.getAttribute("data-jump-line-ids") || "")
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean);
        jumpToClaimTarget(targetName, { ...payload, lineIds: payload.line_ids || lineIds });
        return;
      }

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
    if (button.classList.contains("btn")) {
      button.classList.add("loading");
    } else {
      button.textContent = "Working…";
    }

    try {
      switch (action) {
        case "open-api-docs":
          window.open(window.api.getDocsUrl(), "_blank", "noopener");
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
        case "apply-line-diagnosis-links":
          await handleApplyLineDiagnosisLinks();
          break;
        case "add-attachment":
          await handleAddAttachment(false);
          break;
        case "mark-attachment-provided":
          await handleAddAttachment(true);
          break;
        case "delete-attachment":
          await handleDeleteAttachment(id);
          break;
        case "submit-direct":
          await handleSubmitClaim("direct");
          break;
        case "submit-switch":
          await handleSubmitClaim("switch");
          break;
        case "generate-edi":
          await handleGenerateEdi();
          break;
        case "validate-edi":
          await handleValidateEdi();
          break;
        case "download-edi":
          await handleDownloadEdi();
          break;
        case "submit-edi-switch":
          await handleSubmitEdiSwitch();
          break;
        case "copy-canonical-json":
          await handleCopyCanonicalJson();
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
        case "view-audit-detail":
          await handleViewAuditDetail(id);
          break;
        case "edit-patient":
          await handleEditPatient(id);
          break;
        case "view-provider-workspace":
          state.selectedProviderId = Number(id);
          renderProviderWorkspace();
          break;
        case "delete-patient":
          await handleDeletePatient(id);
          break;
        case "view-patient-claim-context":
          await handleViewPatientClaimContext(id);
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
        case "new-pmb-mapping":
          await handleCreatePmbMapping();
          break;
        case "edit-pmb-mapping":
          await handleEditPmbMapping(button);
          break;
        case "delete-pmb-mapping":
          await handleDeletePmbMapping(button);
          break;
        case "simulate-pmb-mapping":
          await handleSimulatePmbMapping();
          break;
        case "view-transport-detail":
          await handleViewTransportDetail(id);
          break;
        default:
          throw new Error(`Unsupported action: ${action}`);
      }
    } catch (error) {
      showToast(formatErrorMessage(error, action?.replaceAll("-", " ") || "complete the action"), "error", {
        title: "Action failed",
      });
    } finally {
      button.disabled = false;
      button.classList.remove("loading");
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
    state.patients = patients;
    renderTable(
      patients,
      8,
      (patient) => {
        const isReady = !!(patient.email && patient.phone);
        const readinessLabel = isReady ? "READY" : "INCOMPLETE";
        const readinessStyle = isReady
          ? "background:#ecfdf5;color:#065f46;border:1px solid #10b981;"
          : "background:#fffbeb;color:#92400e;border:1px solid #f59e0b;";
        return `
          <tr style="cursor:pointer" tabindex="0"
              onclick="openPatientProfile(${patient.id})"
              onkeydown="if(event.key==='Enter'||event.key===' ')openPatientProfile(${patient.id})">
            <td class="code">${escapeHtml(patient.mrn)}</td>
            <td>${escapeHtml(patient.name)}</td>
            <td>${escapeHtml(patient.email)}</td>
            <td>${escapeHtml(patient.phone)}</td>
            <td><span class="chip ${statusClass(patient.status)}">${escapeHtml(patient.status)}</span></td>
            <td><span style="padding:0.2rem 0.6rem;border-radius:999px;font-size:0.75rem;font-weight:600;${readinessStyle}" title="${isReady ? "All required fields present" : "Missing contact, scheme or provider info"}">${readinessLabel}</span></td>
            <td data-balance-id="${patient.id}">—</td>
            <td class="row-actions" onclick="event.stopPropagation()">${renderPatientActions(patient.id)}</td>
          </tr>
        `;
      },
      "No patients found.",
    );
    // Load outstanding balances in background (non-blocking)
    _loadPatientBalances(patients);
    if (patients.length) {
      const targetId = state.selectedPatientId || patients[0].id;
      await handleViewPatientClaimContext(targetId);
    }
  }

  async function _loadPatientBalances(patients) {
    for (const p of patients) {
      try {
        const bal = await window.api.getPatientBalance(p.id);
        const cell = document.querySelector(`[data-balance-id="${p.id}"]`);
        if (cell) {
          const cents = bal.balance_cents || 0;
          cell.textContent = cents > 0 ? formatCurrency(cents / 100) : "R0.00";
          if (cents > 0) cell.style.color = "#b42318";
        }
      } catch (_) { /* balance display is non-critical */ }
    }
  }

  function renderPatientClaimContext() {
    const container = document.getElementById("patient-claim-context");
    if (!container) {
      return;
    }
    const context = state.patientClaimContext;
    const profile = context?.claim_ready_profile;
    if (!profile) {
      container.textContent = "No claim context found for this patient.";
      return;
    }
    container.innerHTML = `
      <div class="panel" style="display:grid;gap:8px;">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
          <strong>${escapeHtml(profile.patient?.name || context.patient?.name || "Patient")}</strong>
          <a class="chip info" href="${escapeHtml(profile.open_claim_url || "#")}">Open claim</a>
        </div>
        <div class="muted">Member ${escapeHtml(profile.member_number)} · Dependant ${escapeHtml(profile.dependant_code)} · Scheme ${escapeHtml(profile.scheme_id)} / ${escapeHtml(profile.plan_option_id)}</div>
        <div class="muted">Provider ${escapeHtml(profile.provider?.name || "-")} · Practice ${escapeHtml(profile.provider?.practice_number || "-")} · Service ${escapeHtml(profile.visit?.service_date || "-")}</div>
        <div class="muted">Diagnoses: ${escapeHtml((profile.diagnoses || []).map((item) => item.icd10_code).join(", ") || "-")}</div>
        <div class="muted">Tariffs: ${escapeHtml((profile.charge_capture?.tariff_codes || []).join(", ") || "-")} · Claimed total ${formatCurrency(profile.charge_capture?.claimed_total || 0)}</div>
        <div class="muted">Preauth: ${escapeHtml((profile.preauthorisations || []).map((item) => item.auth_number).join(", ") || "-")} · Attachments ${escapeHtml(String((profile.attachments || []).length))}</div>
        <div class="muted">Consent ${escapeHtml(profile.consent?.status || "-")} · Evidence <span class="code">${escapeHtml(profile.evidence_packet_url || "-")}</span></div>
        <div class="muted">Missing indicators: ${escapeHtml((profile.missing_indicators || []).join(", ") || "None")}</div>
      </div>
    `;
  }

  function renderPatientTimeline() {
    const container = document.getElementById("patient-timeline");
    if (!container) {
      return;
    }
    const timeline = state.patientTimeline?.timeline || [];
    if (!timeline.length) {
      container.textContent = "No timeline events found for this patient.";
      return;
    }
    container.innerHTML = timeline
      .slice(0, 12)
      .map(
        (item) => `
          <article style="border-bottom:1px solid #e5e7eb;padding:8px 0;">
            <div style="display:flex;justify-content:space-between;gap:12px;">
              <strong>${escapeHtml(item.event_type)}</strong>
              <span class="muted">${escapeHtml(formatDateTime(item.timestamp))}</span>
            </div>
            <div class="muted">${escapeHtml(item.claim_number || `Claim ${item.claim_id}`)}</div>
          </article>
        `,
      )
      .join("");
  }

  async function loadProviders() {
    const providers = await window.api.getProviders();
    state.providers = providers;
    state.claims = state.claims.length ? state.claims : await window.api.getClaims().catch(() => []);
    state.patients = state.patients.length ? state.patients : await window.api.getPatients().catch(() => []);
    renderTable(
      providers,
      6,
      (provider) => `
        <tr style="cursor:pointer;" tabindex="0"
            onclick="(function(){window._app&&window._app.selectProvider(${provider.id});})()"
            onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();window._app&&window._app.selectProvider(${provider.id});}">
          <td class="code">${escapeHtml(provider.npi)}</td>
          <td>${escapeHtml(provider.name)}</td>
          <td>${escapeHtml(provider.specialty)}</td>
          <td>${escapeHtml(provider.email)}</td>
          <td><span class="chip ${statusClass(provider.status)}">${escapeHtml(provider.status)}</span></td>
          <td class="row-actions" onclick="event.stopPropagation()">${renderProviderActions(provider.id)}</td>
        </tr>
      `,
      "No providers found.",
    );
    if (providers.length) {
      state.selectedProviderId = state.selectedProviderId || providers[0].id;
      renderProviderWorkspace();
    }
  }

  function renderProviderWorkspace() {
    const container = document.getElementById("provider-workspace");
    if (!container) return;
    const provider = (state.providers || []).find(p => p.id === state.selectedProviderId);
    if (!provider) {
      container.innerHTML = '<div class="muted">Select a provider to view details.</div>';
      return;
    }
    const providerClaims = (state.claims || []).filter(c => c.provider_id === provider.id);
    const submitted = providerClaims.filter(c => c.status === "submitted").length;
    const closed    = providerClaims.filter(c => c.status === "closed").length;
    const draft     = providerClaims.filter(c => c.status === "draft").length;
    const statusHtml = `
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;">
        <span class="chip">${providerClaims.length} total claims</span>
        ${draft    ? `<span class="chip warn">${draft} draft</span>` : ""}
        ${submitted ? `<span class="chip info">${submitted} submitted</span>` : ""}
        ${closed   ? `<span class="chip pass">${closed} closed</span>` : ""}
      </div>`;
    container.innerHTML = `
      <div class="panel" style="display:grid;gap:10px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
          <div>
            <strong style="font-size:1rem;">${escapeHtml(provider.name)}</strong>
            <div class="muted" style="margin-top:2px;">${escapeHtml(provider.specialty)}</div>
          </div>
          <span class="chip ${statusClass(provider.status)}">${escapeHtml(provider.status)}</span>
        </div>
        <div style="display:grid;grid-template-columns:max-content 1fr;gap:4px 16px;font-size:0.85rem;">
          <span class="muted">NPI / PCNS</span><span class="code">${escapeHtml(provider.npi)}</span>
          <span class="muted">Practice no.</span><span class="code">${escapeHtml(provider.practice_number || "—")}</span>
          <span class="muted">Discipline</span><span>${escapeHtml(provider.discipline || provider.specialty)}</span>
          <span class="muted">Email</span><span>${escapeHtml(provider.email || "—")}</span>
          <span class="muted">Phone</span><span>${escapeHtml(provider.phone || "—")}</span>
          <span class="muted">DSP</span><span>${provider.is_dsp_provider ? "Yes" : "No"}</span>
        </div>
        ${statusHtml}
        <div style="margin-top:6px;display:flex;gap:8px;">
          <button class="btn secondary" style="font-size:0.8rem;" data-action="edit-provider" data-id="${provider.id}">Edit provider</button>
          <a class="chip info" href="claims.html" style="font-size:0.8rem;">View claims</a>
        </div>
      </div>`;
  }

  async function loadClaims() {
    const claims = await window.api.getClaims();
    state.claims = claims;
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
    state.auditLogs = logs;
    renderAuditTrail();
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
    state.pmbReference = settings.pmb_reference || null;
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

    const mappingBody = document.getElementById("pmb-mapping-rows");
    if (mappingBody) {
      const mappings = settings.pmb_reference?.mappings || [];
      mappingBody.innerHTML = mappings.length
        ? mappings
            .map(
              (mapping) => `
                <tr>
                  <td class="code">${escapeHtml(mapping.mapping_id)}</td>
                  <td>${escapeHtml(mapping.icd10_code)}</td>
                  <td>${escapeHtml(mapping.pmb_condition_id)}</td>
                  <td>${escapeHtml(mapping.match_type)}</td>
                  <td>${escapeHtml(mapping.effective_from || "-")}</td>
                  <td class="row-actions">
                    <button class="chip" data-action="edit-pmb-mapping" data-mapping-id="${escapeHtml(mapping.mapping_id)}">Edit</button>
                    <button class="chip warn" data-action="delete-pmb-mapping" data-mapping-id="${escapeHtml(mapping.mapping_id)}">Delete</button>
                  </td>
                </tr>
              `,
            )
            .join("")
        : '<tr><td colspan="6" style="text-align:center;color:#999;">No PMB mappings found.</td></tr>';
    }

    const retentionEl = document.getElementById("settings-retention");
    const retentionJsonEl = document.getElementById("settings-retention-json");
    const retentionRaw = { retention: settings.retention, retention_matrix: settings.retention_matrix, schema_registry: settings.schema_registry };
    if (retentionJsonEl) {
      retentionJsonEl.textContent = JSON.stringify(retentionRaw, null, 2);
    }
    if (retentionEl) {
      const matrix = settings.retention_matrix || [];
      if (matrix.length) {
        retentionEl.className = "retention-grid";
        retentionEl.innerHTML = matrix.map((row) => `
          <div class="retention-card">
            <div class="artifact">${escapeHtml(row.artifact || "-")}</div>
            <div class="rc-row"><span>Retention</span><span>${escapeHtml(row.retention || "-")}</span></div>
            <div class="rc-row"><span>Storage</span><span>${escapeHtml(row.storage_type || "-")}</span></div>
            <div class="rc-row"><span>Purge</span><span>${escapeHtml(row.purge_behavior || "-")}</span></div>
            ${row.audit_exceptions ? `<div class="rc-row"><span>Audit</span><span>${escapeHtml(row.audit_exceptions)}</span></div>` : ""}
          </div>`).join("");
      } else {
        retentionEl.textContent = "No retention matrix configured.";
      }
    }
  }

  async function loadClaimDetail() {
    const claimId = state.claimId || 1;
    // Fire all requests in parallel — including structuredPayload — to avoid sequential round-trips
    const [claim, diagnoses, lineItems, attachments, transportLogs, icd10Reference, auditLogs, structuredPayload] =
      await Promise.all([
        window.api.getClaim(claimId),
        window.api.getClaimDiagnoses(claimId),
        window.api.getClaimLineItems(claimId),
        window.api.getClaimAttachments(claimId),
        window.api.getClaimTransportLogs(claimId),
        state.icd10Reference.length ? Promise.resolve(state.icd10Reference) : window.api.getIcd10Reference(),
        state.auditLogs.length ? Promise.resolve(state.auditLogs) : window.api.getAuditLogs().catch(() => []),
        window.api.getStructuredClaimPayload(claimId, null).catch(() => null),
      ]);
    state.claimId = claim.id;
    state.claimDetail = claim;
    state.claimDiagnoses = diagnoses || [];
    state.claimLineItems = lineItems || [];
    state.claimAttachments = attachments || [];
    state.claimTransportLogs = transportLogs || [];
    state.latestEdiArtifact = claim.latest_edi_artifact || null;
    state.icd10Reference = icd10Reference || [];
    state.auditLogs = auditLogs || [];
    state.structuredPayload = structuredPayload || null;
    // Reflect transport log history in stepper without resetting in-progress state
    if (state.ediStepperState.generate === "idle" && transportLogs?.length) {
      const events = new Set((transportLogs || []).map((l) => l.event));
      state.ediStepperState = {
        generate: events.has("GENERATED") ? "complete" : "idle",
        validate: events.has("VALIDATED") ? "complete" : "idle",
        submit: events.has("SENT") ? "complete" : "idle",
        response: events.has("RESPONSE") ? "complete" : "idle",
      };
    }

    const memberLabel = claim.member_number || `Patient ${claim.patient_id}`;

    // Sticky cockpit header
    setTextById("claim-number", claim.claim_number);
    setTextById("claim-member", memberLabel);
    setChipById("claim-status-chip", claim.status, claimStatusClass(claim));

    // Right-column summary mirror
    setTextById("claim-number-r", claim.claim_number);
    setTextById("claim-member-r", memberLabel);
    setChipById("claim-status-r", claim.status, claimStatusClass(claim));
    setTextById("claim-created-at", claim.created_at ? formatDateTime(claim.created_at) : "—");
    setTextById("claim-version", claim.version != null ? String(claim.version) : "—");

    // Lifecycle chips
    setTextById("readiness-status", upperCaseValue(claim.readiness_status));
    setTextById("closure-status", claim.latest_snapshot ? "PASS" : "PENDING");
    setTextById("post-closure-status", claim.validation_status ? upperCaseValue(claim.validation_status) : "PENDING");

    renderDiagnosisReferenceOptions();
    renderClaimDiagnoses();
    renderClaimLineDiagnosisOptions();
    renderClaimLineItems();
    renderClaimAttachments();
    renderAttachmentsSummary();
    renderQuickAudit();
    renderClaimPmbSummary(
      claim.latest_pmb_decision,
      claim.latest_benefit_route_decision,
      claim.latest_costing_preview,
    );
    renderSubmissionStepper(state.ediStepperState);
    renderStructuredPayload();
    renderEdiPanel();
    renderTransportTimeline();
  }

  function renderDiagnosisReferenceOptions() {
    const datalist = document.getElementById("icd10-options");
    if (!datalist) return;
    const searchInput = document.getElementById("diagnosis-search-input");

    function buildOptions(query) {
      const codes = state.icd10Reference || [];
      const q = (query || "").toLowerCase().trim();
      const matches = q.length < 2
        ? codes.slice(0, 80)
        : codes.filter(item =>
            item.code.toLowerCase().includes(q) ||
            (item.description || "").toLowerCase().includes(q)
          ).slice(0, 80);
      datalist.innerHTML = matches
        .map(item => {
          const label = escapeHtml(`${item.code} - ${item.description || ""}`);
          return `<option value="${label}">${label}</option>`;
        })
        .join("");
    }

    buildOptions("");
    if (searchInput && !searchInput._icd10Wired) {
      searchInput._icd10Wired = true;
      searchInput.addEventListener("input", () => buildOptions(searchInput.value));
    }
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

  function renderClaimLineDiagnosisOptions() {
    const select = document.getElementById("line-diagnosis-bulk-select");
    if (!select) {
      return;
    }
    select.innerHTML = (state.claimDiagnoses || [])
      .map(
        (diagnosis) =>
          `<option value="${escapeHtml(diagnosis.diagnosis_id)}">${escapeHtml(
            `${diagnosis.icd10_code} ${diagnosis.is_primary ? "(Primary)" : "(Secondary)"}`,
          )}</option>`,
      )
      .join("");
  }

  function renderClaimLineItems() {
    const container = document.getElementById("line-items-list");
    if (!container) {
      return;
    }
    const items = state.claimLineItems || [];
    if (!items.length) {
      container.innerHTML =
        '<div class="panel"><strong>No line items captured.</strong><div class="muted" style="margin-top:6px;">Add billable lines to complete the claim submission dataset.</div></div>';
      return;
    }
    container.innerHTML = `
      <table class="table">
        <thead>
          <tr><th>Select</th><th>Line</th><th>Tariff</th><th>Qty</th><th>Claimed</th><th>Diagnosis</th><th>Status</th></tr>
        </thead>
        <tbody>
          ${items
            .map((item) => {
              const selectedIds = new Set(item.diagnosis_ids || []);
              const options = (state.claimDiagnoses || [])
                .map(
                  (diagnosis) =>
                    `<option value="${escapeHtml(diagnosis.diagnosis_id)}" ${
                      selectedIds.has(diagnosis.diagnosis_id) ? "selected" : ""
                    }>${escapeHtml(`${diagnosis.icd10_code}${diagnosis.is_primary ? " (Primary)" : ""}`)}</option>`,
                )
                .join("");
              const highlight = (state.highlightedLineIds || []).includes(item.line_id) || item.missing_diagnosis_link;
              return `
                <tr data-line-id="${escapeHtml(item.line_id)}" style="${
                  highlight ? "background:#fff7ed;box-shadow:inset 0 0 0 1px #fb923c;" : ""
                }">
                  <td><input type="checkbox" data-line-select="${escapeHtml(item.line_id)}" /></td>
                  <td class="code">${escapeHtml(item.line_id)}</td>
                  <td>${escapeHtml(item.service_code)}</td>
                  <td>${escapeHtml(String(item.quantity))}</td>
                  <td>${formatCurrency(item.claimed_amount)}</td>
                  <td>
                    <select class="input" data-line-diagnosis-select="${escapeHtml(item.line_id)}" multiple size="3">${options}</select>
                  </td>
                  <td><span class="chip ${item.missing_diagnosis_link ? "warn" : "pass"}">${escapeHtml(
                    item.diagnosis_link_status,
                  )}</span></td>
                </tr>
              `;
            })
            .join("")}
        </tbody>
      </table>
    `;
  }

  function renderClaimAttachments() {
    const container = document.getElementById("attachments-list");
    const requirementContainer = document.getElementById("attachment-requirements");
    if (!container) {
      return;
    }
    const attachments = state.claimAttachments || [];
    const requiredTypes = state.highlightedAttachmentTypes.required || [];
    const recommendedTypes = state.highlightedAttachmentTypes.recommended || [];

    if (requirementContainer) {
      const requiredMarkup = requiredTypes.length
        ? requiredTypes.map((item) => `<span class="chip warn">${escapeHtml(item)}</span>`).join(" ")
        : '<span class="muted">No required documents highlighted.</span>';
      const recommendedMarkup = recommendedTypes.length
        ? recommendedTypes.map((item) => `<span class="chip info">${escapeHtml(item)}</span>`).join(" ")
        : '<span class="muted">No recommended documents highlighted.</span>';
      requirementContainer.innerHTML = `
        <div class="drawer-grid">
          <div class="mini-card">
            <strong>Required</strong>
            <div class="muted" style="margin-top:6px;">${requiredMarkup}</div>
          </div>
          <div class="mini-card">
            <strong>Recommended</strong>
            <div class="muted" style="margin-top:6px;">${recommendedMarkup}</div>
          </div>
        </div>
      `;
    }

    if (!attachments.length) {
      container.innerHTML =
        '<div class="panel"><strong>No attachments on this claim.</strong><div class="muted" style="margin-top:6px;">Use Add document or Mark as provided to satisfy attachment and PMB evidence warnings.</div></div>';
      return;
    }

    container.innerHTML = `
      <table class="table">
        <thead>
          <tr><th>Type</th><th>Filename</th><th>Status</th><th>Uploaded</th><th>Actions</th></tr>
        </thead>
        <tbody>
          ${attachments
            .map((document) => {
              const isRequired = requiredTypes.includes(document.doc_type);
              const isRecommended = recommendedTypes.includes(document.doc_type);
              return `
                <tr style="${isRequired ? "background:#fff7ed;" : isRecommended ? "background:#f0f9ff;" : ""}">
                  <td><span class="chip ${isRequired ? "warn" : isRecommended ? "info" : ""}">${escapeHtml(document.doc_type)}</span></td>
                  <td class="code">${escapeHtml(document.filename)}</td>
                  <td>${escapeHtml(document.status)}</td>
                  <td>${escapeHtml(formatDateTime(document.uploaded_at))}</td>
                  <td class="row-actions">
                    <button class="chip warn" data-action="delete-attachment" data-id="${escapeHtml(document.document_id)}">Remove</button>
                  </td>
                </tr>
              `;
            })
            .join("")}
        </tbody>
      </table>
    `;
  }

  function canonicalToStages(payload) {
    if (!payload) return [];
    const c = payload.canonical_json || payload;
    const def = (v) => v != null && v !== "" && !(Array.isArray(v) && v.length === 0);
    const tile = (name, summary, fields, missing) => ({
      name,
      summary,
      fields: fields.filter((f) => def(f.value)),
      missing: missing.filter((m) => !def(m.present)),
      complete: missing.every((m) => def(m.present)),
    });
    return [
      tile("Patient & Member", "Demographics and scheme membership",
        [
          { label: "Patient ID", value: c.patient_id },
          { label: "Member #", value: c.member_number },
          { label: "Scheme", value: c.scheme_name },
          { label: "Option", value: c.scheme_option },
          { label: "DoB", value: c.date_of_birth },
        ],
        [
          { label: "Patient ID", present: c.patient_id },
          { label: "Scheme", present: c.scheme_name },
        ],
      ),
      tile("Provider", "Treating provider and facility",
        [
          { label: "Provider", value: c.provider_name || c.provider_id },
          { label: "Facility", value: c.facility_name },
          { label: "Practice #", value: c.practice_number },
          { label: "Treating Dr", value: c.treating_doctor },
        ],
        [{ label: "Provider", present: c.provider_id }],
      ),
      tile("Diagnoses", "ICD-10 codes linked to this claim",
        (c.diagnoses || []).map((d, i) => ({
          label: i === 0 ? "Primary" : `Secondary ${i}`,
          value: d.icd10_code || d,
        })),
        [{ label: "Primary ICD-10", present: (c.diagnoses || []).length }],
      ),
      tile("Service Lines", "Billed procedures and tariff codes",
        (c.line_items || c.service_lines || []).map((l, i) => ({
          label: `Line ${i + 1}`,
          value: `${l.tariff_code || l.procedure_code || "?"} — ${formatCurrency((l.billed_amount_cents || l.billed_amount || 0) / 100)}`,
        })),
        [{ label: "At least one service line", present: (c.line_items || c.service_lines || []).length }],
      ),
      tile("PMB & Routing", "Prescribed minimum benefit decision",
        [
          { label: "PMB status", value: c.pmb_status },
          { label: "Route", value: c.benefit_route },
          { label: "Condition", value: c.pmb_condition_name || c.condition_name },
          { label: "Pricing basis", value: c.pricing_basis },
        ],
        [],
      ),
      tile("Financials", "Amounts and liability",
        [
          { label: "Billed total", value: formatCurrency((c.total_billed_cents || c.total_billed || 0) / 100) },
          { label: "Scheme allowed", value: formatCurrency((c.allowed_total_cents || c.allowed_total || 0) / 100) },
          { label: "Member liability", value: formatCurrency((c.member_liability_cents || c.member_liability || 0) / 100) },
        ],
        [],
      ),
    ];
  }

  function renderStructuredPayload() {
    const container = document.getElementById("payload-preview");
    const rawEl = document.getElementById("payload-raw-json");
    clearInlineBanner("payload-banner");
    if (!container) return;

    const payload = state.structuredPayload;
    const rawJson = payload?.canonical_json || payload?.canonical_claim || null;

    if (rawEl) {
      rawEl.textContent = rawJson ? JSON.stringify(rawJson, null, 2) : "No canonical JSON available.";
    }

    const tiles = payload?.structured_tiles?.length
      ? payload.structured_tiles.map((t) => ({
          name: t.title,
          summary: t.summary || "",
          fields: t.fields || [],
          missing: (t.missing_fields || []).map((m) => ({ label: m.message, present: false, action: m.action })),
          complete: t.status === "complete",
        }))
      : canonicalToStages(rawJson);

    if (!tiles.length) {
      container.innerHTML =
        '<div class="panel"><strong>No structured payload available.</strong><div class="muted" style="margin-top:6px;">Build the payload or complete the claim workflow to see staged tiles.</div></div>';
      return;
    }

    container.innerHTML = tiles
      .map(
        (tile) => `
          <details class="payload-tile${tile.complete ? "" : " open"}" ${tile.complete ? "" : "open"}>
            <summary class="payload-tile-header">
              <div class="payload-tile-title">
                <span class="payload-tile-name">${escapeHtml(tile.name)}</span>
                <span class="payload-tile-summary">${escapeHtml(tile.summary)}</span>
              </div>
              <span class="chip ${tile.complete ? "pass" : tile.missing?.length ? "warn" : "info"}">${tile.complete ? "COMPLETE" : tile.missing?.length ? "INCOMPLETE" : "PRESENT"}</span>
              <span class="payload-tile-toggle" aria-hidden="true">▾</span>
            </summary>
            <div class="payload-tile-body">
              ${
                tile.fields.length
                  ? `<dl style="display:grid;grid-template-columns:auto 1fr;gap:4px 16px;margin:0;">
                      ${tile.fields
                        .map(
                          (f) =>
                            `<dt style="color:var(--ink-500);font-size:12px;">${escapeHtml(f.label)}</dt>
                             <dd style="margin:0;font-size:12px;font-weight:600;">${escapeHtml(String(f.value ?? "—"))}</dd>`,
                        )
                        .join("")}
                    </dl>`
                  : '<span class="muted" style="font-size:12px;">No fields captured yet.</span>'
              }
              ${
                (tile.missing || []).length
                  ? `<div style="margin-top:10px;display:grid;gap:6px;">
                      ${(tile.missing || [])
                        .map(
                          (m) => `
                            <div class="payload-missing-item">
                              <span style="font-size:12px;">${escapeHtml(m.label || m.message || "Missing field")}</span>
                              ${
                                m.action
                                  ? `<button type="button" class="chip" data-jump-target="${escapeHtml(m.action.target)}">${escapeHtml(m.action.label || `Go to ${m.action.target}`)}</button>`
                                  : ""
                              }
                            </div>`,
                        )
                        .join("")}
                    </div>`
                  : ""
              }
            </div>
          </details>`,
      )
      .join("");
  }

  function setInlineBanner(id, message, tone = "error") {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = message;
    el.className = `inline-banner ${tone}`;
    el.removeAttribute("hidden");
  }

  function clearInlineBanner(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = "";
    el.setAttribute("hidden", "");
  }

  function renderSubmissionStepper(stepStates) {
    const stepper = document.getElementById("submission-stepper");
    if (!stepper) return;
    const keys = ["generate", "validate", "submit", "response"];
    keys.forEach((key) => {
      const step = stepper.querySelector(`[data-step="${key}"]`);
      if (step) step.dataset.state = stepStates[key] || "idle";
    });
  }

  function renderEdiPanel() {
    const artifact = state.latestEdiArtifact;
    clearInlineBanner("edi-error-banner");

    // Status feedback text
    const feedback = document.getElementById("edi-feedback");
    if (feedback) {
      feedback.textContent = artifact
        ? `Artifact ${artifact.artifact_id} · ${artifact.validation_errors?.length ? "Validation issues present" : "Ready for submission"}`
        : "Generate an EDI artifact to validate, export, or submit.";
    }

    // Artifact info card
    const infoCard = document.getElementById("edi-artifact-info");
    if (infoCard) {
      if (artifact) {
        setTextById("edi-artifact-id", artifact.artifact_id || "—");
        const validChip = document.getElementById("edi-validation-chip");
        if (validChip) {
          const hasErrors = artifact.validation_errors?.length;
          validChip.textContent = hasErrors ? "ISSUES" : artifact.validated_at ? "VALID" : "PENDING";
          validChip.className = `chip ${hasErrors ? "fail" : artifact.validated_at ? "pass" : ""}`;
        }
        infoCard.style.display = "";
      } else {
        infoCard.style.display = "none";
      }
    }

    // Pre-fill idempotency key suggestion
    const keyInput = document.getElementById("edi-idempotency-key");
    if (keyInput && !keyInput.value && state.claimDetail) {
      keyInput.placeholder = `edi-switch-${state.claimDetail.id || ""}-v${state.claimDetail.version || "1"}`;
    }

    // Enable submit button only when validated without errors
    const submitBtn = document.getElementById("submit-edi-btn");
    if (submitBtn) {
      const canSubmit = artifact && artifact.validated_at && !artifact.validation_errors?.length;
      submitBtn.disabled = !canSubmit;
    }

    // Raw EDI pre
    setPreById("edi-preview", artifact?.content || state.claimDetail?.latest_payload?.pseudo_edi || "No EDI artifact generated yet.");
  }

  function renderTransportTimeline() {
    const container = document.getElementById("transport-log-timeline");
    if (!container) return;

    const filterEl = document.getElementById("transport-filter");
    const filterVal = filterEl?.value || "";
    const logs = (state.claimTransportLogs || []).filter((l) => !filterVal || l.event === filterVal);

    if (!logs.length) {
      container.innerHTML = '<span class="muted">No transport events yet.</span>';
      return;
    }

    const eventTone = (evt) => {
      if (evt === "GENERATED") return "info";
      if (evt === "VALIDATED") return "pass";
      if (evt === "SENT") return "pass";
      if (evt === "RESPONSE") return "pass";
      return "";
    };

    container.innerHTML = logs
      .map(
        (log) => `
          <div class="transport-event">
            <div class="transport-event-main">
              <span class="chip ${eventTone(log.event)}" style="font-size:11px;">${escapeHtml(log.event || "—")}</span>
              <span class="muted" style="font-size:11px;">${escapeHtml(formatDateTime(log.created_at))}</span>
            </div>
            <div class="transport-event-detail">
              ${escapeHtml(log.message || log.details?.message || JSON.stringify(log.details || {}))}
            </div>
            <div class="transport-event-actions">
              <button class="chip" style="font-size:11px;" data-action="view-transport-detail" data-id="${escapeHtml(String(log.log_id || log.id || ""))}">Details</button>
            </div>
          </div>
        `,
      )
      .join("");

    // Re-bind filter change
    if (filterEl && !filterEl.dataset.bound) {
      filterEl.dataset.bound = "1";
      filterEl.addEventListener("change", () => renderTransportTimeline());
    }
  }

  function handleViewTransportDetail(logId) {
    const log = (state.claimTransportLogs || []).find(
      (l) => String(l.log_id || l.id || "") === String(logId),
    );
    if (!log) {
      toastInfo("Transport event not found in local state.");
      return;
    }
    showDrawer({
      title: `Transport event · ${escapeHtml(log.event || "—")}`,
      subtitle: formatDateTime(log.created_at),
      content: `<pre style="font-size:11px;overflow:auto;max-height:340px;">${escapeHtml(JSON.stringify(log, null, 2))}</pre>`,
      actions: [
        {
          label: "Copy JSON",
          onClick: () => navigator.clipboard.writeText(JSON.stringify(log, null, 2)).then(() => toastSuccess("Copied", { duration: 2000 })),
          className: "chip info",
        },
      ],
    });
  }

  function renderAttachmentsSummary() {
    const container = document.getElementById("attachments-summary");
    if (!container) return;
    const attachments = state.claimAttachments || [];
    if (!attachments.length) {
      container.innerHTML = '<span class="muted">No attachments on this claim.</span>';
      return;
    }
    const counts = attachments.reduce((acc, a) => {
      acc[a.status] = (acc[a.status] || 0) + 1;
      return acc;
    }, {});
    const chips = Object.entries(counts)
      .map(([status, n]) => `<span class="chip ${status === "PROVIDED" ? "pass" : "warn"}">${escapeHtml(status)} (${n})</span>`)
      .join(" ");
    container.innerHTML = `<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px;">${chips}</div>
      <table class="table" style="font-size:12px;">
        <thead><tr><th>Type</th><th>Status</th><th>File</th></tr></thead>
        <tbody>
          ${attachments
            .map(
              (a) => `<tr>
                <td><span class="chip ${["REQUIRED", "MISSING"].includes(a.status) ? "warn" : "info"}" style="font-size:11px;">${escapeHtml(a.doc_type)}</span></td>
                <td>${escapeHtml(a.status)}</td>
                <td class="code" style="font-size:11px;">${escapeHtml(a.filename || "—")}</td>
              </tr>`,
            )
            .join("")}
        </tbody>
      </table>`;
  }

  function renderQuickAudit() {
    const container = document.getElementById("quick-audit-list");
    if (!container) return;
    const logs = state.auditLogs || [];
    const claimId = state.claimId;
    const relevant = claimId
      ? logs.filter((l) => l.resource_id === claimId || l.claim_id === claimId).slice(-3).reverse()
      : logs.slice(-3).reverse();
    if (!relevant.length) {
      container.innerHTML = '<span class="muted">No recent activity found.</span>';
      return;
    }
    const badgeClass = (action) => {
      if (action === "CREATE" || action === "create") return "create";
      if (action === "UPDATE" || action === "update") return "update";
      if (action === "DELETE" || action === "delete") return "delete";
      if (action === "SUBMIT" || action === "submit") return "submit";
      return "system";
    };
    container.innerHTML = relevant
      .map(
        (l) => `<div style="display:flex;flex-direction:column;gap:2px;padding:6px 0;border-bottom:1px solid var(--line-200);">
          <div style="display:flex;align-items:center;gap:8px;">
            <span class="audit-badge ${badgeClass(l.action)}">${escapeHtml(l.action || "—")}</span>
            <span style="font-size:12px;font-weight:600;">${escapeHtml(l.resource_type || l.entity || "—")}</span>
          </div>
          <span class="muted" style="font-size:11px;">${escapeHtml(formatDateTime(l.created_at || l.timestamp))} · ${escapeHtml(l.user_email || l.performed_by || "system")}</span>
        </div>`,
      )
      .join("")
      + `<div style="margin-top:6px;"><a class="chip info" style="font-size:11px;" href="audit.html">View all events</a></div>`;
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
    const evaluatedList = (pmbDecision?.evaluated_icd10_list || []).join(", ") || "-";
    const adminAction = pmbDecision?.action;

    container.innerHTML = `
      <div class="panel" style="display:grid;gap:8px;">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
          <strong>${escapeHtml(pmbStatus)}</strong>
          <span class="chip ${
            pmbStatus === "CONFIRMED" ? "pass" : pmbStatus === "NOT_DETECTED" ? "info" : pmbStatus === "UNKNOWN" ? "fail" : "warn"
          }">${escapeHtml(pmbDecision?.reason_code || routingDecision?.reason_code || "PMB")}</span>
        </div>
        <div class="muted">ICD-10: ${escapeHtml(pmbDecision?.matched_icd10 || "-")} · Mapping: ${escapeHtml(pmbDecision?.mapping_id || "-")} · Condition: ${escapeHtml(pmbDecision?.condition_id || "-")} (${escapeHtml(pmbDecision?.condition_name || "-")})</div>
        <div class="muted">Route: ${escapeHtml(route)} · Provider marked PMB: ${escapeHtml(pmbDecision?.provider_marked_pmb ? "yes" : "no")} · System auto-flagged: ${escapeHtml(pmbDecision?.auto_flagged ? "yes" : "no")}</div>
        <div class="muted">Pricing basis: ${escapeHtml(pricingBasis)} · Scheme allowed: ${formatCurrency(costingPreview?.allowed_total || 0)} · PMB allowed: ${escapeHtml(pmbAllowed)}</div>
        <div class="muted">Member liability estimate: ${formatCurrency(costingPreview?.member_liability_estimate || 0)}</div>
        <div class="muted">Evaluated ICD-10 list: ${escapeHtml(evaluatedList)} · Mapping version: ${escapeHtml(pmbDecision?.mapping_table_version || "-")} · Effective date: ${escapeHtml(pmbDecision?.effective_date_used || "-")}</div>
        <div class="muted">Detection reason: ${escapeHtml(pmbDecision?.detection_reason || "-")} · ${escapeHtml(pmbDecision?.line_level_evaluation_limited ? "Line-level confirmation limited by missing diagnosis linkage." : "")}</div>
        <div class="muted">${escapeHtml(pmbDecision?.explainability || routingDecision?.message || "")}</div>
        ${
          adminAction && state.role === "Administrator"
            ? `<div><a class="chip info" href="settings.html#pmb-mapping-admin">Configure PMB mapping</a></div>`
            : ""
        }
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

  function setLineItemsFeedback(message, tone = "info") {
    const element = document.getElementById("line-items-feedback");
    if (!element) {
      return;
    }
    element.textContent = message || "";
    element.style.color =
      tone === "error" ? "var(--fail)" : tone === "success" ? "var(--pass)" : "var(--ink-500)";
  }

  function setAttachmentsFeedback(message, tone = "info") {
    // Legacy element (full attachments card) — fall back to inline banner in new layout
    const legacy = document.getElementById("attachments-feedback");
    if (legacy) {
      legacy.textContent = message || "";
      legacy.style.color = tone === "error" ? "var(--fail)" : tone === "success" ? "var(--pass)" : "var(--ink-500)";
      return;
    }
    if (message) {
      setInlineBanner("attachments-summary", message, tone === "success" ? "success" : tone === "error" ? "error" : "warn");
    } else {
      clearInlineBanner("attachments-summary");
    }
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

  async function handleApplyLineDiagnosisLinks() {
    const selectedLineIds = Array.from(document.querySelectorAll("[data-line-select]:checked")).map((input) =>
      input.getAttribute("data-line-select"),
    );
    if (!selectedLineIds.length) {
      setLineItemsFeedback("Select at least one line item first.", "error");
      return;
    }
    const bulkSelect = document.getElementById("line-diagnosis-bulk-select");
    const diagnosisIds = Array.from(bulkSelect?.selectedOptions || []).map((option) => option.value);
    for (const lineId of selectedLineIds) {
      const rowSelect = document.querySelector(`[data-line-diagnosis-select="${CSS.escape(lineId)}"]`);
      const rowDiagnosisIds = Array.from(rowSelect?.selectedOptions || []).map((option) => option.value);
      const idsToApply = rowDiagnosisIds.length ? rowDiagnosisIds : diagnosisIds;
      if (!idsToApply.length) {
        setLineItemsFeedback("Choose one or more diagnoses to link to the selected lines.", "error");
        return;
      }
      await window.api.updateClaimLineDiagnosisLinks(resolveClaimId(state.claimId), lineId, idsToApply);
    }
    setLineItemsFeedback("Diagnosis links saved. Post-closure validation is rerunning.", "success");
    const result = await window.api.postClosureValidate(resolveClaimId(state.claimId));
    await refreshClaimViews();
    showValidationSummaryModal(`Post-closure validation: ${result.claim_number || result.claim_id}`, result);
  }

  async function handleAddAttachment(markProvided = false) {
    const requiredType = state.highlightedAttachmentTypes.required?.[0] || "MOTIVATION";
    const suggestedType = markProvided ? requiredType : state.highlightedAttachmentTypes.recommended?.[0] || requiredType;
    showFormModal({
      title: markProvided ? "Mark attachment as provided" : "Add claim attachment",
      submitLabel: markProvided ? "Save record" : "Attach",
      fields: [
        {
          name: "doc_type",
          label: "Document type",
          type: "select",
          value: suggestedType,
          options: ["MOTIVATION", "REPORT", "INVOICE", "PROOF_OF_PAYMENT", "OTHER"].map((value) => ({ value, label: value })),
        },
        {
          name: "filename",
          label: "Filename",
          value: markProvided ? `${suggestedType.toLowerCase()}-provided.txt` : `${suggestedType.toLowerCase()}-upload.pdf`,
        },
        {
          name: "storage_ref",
          label: "Storage reference",
          value: `demo/${resolveClaimId(state.claimId)}/${suggestedType.toLowerCase()}`,
        },
      ],
      onSubmit: async (values, close) => {
        const result = await window.api.addClaimAttachment(resolveClaimId(state.claimId), values);
        close();
        setAttachmentsFeedback(`${values.doc_type} saved. Validation is rerunning.`, "success");
        showToast(`${values.doc_type} attached to claim ${resolveClaimId(state.claimId)}.`, "success", {
          title: markProvided ? "Document recorded" : "Attachment uploaded",
        });
        await refreshClaimViews();
        if (result.post_closure_validation) {
          showValidationSummaryModal(`Post-closure validation: claim ${resolveClaimId(state.claimId)}`, result.post_closure_validation);
        }
      },
    });
  }

  async function handleDeleteAttachment(documentId) {
    const confirmed = await showConfirmDialog({
      title: "Remove attachment",
      message: "Remove this attachment from the claim? This action is audited.",
      confirmLabel: "Remove",
    });
    if (!confirmed) {
      return;
    }
    const result = await window.api.deleteClaimAttachment(resolveClaimId(state.claimId), documentId);
    setAttachmentsFeedback("Attachment removed. Validation is rerunning.", "success");
    showToast("Attachment removed and audit evidence recorded.", "success", {
      title: "Attachment removed",
    });
    await refreshClaimViews();
    if (result.post_closure_validation) {
      showValidationSummaryModal(`Post-closure validation: claim ${resolveClaimId(state.claimId)}`, result.post_closure_validation);
    }
  }

  async function handleRunReadiness(claimId) {
    const targetId = resolveClaimId(claimId);
    const result = await window.api.runReadinessCheck(targetId);
    showToast(`Readiness completed for claim ${result.claim_number || targetId}.`, result.validation_summary?.blockers?.length ? "warn" : "success", {
      title: "Readiness complete",
    });
    showValidationSummaryModal(`Readiness: ${result.claim_number || `claim ${result.claim_id}`}`, result);
    await refreshClaimViews();
  }

  async function handleCloseClaim(claimId) {
    const targetId = resolveClaimId(claimId);
    const confirmed = await showConfirmDialog({
      title: "Close claim",
      message: "Close this claim for billing and create an immutable snapshot?",
      confirmLabel: "Close claim",
    });
    if (!confirmed) {
      return;
    }

    const result = await window.api.closeClaim(targetId);
    if (result.status === "blocked" || result.status === "override_required") {
      showValidationSummaryModal(`Closure ${result.status}: ${result.claim_number || result.claim_id}`, result);
      await refreshClaimViews();
      return;
    }
    showToast(`Claim ${result.claim_number || targetId} closed for billing.`, "success", {
      title: "Claim closed",
    });
    showValidationSummaryModal(`Claim closed: ${result.claim_number || result.claim_id}`, result);
    await refreshClaimViews();
  }

  async function handlePostClosureValidation(claimId) {
    const targetId = resolveClaimId(claimId);
    const result = await window.api.postClosureValidate(targetId);
    showToast(`Post-closure validation finished for claim ${result.claim_number || targetId}.`, result.validation_summary?.warnings?.length ? "warn" : "success", {
      title: "Validation complete",
    });
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
    showToast(`Payload built for ${result.claim_number || `claim ${result.claim_id}`}.`, "success", {
      title: "Payload generated",
    });
    await refreshClaimViews();
  }

  async function handleSubmitClaim(channel) {
    const targetId = resolveClaimId(state.claimId);
    const result = await window.api.submitClaim(targetId, channel);
    if (result.status === "blocked" || result.error) {
      showValidationSummaryModal("Submission blocked", result);
      return;
    }
    showToast(`Claim submitted via ${result.channel}. Status: ${result.submission_status}.`, "success", {
      title: "Submission complete",
    });
    await refreshClaimViews();
  }

  async function handleViewRemittance() {
    const targetId = resolveClaimId(state.claimId);
    const remittance = await window.api.getClaimRemittance(targetId);
    const reconciliation = await window.api._request(`/payments/claims/${targetId}/reconciliation`, "GET");
    const remittanceData = remittance.remittance || {};
    const { close } = showDrawer({
      title: `Remittance review · Claim ${targetId}`,
      subtitle: `Status ${remittance.status || "-"} · Batch ${remittance.reference || "-"}`,
      content: `
        <div class="drawer-grid">
          <div class="mini-card">
            <strong>Totals</strong>
            <div class="muted">Claimed ${formatCurrency(remittanceData.totals?.claimed || 0)}</div>
            <div class="muted">Paid ${formatCurrency(remittanceData.totals?.paid || 0)}</div>
            <div class="muted">Adjustments ${formatCurrency(remittanceData.totals?.adjustments || 0)}</div>
          </div>
          <div class="mini-card">
            <strong>Reconciliation</strong>
            <div class="muted">Status ${escapeHtml((reconciliation.reconciliation || {}).status || reconciliation.status || "-")}</div>
            <div class="muted">Exceptions ${escapeHtml(((reconciliation.reconciliation || {}).exception_reasons || []).join(", ") || "None")}</div>
          </div>
        </div>
        <div class="mini-card" style="margin-top:16px;">
          <strong>Line breakdown</strong>
          <table class="table" style="margin-top:10px;">
            <thead><tr><th>Line</th><th>Status</th><th>Paid</th><th>Adjustment</th></tr></thead>
            <tbody>
              ${(remittanceData.lines || [])
                .map(
                  (line) => `
                    <tr>
                      <td class="code">${escapeHtml(line.line_id)}</td>
                      <td>${escapeHtml(line.status)}</td>
                      <td>${formatCurrency(line.paid_amount || 0)}</td>
                      <td>${formatCurrency(line.adjustment_amount || 0)}</td>
                    </tr>
                  `,
                )
                .join("") || '<tr><td colspan="4" class="muted">No remittance lines available.</td></tr>'}
            </tbody>
          </table>
        </div>
      `,
      actions: [
        {
          label: "Download remittance JSON",
          onClick: () => downloadJson(`remittance-claim-${targetId}.json`, remittance),
          className: "chip info",
        },
      ],
    });
    void close;
  }

  async function handleViewEvidence() {
    const targetId = resolveClaimId(state.claimId);
    const evidence = await window.api.getClaimEvidence(targetId);
    showDrawer({
      title: `Evidence pack · Claim ${targetId}`,
      subtitle: `Last updated ${formatDateTime(state.claimDetail?.updated_at || state.claimDetail?.created_at || new Date().toISOString())}`,
      content: buildEvidencePackMarkup(evidence),
      actions: [
        {
          label: "Download full pack JSON",
          onClick: () => downloadJson(`evidence-pack-claim-${targetId}.json`, evidence),
          className: "chip info",
        },
      ],
    });
  }

  async function handleGenerateEdi() {
    state.ediStepperState = { generate: "active", validate: "idle", submit: "idle", response: "idle" };
    renderSubmissionStepper(state.ediStepperState);
    clearInlineBanner("edi-error-banner");
    try {
      const result = await window.api.generateClaimEdi(resolveClaimId(state.claimId), state.claimDetail.version);
      state.latestEdiArtifact = result.artifact;
      state.claimTransportLogs = await window.api.getClaimTransportLogs(resolveClaimId(state.claimId));
      state.ediStepperState.generate = "complete";
      renderSubmissionStepper(state.ediStepperState);
      renderEdiPanel();
      renderTransportTimeline();
      showToast(`EDI generated for claim ${resolveClaimId(state.claimId)}.`, "success", { title: "EDI generated" });
    } catch (err) {
      state.ediStepperState.generate = "error";
      renderSubmissionStepper(state.ediStepperState);
      setInlineBanner("edi-error-banner", formatErrorMessage(err, "generate EDI"), "error");
      throw err;
    }
  }

  async function handleValidateEdi() {
    state.ediStepperState.validate = "active";
    renderSubmissionStepper(state.ediStepperState);
    clearInlineBanner("edi-error-banner");
    try {
      const result = await window.api.validateClaimEdi(resolveClaimId(state.claimId), state.claimDetail.version);
      state.latestEdiArtifact = result.artifact;
      state.claimTransportLogs = await window.api.getClaimTransportLogs(resolveClaimId(state.claimId));
      state.ediStepperState.validate = result.valid ? "complete" : "error";
      renderSubmissionStepper(state.ediStepperState);
      renderEdiPanel();
      renderTransportTimeline();
      showToast(
        result.valid ? "EDI validation passed." : `EDI validation failed: ${(result.errors || []).join(", ")}`,
        result.valid ? "success" : "error",
        { title: "EDI validation" },
      );
    } catch (err) {
      state.ediStepperState.validate = "error";
      renderSubmissionStepper(state.ediStepperState);
      setInlineBanner("edi-error-banner", formatErrorMessage(err, "validate EDI"), "error");
      throw err;
    }
  }

  async function handleDownloadEdi() {
    const content = await window.api.downloadClaimEdi(resolveClaimId(state.claimId), state.claimDetail.version);
    const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `claim-${resolveClaimId(state.claimId)}-v${state.claimDetail.version}.edi.txt`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
  }

  async function handleSubmitEdiSwitch() {
    const keyInput = document.getElementById("edi-idempotency-key");
    const suggestedKey = keyInput?.value || `edi-switch-${resolveClaimId(state.claimId)}-v${state.claimDetail.version}`;
    const idempotencyKey = await showInputDialog({
      title: "Submit via Switch",
      label: "Idempotency key",
      value: suggestedKey,
      submitLabel: "Submit",
    });
    if (idempotencyKey === null) return;

    state.ediStepperState.submit = "active";
    renderSubmissionStepper(state.ediStepperState);
    clearInlineBanner("edi-error-banner");
    try {
      const result = await window.api.submitClaimEdi(
        resolveClaimId(state.claimId),
        state.claimDetail.version,
        "SWITCH",
        idempotencyKey || null,
      );
      if (result.status === "blocked") {
        state.ediStepperState.submit = "error";
        renderSubmissionStepper(state.ediStepperState);
        setInlineBanner("edi-error-banner", `EDI submission blocked: ${(result.errors || []).join(", ")}`, "error");
        showToast(`EDI submission blocked: ${(result.errors || []).join(", ")}`, "error", { title: "Submission blocked" });
        return;
      }
      state.latestEdiArtifact = result.artifact;
      state.claimTransportLogs = result.transport_logs || [];
      state.ediStepperState.submit = "complete";
      state.ediStepperState.response = result.submission ? "complete" : "idle";
      renderSubmissionStepper(state.ediStepperState);
      await refreshClaimViews();
      renderEdiPanel();
      renderTransportTimeline();
      showToast(
        `Submitted via Switch. Claim status: ${result.submission?.submission_status || result.submission?.status || "-"}.`,
        "success",
        { title: "Switch submission completed" },
      );
    } catch (err) {
      state.ediStepperState.submit = "error";
      renderSubmissionStepper(state.ediStepperState);
      setInlineBanner("edi-error-banner", formatErrorMessage(err, "submit EDI"), "error");
      throw err;
    }
  }

  async function handleCopyCanonicalJson() {
    const payload = state.structuredPayload?.canonical_json || state.claimDetail?.latest_payload?.canonical_claim;
    if (!payload) {
      throw new Error("No canonical payload is available to copy.");
    }
    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    showToast("Canonical JSON copied to clipboard.", "success", {
      title: "Copied",
      duration: 2600,
    });
  }

  async function handleViewPatientClaimContext(patientId) {
    state.selectedPatientId = Number(patientId);
    const [claimContext, timeline] = await Promise.all([
      window.api.getPatientClaimContext(state.selectedPatientId),
      window.api.getPatientTimeline(state.selectedPatientId),
    ]);
    state.patientClaimContext = claimContext;
    state.patientTimeline = timeline;
    renderPatientClaimContext();
    renderPatientTimeline();
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
    showToast(`Draft policy version created for ${activeProfileId}.`, "success", {
      title: "Policy version created",
    });
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
    const confirmed = await showConfirmDialog({
      title: "Activate policy version",
      message: `Activate ${profileId} v${version}? Changes are audited.`,
      confirmLabel: "Activate",
    });
    if (!confirmed) {
      return;
    }
    await window.api.activatePolicyProfile(profileId, version);
    showToast(`${profileId} v${version} is now active.`, "success", {
      title: "Policy activated",
    });
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

  async function handleCreatePmbMapping() {
    if (state.role !== "Administrator") {
      throw new Error("Only Administrators may manage PMB mappings.");
    }
    const conditions = state.pmbReference?.conditions || [];
    showFormModal({
      title: "Create PMB Mapping",
      submitLabel: "Create",
      fields: [
        { name: "mapping_id", label: "Mapping ID" },
        { name: "icd10_code", label: "ICD-10 Code" },
        {
          name: "pmb_condition_id",
          label: "Condition",
          type: "select",
          options: conditions.map((item) => ({ value: item.condition_id, label: `${item.condition_id} - ${item.name}` })),
        },
        {
          name: "match_type",
          label: "Match Type",
          type: "select",
          value: "EXACT",
          options: statusOptions(["exact", "prefix"]),
        },
        { name: "effective_from", label: "Effective From", type: "date", value: new Date().toISOString().slice(0, 10) },
      ],
      onSubmit: async (values, close) => {
        await window.api.createPmbMapping({
          mapping_id: values.mapping_id,
          icd10_code: values.icd10_code,
          pmb_condition_id: values.pmb_condition_id,
          match_type: String(values.match_type).toUpperCase(),
          effective_from: values.effective_from,
        });
        close();
        await loadSettings();
      },
    });
  }

  async function handleEditPmbMapping(button) {
    if (state.role !== "Administrator") {
      throw new Error("Only Administrators may manage PMB mappings.");
    }
    const mappingId = button.getAttribute("data-mapping-id");
    const mapping = (state.pmbReference?.mappings || []).find((item) => item.mapping_id === mappingId);
    const conditions = state.pmbReference?.conditions || [];
    if (!mapping) {
      throw new Error("PMB mapping not found.");
    }
    showFormModal({
      title: `Edit ${mappingId}`,
      submitLabel: "Save",
      fields: [
        { name: "icd10_code", label: "ICD-10 Code", value: mapping.icd10_code },
        {
          name: "pmb_condition_id",
          label: "Condition",
          type: "select",
          value: mapping.pmb_condition_id,
          options: conditions.map((item) => ({ value: item.condition_id, label: `${item.condition_id} - ${item.name}` })),
        },
        {
          name: "match_type",
          label: "Match Type",
          type: "select",
          value: mapping.match_type,
          options: statusOptions(["exact", "prefix"]),
        },
        { name: "effective_from", label: "Effective From", type: "date", value: mapping.effective_from },
        {
          name: "active",
          label: "Active",
          type: "select",
          value: mapping.active ? "true" : "false",
          options: [
            { value: "true", label: "True" },
            { value: "false", label: "False" },
          ],
        },
      ],
      onSubmit: async (values, close) => {
        await window.api.updatePmbMapping(mappingId, {
          icd10_code: values.icd10_code,
          pmb_condition_id: values.pmb_condition_id,
          match_type: String(values.match_type).toUpperCase(),
          effective_from: values.effective_from,
          active: values.active === "true",
        });
        close();
        await loadSettings();
      },
    });
  }

  async function handleDeletePmbMapping(button) {
    if (state.role !== "Administrator") {
      throw new Error("Only Administrators may manage PMB mappings.");
    }
    const mappingId = button.getAttribute("data-mapping-id");
    const confirmed = await showConfirmDialog({
      title: "Delete PMB mapping",
      message: `Delete PMB mapping ${mappingId}?`,
      confirmLabel: "Delete",
    });
    if (!confirmed) {
      return;
    }
    await window.api.deletePmbMapping(mappingId);
    showToast(`PMB mapping ${mappingId} deleted.`, "success", {
      title: "Mapping deleted",
    });
    await loadSettings();
  }

  async function handleSimulatePmbMapping() {
    const input = document.getElementById("pmb-simulate-icd10");
    const output = document.getElementById("pmb-simulation-output");
    const code = String(input?.value || "").trim().toUpperCase();
    if (!code) {
      throw new Error("Enter an ICD-10 code to simulate.");
    }
    const result = await window.api.simulatePmbMapping(code);
    if (output) {
      output.innerHTML = `
        <div class="mini-card">
          <strong>${escapeHtml(code)}</strong>
          <div class="muted">Matches ${(result.matches || []).length} · Impacted claims ${(result.impacted_claims || []).length}</div>
          <div class="muted" style="margin-top:8px;">${escapeHtml(JSON.stringify(result, null, 2))}</div>
        </div>
      `;
    }
  }

  async function handleDownloadReport(reportId) {
    const report = await window.api.getReport(reportId);
    showToast(`Report ready: ${report.name}.`, "success", {
      title: "Report generated",
    });
    downloadJson(`${report.name.replace(/\s+/g, "-").toLowerCase()}.json`, report);
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

    const confirmed = await showConfirmDialog({
      title: "Delete patient",
      message: "Delete this patient record?",
      confirmLabel: "Delete",
    });
    if (!confirmed) {
      return;
    }

    await window.api.deletePatient(patientId);
    showToast("Patient deleted.", "success", { title: "Patient deleted" });
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

    const confirmed = await showConfirmDialog({
      title: "Delete provider",
      message: "Delete this provider record?",
      confirmLabel: "Delete",
    });
    if (!confirmed) {
      return;
    }

    await window.api.deleteProvider(providerId);
    showToast("Provider deleted.", "success", { title: "Provider deleted" });
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

    const confirmed = await showConfirmDialog({
      title: "Delete user",
      message: "Delete this user account?",
      confirmLabel: "Delete",
    });
    if (!confirmed) {
      return;
    }

    await window.api.deleteUser(userId);
    showToast("User deleted.", "success", { title: "User deleted" });
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
    const actions = [
      `<button class="chip info" data-action="view-patient-claim-context" data-id="${patientId}">Claim-ready profile</button>`,
    ];
    if (!hasPermission("patients", "write")) {
      actions.push('<span class="muted">Read only</span>');
      return actions.join(" ");
    }

    const deleteButton = hasPermission("patients", "delete")
      ? `<button class="chip warn" data-action="delete-patient" data-id="${patientId}">Delete</button>`
      : "";

    actions.push(`<button class="chip" data-action="edit-patient" data-id="${patientId}">Edit</button>`);
    if (deleteButton) {
      actions.push(deleteButton);
    }
    return actions.join(" ");
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
        const lineIds = String(button.getAttribute("data-jump-line-ids") || "")
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean);
        if (jumpToClaimTarget(targetName, { lineIds })) {
          close();
        }
      });
    });
  }

  function jumpToClaimTarget(targetName, options = {}) {
    if (targetName === "PMB_MAPPING_ADMIN") {
      location.href = "settings.html#pmb-mapping-admin";
      return true;
    }
    const selectorValue = String(targetName || "").replaceAll("\\", "\\\\").replaceAll('"', '\\"');
    const target =
      document.querySelector(`[data-field="${selectorValue}"]`) ||
      document.getElementById(targetName);
    if (!target) {
      return false;
    }
    if (targetName === "line_items") {
      state.highlightedLineIds = options.lineIds?.length
        ? options.lineIds
        : (state.claimLineItems || [])
            .filter((item) => item.missing_diagnosis_link)
            .map((item) => item.line_id);
      renderClaimLineItems();
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
            const jumpTarget = item.action?.target || item.action_target || item.jump_target || item.affected_fields?.[0] || "";
            const jumpLabel = jumpTarget === "line_items" ? "Jump to line items" : `Jump to ${jumpTarget}`;
            const jumpLineIds = (item.action?.line_ids || item.affected_line_ids || []).join(",");
            const jumpButton = jumpTarget
              ? `<button type="button" class="chip" data-jump-target="${escapeHtml(jumpTarget)}" data-jump-line-ids="${escapeHtml(jumpLineIds)}">${escapeHtml(jumpLabel)}</button>`
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
    const conditionName = pmbDecision?.condition_name || "-";
    const evaluatedIcd10List = (pmbDecision?.evaluated_icd10_list || []).join(", ") || matchedCode;
    const pmbMessage =
      pmbDecision?.message ||
      routingDecision?.message ||
      legacyItems[0]?.message ||
      "No PMB decision returned.";
    const routeLabel = routingDecision?.route || legacyItems[0]?.route || "-";
    const routeReason = routingDecision?.reason_code || legacyItems[0]?.reason_code || "-";
    const providerMarked = pmbDecision?.provider_marked_pmb ?? routingDecision?.provider_marked_pmb ?? legacyItems[0]?.provider_marked_pmb;
    const autoFlagged = pmbDecision?.auto_flagged;
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
            ICD-10: ${escapeHtml(matchedCode)} · Mapping: ${escapeHtml(mappingId)} · Condition: ${escapeHtml(conditionId)} (${escapeHtml(conditionName)}) ·
            Provider marked PMB: ${escapeHtml(providerMarked ? "yes" : "no")} · System auto-flagged: ${escapeHtml(autoFlagged ? "yes" : "no")}
          </p>
          <p style="margin:0;color:#64748b;font-size:.9rem;">
            Route: ${escapeHtml(routeLabel)} · Route reason: ${escapeHtml(routeReason)} · Pricing basis:
            ${escapeHtml(costingPreview?.pricing_basis || "-")}
          </p>
          <p style="margin:0;color:#64748b;font-size:.9rem;">
            Evaluated ICD-10 list: ${escapeHtml(evaluatedIcd10List)} · Mapping version: ${escapeHtml(
              pmbDecision?.mapping_table_version || "-",
            )} · Effective date: ${escapeHtml(pmbDecision?.effective_date_used || "-")}
          </p>
          <p style="margin:0;color:#64748b;font-size:.9rem;">${escapeHtml(
            pmbDecision?.explainability || "",
          )}</p>
          <p style="margin:0;color:#64748b;font-size:.9rem;">
            Scheme allowed: ${escapeHtml(schemeAllowed)} · PMB allowed: ${escapeHtml(pmbAllowed)} · Member liability estimate:
            ${escapeHtml(liability)}
          </p>
          ${pendingReviewNote ? `<p style="margin:0;color:#0f567b;font-size:.9rem;">${escapeHtml(pendingReviewNote)}</p>` : ""}
          ${
            pmbDecision?.action?.target === "PMB_MAPPING_ADMIN" && state.role === "Administrator"
              ? `<div><button type="button" class="chip info" data-jump-target="PMB_MAPPING_ADMIN">Configure PMB mapping</button></div>`
              : ""
          }
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
        toastError(error.message || "Unable to save your changes.");
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

  // ===== PATIENT PROFILE DRAWER =====
  async function openPatientProfile(patientId) {
    try {
      const [context, balance, invoices] = await Promise.all([
        window.api.getPatientClaimContext(patientId),
        window.api.getPatientBalance(patientId).catch(() => ({ balance_cents: 0, credit_cents: 0 })),
        window.api.getPatientInvoices(patientId).catch(() => []),
      ]);
      // Flatten claim_ready_profile up to the top level expected by renderPatientProfileDrawer
      const profile = context?.claim_ready_profile || context || {};
      renderPatientProfileDrawer(patientId, profile, balance, invoices);
    } catch (e) {
      toastError("Could not load patient profile.");
    }
  }

  function renderPatientProfileDrawer(patientId, profile, balance, invoices = []) {
    let drawer = document.getElementById("patient-profile-drawer");
    if (!drawer) {
      drawer = document.createElement("div");
      drawer.id = "patient-profile-drawer";
      drawer.style.cssText = "position:fixed;top:0;right:0;height:100vh;width:460px;background:#fff;box-shadow:-4px 0 20px rgba(0,0,0,0.15);z-index:1000;overflow-y:auto;padding:1.5rem;transform:translateX(100%);transition:transform 0.25s ease;";
      document.body.appendChild(drawer);
    }

    const readinessColor = profile.readiness === "READY" ? "#10b981" : "#f59e0b";
    const missingHtml = (profile.missing_items || []).slice(0, 3).map(item =>
      `<li style="font-size:0.8rem;color:#6b7280">${escapeHtml(item.label)}</li>`
    ).join("");

    const balanceCents = balance?.balance_cents ?? 0;
    const creditCents  = balance?.credit_cents ?? 0;

    const billingHtml = profile.billing_summary ? `
      <div style="background:#f9fafb;border-radius:8px;padding:0.875rem;margin-top:0.875rem">
        <div style="font-weight:600;margin-bottom:0.5rem;font-size:0.875rem">Billing Summary</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.25rem;font-size:0.8rem">
          <span style="color:#6b7280">Claimed:</span><span>${formatCurrency((profile.billing_summary.claimed_cents||0)/100)}</span>
          <span style="color:#6b7280">Scheme allowed:</span><span>${formatCurrency((profile.billing_summary.scheme_allowed_cents||0)/100)}</span>
          <span style="color:#6b7280">Member liability:</span><span style="color:#ef4444;font-weight:600">${formatCurrency((profile.billing_summary.member_liability_cents||0)/100)}</span>
        </div>
      </div>` : "";

    // Membership section
    const memberHtml = `
      <div style="background:#f9fafb;border-radius:8px;padding:0.875rem;margin-top:0.875rem;font-size:0.8rem">
        <div style="font-weight:600;margin-bottom:0.5rem">Membership</div>
        <div style="display:grid;grid-template-columns:max-content 1fr;gap:0.2rem 0.75rem;color:#374151">
          <span style="color:#6b7280">Scheme</span><span>${escapeHtml(profile.scheme_id || "-")}</span>
          <span style="color:#6b7280">Option</span><span>${escapeHtml(profile.plan_option_id || "-")}</span>
          <span style="color:#6b7280">Number</span><span>${escapeHtml(profile.member_number || "-")}</span>
          <span style="color:#6b7280">Dependant</span><span>${escapeHtml(profile.dependant_code || "00")}</span>
        </div>
      </div>`;

    // Outstanding invoices section
    const openInvoices = (invoices || []).filter(inv => (inv.status || inv.Status || "OPEN") !== "PAID" && (inv.status || "OPEN") !== "VOIDED");
    const invoicesHtml = openInvoices.length ? `
      <div style="background:#fef2f2;border-radius:8px;padding:0.875rem;margin-top:0.875rem;font-size:0.8rem">
        <div style="font-weight:600;margin-bottom:0.5rem;color:#991b1b">Outstanding Invoices (${openInvoices.length})</div>
        ${openInvoices.map(inv => `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:0.4rem 0;border-bottom:1px solid #fee2e2">
            <div>
              <span style="font-family:var(--mono);font-size:0.75rem;color:#6b7280">${escapeHtml(inv.id || "-")}</span>
              <span style="margin-left:0.5rem;background:#fca5a5;color:#7f1d1d;padding:0.1rem 0.4rem;border-radius:4px;font-size:0.7rem">${escapeHtml(inv.status || "OPEN")}</span>
            </div>
            <div style="display:flex;align-items:center;gap:0.5rem">
              <strong style="color:#991b1b">${formatCurrency(((inv.total_cents||0) - (inv.paid_cents||0)) / 100)}</strong>
              <button class="chip warn" style="font-size:0.7rem" onclick="handlePayInvoice(${patientId}, ${JSON.stringify((inv.total_cents||0) - (inv.paid_cents||0)).replace(/"/g, "&quot;")}, '${escapeHtml(inv.id || "")}')">Pay now</button>
            </div>
          </div>`).join("")}
        <div style="margin-top:0.5rem;font-size:0.75rem;color:#6b7280">Total outstanding: <strong style="color:#991b1b">${formatCurrency(openInvoices.reduce((s, inv) => s + Math.max(0, (inv.total_cents||0) - (inv.paid_cents||0)), 0) / 100)}</strong></div>
      </div>` : (balanceCents > 0 ? "" : `<div style="background:#ecfdf5;border-radius:8px;padding:0.75rem;margin-top:0.875rem;font-size:0.8rem;color:#065f46">No outstanding invoices.</div>`);

    drawer.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.25rem">
        <h3 style="margin:0;font-size:1rem">${escapeHtml(profile.patient?.name || "Patient Profile")}</h3>
        <button onclick="closePatientProfile()" style="background:none;border:none;font-size:1.25rem;cursor:pointer;color:#6b7280">&times;</button>
      </div>
      <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.75rem">
        <span style="background:${readinessColor};color:#fff;padding:0.2rem 0.6rem;border-radius:999px;font-size:0.75rem;font-weight:600">${escapeHtml(profile.readiness || "UNKNOWN")}</span>
        ${balanceCents > 0 ? `<span style="background:#fef2f2;color:#991b1b;padding:0.2rem 0.6rem;border-radius:999px;font-size:0.75rem;font-weight:600">Outstanding: ${formatCurrency(balanceCents/100)}</span>` : ""}
        ${creditCents > 0 ? `<span style="background:#ecfdf5;color:#065f46;padding:0.2rem 0.6rem;border-radius:999px;font-size:0.75rem;font-weight:600">Credit: ${formatCurrency(creditCents/100)}</span>` : ""}
      </div>
      ${missingHtml ? `<div style="background:#fffbeb;border-radius:8px;padding:0.75rem;margin-bottom:0.75rem"><div style="font-size:0.8rem;font-weight:600;color:#92400e;margin-bottom:0.25rem">Action required:</div><ul style="margin:0;padding-left:1rem">${missingHtml}</ul></div>` : ""}
      ${memberHtml}
      ${billingHtml}
      ${invoicesHtml}
      <div style="margin-top:1.25rem;display:flex;flex-direction:column;gap:0.5rem">
        ${(profile.claim_id || profile.active_claim_id) ? `<a href="claim_detail.html?id=${profile.claim_id || profile.active_claim_id}" class="btn" style="text-align:center;font-size:0.875rem">Open Active Claim</a>` : ""}
        ${(profile.claim_id || profile.active_claim_id) ? `<a href="claim_detail.html?id=${profile.claim_id || profile.active_claim_id}#diagnoses" class="btn secondary" style="text-align:center;font-size:0.875rem">Jump to Diagnoses</a>` : ""}
        ${(profile.claim_id || profile.active_claim_id) ? `<a href="claim_detail.html?id=${profile.claim_id || profile.active_claim_id}#attachments" class="btn secondary" style="text-align:center;font-size:0.875rem">Jump to Attachments</a>` : ""}
      </div>
    `;

    requestAnimationFrame(() => { drawer.style.transform = "translateX(0)"; });
  }

  async function handlePayInvoice(patientId, amountCents, invoiceId) {
    if (!amountCents || amountCents <= 0) {
      toastError("Invalid invoice amount.");
      return;
    }
    try {
      const result = await window.api.recordPatientPayment(patientId, amountCents, "EFT");
      toastSuccess(`Payment of ${formatCurrency(amountCents / 100)} recorded successfully. Invoice ${escapeHtml(invoiceId)} updated.`);
      // Refresh drawer
      await openPatientProfile(patientId);
      // Refresh balance cell in table
      const cell = document.querySelector(`[data-balance-id="${patientId}"]`);
      if (cell) {
        const bal = await window.api.getPatientBalance(patientId);
        const cents = bal.balance_cents || 0;
        cell.textContent = cents > 0 ? formatCurrency(cents / 100) : "R0.00";
        cell.style.color = cents > 0 ? "#b42318" : "";
      }
    } catch (e) {
      toastError(`Payment failed: ${e.message}`);
    }
  }
  window.handlePayInvoice = handlePayInvoice;

  function closePatientProfile() {
    const drawer = document.getElementById("patient-profile-drawer");
    if (drawer) { drawer.style.transform = "translateX(100%)"; }
  }

  // Expose drawer functions on window so inline onclick handlers work
  window.openPatientProfile = openPatientProfile;
  window.closePatientProfile = closePatientProfile;
  window._app = {
    selectProvider(id) {
      state.selectedProviderId = Number(id);
      renderProviderWorkspace();
    },
  };
  // ===== END PATIENT PROFILE DRAWER =====

  // ===== EVIDENCE PACK =====
  function buildEvidencePackMarkup(evidence) {
    const claim = evidence.claim || {};
    const docs = evidence.documents || [];
    const pmbDecisions = evidence.pmb_decisions || [];
    const routeDecisions = evidence.benefit_route_decisions || [];
    const costingPreviews = evidence.costing_previews || [];
    const bundles = evidence.decision_bundles || [];
    const submissions = evidence.submissions || [];
    const transportLogs = evidence.transport_logs || [];
    const remittances = evidence.remittances || [];
    const payloads = evidence.payloads || [];
    const ediArtifacts = evidence.edi_artifacts || [];

    const latestPmb = pmbDecisions[pmbDecisions.length - 1] || {};
    const latestRoute = routeDecisions[routeDecisions.length - 1] || {};
    const latestCosting = costingPreviews[costingPreviews.length - 1] || {};
    const latestPayload = payloads[payloads.length - 1] || {};
    const latestEdi = ediArtifacts[ediArtifacts.length - 1] || {};
    const latestRemittance = remittances[remittances.length - 1] || {};

    const tabs = ["Snapshot", "Decisions", "Documents", "Submission", "Remittance", "Payloads"];

    const tabBar = `<div class="ep-tabs">${tabs.map((t, i) =>
      `<button class="ep-tab${i === 0 ? " active" : ""}" data-ep-tab="${i}" type="button">${escapeHtml(t)}</button>`
    ).join("")}</div>`;

    // Tab 0 — Snapshot
    const lineItems = (claim.line_items || []);
    const diagnoses = (claim.diagnoses || []);
    const snapshotPane = `
      <div class="ep-pane active" data-ep-pane="0">
        <div class="ep-section">
          <h4>Claim</h4>
          <dl class="ep-dl">
            <dt>Claim #</dt><dd>${escapeHtml(claim.claim_number || String(claim.id || "-"))}</dd>
            <dt>Service date</dt><dd>${escapeHtml(claim.service_date || "-")}</dd>
            <dt>Status</dt><dd><span class="chip ${claimStatusClass(claim)}">${escapeHtml(claim.status || "-")}</span></dd>
            <dt>Member</dt><dd>${escapeHtml(claim.member_number || "-")}</dd>
            <dt>Scheme</dt><dd>${escapeHtml(claim.scheme_code || claim.scheme || "-")} · ${escapeHtml(claim.scheme_option || "-")}</dd>
            <dt>Provider</dt><dd>${escapeHtml(claim.provider_name || String(claim.provider_id || "-"))}</dd>
          </dl>
        </div>
        ${lineItems.length ? `
          <div class="ep-section">
            <h4>Line items</h4>
            <table class="table">
              <thead><tr><th>Code</th><th>Description</th><th>Amount</th></tr></thead>
              <tbody>${lineItems.map(l => `
                <tr>
                  <td class="code">${escapeHtml(l.service_code || l.line_id || "-")}</td>
                  <td>${escapeHtml(l.description || "-")}</td>
                  <td>${formatCurrency(l.amount_cents != null ? l.amount_cents / 100 : l.amount_rand || 0)}</td>
                </tr>`).join("")}
              </tbody>
            </table>
          </div>` : ""}
        ${diagnoses.length ? `
          <div class="ep-section">
            <h4>Diagnoses</h4>
            <table class="table">
              <thead><tr><th>ICD-10</th><th>Description</th><th>Type</th></tr></thead>
              <tbody>${diagnoses.map(d => `
                <tr>
                  <td class="code">${escapeHtml(d.icd10_code || d.code || "-")}</td>
                  <td>${escapeHtml(d.description || "-")}</td>
                  <td><span class="chip ${d.diagnosis_type === "PRIMARY" ? "pass" : "info"}">${escapeHtml(d.diagnosis_type || "-")}</span></td>
                </tr>`).join("")}
              </tbody>
            </table>
          </div>` : ""}
      </div>`;

    // Tab 1 — Decisions
    const decisionsPane = `
      <div class="ep-pane" data-ep-pane="1">
        <div class="ep-section">
          <h4>PMB decision</h4>
          <dl class="ep-dl">
            <dt>Status</dt><dd><span class="chip ${latestPmb.pmb_status === "CONFIRMED" ? "pass" : latestPmb.pmb_status === "NOT_DETECTED" ? "warn" : "info"}">${escapeHtml(latestPmb.pmb_status || "NOT_EVALUATED")}</span></dd>
            <dt>Condition</dt><dd>${escapeHtml(latestPmb.pmb_condition_id || latestPmb.condition_name || "-")}</dd>
            <dt>Reason</dt><dd>${escapeHtml(latestPmb.reason || latestPmb.decision_reason || "-")}</dd>
          </dl>
        </div>
        <div class="ep-section">
          <h4>Benefit routing</h4>
          <dl class="ep-dl">
            <dt>Decision</dt><dd>${escapeHtml(latestRoute.routing_decision || "-")}</dd>
            <dt>Coverage %</dt><dd>${escapeHtml(String(latestRoute.coverage_percentage != null ? latestRoute.coverage_percentage + "%" : "-"))}</dd>
            <dt>Co-payment</dt><dd>${latestRoute.copay_amount_cents != null ? formatCurrency(latestRoute.copay_amount_cents / 100) : escapeHtml(latestRoute.copay_amount || "-")}</dd>
          </dl>
        </div>
        ${latestCosting.total_cents != null || latestCosting.total_rand != null ? `
          <div class="ep-section">
            <h4>Costing preview</h4>
            <dl class="ep-dl">
              <dt>Total</dt><dd>${formatCurrency(latestCosting.total_cents != null ? latestCosting.total_cents / 100 : latestCosting.total_rand || 0)}</dd>
              <dt>Scheme portion</dt><dd>${formatCurrency(latestCosting.scheme_portion_cents != null ? latestCosting.scheme_portion_cents / 100 : latestCosting.scheme_portion || 0)}</dd>
              <dt>Member portion</dt><dd>${formatCurrency(latestCosting.member_portion_cents != null ? latestCosting.member_portion_cents / 100 : latestCosting.member_portion || 0)}</dd>
            </dl>
          </div>` : ""}
        ${bundles.length ? `
          <div class="ep-section">
            <h4>Decision bundles (${bundles.length})</h4>
            <ul style="margin:0;padding-left:1rem;font-size:12px;display:flex;flex-direction:column;gap:3px;">
              ${bundles.slice(0, 8).map(b => `<li>${escapeHtml(b.bundle_id || b.bundle_type || JSON.stringify(b).slice(0, 60))}</li>`).join("")}
              ${bundles.length > 8 ? `<li style="color:var(--ink-500)">…and ${bundles.length - 8} more</li>` : ""}
            </ul>
          </div>` : ""}
      </div>`;

    // Tab 2 — Documents
    const docsPane = `
      <div class="ep-pane" data-ep-pane="2">
        ${docs.length ? `
          <div class="ep-section">
            <h4>Claim documents (${docs.length})</h4>
            <table class="table">
              <thead><tr><th>Type</th><th>Filename</th><th>Status</th><th>Uploaded</th></tr></thead>
              <tbody>${docs.map(d => `
                <tr>
                  <td><span class="chip info">${escapeHtml(d.doc_type || "-")}</span></td>
                  <td class="code">${escapeHtml(d.filename || "-")}</td>
                  <td>${escapeHtml(d.status || "-")}</td>
                  <td>${escapeHtml(formatDateTime(d.uploaded_at || "-"))}</td>
                </tr>`).join("")}
              </tbody>
            </table>
          </div>` : `<div class="ep-section"><p class="muted">No documents attached to this claim.</p></div>`}
      </div>`;

    // Tab 3 — Submission
    const submissionPane = `
      <div class="ep-pane" data-ep-pane="3">
        ${submissions.length ? `
          <div class="ep-section">
            <h4>Submission history (${submissions.length})</h4>
            <table class="table">
              <thead><tr><th>Channel</th><th>Status</th><th>Idempotency key</th><th>Submitted</th></tr></thead>
              <tbody>${submissions.map(s => `
                <tr>
                  <td>${escapeHtml(s.submission_channel || s.channel || "-")}</td>
                  <td><span class="chip ${s.submission_status === "ACCEPTED" || s.submission_status === "SUCCESS" ? "pass" : "info"}">${escapeHtml(s.submission_status || s.status || "-")}</span></td>
                  <td class="code">${escapeHtml(s.idempotency_key || "-")}</td>
                  <td>${escapeHtml(formatDateTime(s.submitted_at || s.created_at || "-"))}</td>
                </tr>`).join("")}
              </tbody>
            </table>
          </div>` : `<div class="ep-section"><p class="muted">No submissions recorded.</p></div>`}
        ${transportLogs.length ? `
          <div class="ep-section">
            <h4>Transport log</h4>
            <div style="font-size:11px;font-family:var(--mono);background:#0b1220;color:#eaf2ff;border-radius:8px;padding:10px;overflow:auto;max-height:180px;">
              ${transportLogs.map(l => escapeHtml(`[${l.timestamp || ""}] ${l.direction || ""} ${l.endpoint || l.event || ""} ${l.status_code ? "→ " + l.status_code : ""}`)).join("<br>")}
            </div>
          </div>` : ""}
      </div>`;

    // Tab 4 — Remittance
    const remittancePane = `
      <div class="ep-pane" data-ep-pane="4">
        ${latestRemittance.remittance_id || latestRemittance.id ? `
          <div class="ep-section">
            <h4>Remittance summary</h4>
            <dl class="ep-dl">
              <dt>Remittance ID</dt><dd class="code">${escapeHtml(latestRemittance.remittance_id || latestRemittance.id || "-")}</dd>
              <dt>Approved</dt><dd>${formatCurrency((latestRemittance.totals?.approved || latestRemittance.approved_amount_cents || 0) / 100)}</dd>
              <dt>Paid</dt><dd>${formatCurrency((latestRemittance.totals?.paid || latestRemittance.paid_amount_cents || 0) / 100)}</dd>
              <dt>Status</dt><dd>${escapeHtml(latestRemittance.status || "-")}</dd>
            </dl>
          </div>` : `<div class="ep-section"><p class="muted">No remittance recorded for this claim.</p></div>`}
      </div>`;

    // Tab 5 — Payloads
    const canonicalJson = latestPayload.canonical_claim ? JSON.stringify(latestPayload.canonical_claim, null, 2) : null;
    const ediContent = latestEdi.content || latestPayload.pseudo_edi || null;
    const payloadsPane = `
      <div class="ep-pane" data-ep-pane="5">
        ${canonicalJson ? `
          <div class="ep-section">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <h4 style="margin:0">Canonical payload</h4>
              <button class="chip info" type="button" onclick="navigator.clipboard.writeText(this.closest('.ep-section').querySelector('pre').textContent)">Copy</button>
            </div>
            <pre style="max-height:220px;overflow:auto;font-size:11px;">${escapeHtml(canonicalJson)}</pre>
          </div>` : ""}
        ${ediContent ? `
          <div class="ep-section">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <h4 style="margin:0">EDI format</h4>
              <button class="chip info" type="button" onclick="navigator.clipboard.writeText(this.closest('.ep-section').querySelector('pre').textContent)">Copy</button>
            </div>
            <pre style="max-height:180px;overflow:auto;font-size:11px;">${escapeHtml(ediContent)}</pre>
          </div>` : ""}
        ${!canonicalJson && !ediContent ? `<div class="ep-section"><p class="muted">No payload generated yet. Run Build Payload to generate.</p></div>` : ""}
      </div>`;

    const markup = `
      ${tabBar}
      ${snapshotPane}
      ${decisionsPane}
      ${docsPane}
      ${submissionPane}
      ${remittancePane}
      ${payloadsPane}
    `;

    // Wire up tab switching after a tick (content injected into DOM by showDrawer)
    setTimeout(() => {
      document.querySelectorAll(".ep-tab").forEach((tab) => {
        tab.addEventListener("click", () => {
          const idx = tab.getAttribute("data-ep-tab");
          document.querySelectorAll(".ep-tab").forEach((t) => t.classList.remove("active"));
          document.querySelectorAll(".ep-pane").forEach((p) => p.classList.remove("active"));
          tab.classList.add("active");
          const pane = document.querySelector(`.ep-pane[data-ep-pane="${idx}"]`);
          if (pane) pane.classList.add("active");
        });
      });
    }, 0);

    return markup;
  }
  // ===== END EVIDENCE PACK =====

  // ===== AUDIT TRAIL =====
  function _auditBadgeClass(action) {
    if (!action) return "system";
    const a = action.toUpperCase();
    if (a.includes("CREAT") || a.includes("ADD")) return "create";
    if (a.includes("DELET") || a.includes("REMOV") || a.includes("VOID")) return "delete";
    if (a.includes("SUBMIT")) return "submit";
    if (a.includes("VALID") || a.includes("READINESS") || a.includes("CLOSURE")) return "validate";
    if (a.includes("UPDAT") || a.includes("EDIT") || a.includes("PATCH") || a.includes("ACTIV")) return "update";
    return "system";
  }

  function renderAuditTrail() {
    const tbody = document.querySelector(".table tbody");
    if (!tbody) return;
    const logs = state.auditLogs || [];
    if (!logs.length) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#999;">No audit events found.</td></tr>';
      return;
    }

    // Inject filter bar above the table if not already present
    const tableCard = tbody.closest(".card");
    if (tableCard && !tableCard.querySelector(".audit-filter-bar")) {
      const filterBar = document.createElement("div");
      filterBar.className = "audit-filter-bar";
      const actionTypes = [...new Set(logs.map((l) => l.action).filter(Boolean))].sort();
      filterBar.innerHTML = `
        <span style="font-size:12px;color:var(--ink-500)">Filter:</span>
        <select id="audit-filter-action">
          <option value="">All actions</option>
          ${actionTypes.map((a) => `<option value="${escapeHtml(a)}">${escapeHtml(a)}</option>`).join("")}
        </select>
        <select id="audit-filter-resource">
          <option value="">All resources</option>
          ${[...new Set(logs.map((l) => (l.resource || "").split(":")[0]).filter(Boolean))].sort()
            .map((r) => `<option value="${escapeHtml(r)}">${escapeHtml(r)}</option>`).join("")}
        </select>
      `;
      tableCard.insertBefore(filterBar, tableCard.querySelector("table"));
      filterBar.querySelector("#audit-filter-action").addEventListener("change", renderAuditTrail);
      filterBar.querySelector("#audit-filter-resource").addEventListener("change", renderAuditTrail);
    }

    const actionFilter = document.getElementById("audit-filter-action")?.value || "";
    const resourceFilter = document.getElementById("audit-filter-resource")?.value || "";

    const filtered = logs.filter((l) => {
      if (actionFilter && l.action !== actionFilter) return false;
      if (resourceFilter && !(l.resource || "").startsWith(resourceFilter)) return false;
      return true;
    });

    tbody.innerHTML = filtered.length
      ? filtered.map((log) => `
          <tr>
            <td><span class="audit-badge ${_auditBadgeClass(log.action)}">${escapeHtml(log.action || "-")}</span></td>
            <td class="code">${escapeHtml(log.resource || "-")}</td>
            <td>${escapeHtml(log.username || log.user_id || "-")}</td>
            <td>${escapeHtml(formatDateTime(log.timestamp || "-"))}</td>
            <td class="row-actions">
              <button class="chip info" data-action="view-audit-detail" data-id="${escapeHtml(log.id || "")}">Details</button>
            </td>
          </tr>`).join("")
      : '<tr><td colspan="5" style="text-align:center;color:#999;">No events match the current filter.</td></tr>';
  }

  async function handleViewAuditDetail(auditEventId) {
    if (!auditEventId) {
      toastError("No audit event ID provided.");
      return;
    }
    const event = await window.api.getAuditEvent(auditEventId);
    const detail = event.detail || {};
    const detailJson = JSON.stringify(detail, null, 2);

    showDrawer({
      title: `Audit event · ${escapeHtml(event.event_type || auditEventId)}`,
      subtitle: `${escapeHtml(event.entity_type || "-")} · ${escapeHtml(event.entity_id || "-")} · ${escapeHtml(formatDateTime(event.timestamp || "-"))}`,
      content: `
        <div class="drawer-grid">
          <div class="mini-card">
            <strong>Actor</strong>
            ${escapeHtml(event.actor || "-")}
            <div class="muted">${escapeHtml(event.role || "-")}</div>
          </div>
          <div class="mini-card">
            <strong>Policy</strong>
            ${escapeHtml(event.policy_profile_id || "-")}
            <div class="muted">v${escapeHtml(String(event.policy_version || "-"))}</div>
          </div>
        </div>
        ${Object.keys(event.hashes || {}).length ? `
          <div class="mini-card" style="margin-top:2px;">
            <strong>Snapshot hashes</strong>
            ${Object.entries(event.hashes).map(([k, v]) =>
              `<div class="muted" style="font-family:var(--mono);font-size:11px;margin-top:3px;">${escapeHtml(k)}: ${escapeHtml(String(v).slice(0, 20))}…</div>`
            ).join("")}
          </div>` : ""}
        <div class="mini-card" style="margin-top:2px;">
          <strong>Detail</strong>
          <pre style="margin-top:6px;max-height:300px;overflow:auto;font-size:11px;">${escapeHtml(detailJson)}</pre>
        </div>
      `,
    });
  }
  // ===== END AUDIT TRAIL =====
})();
