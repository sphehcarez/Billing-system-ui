# UI Redesign Checklist: Before/After Components

Date created: `2026-04-17`

## Component 1: Evidence Pack Modal

### Current State (BEFORE)

```html
<!-- Evidence packet displays as:
1. Full JSON dump in <pre> element
2. Alert-based layout with insufficient context
3. No structured sections
4. Difficult to scan for specific information
-->

<div class="evidence-packet-container">
  <pre id="evidence-json">{...full claim JSON...}</pre>
  <button onclick="downloadJSON()">Download</button>
</div>
```

**Problems:**
- ❌ Not scannable - requires reading full JSON
- ❌ No visual hierarchy
- ❌ Missing context panels (decision bundles, payloads)
- ❌ No section navigation
- ❌ No costing visibility

### New Design (AFTER)

```html
<div class="evidence-pack-drawer">
  <!-- Header with close/download -->
  <div class="drawer-header">
    <h2>Evidence Pack · Claim #13</h2>
    <div class="header-actions">
      <button class="btn-secondary" onclick="downloadPackZip()">📦 Download Pack</button>
      <button class="btn-secondary" onclick="downloadJSON()">📄 Download JSON</button>
      <button class="btn-icon" onclick="closeEvidenceDrawer()">✕</button>
    </div>
  </div>

  <!-- Navigation tabs -->
  <div class="tab-bar">
    <button class="tab active" data-tab="snapshot">Snapshot</button>
    <button class="tab" data-tab="decisions">Decisions</button>
    <button class="tab" data-tab="attachments">Attachments</button>
    <button class="tab" data-tab="submission">Submission</button>
    <button class="tab" data-tab="remittance">Remittance</button>
    <button class="tab" data-tab="payloads">Payloads</button>
  </div>

  <!-- Tab contents -->
  <div class="tab-content">
    <!-- Snapshot Tab -->
    <div id="tab-snapshot" class="tab-pane active">
      <div class="card">
        <h3>Claim Snapshot</h3>
        <dl>
          <dt>Claim Number:</dt><dd>CLM-2026-0001</dd>
          <dt>Service Date:</dt><dd>2026-04-15</dd>
          <dt>Member:</dt><dd>John Doe (MEM900001)</dd>
          <dt>Scheme:</dt><dd>Discovery Health · option02</dd>
          <dt>Provider:</dt><dd>Dr. Thabo Mthembu (NPI-ZA-001)</dd>
          <dt>Status:</dt><dd>
            <span class="badge badge-ready">Ready to Submit</span>
          </dd>
        </dl>
      </div>

      <div class="card">
        <h3>Line Items</h3>
        <table class="table-compact">
          <thead>
            <tr><th>Service</th><th>Amount</th><th>Status</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>CONS001 - Consultation</td>
              <td>R 450.00</td>
              <td><span class="badge badge-linked">Linked</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card">
        <h3>Diagnoses</h3>
        <table class="table-compact">
          <thead>
            <tr><th>ICD-10</th><th>Description</th><th>Type</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>I10</td>
              <td>Essential hypertension</td>
              <td><span class="badge badge-primary">PRIMARY</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Decisions Tab -->
    <div id="tab-decisions" class="tab-pane">
      <div class="card">
        <h3>PMB Decision</h3>
        <dl>
          <dt>PMB Status:</dt><dd>CONFIRMED</dd>
          <dt>Decision Reason:</dt><dd>Hypertension (I10) is on PMB list</dd>
          <dt>Condition Name:</dt><dd>Essential hypertension</dd>
          <dt>Auto-flagged:</dt><dd>No</dd>
          <dt>Evidence Present:</dt><dd>
            <span class="badge badge-success">MOTIVATION</span>
          </dd>
        </dl>
      </div>

      <div class="card">
        <h3>Benefit Routing</h3>
        <dl>
          <dt>Routing Decision:</dt><dd>COVERED</dd>
          <dt>Coverage Percentage:</dt><dd>100%</dd>
          <dt>Co-payment:</dt><dd>R 50.00 (member responsibility)</dd>
        </dl>
      </div>

      <div class="card">
        <h3>Decision Bundles</h3>
        <ul class="bundle-list">
          <li>PMB_DTP_001: Hypertension management</li>
          <li>BENEFIT_ROUTING_001: Standard coverage</li>
          <li>COSTING_PREVIEW_001: Estimated cost R 400.00</li>
        </ul>
      </div>
    </div>

    <!-- Attachments Tab -->
    <div id="tab-attachments" class="tab-pane">
      <div class="card">
        <h3>Claim Documents</h3>
        <ul class="document-list">
          <li>
            <span class="doc-type">MOTIVATION</span>
            <span class="doc-name">motivation.pdf</span>
            <span class="doc-size">245 KB</span>
            <button class="btn-icon" title="Download">⬇</button>
          </li>
        </ul>
      </div>
      <button class="btn-primary" onclick="openAttachmentUpload()">
        + Add Document
      </button>
    </div>

    <!-- Submission Tab -->
    <div id="tab-submission" class="tab-pane">
      <div class="card">
        <h3>Submission History</h3>
        <timeline>
          <event status="success">
            <span class="time">2026-04-17 14:32 UTC</span>
            <span class="action">Submitted to scheme</span>
            <span class="idempotency">key: cdc5e321</span>
          </event>
          <event status="pending">
            <span class="time">2026-04-17 14:32 UTC</span>
            <span class="action">Awaiting response</span>
          </event>
        </timeline>
      </div>

      <div class="card">
        <h3>Transport Log</h3>
        <pre class="log-viewer">[2026-04-17 14:32:01] HTTP POST /claims/submit → 202 Accepted
[2026-04-17 14:32:02] Connection established
[2026-04-17 14:32:03] Waiting for response...
</pre>
      </div>
    </div>

    <!-- Remittance Tab -->
    <div id="tab-remittance" class="tab-pane">
      <div class="card">
        <h3>Remittance Details</h3>
        <dl>
          <dt>Remittance ID:</dt><dd>REM-2026-0001</dd>
          <dt>Amount Approved:</dt><dd>R 400.00</dd>
          <dt>Amount Paid:</dt><dd>R 350.00</dd>
          <dt>Exceptions:</dt><dd>
            <span class="badge badge-warning">1 exception</span>
          </dd>
        </dl>

        <table class="table-compact">
          <thead>
            <tr><th>Line Item</th><th>Approved</th><th>Paid</th><th>Status</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>CONS001</td>
              <td>R 450.00</td>
              <td>R 450.00</td>
              <td><span class="badge badge-success">PAID</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Payloads Tab -->
    <div id="tab-payloads" class="tab-pane">
      <div class="card">
        <h3>Canonical Payload</h3>
        <pre class="json-viewer">{
  "claim_id": 13,
  "claim_number": "CLM-2026-0001",
  "member_number": "MEM900001",
  ...
}</pre>
        <button class="btn-secondary" onclick="downloadPayload('canonical')">Copy</button>
      </div>

      <div class="card">
        <h3>EDI Format Payload</h3>
        <pre class="edi-viewer">EDI|CLM-2026-0001|MEM900001|...
SRV|CONS001|450.00|...
DIA|I10|PRIMARY|...
</pre>
        <button class="btn-secondary" onclick="downloadPayload('edi')">Copy</button>
      </div>
    </div>
  </div>
</div>
```

