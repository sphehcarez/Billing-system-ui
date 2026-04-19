/**
 * API Client for Med Directory Billing System
 * Handles all communication with the FastAPI backend
 */

function resolveApiBaseUrl() {
  const explicitMeta = document.querySelector('meta[name="medhealth-api-base"]')?.content?.trim();
  const storedOverride = localStorage.getItem("medhealth_api_base_url")?.trim();
  const candidate = explicitMeta || storedOverride;
  if (candidate) {
    return new URL(candidate, window.location.origin).toString().replace(/\/$/, "");
  }
  if (window.location.port === "8001") {
    return new URL("/api", window.location.origin).toString().replace(/\/$/, "");
  }
  if (window.location.protocol.startsWith("http") && window.location.hostname) {
    return `${window.location.protocol}//${window.location.hostname}:8001/api`;
  }
  return "http://localhost:8001/api";
}

const API_BASE_URL = resolveApiBaseUrl();
const API_ORIGIN = API_BASE_URL.replace(/\/api$/, "");

class BillingAPI {
  constructor() {
    this.token = localStorage.getItem("api_token") || null;
    this.role = localStorage.getItem("api_role") || localStorage.getItem("role") || null;
    this.tenantId = localStorage.getItem("api_tenant_id") || null;
    this.practiceId = localStorage.getItem("api_practice_id") || null;
    this.baseUrl = API_BASE_URL;
    this.origin = API_ORIGIN;
  }

  // =========================================================================
  // AUTHENTICATION
  // =========================================================================

