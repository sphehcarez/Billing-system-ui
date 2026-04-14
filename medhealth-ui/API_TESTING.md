# 📡 API Testing Guide - cURL Examples

## Quick Reference

### Base URL
```
http://localhost:8001/api
```

### Headers
```
Content-Type: application/json
Token: <your-jwt-token>
```

Or pass token as query parameter: `?token=<jwt-token>`

---

## 1. Authentication

### Login
```bash
curl -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "role": "Administrator"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "role": "Administrator"
}
```

**Store this token for subsequent requests:**
```bash
TOKEN="eyJhbGc..."
```

---

## 2. Patients

### List All Patients
```bash
curl -X GET "http://localhost:8001/api/patients?token=$TOKEN"
```

### Get Specific Patient
```bash
curl -X GET "http://localhost:8001/api/patients/1?token=$TOKEN"
```

### Create New Patient
```bash
curl -X POST "http://localhost:8001/api/patients?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "mrn": "MRN100",
    "dob": "1988-09-12",
    "email": "alice@example.com",
    "phone": "555-0100",
    "status": "active"
  }'
```

### Update Patient
```bash
curl -X PUT "http://localhost:8001/api/patients/1?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe Updated",
    "mrn": "MRN002",
    "dob": "1992-03-22",
    "email": "jane.new@example.com",
    "phone": "555-0002",
    "status": "active"
  }'
```

### Delete Patient
```bash
curl -X DELETE "http://localhost:8001/api/patients/1?token=$TOKEN"
```

---

## 3. Providers

### List All Providers
```bash
curl -X GET "http://localhost:8001/api/providers?token=$TOKEN"
```

### Get Specific Provider
```bash
curl -X GET "http://localhost:8001/api/providers/1?token=$TOKEN"
```

### Create New Provider
```bash
curl -X POST "http://localhost:8001/api/providers?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Emily Brown",
    "npi": "NPI100",
    "specialty": "Pediatrics",
    "email": "emily@example.com",
    "phone": "555-2001",
    "status": "active"
  }'
```

### Update Provider
```bash
curl -X PUT "http://localhost:8001/api/providers/1?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Robert Johnson Updated",
    "npi": "NPI001",
    "specialty": "Internal Medicine",
    "email": "robert.new@example.com",
    "phone": "555-1001",
    "status": "active"
  }'
```

---

## 4. Claims

### List All Claims
```bash
curl -X GET "http://localhost:8001/api/claims?token=$TOKEN"
```

### Get Specific Claim
```bash
curl -X GET "http://localhost:8001/api/claims/1?token=$TOKEN"
```

### Create New Claim
```bash
curl -X POST "http://localhost:8001/api/claims?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_number": "CLM100",
    "patient_id": 1,
    "provider_id": 1,
    "amount": 2500.50,
    "status": "open",
    "readiness_status": "pending"
  }'
```

### Update Claim
```bash
curl -X PUT "http://localhost:8001/api/claims/1?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_number": "CLM001",
    "patient_id": 1,
    "provider_id": 1,
    "amount": 1600.00,
    "status": "open",
    "readiness_status": "pending"
  }'
```

### Run Readiness Check
```bash
curl -X POST "http://localhost:8001/api/claims/1/readiness?token=$TOKEN"
```

**Response:**
```json
{
  "claim_id": 1,
  "status": "validated",
  "message": "Readiness check passed"
}
```

### Close Claim
```bash
curl -X POST "http://localhost:8001/api/claims/1/close?token=$TOKEN"
```

**Response:**
```json
{
  "claim_id": 1,
  "status": "closed",
  "message": "Claim closed successfully"
}
```

### Post-Closure Validation
```bash
curl -X POST "http://localhost:8001/api/claims/1/validate?token=$TOKEN"
```

**Response:**
```json
{
  "claim_id": 1,
  "validation_status": "valid",
  "message": "Post-closure validation passed"
}
```

---

## 5. Payments

### List All Payments
```bash
curl -X GET "http://localhost:8001/api/payments?token=$TOKEN"
```

### Get Specific Payment
```bash
curl -X GET "http://localhost:8001/api/payments/1?token=$TOKEN"
```

### Create New Payment
```bash
curl -X POST "http://localhost:8001/api/payments?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_id": 1,
    "amount": 1500.00,
    "payment_date": "2024-01-20",
    "method": "ACH",
    "status": "pending"
  }'
```

---

## 6. Users

### List All Users
```bash
curl -X GET "http://localhost:8001/api/users?token=$TOKEN"
```

### Create New User
```bash
curl -X POST "http://localhost:8001/api/users?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "role": "Billing Specialist",
    "status": "active"
  }'
```

---

## 7. Reports

### List All Reports
```bash
curl -X GET "http://localhost:8001/api/reports?token=$TOKEN"
```