**Improvements:**
- ✅ Tabbed interface for section organization
- ✅ Readable tables instead of JSON
- ✅ Clear visual hierarchy with cards
- ✅ Quick access to download/copy actions
- ✅ Document/submission/remittance visibility
- ✅ Scannable within 30 seconds

---

## Component 2: Remittance Review Panel

### Current State (BEFORE)

```javascript
// Currently displays as:
const remittanceText = `
Remittance Approved: $${remittance.approved_amount}
Remittance Paid: $${remittance.paid_amount}
Status: ${remittance.status}
`;
alert(remittanceText);  // Alert box or embedded text
```

**Problems:**
- ❌ No visual summary
- ❌ No line-item breakdown
- ❌ Exception reasons hidden
- ❌ Reconciliation state unclear

### New Design (AFTER)

```html
<div class="remittance-panel">
  <!-- Summary card -->
  <div class="card card-elevated">
    <h2>Remittance Review</h2>
    <div class="summary-grid">
      <div class="metric">
        <span class="label">Amount Approved</span>
        <span class="value amount">R 450.00</span>
      </div>
      <div class="metric">
        <span class="label">Amount Paid</span>
        <span class="value amount">R 350.00</span>
      </div>
      <div class="metric">
        <span class="label">Difference</span>
        <span class="value amount negative">-R 100.00</span>
      </div>
      <div class="metric">
        <span class="label">Status</span>
        <span class="value badge badge-warning">Partial Payment</span>
      </div>
    </div>
  </div>

  <!-- Line-item breakdown -->
  <div class="card">
    <h3>Line Item Details</h3>
    <table class="table">
      <thead>
        <tr>
          <th>Service Code</th>
          <th>Description</th>
          <th>Approved Amount</th>
          <th>Paid Amount</th>
          <th>Status</th>
          <th>Exception</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>CONS001</td>
          <td>Consultation 30 min</td>
          <td>R 450.00</td>
          <td>R 350.00</td>
          <td><span class="badge badge-info">Partial</span></td>
          <td><span class="badge badge-warning">Co-payment applied</span></td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- Exceptions -->
  <div class="card" id="exceptions-card" style="display:none;">
    <h3>Reconciliation Exceptions</h3>
    <ul class="exception-list">
      <li>
        <span class="icon">⚠️</span>
        <span class="code">COPAYM-001</span>
        <span class="message">Co-payment of R 100 applied per scheme rule</span>
        <button class="btn-secondary" onclick="resolveException(1)">Acknowledge</button>
      </li>
    </ul>
  </div>

  <!-- Actions -->
  <div class="actions">
    <button class="btn-secondary" onclick="downloadRemittance()">📄 Download Remittance</button>
    <button class="btn-secondary" onclick="exportReconciliation()">📊 Export Reconciliation</button>
  </div>
</div>
```

