# Operations Notes

## System design issues identified

1. Schema drift risk
   The original backend used `Base.metadata.create_all()` at startup. That is convenient for a prototype, but it is unsafe once real fee data exists because schema changes can drift across environments and cannot be reviewed or rolled back cleanly.

2. Heavy search payloads
   The original student search API returned full fee summaries and payment history for every result row. That scales poorly and makes the UI slower as records grow.

3. Concurrent payment race
   Payment validation originally happened only at the API layer without locking the student record. Two admins recording payments at the same time could over-allocate the same fee component.

4. Weak audit trail for receipts
   Payments had timestamps and notes, but no formal receipt number to reference offline entries.

5. Health endpoint did not verify the database
   The previous `/health` response could stay green even if PostgreSQL connectivity had failed.

6. Fee edits could invalidate paid balances
   The original update flow allowed a student fee setup to be reduced below money already collected, which would make balances inconsistent and hide an accounting error.

7. Long-running backend connections could go stale
   With a small internal deployment, the app may sit idle for long periods. Without connection health checks, the first request after a database restart can fail because the pool still holds dead connections.

8. Duplicate student Aadhaar numbers were possible
   The earlier schema allowed the same student Aadhaar number to be reused across multiple records, which would undermine identity integrity and make student records ambiguous.

## What is fixed in this codebase

- Alembic migrations are now part of the project startup flow.
- Student search returns lightweight list items; full payment history loads only for the selected student.
- Payment recording now locks the student row before validating and writing allocations.
- Each payment receives a receipt number in the format `SSHS-YYYY-000001`.
- The health endpoint now verifies database connectivity with `SELECT 1`.
- Student fee edits are blocked if they would reduce any component below the amount already received.
- PostgreSQL check constraints now enforce non-negative fee values and keep transport concession within the transport fee.
- SQLAlchemy now uses `pool_pre_ping`, so stale database connections are recycled instead of causing avoidable request failures.
- Student Aadhaar numbers are now normalized, legacy invalid values are cleared during migration, and duplicates are blocked at both the API and database layers.
- The selected student can now produce a PDF fee statement showing component-wise paid amounts, balances, and totals.

## Database failure strategy

### 1. Use migrations

Yes. Use Alembic migrations for every schema change.

Why:

- schema changes become explicit and reviewable
- production and local databases stay consistent
- roll-forward and recovery steps become predictable

Run manually if needed:

```powershell
cd backend
.\.venv\Scripts\python -m alembic upgrade head
```

### 2. Do not use triggers for backups

No. Database triggers are not the right mechanism for nightly backups.

Why not:

- triggers run inside transactions, not on schedules
- they increase write-path complexity
- they are the wrong tool for filesystem-level backups

Use scheduled external backups instead.

### 3. Use nightly `pg_dump`

Recommended baseline for this school portal:

- run `backup.ps1` every night using Windows Task Scheduler
- keep at least 14 days of backups
- copy backups to another machine, external drive, or cloud folder

Manual backup:

```powershell
.\backup.ps1
```

### 4. If the school needs stronger recovery guarantees

If losing even one day of payments is unacceptable, add:

- PostgreSQL WAL archiving
- point-in-time recovery
- a tested restore process on another machine

That is better than relying only on nightly dumps.

### 5. Test restores regularly

Backups are only useful if restore works. At least once a month:

1. create a fresh test database
2. restore the latest dump
3. verify login, student search, balances, and payment history

## Remaining recommendations

- Encrypt or tokenize Aadhaar values at rest if this is going beyond a small internal deployment.
- Store backups off the same PC so disk failure or ransomware does not destroy both the live DB and the backups.
- Add a separate audit log table if future requirements include payment edits, reversals, or deletion tracking.
