# Implementation Checklist: Claim Role Handoff + Onboarding Workflow Integration

**Status:** Ready for implementation
**Target Files:** 6 backend & frontend files + 3 test files
**Estimated Scope:** 1-2 days development + testing

---

## Phase 1: Backend Claim Model Extension

### ✅ Task 1.1: Extend ClaimRecord model

**File:** `medhealth-ui/backend/platform_core.py`

**Location:** Find the `ClaimRecord` class definition (around line 200-300)

**Change:** Add workflow metadata fields to the `ClaimRecord` Pydantic model after existing fields like `version` and `status`.

```python
# Add these fields to ClaimRecord class:
eligible_roles: List[str] = []
last_completed_role: Optional[str] = None
role_action_history: List[Dict[str, Any]] = []
affected_roles: List[str] = []
state_progression: List[Dict[str, Any]] = []
onboarding_status: Optional[str] = None
onboarding_blockers: List[Dict[str, Any]] = []
onboarding_actions: List[Dict[str, Any]] = []
```

**Verification:** Run `python -c "from medhealth-ui.backend.platform_core import ClaimRecord; print('OK')"` — should print OK with no errors.

---

### ✅ Task 1.2: Add metadata derivation helper

**File:** `medhealth-ui/backend/platform_core.py`

**Location:** Add a new method to the `PlatformStore` class around line 1000-1100

**Change:** Add a helper method to derive onboarding blockers from provider/practice state.

```python
def _derive_onboarding_context(self, claim: ClaimRecord) -> Dict[str, Any]:
    """Derive onboarding blockers and context from provider and practice onboarding status."""
    provider = self.providers.get(claim.provider_id)
    patient = self.patients.get(claim.patient_id)
    
    blockers = []
    actions = []
    
    if provider:
        practice = self.practices.get(provider.practice_id)
        
        # Check practice onboarding status
        if practice and practice.onboarding_status != "approved":
            blockers.append({
                "type": "PRACTICE_ONBOARDING",
                "reason_code": f"PRACTICE_ONBOARDING_{practice.onboarding_status.upper()}",
                "message": f"Practice '{practice.name}' onboarding status is {practice.onboarding_status}",
                "severity": "WARNING" if practice.onboarding_status == "pending_review" else "INFO",
                "affected_field": "provider_id",
                "remediation": f"Contact practice to complete onboarding",
            })
            actions.append({
                "type": "NAVIGATE_PRACTICE_PROFILE",
                "target": f"/providers.html?practice_id={practice.id}",
                "label": "View Practice Profile",
            })
        
        # Check provider onboarding status
        if provider.onboarding_status != "approved":
            blockers.append({
                "type": "PROVIDER_ONBOARDING",
                "reason_code": f"PROVIDER_ONBOARDING_{provider.onboarding_status.upper()}",
                "message": f"Provider '{provider.name}' onboarding status is {provider.onboarding_status}",
                "severity": "WARNING" if provider.onboarding_status == "pending_review" else "INFO",
                "affected_field": "provider_id",
                "remediation": f"Contact provider to complete onboarding",
            })
            actions.append({
                "type": "NAVIGATE_PROVIDER_PROFILE",
                "target": f"/providers.html?provider_id={provider.id}",
                "label": "View Provider Profile",
            })
    
    return {
        "onboarding_status": provider.onboarding_status if provider else None,
        "onboarding_blockers": blockers,
        "onboarding_actions": actions,
    }
```

**Verification:** Method parses without syntax errors.

---

### ✅ Task 1.3: Update get_claim to include metadata

**File:** `medhealth-ui/backend/platform_core.py`

**Location:** Find method `get_claim(self, claim_id: int)` around line 1300

**Change:** Augment the returned claim payload with workflow and onboarding metadata.