**Improvements:**
- ✅ Summary metrics visible at a glance
- ✅ Line-item details table for audit
- ✅ Exception reasons clearly listed
- ✅ Difference highlighted in red
- ✅ Professional card layout
- ✅ Action buttons for download/export

---

## Component 3: Submission Tool Stepper

### Current State (BEFORE)

```html
<!-- Current: Simple button + status text -->
<div>
  <button onclick="submitClaim()">Submit to Scheme</button>
  <p id="submission-status">Not submitted</p>
</div>
```

**Problems:**
- ❌ No step visualization
- ❌ User doesn't know which phase they're in
- ❌ No progress indication
- ❌ No transport log visibility

### New Design (AFTER)

```html
<div class="submission-stepper">
  <!-- Stepper header -->
  <div class="stepper-header">
    <div class="step" data-step="1" data-status="complete">
      <div class="step-circle">✓</div>
      <div class="step-label">Generate</div>
    </div>
    <div class="step-line complete"></div>
    
    <div class="step" data-step="2" data-status="complete">
      <div class="step-circle">✓</div>
      <div class="step-label">Validate</div>
    </div>
    <div class="step-line active"></div>
    
    <div class="step" data-step="3" data-status="active">
      <div class="step-circle">⏳</div>
      <div class="step-label">Submit</div>
    </div>
    <div class="step-line"></div>
    
    <div class="step" data-step="4" data-status="pending">
      <div class="step-circle">4</div>
      <div class="step-label">Response</div>
    </div>
  </div>

  <!-- Step content panels -->
  <div class="step-content">
    <!-- Generate Panel -->
    <div class="step-panel" id="panel-generate" style="display:none;">
      <h3>Step 1: Generate Submission</h3>
      <div class="card">
        <dl>
          <dt>Canonical Payload:</dt>
          <dd>Generated ✓</dd>
          <dt>EDI Format:</dt>
          <dd>Generated ✓</dd>
          <dt>Idempotency Key:</dt>
          <dd>
            <code>cdc5e321-a3b2-4c1d-9e0f-2a3b4c5d6e7f</code>
            <button class="btn-icon" onclick="generateNewKey()">🔄</button>
          </dd>
        </dl>
      </div>
      <button class="btn-primary" onclick="nextStep()">Next: Validate</button>
    </div>

    <!-- Validate Panel -->
    <div class="step-panel" id="panel-validate" style="display:none;">
      <h3>Step 2: Validate Submission</h3>
      <div class="card">
        <ul class="checklist">
          <li><span class="check">✓</span> All line items have diagnoses</li>
          <li><span class="check">✓</span> PMB decision documented</li>
          <li><span class="check">✓</span> No blocking exceptions</li>
        </ul>
      </div>
      <button class="btn-secondary" onclick="previousStep()">Back</button>
      <button class="btn-primary" onclick="nextStep()">Next: Submit</button>
    </div>

    <!-- Submit Panel -->
    <div class="step-panel" id="panel-submit" style="display:block;">
      <h3>Step 3: Submit to Scheme</h3>
      <div class="card">
        <p>Ready to submit to scheme. Click below to proceed.</p>
        <button class="btn-primary" onclick="confirmSubmit()" id="submit-btn">
          📤 Submit Now
        </button>
      </div>

      <!-- Transport Log -->
      <div class="card card-monospace" id="transport-log" style="display:none;">
        <h4>Transport Log</h4>
        <pre id="log-content"></pre>
      </div>

      <button class="btn-secondary" onclick="previousStep()">Back</button>
    </div>

    <!-- Response Panel -->
    <div class="step-panel" id="panel-response" style="display:none;">
      <h3>Step 4: Scheme Response</h3>
      <div class="card" id="response-status">
        <p>Awaiting response from scheme...</p>
        <div class="spinner"></div>
      </div>

      <button class="btn-secondary" onclick="previousStep()">Back</button>
    </div>
  </div>

  <!-- Overall actions -->
  <div class="stepper-actions">
    <button class="btn-secondary" onclick="downloadSubmissionPack()">📦 Download Pack</button>
    <button class="btn-secondary" onclick="resetStepper()">↻ Reset</button>
  </div>
</div>
```

