# Money & Rounding Policy (Appendix C)

## Column Type
- **DB:** `BIGINT NOT NULL` named `*_cents`
- **Python:** `int`
- **API serialization:** `cents_to_str(cents: int) -> str` — e.g. `17300` → `"173.00"`
- **Display (ZAR):** `R1 730.00` with thousands separator

## Rounding
- Method: `ROUND_HALF_EVEN` (banker's rounding) at the **line-item level**
- Total rule: `total_cents = sum(line.rounded_cents for line in lines)` — **NOT** `round(sum(raw_line_values))`
- Python: use `Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)`

## Serialization
```python
def cents_to_str(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    abs_cents = abs(cents)
    return f"{sign}{abs_cents // 100}.{abs_cents % 100:02d}"
```

## Anti-patterns
| ❌ Wrong | ✅ Right |
|---|---|
| `FLOAT`, `DOUBLE`, `NUMERIC` without scale | `BIGINT` cents |
| `round(sum(raw_lines), 2)` | `sum(round_half_even_cents(line) for line in lines)` |
| String-decimal arithmetic | Convert to int cents, compute, serialize back |
| `member_liability = claimed - allowed` (floats) | `liability = max(0, claimed_cents - allowed_cents)` |

## Member Liability
```python
member_liability_cents = max(0, claimed_total_cents - scheme_allowed_cents)
```
- Never negative
- If `scheme_allowed_cents > claimed_total_cents` → excess becomes `patient_balances.credit_cents`
- No invoice created when `member_liability_cents == 0`