```python
def get_claim(self, claim_id: int) -> Dict[str, Any]:
    claim = self.claims[claim_id]
    payload = claim.model_dump(mode="json")
    
    # Add workflow metadata
    payload["eligible_roles"] = claim.eligible_roles or []
    payload["last_completed_role"] = claim.last_completed_role
    payload["role_action_history"] = claim.role_action_history or []
    payload["affected_roles"] = claim.affected_roles or []
    payload["state_progression"] = claim.state_progression or []
    
    # Add onboarding context
    onboarding_context = self._derive_onboarding_context(claim)
    payload["onboarding_status"] = onboarding_context.get("onboarding_status")
    payload["onboarding_blockers"] = onboarding_context.get("onboarding_blockers", [])
    payload["onboarding_actions"] = onboarding_context.get("onboarding_actions", [])
    
    return payload
```

**Verification:** Call `get_claim(1)` in test — payload includes all new fields.

---

### ✅ Task 1.4: Update run_readiness to return workflow metadata

**File:** `medhealth-ui/backend/platform_core.py`

**Location:** Find method `run_readiness(self, claim_id: int)` around line 1500

**Change:** Append workflow and onboarding metadata to the readiness result.

```python
# At the end of run_readiness(), before the return statement, add:
result["affected_roles"] = claim.affected_roles or ["billing_reviewer", "operations"]
result["state_progression"] = [
    {"status": "DRAFT", "completed_at": claim.created_at, "completed_by": "system"},
    {"status": "READINESS_CHECK", "completed_at": utc_now() if result["is_ready"] else None},
]

# Add onboarding context
onboarding_context = self._derive_onboarding_context(claim)
result["onboarding_blockers"] = onboarding_context.get("onboarding_blockers", [])
result["onboarding_actions"] = onboarding_context.get("onboarding_actions", [])
```

**Verification:** Call `run_readiness(claim_id)` — result includes workflow and onboarding fields.

---

### ✅ Task 1.5: Update close_claim to return workflow metadata

**File:** `medhealth-ui/backend/platform_core.py`

**Location:** Find method `close_claim(self, claim_id: int)` around line 1700

**Change:** Append workflow and onboarding metadata to the closure result.

```python
# At the end of close_claim(), before the return statement, add:
result["affected_roles"] = ["operations", "remittance_team"]
result["state_progression"] = [
    {"status": "DRAFT", "completed_at": claim.created_at},
    {"status": "READINESS_CHECK", "completed_at": claim.updated_at},
    {"status": "CLOSED", "completed_at": utc_now()},
]

# Add onboarding context
onboarding_context = self._derive_onboarding_context(claim)
result["onboarding_blockers"] = onboarding_context.get("onboarding_blockers", [])
result["onboarding_actions"] = onboarding_context.get("onboarding_actions", [])
```

**Verification:** Call `close_claim(claim_id)` — result includes workflow and onboarding fields.

---

### ✅ Task 1.6: Update post-closure validation

**File:** `medhealth-ui/backend/platform_core.py`

**Location:** Find method `run_post_closure_validation(self, claim_id: int)` around line 1800

**Change:** Append workflow and onboarding metadata to the validation result.

```python
# At the end of run_post_closure_validation(), before the return statement, add:
result["affected_roles"] = ["billing_auditor", "compliance_officer"]
result["state_progression"] = [
    {"status": "CLOSED", "completed_at": claim.updated_at},
    {"status": "POST_CLOSURE_VALIDATION", "completed_at": utc_now() if result["validation_passed"] else None},
]

# Add onboarding context
onboarding_context = self._derive_onboarding_context(claim)
result["onboarding_blockers"] = onboarding_context.get("onboarding_blockers", [])
result["onboarding_actions"] = onboarding_context.get("onboarding_actions", [])
```

**Verification:** Call `run_post_closure_validation(claim_id)` — result includes workflow and onboarding fields.

---

### ✅ Task 1.7: Update submit_claim to return workflow metadata

**File:** `medhealth-ui/backend/platform_core.py`

**Location:** Find method `submit_claim(self, claim_id: int, submission_context: Dict[str, Any])` around line 2000

**Change:** Append workflow and onboarding metadata to the submission result.

```python
# At the end of submit_claim(), before the return statement, add:
result["affected_roles"] = ["submissions_team", "pmb_reviewer"]
result["state_progression"] = [
    {"status": "CLOSED", "completed_at": claim.updated_at},
    {"status": "SUBMITTED", "completed_at": utc_now()},
]

# Add onboarding context
onboarding_context = self._derive_onboarding_context(claim)
result["onboarding_blockers"] = onboarding_context.get("onboarding_blockers", [])
result["onboarding_actions"] = onboarding_context.get("onboarding_actions", [])
```