**CSS for Stepper:**

```css
.stepper-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.step-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  background: #e2e8f0;
  color: #475569;
  transition: all 0.3s ease;
}

.step[data-status="complete"] .step-circle {
  background: #22c55e;
  color: white;
}

.step[data-status="active"] .step-circle {
  background: #3b82f6;
  color: white;
  animation: pulse 2s infinite;
}

.step-line {
  flex: 1;
  height: 2px;
  background: #cbd5e1;
  margin: 0 0.5rem;
}

.step-line.complete {
  background: #22c55e;
}

.step-line.active {
  background: #3b82f6;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.7); }
  50% { box-shadow: 0 0 0 10px rgba(59, 130, 246, 0); }
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

**Improvements:**
- ✅ Clear phase visualization with stepper
- ✅ Progress indicators (✓, ⏳, numbers)
- ✅ Step-by-step navigation
- ✅ Transport log embedded for debugging
- ✅ New idempotency key generation option
- ✅ Checklist of validation criteria

---

## Component 4: Audit Trail Filters & Details

### Current State (BEFORE)

```html
<!-- Current: Simple table with no interactivity -->
<table>
  <tr>
    <td>claim_id=13, action=create, actor=billing_specialist</td>
  </tr>
  <tr>
    <td>full JSON details...</td>
  </tr>
