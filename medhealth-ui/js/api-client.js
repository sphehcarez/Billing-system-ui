/**
 * API Client for Med Directory Billing System
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = "http://localhost:8001/api";

class BillingAPI {
  constructor() {
    this.token = localStorage.getItem("api_token") || null;
    this.role = localStorage.getItem("api_role") || localStorage.getItem("role") || null;
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
      this.role = data.role;
      localStorage.setItem("api_token", this.token);
      localStorage.setItem("api_role", this.role);
      localStorage.setItem("role", this.role);
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
    localStorage.removeItem("api_token");
    localStorage.removeItem("api_role");
    localStorage.removeItem("role");
  }

  isAuthenticated() {
    return Boolean(this.token);
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
      const response = await fetch(`${API_BASE_URL}${endpoint}`, options);

      if (response.status === 401) {
        this.logout();
        throw new Error("Unauthorized - please login again");
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "API request failed");
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

  async getClaimEvidence(claimId) {
    return this._request(`/claims/${claimId}/evidence`, "GET");
  }
}

// Create global API instance
window.api = new BillingAPI();