### Generate New Report
```bash
curl -X POST "http://localhost:8001/api/reports/generate?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "claims_summary",
    "period": "Q1 2024"
  }'
```

---

## 8. Audit Logs

### Get Audit Logs
```bash
curl -X GET "http://localhost:8001/api/audit-logs?token=$TOKEN"
```

---

## 9. Settings

### Get System Settings
```bash
curl -X GET "http://localhost:8001/api/settings?token=$TOKEN"
```

### Update Settings
```bash
curl -X PUT "http://localhost:8001/api/settings?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "api_version": "1.0.0",
    "demo_mode": true,
    "rbac_enabled": true
  }'
```

---

## 10. API Documentation

### Get API Info
```bash
curl -X GET "http://localhost:8001/api/docs"
```

### Health Check
```bash
curl -X GET "http://localhost:8001/"
```

---

## Complete Workflow Example

```bash
#!/bin/bash

# 1. Login
RESPONSE=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123",
    "role": "Administrator"
  }')

TOKEN=$(echo $RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Token: $TOKEN"

# 2. List patients
echo "Getting patients..."
curl -X GET "http://localhost:8001/api/patients?token=$TOKEN" | jq .

# 3. Create new claim
echo "Creating claim..."
CLAIM=$(curl -s -X POST "http://localhost:8001/api/claims?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_number": "CLM999",
    "patient_id": 1,
    "provider_id": 1,
    "amount": 3000.00,
    "status": "open",
    "readiness_status": "pending"
  }')

CLAIM_ID=$(echo $CLAIM | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
echo "Created claim ID: $CLAIM_ID"

# 4. Run readiness check
echo "Running readiness check..."
curl -s -X POST "http://localhost:8001/api/claims/$CLAIM_ID/readiness?token=$TOKEN" | jq .

# 5. Close claim
echo "Closing claim..."
curl -s -X POST "http://localhost:8001/api/claims/$CLAIM_ID/close?token=$TOKEN" | jq .

# 6. Validate closure
echo "Validating closure..."
curl -s -X POST "http://localhost:8001/api/claims/$CLAIM_ID/validate?token=$TOKEN" | jq .

# 7. Get audit logs
echo "Getting audit logs..."
curl -s -X GET "http://localhost:8001/api/audit-logs?token=$TOKEN" | jq .
```

---

## Testing Tools

### Postman
1. Import Collection: Use these curl examples to create requests in Postman
2. Environment: Add variables for `$TOKEN` and `BASE_URL`
3. Pre-request Scripts: Auto-refresh token before each request

### Insomnia
1. File → New → Request Collection
2. Create folder for each module (Patients, Providers, Claims, etc.)
3. Add requests from examples above

### Browser DevTools
```javascript
// In browser console
const token = '<your-token>';
fetch('http://localhost:8001/api/patients?token=' + token)
  .then(r => r.json())
  .then(d => console.log(d))
```

### Python Requests
```python
import requests

TOKEN = 'eyJ0eXAi...'
HEADERS = {'Content-Type': 'application/json', 'Token': TOKEN}

# Get patients
resp = requests.get('http://localhost:8001/api/patients?token=' + TOKEN)
print(resp.json())

# Create claim
data = {
    'claim_number': 'CLM555',
    'patient_id': 1,
    'provider_id': 1,
    'amount': 2000.00
}
resp = requests.post('http://localhost:8001/api/claims?token=' + TOKEN,
                     json=data, headers=HEADERS)
print(resp.json())
```

---

## Error Responses

### 401 Unauthorized
```json
{"detail": "Invalid token"}
{"detail": "Token expired"}
{"detail": "Authorization token missing"}
```

### 404 Not Found
```json
{"detail": "Patient not found"}
{"detail": "Claim not found"}
```

### 400 Bad Request
```json
{"detail": [
  {
    "loc": ["body", "name"],
    "msg": "field required",
    "type": "value_error.missing"
  }
]}
```

---

## Tips

✅ **Always save the token** from login response  
✅ **Token expires in 30 minutes** - login again if requests fail  
✅ **Use jq tool** for pretty-printing JSON: `| jq .`  
✅ **Test in Swagger UI** first at http://localhost:8001/docs  
✅ **Check audit logs** to verify actions were recorded  
✅ **Read full docs** at http://localhost:8001/api/docs  

---

## Quick Token Extraction

### Save token to file
```bash
TOKEN=$(curl -s -X POST "http://localhost:8001/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123","role":"Administrator"}' | jq -r '.access_token')

echo $TOKEN > token.txt
source token.txt
```

### Reuse token in multiple requests
```bash
curl -X GET "http://localhost:8001/api/patients?token=$TOKEN"
curl -X GET "http://localhost:8001/api/providers?token=$TOKEN"
curl -X GET "http://localhost:8001/api/claims?token=$TOKEN"
```

---

**Ready to test the API!** 🚀