</table>
```

**Problems:**
- ❌ No filtering capability
- ❌ No expandable details
- ❌ Difficult to find specific events
- ❌ JSON payload too verbose

### New Design (AFTER)

```html
<div class="audit-trail-panel">
  <!-- Filter bar -->
  <div class="filter-bar">
    <div class="filter-group">
      <label>Action Type:</label>
      <select id="filter-action" onchange="applyFilters()">
        <option value="">All</option>
        <option value="create">Create</option>
        <option value="update">Update</option>
        <option value="validate">Validate</option>
        <option value="submit">Submit</option>
        <option value="close">Close</option>
      </select>
    </div>

    <div class="filter-group">
      <label>Date Range:</label>
      <input type="date" id="filter-date-from" onchange="applyFilters()">
      <span>to</span>
      <input type="date" id="filter-date-to" onchange="applyFilters()">
    </div>

    <div class="filter-group">
      <label>Actor Role:</label>
      <select id="filter-role" onchange="applyFilters()">
        <option value="">All</option>
        <option value="Billing Specialist">Billing Specialist</option>
        <option value="Administrator">Administrator</option>
        <option value="Provider">Provider</option>
      </select>
    </div>

    <button class="btn-secondary" onclick="clearFilters()">Clear Filters</button>
  </div>

  <!-- Audit events table -->
  <table class="audit-table">
    <thead>
      <tr>
        <th>Timestamp</th>
        <th>Action</th>
        <th>Actor</th>
        <th>Resource</th>
        <th>Details</th>
      </tr>
    </thead>
    <tbody id="audit-events">
      <!-- Rows populated by JavaScript -->
      <tr class="audit-event">
        <td>2026-04-17 14:32:01 UTC</td>
        <td><span class="badge badge-info">UPDATE</span></td>
        <td>billing_specialist_001</td>
        <td>claim_diagnosis [id=42]</td>
        <td>
          <button class="btn-small" onclick="toggleDetails(this)">▼ Details</button>
        </td>
      </tr>
      <tr class="audit-details" style="display:none;">
        <td colspan="5">
          <div class="details-drawer">
            <h4>Change Details</h4>
            <div class="change-summary">
              <dl>
                <dt>Field:</dt><dd>is_primary</dd>
                <dt>Before:</dt><dd><code>false</code></dd>
                <dt>After:</dt><dd><code>true</code></dd>
                <dt>Reason:</dt><dd>User manually marked as primary diagnosis</dd>
              </dl>
            </div>
            <button class="btn-secondary" onclick="openEvidencePack(13)">
              Open Evidence Pack
            </button>
          </div>
        </td>
      </tr>

      <tr class="audit-event">
        <td>2026-04-17 14:31:45 UTC</td>
        <td><span class="badge badge-success">CREATE</span></td>
        <td>billing_specialist_001</td>
        <td>claim_attachment [id=123]</td>
        <td>
          <button class="btn-small" onclick="toggleDetails(this)">▼ Details</button>
        </td>
      </tr>
      <tr class="audit-details" style="display:none;">
        <td colspan="5">
          <div class="details-drawer">
            <h4>Attachment Created</h4>
            <dl>
              <dt>Filename:</dt><dd>motivation.pdf</dd>
              <dt>Type:</dt><dd>MOTIVATION</dd>
              <dt>Size:</dt><dd>245 KB</dd>
              <dt>Storage:</dt><dd>local://evidence/motivation.pdf</dd>
            </dl>
          </div>
        </td>
      </tr>
    </tbody>
  </table>

  <!-- Pagination -->
  <div class="pagination">
    <button class="btn-secondary" onclick="previousPage()">← Previous</button>
    <span class="page-indicator">Page 1 of 5 (47 events)</span>
    <button class="btn-secondary" onclick="nextPage()">Next →</button>
  </div>
</div>
```

**Improvements:**
- ✅ Filter by action type, date, actor role
- ✅ Expandable details drawer (not raw JSON)
- ✅ Visual badges for action types
- ✅ Link to open Evidence Pack
- ✅ Pagination for large audit trails
- ✅ Human-readable change summaries

---

## Component 5: Patient Registry Clickable Profiles

### Current State (BEFORE)

```html
<!-- Current: Read-only table -->
<table>
  <tr>
    <td>John Doe</td>
    <td>MEM900001</td>
    <td>Discovery Health</td>
  </tr>
