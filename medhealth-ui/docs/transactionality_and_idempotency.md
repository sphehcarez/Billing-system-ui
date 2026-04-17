# Transactionality & Idempotency Policy (Appendix D)

## Transaction Boundary

`ReconciliationService.apply_remittance(claim_id, remittance)` runs in **one DB transaction**:

```
BEGIN;
  INSERT INTO reconciliations ...
  IF member_liability_cents > 0:
    INSERT INTO invoices (UNIQUE claim_id — concurrent duplicate → 409)
    INSERT INTO copay_items ...
    UPDATE patient_balances SET balance_cents += member_liability_cents
  ELSE IF paid > claimed:
    UPDATE patient_balances SET credit_cents += (paid - claimed)
  INSERT INTO outbox_events (type=COPAY_INVOICE_CREATED, emitted_at=NULL)
COMMIT;
```

**Audit events go to `outbox_events` only.** A background worker polls `WHERE emitted_at IS NULL`, fires the webhook, then sets `emitted_at`. Webhook failures never roll back the money transaction.

## Concurrency Safety
- `UNIQUE(invoices.claim_id)` — two concurrent remittances for the same claim: exactly one succeeds, the other gets a unique-constraint violation → 409 response.
- Isolation: `READ COMMITTED` (Postgres default) + unique constraints for correctness.

## Idempotency — `POST /patients/{id}/payments`

**Client** must send: `Idempotency-Key: <uuid-v4>`

**Server behavior:**

| Scenario | Response |
|---|---|
| Key not seen before | Process payment, store `(key, body_hash, response_json)`, return 200 |
| Same key + same body | Return stored response, HTTP 200, **no re-processing** |
| Same key + different body | Return HTTP 422 `{"error": "IDEMPOTENCY_KEY_REUSED"}` |

**Storage:** `idempotency_keys` table. Keys purged after 24h by nightly job.

```python
# Server-side check
body_hash = sha256(json.dumps(body, sort_keys=True)).hexdigest()[:16]
stored = db.query("SELECT * FROM idempotency_keys WHERE idempotency_key = %s", [key])
if stored:
    if stored.body_hash != body_hash:
        raise HTTP422("IDEMPOTENCY_KEY_REUSED")
    return json.loads(stored.response_json)
# ... process payment ...
db.insert("idempotency_keys", {key, body_hash, json.dumps(response), now})
```

## Reversal Path
`ReconciliationService.reverse(claim_id)`:
1. Mark `invoices.status = 'VOIDED'`
2. Restore `patient_balances.balance_cents -= invoice.total_cents` (but `>= 0`)
3. Payments already applied remain; excess becomes `credit_cents`
4. Emit outbox event `COPAY_INVOICE_VOIDED`

## Outbox Worker (jobs.py / Celery)
```python
# Poll every 30s
events = db.query("SELECT * FROM outbox_events WHERE emitted_at IS NULL ORDER BY id LIMIT 50")
for event in events:
    try:
        emit_webhook(event)
        db.execute("UPDATE outbox_events SET emitted_at = NOW() WHERE id = %s", [event.id])
    except Exception:
        # Retry later — exponential backoff via Celery retry
        pass
```