**Verification:** Call `submit_claim(claim_id, {...})` — result includes workflow and onboarding fields.

---

## Phase 2: Backend API and Realtime Transport

### ✅ Task 2.1: Add WebSocket infrastructure

**File:** `medhealth-ui/backend/platform_api.py`

**Location:** Add imports near the top (around line 1-20)

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set
import asyncio
```

**Location:** Add module-level WebSocket registry after imports

```python
# Global WebSocket subscriber registry
# Format: {claim_id: Set[WebSocket]}
_claim_subscribers: dict[int, Set[WebSocket]] = {}

async def broadcast_claim_update(claim_id: int, update_data: Dict[str, Any]) -> None:
    """Broadcast a claim update to all subscribers for this claim."""
    if claim_id not in _claim_subscribers:
        return
    
    subscribers = list(_claim_subscribers[claim_id])
    disconnected = []
    
    for websocket in subscribers:
        try:
            await websocket.send_json({
                "type": "claim_update",
                "claim_id": claim_id,
                "timestamp": utc_now(),
                "data": update_data
            })
        except RuntimeError:
            disconnected.append(websocket)
    
    # Clean up disconnected clients
    for websocket in disconnected:
        _claim_subscribers[claim_id].discard(websocket)
```

**Verification:** File imports without errors.

---

### ✅ Task 2.2: Add WebSocket endpoint

**File:** `medhealth-ui/backend/platform_api.py`

**Location:** Add after the last `@app.websocket()` endpoint or at the end of API definitions (around line 700)

```python
@app.websocket("/ws/claims/{claim_id}")
async def websocket_claim_updates(websocket: WebSocket, claim_id: int, token: str = None):
    """WebSocket endpoint for real-time claim updates.
    
    Auth: pass token as query param: /ws/claims/123?token=Bearer%20...
    """
    # Authenticate
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return
    
    try:
        current_user = get_current_user(token)
    except:
        await websocket.close(code=1008, reason="Invalid authentication token")
        return
    
    # Verify user can access this claim
    try:
        claim = db.claims.get(claim_id)
        if not claim:
            await websocket.close(code=1008, reason="Claim not found")
            return
        ensure_scope_access(current_user, claim.tenant_id)
    except:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    # Register subscriber
    await websocket.accept()
    if claim_id not in _claim_subscribers:
        _claim_subscribers[claim_id] = set()
    _claim_subscribers[claim_id].add(websocket)
    
    try:
        # Keep connection open; listen for heartbeat or disconnect
        while True:
            data = await websocket.receive_text()
            # Optional: handle ping messages or commands
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        _claim_subscribers[claim_id].discard(websocket)
        if not _claim_subscribers[claim_id]:
            del _claim_subscribers[claim_id]