</table>
```

**Problems:**
- ❌ No interaction capability
- ❌ No claim context visibility
- ❌ Cannot navigate to patient details

### New Design (AFTER)

```html
<div class="patient-registry-panel">
  <!-- Search & Filter -->
  <div class="search-bar">
    <input type="text" id="patient-search" placeholder="Search by name or membership #">
    <select id="scheme-filter" onchange="filterPatients()">
      <option value="">All Schemes</option>
      <option value="DH">Discovery Health</option>
      <option value="GEMS">GEMS</option>
      <option value="Bonitas">Bonitas</option>
    </select>
  </div>

  <!-- Patient cards grid -->
  <div class="patient-grid">
    <div class="patient-card clickable" onclick="openPatientDetail(1)">
      <!-- Profile section -->
      <div class="card-header">
        <h3>John Doe</h3>
        <span class="member-badge">MEM900001</span>
      </div>

      <!-- Quick info -->
      <div class="quick-info">
        <dl>
          <dt>Scheme:</dt><dd>Discovery Health · Option 2</dd>
          <dt>Provider:</dt><dd>Dr. Thabo Mthembu</dd>
          <dt>Member Since:</dt><dd>2024-01-15</dd>
        </dl>
      </div>

      <!-- Status indicators -->
      <div class="status-indicators">
        <div class="indicator" title="Claims awaiting validation">
          <span class="icon">📋</span>
          <span class="count">2</span>
          <span class="label">Pending Claims</span>
        </div>
        <div class="indicator" title="Diagnoses recorded">
          <span class="icon">🏥</span>
          <span class="count">3</span>
          <span class="label">Diagnoses</span>
        </div>
        <div class="indicator" title="Uploaded documents">
          <span class="icon">📎</span>
          <span class="count">1</span>
          <span class="label">Attachments</span>
        </div>
      </div>

      <!-- Action button -->
      <button class="btn-primary full-width">
        View Patient Profile →
      </button>
    </div>

    <!-- More patient cards... -->
  </div>

  <!-- Pagination -->
  <div class="pagination">
    <span>Showing 1-12 of 47 patients</span>
    <button class="btn-secondary" onclick="nextPage()">Next</button>
  </div>
</div>

<!-- Patient Detail Modal -->
<div id="patient-detail-modal" class="modal" style="display:none;">
  <div class="modal-content">
    <!-- Header -->
    <div class="modal-header">
      <h2>Patient Profile</h2>
      <button class="btn-icon" onclick="closePatientDetail()">✕</button>
    </div>

    <!-- Profile card -->
    <div class="card card-elevated">
      <div class="profile-section">
        <div class="profile-info">
          <h3>John Doe</h3>
          <dl>
            <dt>Membership #:</dt><dd>MEM900001</dd>
            <dt>Date of Birth:</dt><dd>1975-03-22 (age 51)</dd>
            <dt>Scheme:</dt><dd>Discovery Health · Option 2</dd>
            <dt>Plan Status:</dt><dd>
              <span class="badge badge-success">Active</span>
            </dd>
          </dl>
        </div>

        <!-- Coverage summary -->
        <div class="coverage-summary">
          <h4>Plan Coverage</h4>
          <ul>
            <li>Annual deductible: R 5,000</li>
            <li>Out of pocket max: R 15,000</li>
            <li>Co-payment: R 50 per GP visit</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Claims section -->
    <div class="card">
      <h3>Recent Claims</h3>
      <table class="table">
        <thead>
          <tr>
            <th>Claim #</th>
            <th>Date</th>
            <th>Service</th>
            <th>Provider</th>
            <th>Amount</th>
            <th>Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>CLM-2026-0001</td>
            <td>2026-04-15</td>
            <td>Consultation</td>
            <td>Dr. Thabo Mthembu</td>
            <td>R 450.00</td>
            <td><span class="badge badge-warning">Pending Validation</span></td>
            <td>
              <button class="btn-small" onclick="openClaimDetail(13)">
                View
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Diagnoses section -->
    <div class="card">
      <h3>Active Diagnoses</h3>
      <ul class="diagnosis-list">
        <li>
          <span class="icd-code">I10</span>
          <span class="description">Essential hypertension</span>
          <span class="last-seen">Last: 2026-04-15</span>
        </li>
        <li>
          <span class="icd-code">E11.9</span>
          <span class="description">Type 2 diabetes</span>
          <span class="last-seen">Last: 2026-04-10</span>
        </li>
      </ul>
    </div>

    <!-- Modal actions -->
    <div class="modal-actions">
      <button class="btn-secondary" onclick="closePatientDetail()">Close</button>
      <button class="btn-primary" onclick="createNewClaimForPatient(1)">
        + New Claim
      </button>
    </div>
  </div>
