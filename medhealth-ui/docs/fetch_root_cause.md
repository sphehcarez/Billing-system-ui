# Root Cause: Failed to Fetch Issues

Date: `2026-04-17`

## Executive Summary

"Failed to fetch" errors in the UI occur when the frontend cannot reach the backend API. The root causes involve:
1. Hard-coded localhost URLs without fallback
2. Mixed-origin requests (UI on :8000, API on :8001) without CORS
3. No health check or connection status indicator
4. Missing error context in toast notifications

## Issue Analysis

### Hard-Coded API URLs

**File:** `js/api-client.js`
**Current State:**
```javascript
const API_BASE = "http://localhost:8001";
```

**Problem:**
- Assumes backend always runs on :8001
- No environment variable fallback
- No protocol detection (http vs https)
- No same-origin option for alternative deployment

### CORS Configuration

**File:** `backend/platform_api.py`
**Current State:**
- No CORS middleware configured
- Backend serves JSON API only
- Frontend on :8000, backend on :8001 = cross-origin

**Problem:**
- When UI dev server runs on :8000 and backend on :8001, browser blocks requests
- No `Access-Control-Allow-Origin` header
- No preflight request handling for POST/PUT/DELETE

### Missing Health Endpoint

**File:** `backend/platform_api.py`
**Current State:**
- Root endpoint exists: `GET /` returns JSON
- No dedicated `/health` endpoint
- No health status indicator in UI

**Problem:**
- Cannot ping API without authenticated request
- UI cannot detect API status without attempting real operation
- No way to show "API unreachable" indicator before user action

### Error Context Loss

**File:** `js/api-client.js`
**Current State:**
```javascript
catch (error) {
  throw { code: "NETWORK_ERROR", message: "Failed to fetch", ... };
}
```

**Problem:**
- Generic "Failed to fetch" does not distinguish between:
  - Network timeout
  - Connection refused (API not running)
  - CORS blocked request
  - HTTP 500 error from API
  - Malformed response
- User left guessing what went wrong

## Reproduction Scenario

**Setup:**
1. UI running on `http://localhost:8000`
2. Backend not running or running on different port
3. User clicks "Run readiness" on claim detail

**Outcome:**
```
Browser console:
  TypeError: Failed to fetch

UI toast:
  "Unable to run readiness. Check the backend on :8001 and try again."

But user has no way to verify if backend is actually running
```

## Fix Strategy

### Option A: Same-Origin (Recommended for Simple Deployments)

**Approach:** Serve UI from backend on `/` and API on `/api`

**Changes:**
1. Update `backend/main.py` to mount static files
2. Update `docker-compose.yml` to remove separate frontend service
3. Set UI `API_BASE = "/api"` (relative path)

**Pros:**
- No CORS complexity
- Works in all deployment models
- Single service to monitor

**Cons:**
- Couples UI build to backend release
- Backend must serve static files

### Option B: CORS + Health Endpoint (Recommended for Microservices)

**Approach:** Enable CORS on backend, add `/health` endpoint

**Changes:**
1. Add FastAPI CORS middleware
2. Add `GET /health` endpoint
3. Add connection status pill in top bar
4. Update `API_BASE` environment variable handling

**Pros:**
- Decouples UI and backend
- Allows different deployment lifecycle
- Health endpoint enables monitoring
- Flexible cross-origin requests

**Cons:**
- Browser CORS restrictions still apply in dev
- More configuration needed

### Selected Approach: **Hybrid**

For this phase:
- **Production:** Same-origin (Option A) - simplest, most robust
- **Development:** CORS + Health (Option B) - allows independent servers
- **Fallback:** Auto-detect API base from `window.location`

**Implementation:**
```javascript
// In js/api-client.js
const API_BASE = 
  process.env.REACT_APP_API_BASE ||  // env override
  "/api" ||                           // same-origin default
  "http://localhost:8001";            // dev fallback
```

## HTTP Status Indicator

**Location:** Top navigation bar

**States:**
- 🟢 **API OK** (green pill) - `/health` responded 200
- 🟡 **Checking** (yellow spinner) - request in flight
- 🔴 **API Down** (red pill) - `/health` failed or timed out
- ⚫ **Unknown** (gray pill) - not yet checked

**Behavior:**
- Ping every 30 seconds
- Hide after 2 failed attempts (reduce noise)
- Click to manually re-check
- Show last check time in tooltip

## Enhanced Error Messages

**Update `js/api-client.js` formatErrorMessage():**

```javascript
function formatErrorMessage(error, attemptedAction = "request") {
  if (!error) return `Unable to ${attemptedAction}.`;
  
  if (error.code === "NETWORK_ERROR") {
    return `Cannot reach the API. Check backend on :8001. Error: ${error.message}`;
  }
  if (error.status === 0) {
    return `API connection refused. Is the backend running on :8001?`;
  }
  if (error.status === 403) {
    return `Request blocked by CORS policy. Check browser console for details.`;
  }
  if (error.status === 500) {
    return `API error: ${error.message}. Check backend logs.`;
  }
  if (error.status === 401) {
    return `Session expired. Please log in again.`;
  }
  
  return `${attemptedAction} failed: ${error.message}`;
}
```

## CORS Configuration (Fallback)

**Update `backend/platform_api.py`:**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://localhost:3000"],  # dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    db_health = database_healthcheck()
    return {"status": "ok", "db": db_health.get("db", "unknown")}
```

## Deployment Scenarios

### Scenario 1: Docker Compose (Single Service)
```
Frontend → http://localhost:8000 (served by backend)
Backend API → http://localhost:8001/api (same service)
API_BASE → "/api"
Result: No CORS issues ✓
```

### Scenario 2: Development (Separate Services)
```
Frontend → http://localhost:8000 (http.server)
Backend API → http://localhost:8001 (uvicorn)
API_BASE → "http://localhost:8001" (or CORS + same-origin fallback)
Result: Works with CORS enabled ✓
```

### Scenario 3: Production (Nginx Reverse Proxy)
```
UI + API → https://medhealth.example.com
Nginx routes:
  /       → frontend (static)
  /api/*  → backend (reverse proxy to localhost:8001)
API_BASE → "/api"
Result: Single origin, no CORS needed ✓
```

## Testing Checklist

- [ ] Start backend on :8001
- [ ] Start UI on :8000
- [ ] Click any API-calling action
- [ ] Should succeed without CORS errors
- [ ] Stop backend
- [ ] Click action again
- [ ] Toast should show "Cannot reach API on :8001"
- [ ] Top bar pill should turn red
- [ ] Restart backend
- [ ] Pill should turn green automatically (within 30s)

## Files to Update

1. `js/api-client.js` - API base URL detection, enhanced error messages
2. `js/app.js` - Health check component, connection status pill
3. `css/styles.css` - Health pill styling
4. `backend/platform_api.py` - Add /health endpoint, CORS middleware
5. `backend/docker-entrypoint.sh` - Frontend mounting (if Option A selected)
6. `docker-compose.yml` - Remove separate frontend service (if Option A selected)

## Status

✅ **Analysis complete**
⏳ **Implementation pending** - Start with Option B (CORS + Health), keep Option A as future refactor