```

**Verification:** Endpoint definition is syntactically correct.

---

### ✅ Task 2.3: Broadcast on claim state changes

**File:** `medhealth-ui/backend/platform_api.py`

**Location:** At the end of `run_readiness()` endpoint, after `db.run_readiness()` call

```python
# Add after the readiness result is obtained:
claim = db.get_claim(claim_id)
await broadcast_claim_update(claim_id, {
    "status": claim.status,
    "affected_roles": result.get("affected_roles", []),
    "state_progression": result.get("state_progression", []),
    "onboarding_blockers": result.get("onboarding_blockers", []),
})
```

**Verification:** Broadcast call is syntactically correct.

---

### ✅ Task 2.4: Broadcast on close_claim

**File:** `medhealth-ui/backend/platform_api.py`

**Location:** At the end of `close_claim()` endpoint, after `db.close_claim()` call

```python
# Add after the closure result is obtained:
claim = db.get_claim(claim_id)
await broadcast_claim_update(claim_id, {
    "status": claim.status,
    "affected_roles": result.get("affected_roles", []),
    "state_progression": result.get("state_progression", []),
    "onboarding_blockers": result.get("onboarding_blockers", []),
})
```

**Verification:** Broadcast call is syntactically correct.

---

### ✅ Task 2.5: Broadcast on post-closure validation

**File:** `medhealth-ui/backend/platform_api.py`

**Location:** At the end of `run_post_closure_validation()` endpoint

```python
# Add after the validation result is obtained:
claim = db.get_claim(claim_id)
await broadcast_claim_update(claim_id, {
    "status": claim.status,
    "affected_roles": result.get("affected_roles", []),
    "state_progression": result.get("state_progression", []),
    "onboarding_blockers": result.get("onboarding_blockers", []),
})
```

**Verification:** Broadcast call is syntactically correct.

---

### ✅ Task 2.6: Broadcast on submit_claim

**File:** `medhealth-ui/backend/platform_api.py`

**Location:** At the end of `submit_claim()` endpoint, after `db.submit_claim()` call

```python
# Add after the submission result is obtained:
claim = db.get_claim(claim_id)
await broadcast_claim_update(claim_id, {
    "status": claim.status,
    "affected_roles": result.get("affected_roles", []),
    "state_progression": result.get("state_progression", []),
    "onboarding_blockers": result.get("onboarding_blockers", []),
})
```

**Verification:** Broadcast call is syntactically correct.

---

## Phase 3: Frontend Claim Detail UI

### ✅ Task 3.1: Add HTML panels for workflow and onboarding

**File:** `medhealth-ui/claim_detail.html`

**Location:** Find the claim detail sidebar section (around line 300-400) and add these panels before the closing `</div>` of the sidebar.

```html
<!-- Role Handoff Progress Panel -->
<div class="panel role-progress-panel" id="roleProgressPanel" style="display:none;">
    <h3>Workflow Handoff</h3>
    <div class="role-history">
        <div class="role-item">
            <span class="label">Current Status:</span>
            <span class="value" id="currentRoleStatus">-</span>
        </div>
        <div class="role-item">
            <span class="label">Last Completed:</span>
            <span class="value" id="lastCompletedRole">-</span>
        </div>
        <div class="role-item">
            <span class="label">Eligible Next:</span>
            <span class="value" id="eligibleRoles">-</span>
        </div>
    </div>
    <div id="stateProgression" class="state-progression">
        <!-- Timeline will be rendered here -->
    </div>
</div>

<!-- Onboarding Status Panel -->
<div class="panel onboarding-panel" id="onboardingPanel" style="display:none;">
    <h3>Onboarding Status</h3>
    <div id="onboardingStatus" class="onboarding-status">
        <span class="label">Provider Onboarding:</span>
        <span class="value" id="providerOnboardingStatus">-</span>
    </div>
    <div id="onboardingBlockers" class="onboarding-blockers">
        <!-- Blockers will be rendered here -->
    </div>
    <div id="onboardingActions" class="onboarding-actions">
        <!-- Actions will be rendered here -->
    </div>