</div>
```

**CSS for Patient Cards:**

```css
.patient-card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  background: #f8fafc;
  transition: all 0.2s ease;
}

.patient-card.clickable {
  cursor: pointer;
}

.patient-card.clickable:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
  background: #fff;
}

.status-indicators {
  display: flex;
  gap: 1rem;
  margin: 1rem 0;
  padding: 1rem 0;
  border-top: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}

.indicator {
  flex: 1;
  text-align: center;
}

.indicator .icon {
  display: block;
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.indicator .count {
  display: block;
  font-size: 1.5rem;
  font-weight: 600;
  color: #1e293b;
}

.indicator .label {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
}
```

**Improvements:**
- ✅ Clickable patient cards with hover effect
- ✅ Quick status indicators (claims, diagnoses, attachments)
- ✅ Detailed modal with full profile, claims, diagnoses
- ✅ Link to open specific claims
- ✅ Create new claim button
- ✅ Member scheme and coverage information
- ✅ Search and filtering by scheme

---

## CSS Foundation Changes

Add to `css/styles.css`:

```css
/* Card system */
.card {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 1rem;
}

.card.card-elevated {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: #1e293b;
}

/* Badge system */
.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.85rem;
  font-weight: 500;
}

.badge-success {
  background: #dcfce7;
  color: #166534;
}

.badge-warning {
  background: #fef3c7;
  color: #92400e;
}

.badge-info {
  background: #dbeafe;
  color: #1e40af;
}

.badge-danger {
  background: #fee2e2;
  color: #991b1b;
}

/* Tables */
.table-compact {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.table-compact th {
  padding: 0.75rem;
  text-align: left;
  background: #f1f5f9;
  border-bottom: 2px solid #e2e8f0;
  font-weight: 600;
}

.table-compact td {
  padding: 0.75rem;
  border-bottom: 1px solid #e2e8f0;
}

.table-compact tr:hover {
  background: #f8fafc;
}

/* Buttons */
.btn-small {
  padding: 0.4rem 0.8rem;
  font-size: 0.85rem;
  background: #e2e8f0;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-small:hover {
  background: #cbd5e1;
}

.full-width {
  width: 100%;
}

/* Modals */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  border-radius: 12px;
  max-width: 800px;
  max-height: 90vh;
  overflow: auto;
  padding: 2rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
  border-top: 1px solid #e2e8f0;
  padding-top: 1rem;
}

/* Drawers */
.drawer {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 50%;
  max-width: 600px;
  background: #fff;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease;
  z-index: 999;
  overflow: auto;
}

@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

.drawer-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.drawer-header h2 {
  margin: 0;
  font-size: 1.25rem;
}

/* Tabs */
.tab-bar {
  display: flex;
  border-bottom: 2px solid #e2e8f0;
  margin-bottom: 1rem;
  gap: 0;
}

.tab {
  padding: 1rem;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  font-weight: 500;
  color: #64748b;
  transition: all 0.2s;
}

.tab.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.tab:hover {
  color: #1e293b;
}

.tab-content {
  min-height: 400px;
}

.tab-pane {
  display: none;
}

.tab-pane.active {
  display: block;
}
```

---

## Rollout Plan

1. **Phase 5A (Evidence Pack):** Complete by 2026-04-18 10:00
2. **Phase 5B (Remittance Review):** Complete by 2026-04-18 14:00
3. **Phase 5C (Submission Stepper):** Complete by 2026-04-18 18:00
4. **Phase 5D (Audit Trail):** Complete by 2026-04-19 12:00
5. **Phase 5E (Patient Registry):** Complete by 2026-04-19 18:00

**Test each phase:** Open claim in UI, navigate through redesigned component, verify all data displays correctly.