  async login(username, password, role) {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, role }),
      });

      if (!response.ok) {
        throw new Error("Login failed");
      }

      const data = await response.json();
      this.token = data.access_token;
      // Normalize role aliases so they match ROLE_PERMISSIONS keys in app.js
      const roleAliases = {
        admin: "Administrator", administrator: "Administrator",
        "front office": "Front Office", frontdesk: "Front Office",
        billingcore: "Billing", "billing core": "Billing",
        clinical: "Clinical", clinicalcore: "Clinical",
        financecore: "Finance", auditcore: "Audit", audit: "Audit",
        manager: "Practice Manager", "practice manager": "Practice Manager",
        bureau: "Bureau Manager", "bureau manager": "Bureau Manager",
        reception: "Reception / Patient Access", receptionist: "Reception / Patient Access",
        "patient access": "Reception / Patient Access", "reception / patient access": "Reception / Patient Access",
        billing: "Billing Specialist", "billing specialist": "Billing Specialist",
        coder: "Clinical Coder", "clinical coder": "Clinical Coder",
        authz: "Authorisations Coordinator", authorisations: "Authorisations Coordinator", "authorisations coordinator": "Authorisations Coordinator",
        provider: "Healthcare Provider", "healthcare provider": "Healthcare Provider",
        finance: "Finance Officer", "finance officer": "Finance Officer",
        recon: "Reconciliation Specialist", reconciliation: "Reconciliation Specialist", "reconciliation specialist": "Reconciliation Specialist",
        debtor: "Credit Controller", debtors: "Credit Controller", "credit controller": "Credit Controller",
        auditor: "Compliance Auditor", "compliance auditor": "Compliance Auditor",
      };
      const rawRole = data.role || "";
      this.role = roleAliases[rawRole.toLowerCase().trim()] || rawRole;
      this.tenantId = data.tenant_id || null;
      this.practiceId = data.practice_id || null;
      localStorage.setItem("api_token", this.token);
      localStorage.setItem("api_role", this.role);
      localStorage.setItem("role", this.role);
      if (this.tenantId) localStorage.setItem("api_tenant_id", this.tenantId);
      if (this.practiceId) localStorage.setItem("api_practice_id", this.practiceId);
      return data;
    } catch (error) {
      console.error("Login error:", error);
      throw error;
    }
  }

  // =========================================================================
  // HELPER METHODS
  // =========================================================================

  logout() {
    this.token = null;
    this.role = null;
    this.tenantId = null;
    this.practiceId = null;
    localStorage.removeItem("api_token");
    localStorage.removeItem("api_role");
    localStorage.removeItem("role");
    localStorage.removeItem("api_tenant_id");
    localStorage.removeItem("api_practice_id");
  }

  isAuthenticated() {
    return Boolean(this.token);
  }

  getDocsUrl() {
    return `${this.origin}/docs`;
  }

  getHealthUrl() {
    return `${this.origin}/health`;
  }

  async _request(endpoint, method = "GET", body = null) {
    const headers = {};

    if (this.token) {
      headers.Authorization = `Bearer ${this.token}`;
    }

    const options = {
      method,
      headers,
    };

    if (body !== null) {
      headers["Content-Type"] = "application/json";
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, options);

      if (response.status === 401) {
        this.logout();
        const unauthorizedError = new Error("Unauthorized - please login again");
        unauthorizedError.status = 401;
        unauthorizedError.endpoint = endpoint;
        unauthorizedError.method = method;
        throw unauthorizedError;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const apiError = new Error(errorData.detail || `API request failed with ${response.status}`);
        apiError.status = response.status;
        apiError.endpoint = endpoint;
        apiError.method = method;
        throw apiError;
      }

      if (response.status === 204) {
        return null;
      }

      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        return response.json();
      }

      return response.text();
    } catch (error) {
      if (error instanceof TypeError) {
        const networkError = new Error(
          `API unavailable while calling ${method} ${endpoint}. Check the backend on ${this.origin}.`,
        );
        networkError.code = "NETWORK_ERROR";
        networkError.endpoint = endpoint;
        networkError.method = method;
        networkError.apiBaseUrl = this.baseUrl;
        throw networkError;
      }
      console.error(`API Error [${method} ${endpoint}]:`, error);
      throw error;
    }
  }

  // =========================================================================
  // PATIENTS
  // =========================================================================

  async getPatients() {
    return this._request("/patients", "GET");
  }

  async getPatient(id) {
    return this._request(`/patients/${id}`, "GET");
  }

  async getPatientClaimContext(id) {
    return this._request(`/patients/${id}/claim-context`, "GET");
  }

  async getPatientTimeline(id) {
    return this._request(`/patients/${id}/timeline`, "GET");
  }

  async getHealth() {
    const response = await fetch(this.getHealthUrl(), { method: "GET" });
    if (!response.ok) {
      throw new Error(`Health check failed with ${response.status}`);
    }
    return response.json();
  }

  async createPatient(patient) {
    return this._request("/patients", "POST", patient);
  }

  async updatePatient(id, patient) {
    return this._request(`/patients/${id}`, "PUT", patient);
  }

  async deletePatient(id) {
    return this._request(`/patients/${id}`, "DELETE");
  }

  // =========================================================================
  // PROVIDERS
  // =========================================================================

  async getProviders() {
    return this._request("/providers", "GET");
  }

  async getProvider(id) {
    return this._request(`/providers/${id}`, "GET");
  }

  async createProvider(provider) {
    return this._request("/providers", "POST", provider);
  }

  async updateProvider(id, provider) {
    return this._request(`/providers/${id}`, "PUT", provider);
  }

  async deleteProvider(id) {
    return this._request(`/providers/${id}`, "DELETE");
  }

  async getTenants() {
    return this._request("/tenants", "GET");
  }

  async getPractices(tenantId = null) {
    const suffix = tenantId ? `?tenant_id=${encodeURIComponent(tenantId)}` : "";
    return this._request(`/practices${suffix}`, "GET");
  }

  // =========================================================================
  // CLAIMS
  // =========================================================================

  async getClaims() {
    return this._request("/claims", "GET");
  }

  async getClaimWorklist() {
    return this._request("/claims/worklist", "GET");
  }

  async getClaim(id) {
    return this._request(`/claims/${id}`, "GET");
  }

  async createClaim(claim) {
    return this._request("/claims", "POST", claim);
  }

  async updateClaim(id, claim) {
    return this._request(`/claims/${id}`, "PUT", claim);
  }

  async getClaimDiagnoses(claimId) {
    return this._request(`/claims/${claimId}/diagnoses`, "GET");
  }

  async getClaimLineItems(claimId) {
    return this._request(`/claims/${claimId}/line-items`, "GET");
  }

  async getClaimAttachments(claimId) {
    return this._request(`/claims/${claimId}/attachments`, "GET");
  }

  async addClaimAttachment(claimId, payload) {
    return this._request(`/claims/${claimId}/attachments`, "POST", payload);
  }

  async deleteClaimAttachment(claimId, documentId) {
    return this._request(`/claims/${claimId}/attachments/${encodeURIComponent(documentId)}`, "DELETE");
  }

  async updateClaimLineDiagnosisLinks(claimId, lineId, diagnosisIds) {
    return this._request(
      `/claims/${claimId}/line-items/${encodeURIComponent(lineId)}/diagnosis-links`,
      "PUT",
      { diagnosis_ids: diagnosisIds },
    );
  }

  async autoLinkClaimLineDiagnosisLinks(claimId) {
    return this._request(`/claims/${claimId}/line-items/diagnosis-links/auto-link`, "POST");
  }

  async addClaimDiagnosis(claimId, diagnosis) {
    return this._request(`/claims/${claimId}/diagnoses`, "POST", diagnosis);
  }

  async makePrimaryDiagnosis(claimId, diagnosisId) {
    return this._request(`/claims/${claimId}/diagnoses/${encodeURIComponent(diagnosisId)}/make-primary`, "PUT");
  }

  async autoFixPrimaryDiagnosis(claimId) {
    return this._request(`/claims/${claimId}/diagnoses/auto-fix-primary`, "POST");
  }

  async runReadinessCheck(claimId) {
    return this._request(`/claims/${claimId}/readiness`, "POST");
  }

  async closeClaim(claimId) {
    return this._request(`/claims/${claimId}/close`, "POST");
  }

  async postClosureValidate(claimId) {
    return this._request(`/claims/${claimId}/validate`, "POST");
  }

  async buildClaimPayload(claimId) {
    return this._request(`/claims/${claimId}/payload`, "POST");
  }

  async getStructuredClaimPayload(claimId, version) {
    return this._request(`/claims/${claimId}/payloads/${version}/structured`, "GET");
  }

  async generateClaimEdi(claimId, version) {
    return this._request(`/claims/${claimId}/payloads/${version}/edi/generate`, "POST");
  }

  async validateClaimEdi(claimId, version) {
    return this._request(`/claims/${claimId}/payloads/${version}/edi/validate`, "POST");
  }

  async downloadClaimEdi(claimId, version) {
    return this._request(`/claims/${claimId}/payloads/${version}/edi/download`, "GET");
  }

  async submitClaimEdi(claimId, version, channel = "SWITCH", idempotencyKey = null) {
    const params = new URLSearchParams({ channel });
    if (idempotencyKey) {
      params.set("idempotency_key", idempotencyKey);
    }
    return this._request(`/claims/${claimId}/payloads/${version}/edi/submit?${params.toString()}`, "POST");
  }

  async getClaimTransportLogs(claimId) {
    return this._request(`/claims/${claimId}/transport-logs`, "GET");
  }

  // =========================================================================
  // PAYMENTS
  // =========================================================================

  async getPayments() {
    return this._request("/payments", "GET");
  }

  async getPayment(id) {
    return this._request(`/payments/${id}`, "GET");
  }

  async createPayment(payment) {
    return this._request("/payments", "POST", payment);
  }

  async updatePayment(id, payment) {
    return this._request(`/payments/${id}`, "PUT", payment);
  }

  // =========================================================================
  // USERS
  // =========================================================================

  async getUsers() {
    return this._request("/users", "GET");
  }

  async getUser(id) {
    return this._request(`/users/${id}`, "GET");
  }

  async createUser(user) {
    return this._request("/users", "POST", user);
  }

  async updateUser(id, user) {
    return this._request(`/users/${id}`, "PUT", user);
  }

  async deleteUser(id) {
    return this._request(`/users/${id}`, "DELETE");
  }

  // =========================================================================
  // REPORTS
  // =========================================================================

  async getReports() {
    return this._request("/reports", "GET");
  }

  async generateReport(reportType, period) {
    return this._request("/reports/generate", "POST", { report_type: reportType, period });
  }

  async getReport(id) {
    return this._request(`/reports/${id}`, "GET");
  }

  // =========================================================================
  // AUDIT
  // =========================================================================

  async getAuditLogs() {
    return this._request("/audit-logs", "GET");
  }

  async getAuditEvent(auditEventId) {
    return this._request(`/audit/${encodeURIComponent(auditEventId)}`, "GET");
  }

  // =========================================================================
  // PATIENT BALANCES, INVOICES & PAYMENTS
  // =========================================================================

  async getPatientBalance(patientId) {
    return this._request(`/patients/${patientId}/balances`, "GET");
  }

  async getPatientInvoices(patientId) {
    return this._request(`/patients/${patientId}/invoices`, "GET");
  }

  async getPatientPayments(patientId) {
    return this._request(`/patients/${patientId}/payments`, "GET");
  }

  async recordPatientPayment(patientId, amountCents, method = "EFT") {
    const key = `pay-${patientId}-${amountCents}-${Date.now()}`;
    return this._requestWithHeaders(
      `/patients/${patientId}/payments`,
      "POST",
      { amount_cents: amountCents, method },
      { "Idempotency-Key": key },
    );
  }

  async getPatientStatement(patientId) {
    return this._request(`/patients/${patientId}/statement`, "GET");
  }

  async _requestWithHeaders(endpoint, method, body, extraHeaders) {
    const headers = {};
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    if (body !== null) headers["Content-Type"] = "application/json";
    Object.assign(headers, extraHeaders);
    const options = { method, headers };
    if (body !== null) options.body = JSON.stringify(body);
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, options);
      if (response.status === 401) { this.logout(); throw Object.assign(new Error("Unauthorized"), { status: 401 }); }
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw Object.assign(new Error(err.detail || `HTTP ${response.status}`), { status: response.status });
      }
      if (response.status === 204) return null;
      return response.json();
    } catch (error) {
      if (error instanceof TypeError) {
        throw Object.assign(new Error("API unavailable"), { code: "NETWORK_ERROR" });
      }
      throw error;
    }
  }

  // =========================================================================
  // SETTINGS
  // =========================================================================

  async getSettings() {
    return this._request("/settings", "GET");
  }

  async updateSettings(settings) {
    return this._request("/settings", "PUT", settings);
  }

  // =========================================================================
  // DOCS
  // =========================================================================

  async getApiDocs() {
    return this._request("/docs", "GET");
  }

  async getDashboardSummary() {
    return this._request("/dashboard/summary", "GET");
  }

  async getPolicyProfiles() {
    return this._request("/policy-profiles", "GET");
  }

  async createPolicyVersion(policyProfileId) {
    return this._request(`/policy-profiles/${encodeURIComponent(policyProfileId)}/versions`, "POST");
  }

  async updatePolicyProfile(policyProfileId, version, patch) {
    return this._request(
      `/policy-profiles/${encodeURIComponent(policyProfileId)}/versions/${version}`,
      "PATCH",
      patch,
    );
  }

  async activatePolicyProfile(policyProfileId, version) {
    return this._request(
      `/policy-profiles/${encodeURIComponent(policyProfileId)}/versions/${version}/activate`,
      "POST",
    );
  }

  async getRules() {
    return this._request("/rules", "GET");
  }

  async getIcd10Reference() {
    return this._request("/reference/icd10", "GET");
  }

  async getPmbMappingReference() {
    return this._request("/reference/pmb-mappings", "GET");
  }

  async simulatePmbMapping(icd10Code) {
    return this._request(`/reference/pmb-mappings/simulate?icd10_code=${encodeURIComponent(icd10Code)}`, "GET");
  }

  async createPmbMapping(payload) {
    return this._request("/reference/pmb-mappings", "POST", payload);
  }

  async updatePmbMapping(mappingId, payload) {
    return this._request(`/reference/pmb-mappings/${encodeURIComponent(mappingId)}`, "PATCH", payload);
  }

  async deletePmbMapping(mappingId) {
    return this._request(`/reference/pmb-mappings/${encodeURIComponent(mappingId)}`, "DELETE");
  }

  async updateRule(ruleId, patch) {
    return this._request(`/rules/${encodeURIComponent(ruleId)}`, "PATCH", patch);
  }

  // =========================================================================
  // CLAIM WORKFLOWS
  // =========================================================================

  async submitClaim(claimId, channel, idempotencyKey = null) {
    const payload = { channel };
    if (idempotencyKey) {
      payload.idempotency_key = idempotencyKey;
    }
    return this._request(`/claims/${claimId}/submit`, "POST", payload);
  }

  async getClaimRemittance(claimId) {
    return this._request(`/claims/${claimId}/remittance`, "GET");
  }

  async getReconciliationExceptions() {
    return this._request("/payments/reconciliation-exceptions", "GET");
  }

  async resolveReconciliationException(claimId, resolution, note = "", writeOffCents = 0) {
    return this._request(`/payments/claims/${claimId}/reconciliation/resolve`, "POST", {
      resolution,
      note,
      write_off_cents: writeOffCents,
    });
  }

  async getSwitchIntegrationProfile() {
    return this._request("/integrations/switch", "GET");
  }

  async getClaimEvidence(claimId) {
    return this._request(`/claims/${claimId}/evidence`, "GET");
  }
}

// Create global API instance
window.api = new BillingAPI();