</div>
```

**Verification:** HTML is valid and panels are rendering.

---

### ✅ Task 3.2: Update claim detail load in app.js

**File:** `medhealth-ui/js/app.js`

**Location:** Find the `loadClaimDetail()` function around line 800-900

**Change:** Augment claim loading to include workflow and onboarding metadata rendering.

```javascript
async function loadClaimDetail(claimId) {
    const claim = await window.api.getClaim(claimId);
    
    // ... existing render logic ...
    
    // Render workflow panels
    if (claim.affected_roles && claim.affected_roles.length > 0) {
        document.getElementById('roleProgressPanel').style.display = 'block';
        document.getElementById('currentRoleStatus').textContent = 
            claim.status || 'DRAFT';
        document.getElementById('lastCompletedRole').textContent = 
            claim.last_completed_role || 'None';
        document.getElementById('eligibleRoles').textContent = 
            (claim.eligible_roles || []).join(', ') || 'None';
        
        // Render state progression timeline
        const progressionHtml = (claim.state_progression || [])
            .map(item => `
                <div class="progression-item">
                    <div class="status">${item.status}</div>
                    <div class="timestamp">${item.completed_at ? new Date(item.completed_at).toLocaleString() : 'Pending'}</div>
                </div>
            `).join('');
        document.getElementById('stateProgression').innerHTML = progressionHtml;
    }
    
    // Render onboarding panel
    if (claim.onboarding_blockers && claim.onboarding_blockers.length > 0) {
        document.getElementById('onboardingPanel').style.display = 'block';
        document.getElementById('providerOnboardingStatus').textContent = 
            claim.onboarding_status || 'Unknown';
        
        // Render blockers
        const blockersHtml = (claim.onboarding_blockers || [])
            .map(blocker => `
                <div class="blocker ${blocker.severity || 'INFO'}">
                    <div class="reason">${blocker.reason_code}</div>
                    <div class="message">${blocker.message}</div>
                    <div class="remediation">${blocker.remediation}</div>
                </div>
            `).join('');
        document.getElementById('onboardingBlockers').innerHTML = blockersHtml;
        
        // Render action buttons
        const actionsHtml = (claim.onboarding_actions || [])
            .map(action => `
                <a href="${action.target}" class="action-button">
                    ${action.label}
                </a>
            `).join('');
        document.getElementById('onboardingActions').innerHTML = actionsHtml;
    }
    
    // Subscribe to real-time updates
    await subscribeClaimRealtimeUpdates(claimId);
}
```

**Verification:** Function syntax is correct and panels render.

---

### ✅ Task 3.3: Add realtime subscription function

**File:** `medhealth-ui/js/app.js`

**Location:** Add new function after `loadClaimDetail()` around line 950

```javascript
async function subscribeClaimRealtimeUpdates(claimId) {
    const token = localStorage.getItem('authToken');
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProto}//${window.location.host}/ws/claims/${claimId}?token=${encodeURIComponent('Bearer ' + token)}`;
    
    // Try WebSocket first
    let websocket;
    try {
        websocket = new WebSocket(wsUrl);
        websocket.onopen = () => console.log('WebSocket connected for claim', claimId);
        websocket.onmessage = async (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'claim_update') {
                console.log('Received claim update:', message);
                // Reload claim detail to reflect changes
                await loadClaimDetail(claimId);
            }
        };
        websocket.onerror = (error) => {
            console.warn('WebSocket error, falling back to polling:', error);
            fallbackPolling(claimId);
        };
        websocket.onclose = () => {
            console.log('WebSocket closed, starting polling fallback');
            fallbackPolling(claimId);
        };
    } catch (err) {
        console.warn('WebSocket not supported, using polling:', err);
        fallbackPolling(claimId);
    }
}

function fallbackPolling(claimId) {
    // Poll for claim updates every 5 seconds
    const pollInterval = setInterval(async () => {
        try {
            const claim = await window.api.getClaim(claimId);
            const currentStatus = document.getElementById('currentRoleStatus')?.textContent;
            
            // If status changed, reload detail
            if (currentStatus && claim.status !== currentStatus) {
                await loadClaimDetail(claimId);
            }
        } catch (err) {
            console.error('Polling error:', err);
        }
    }, 5000);
    
    // Store interval ID for cleanup if needed
    window._claimPollInterval = pollInterval;
}
```

**Verification:** Functions are syntactically correct.

---

## Phase 4: Frontend Dashboard Worklist Updates

### ✅ Task 4.1: Update dashboard rendering with workflow context

**File:** `medhealth-ui/js/app.js`

**Location:** Find the `renderDashboardWorklist()` function around line 1200-1300

**Change:** Augment worklist rows to show onboarding and role handoff status.

```javascript
// Inside renderDashboardWorklist(), when building each row item, add:
let statusBadges = '';

// Add onboarding badge
if (item.onboarding_blockers && item.onboarding_blockers.length > 0) {
    statusBadges += `<span class="badge badge-warning">Onboarding Blocked</span>`;
}

// Add role status if available
if (item.affected_roles && item.affected_roles.length > 0) {
    statusBadges += `<span class="badge badge-info">Roles: ${item.affected_roles.join(',')}</span>`;
}

// Insert badges into the row HTML:
rowHtml = rowHtml.replace('</div>', `${statusBadges}</div>`);
```

**Verification:** Dashboard renders with status badges.

---

### ✅ Task 4.2: Update CSS for workflow panels

**File:** `medhealth-ui/css/styles.css`

**Location:** Add at the end of the file

```css
/* Workflow and Onboarding Panels */
.role-progress-panel,
.onboarding-panel {
    margin-top: 20px;
    padding: 15px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    background-color: #fafafa;
}

