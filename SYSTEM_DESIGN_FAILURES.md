# System Design Failure Cases

This project is a small FastAPI backend, so the highest-risk failures are data-integrity and trust-boundary failures around fee balances and payments.

## Fixed in Code

- Concurrent or repeated payments could overpay a fee head because outstanding balance was checked before insert without serializing payment writes. Payment creation and financial updates now lock the student row where supported and re-check outstanding balance inside the transaction.
- Parent online payments were immediately marked as successful, which allowed a parent token to fake a paid invoice. Parent payment creation now produces a pending payment intent; only the admin confirmation endpoint can convert it to a successful payment after gateway verification.
- Duplicate receipt or gateway payment identifiers could raise raw database errors or create retry ambiguity. Payment writes now catch integrity conflicts and return HTTP 409, and gateway order/payment ids are unique.
- Fee structure reductions and concessions could create negative balances after payments were already recorded. Fee and concession updates are now validated against existing successful payments and concessions before commit.
- Invalid currency precision and inconsistent academic-year strings could create duplicate records or rounded financial values. Schemas now normalize academic years and reject amounts with more than two decimal places.
- Auth endpoints allowed unlimited login/parent-access guesses. A Redis-backed failed-attempt limiter now returns HTTP 429 after repeated failures and shares counters across API instances.
- Health checks could report healthy even when the database was unavailable. `/health` now verifies database connectivity.
- Database startup used automatic ORM table creation. Startup and `python -m app.db.init_db` now apply versioned migrations from `app/db/migrations.py`.
- Aadhaar values were stored in plaintext. Student registration and parent verification now store and compare keyed HMAC tokens instead of full Aadhaar numbers.
- Admin and payment mutations had limited traceability. Admin student, fee, concession, and payment status changes now write durable sanitized rows to `audit_logs`.

## Remaining Production Considerations

- Online payment confirmation still needs real gateway signature/webhook verification before production use.
- Production should run Redis as shared managed infrastructure or move the same rate-limit policy to an API gateway or WAF.
- `AADHAAR_TOKEN_KEY` must be backed up and managed carefully. Changing it invalidates existing Aadhaar verification tokens unless a controlled re-tokenization plan exists.
