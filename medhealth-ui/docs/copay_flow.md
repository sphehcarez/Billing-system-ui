# Co-pay Flow — End-to-End Sequence (Appendix D)

## Mermaid Sequence Diagram

```mermaid
sequenceDiagram
    participant Scheme as Scheme / Payer
    participant API as Backend API
    participant DB as PostgreSQL
    participant Outbox as Outbox Worker
    participant Patient as Patient Portal

    Scheme->>API: POST /claims/{id}/remittance<br/>{paid_cents, adjustments}
    API->>DB: BEGIN TRANSACTION
    DB-->>API: 
    API->>DB: INSERT reconciliations<br/>(claim_id UNIQUE)
    Note over API,DB: If duplicate claim_id → UNIQUE violation → 409
    API->>API: member_liability_cents = max(0, claimed - paid - adjustments)
    alt liability > 0
        API->>DB: INSERT invoices (UNIQUE claim_id)
        API->>DB: INSERT copay_items (reason_codes)
        API->>DB: UPDATE patient_balances<br/>SET balance_cents += liability
        API->>DB: INSERT outbox_events<br/>{type: COPAY_INVOICE_CREATED}
    else scheme overpaid
        API->>DB: UPDATE patient_balances<br/>SET credit_cents += overpay
        API->>DB: INSERT outbox_events<br/>{type: COPAY_CREDIT_APPLIED}
    end
    API->>DB: COMMIT
    DB-->>API: OK
    API-->>Scheme: 200 {invoice_id, member_liability_cents}

    Outbox->>DB: SELECT * FROM outbox_events WHERE emitted_at IS NULL
    DB-->>Outbox: [events]
    Outbox->>Outbox: emit webhook (retry on fail)
    Outbox->>DB: UPDATE outbox_events SET emitted_at = NOW()

    Patient->>API: GET /patients/{id}/balances
    API-->>Patient: {balance_cents, credit_cents}

    Patient->>API: POST /patients/{id}/payments<br/>Idempotency-Key: <uuid4><br/>{amount_cents, method}
    API->>DB: SELECT idempotency_keys WHERE key = ?
    alt Key exists, same body
        DB-->>API: stored response
        API-->>Patient: 200 (idempotent)
    else Key exists, different body
        API-->>Patient: 422 IDEMPOTENCY_KEY_REUSED
    else New key
        API->>DB: BEGIN TRANSACTION
        API->>DB: INSERT payments
        API->>DB: FIFO allocate across OPEN/PARTIAL invoices
        API->>DB: UPDATE invoices.paid_cents, status
        API->>DB: UPDATE patient_balances.balance_cents (decrement)
        API->>DB: INSERT outbox_events {COPAY_PAYMENT_RECEIVED}
        API->>DB: INSERT idempotency_keys
        API->>DB: COMMIT
        API-->>Patient: 200 {payment_id, status: SUCCESS}
    end
```

## Narrative

### Step 1: Remittance Received
The payer/scheme posts the remittance advice. `ReconciliationService.apply_remittance()` runs inside a single transaction. A `UNIQUE` constraint on `reconciliations.claim_id` prevents double-processing.

### Step 2: Liability Computed
`member_liability_cents = max(0, claimed_total_cents - paid_cents - adjustment_cents)`. Pure integer arithmetic — no floats.

### Step 3: Invoice Created (if liability > 0)
One `invoices` row per claim (enforced by `UNIQUE(invoices.claim_id)`). `copay_items` rows carry the reason codes (e.g. `TARIFF_DIFFERENCE`, `OUT_OF_NETWORK_SHORTFALL`). `patient_balances.balance_cents` is incremented atomically.

### Step 4: Outbox Event Emitted
An `outbox_events` row is written inside the same transaction. The worker picks it up asynchronously — webhook failures never roll back the invoice.

### Step 5: Patient Pays
`POST /patients/{id}/payments` requires an `Idempotency-Key` UUID. The service allocates payment FIFO across open invoices, updates invoice status (`PARTIAL` → `PAID`), decrements balance. Any overpayment becomes `credit_cents`. Repeated requests with the same key return the original response.

## Reversal
`ReconciliationService.reverse(claim_id)` voids the invoice, restores the balance, and emits `COPAY_INVOICE_VOIDED`. Payments already applied remain and become credit.