.role-progress-panel h3,
.onboarding-panel h3 {
    margin-top: 0;
    font-size: 14px;
    font-weight: 600;
    color: #333;
}

.role-history {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.role-item,
.onboarding-status {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
}

.role-item .label,
.onboarding-status .label {
    color: #666;
    font-weight: 500;
}

.role-item .value,
.onboarding-status .value {
    color: #333;
}

.state-progression {
    margin-top: 15px;
    border-top: 1px solid #ddd;
    padding-top: 10px;
}

.progression-item {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    padding: 5px 0;
    border-bottom: 1px solid #eee;
}

.progression-item .status {
    font-weight: 600;
    color: #069;
}

.progression-item .timestamp {
    color: #999;
}

.onboarding-blockers {
    margin-top: 10px;
}

.blocker {
    margin: 8px 0;
    padding: 8px;
    border-left: 3px solid #ff9800;
    background-color: #fff3e0;
    border-radius: 2px;
    font-size: 12px;
}

.blocker.WARNING {
    border-left-color: #ff9800;
    background-color: #fff3e0;
}

.blocker.INFO {
    border-left-color: #2196f3;
    background-color: #e3f2fd;
}

.blocker .reason {
    font-weight: 600;
    color: #d32f2f;
}

.blocker .message {
    margin-top: 3px;
    color: #666;
}

.blocker .remediation {
    margin-top: 3px;
    font-size: 11px;
    color: #999;
    font-style: italic;
}

.onboarding-actions {
    margin-top: 10px;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.action-button {
    display: inline-block;
    padding: 6px 12px;
    background-color: #2196f3;
    color: white;
    text-decoration: none;
    border-radius: 3px;
    font-size: 12px;
    font-weight: 500;
    transition: background-color 0.2s;
}

.action-button:hover {
    background-color: #1976d2;
}

.badge {
    display: inline-block;
    padding: 3px 8px;
    margin-right: 5px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 600;
}

.badge-warning {
    background-color: #fff3e0;
    color: #e65100;
}

.badge-info {
    background-color: #e3f2fd;
    color: #01579b;
}
```

**Verification:** CSS syntax is correct and styles render.

---

## Phase 5: Backend Tests

### ✅ Task 5.1: Add claim metadata test

**File:** `medhealth-ui/backend/tests/test_main_entrypoint_api.py`

**Location:** Add new test method to the existing test class around line 250

```python
def test_get_claim_includes_workflow_and_onboarding_metadata(self) -> None:
    """Test that get_claim returns workflow and onboarding metadata."""
    current_user = self._current_user()
    claim = self._create_test_claim(current_user)
    
    retrieved = platform_api.get_claim(claim["id"], current_user=current_user)
    
    # Verify workflow metadata fields exist
    self.assertIn("eligible_roles", retrieved)
    self.assertIn("last_completed_role", retrieved)
    self.assertIn("role_action_history", retrieved)
    self.assertIn("affected_roles", retrieved)
    self.assertIn("state_progression", retrieved)
    
    # Verify onboarding metadata fields exist
    self.assertIn("onboarding_status", retrieved)
    self.assertIn("onboarding_blockers", retrieved)
    self.assertIn("onboarding_actions", retrieved)
```

**Verification:** Test passes.

---

### ✅ Task 5.2: Add readiness metadata test

**File:** `medhealth-ui/backend/tests/test_main_entrypoint_api.py`

**Location:** Add new test method after previous test

```python
def test_run_readiness_returns_workflow_and_onboarding_metadata(self) -> None:
    """Test that run_readiness returns workflow and onboarding metadata."""
    current_user = self._current_user()
    claim = self._create_test_claim_with_full_context(current_user)
    
    readiness = platform_api.run_readiness(claim["id"], current_user=current_user)
    
    # Verify workflow metadata in result
    self.assertIn("affected_roles", readiness)
    self.assertIn("state_progression", readiness)
    self.assertTrue(isinstance(readiness.get("affected_roles"), list))
    self.assertTrue(isinstance(readiness.get("state_progression"), list))
    
    # Verify onboarding metadata in result
    self.assertIn("onboarding_blockers", readiness)
    self.assertIn("onboarding_actions", readiness)
```

**Verification:** Test passes.

---

### ✅ Task 5.3: Add provider onboarding context test

**File:** `medhealth-ui/backend/tests/test_main_entrypoint_api.py`

**Location:** Add new test method after previous test

```python
def test_provider_onboarding_appears_in_claim_context(self) -> None:
    """Test that provider onboarding status appears in claim workflow context."""
    current_user = self._current_user()
    
    # Create a provider with pending_review onboarding status
    provider = platform_api.create_provider({
        "name": "Dr. Test",
        "npi": "TEST123",
        "email": "test@example.com",
        "phone": "+27 11 555 0001",
        "onboarding_status": "pending_review",
    }, current_user=current_user)
    
    # Create a claim for this provider
    patient = self._create_test_patient(current_user)
    claim = platform_api.create_claim({
        "patient_id": patient["id"],
        "provider_id": provider["id"],
        "service_date": "2024-01-15",
        "claim_amount": 1500.00,
        "member_number": "MEM123",
        "scheme_id": "SCHEME001",
    }, current_user=current_user)
    
    # Get claim and verify onboarding blockers
    retrieved = platform_api.get_claim(claim["id"], current_user=current_user)
    self.assertTrue(len(retrieved.get("onboarding_blockers", [])) > 0)
    
    blockers = retrieved["onboarding_blockers"]
    self.assertTrue(any(b["type"] == "PROVIDER_ONBOARDING" for b in blockers))
```

**Verification:** Test passes and correctly identifies provider onboarding blockers.

---

## Phase 6: Integration Tests

### ✅ Task 6.1: Add multi-user realtime scenario test

**File:** `medhealth-ui/backend/tests/test_main_entrypoint_api.py`

**Location:** Add new test method after previous tests

```python
async def test_multi_user_claim_update_scenario(self) -> None:
    """Test multi-user scenario: user A closes claim, user B sees update via polling."""
    user_a = self._create_test_user(role="billing_team")
    user_b = self._create_test_user(role="auditor")
    
    claim = self._create_test_claim(user_a)
    claim_id = claim["id"]
    
    # User B retrieves initial state
    initial_claim_b = platform_api.get_claim(claim_id, current_user=user_b)
    self.assertEqual(initial_claim_b["status"], "DRAFT")
    
    # User A closes the claim
    platform_api.close_claim(claim_id, current_user=user_a)
    
    # User B retrieves updated state
    updated_claim_b = platform_api.get_claim(claim_id, current_user=user_b)
    self.assertEqual(updated_claim_b["status"], "CLOSED")
    self.assertTrue(len(updated_claim_b.get("state_progression", [])) > 0)
```

**Verification:** Test passes and demonstrates state updates across users.

---

## Verification Checklist

- [ ] Backend syntax check: `python -B -c "import ast, pathlib; [ast.parse(path.read_text(encoding='utf-8')) for path in [pathlib.Path('medhealth-ui/backend/platform_core.py'), pathlib.Path('medhealth-ui/backend/platform_api.py')]]"`
- [ ] Run backend tests: `python -B -m unittest discover -s medhealth-ui/backend/tests -v`
- [ ] Frontend syntax check: `node --check medhealth-ui/js/app.js`
- [ ] Manual test: Open claim detail and verify workflow and onboarding panels render
- [ ] Realtime test: Open claim in two browsers and verify updates after workflow action
- [ ] Dashboard test: Verify worklist rows show onboarding badges and role status

---

## Deployment Checklist

1. Review all Phase 1-5 changes for correctness
2. Run all verification checks (pass required)
3. Deploy backend changes
4. Deploy frontend changes
5. Run integration tests in staging environment
6. Verify realtime updates work end-to-end
7. Document any configuration changes or known limitations

---

## Notes

- All code changes are designed to be backward compatible
- Existing API responses retain all previous fields
- New fields are additive and do not break existing clients
- Onboarding integration uses existing provider/practice onboarding_status field
- WebSocket broadcast is fire-and-forget; failed sends are logged but don't block workflow
