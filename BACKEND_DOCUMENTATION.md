# Backend Documentation

## What This Backend Does

This backend powers a school fee portal. It lets the school administration manage student fee records and lets parents safely check and pay fees for their own child.

The backend supports two main users:

- School administrators, who can create student records, assign yearly fees, apply concessions, record offline payments, and confirm online payments.
- Parents, who can verify themselves using a student's roll number, date of birth, and Aadhaar number, then view fee details, start online payments, see payment history, and download invoices for successful payments.

The backend is built with FastAPI and stores data using SQLAlchemy models. It can use PostgreSQL in a normal deployment and SQLite for local/demo use.

## Main Business Flow

1. The admin creates a student profile.
2. The admin assigns the student's fee structure for an academic year.
3. The admin can apply concessions, such as transport concession or other general concession.
4. A parent verifies access using the child's roll number, date of birth, and Aadhaar number.
5. The parent views the fee summary for an academic year.
6. The parent can create an online payment request.
7. The online payment stays pending until it is confirmed by the admin or payment-verification side.
8. Once payment is successful, the system generates invoice details.
9. Admins can also directly record offline payments such as cash, cheque, bank transfer, or offline collection.

## System Design Challenges Solved

### Safe Parent Access

The system does not require a permanent parent account for basic parent access. Instead, the parent proves access using student-specific information. After verification, the backend gives a token that is limited to exactly one student.

This solves an important access-control problem: a parent cannot use their token to view or pay fees for another student.

### Separation Between Parent Actions and Payment Success

A parent can start an online payment, but the backend does not immediately treat that payment as successful. The payment is first stored as pending.

Only the confirmation flow can mark that payment as successful. This avoids a serious trust issue where a parent could create a payment record and instantly receive a paid invoice without real gateway confirmation.

### Preventing Overpayment During Concurrent Requests

The backend checks outstanding balances before recording payments. It also locks the student/payment-related data during critical payment operations and re-checks the balance inside the transaction.

This helps prevent cases where two payment requests happen at the same time and both appear valid individually, but together exceed the actual outstanding fee.

### Protecting Fee Balances From Bad Updates

The system prevents admins from reducing fee structures or increasing concessions in a way that would make existing successful payments invalid.

For example, if a student has already paid a fee head, the assigned fee cannot later be reduced below the amount already paid. Similarly, concessions cannot exceed the actual remaining payable amount.

### Avoiding Duplicate Payment Records

Receipt numbers, online order identifiers, and gateway payment identifiers are treated as unique. If the same identifier is reused, the backend returns a conflict instead of silently creating duplicate financial records.

This is important for retry scenarios, payment gateway callbacks, and manual admin entry.

### Consistent Validation

The backend normalizes and validates important values before saving them:

- Academic years must follow a single-year format such as 2024-2025.
- Money values must be valid currency amounts with no more than two decimal places.
- Fee heads must be from the allowed list.
- Online and offline payment modes are checked separately.
- Aadhaar and mobile fields are normalized to digits.

### Shared Brute-Force Protection

Login and parent-access attempts are rate-limited after repeated failures. This reduces repeated guessing of admin passwords or parent verification details.

The limiter uses Redis so failed attempts are shared across API processes and servers. If Redis is unavailable, authentication endpoints return HTTP 503 instead of silently bypassing the limiter.

### Versioned Database Migrations

The app applies versioned database migrations from `app/db/migrations.py` on startup and through `python -m app.db.init_db`. It does not use automatic ORM table creation.

### Aadhaar Tokenization

Aadhaar input is accepted only for verification and student registration. The database stores deterministic HMAC tokens, not full Aadhaar numbers. Parent access compares the provided Aadhaar number after tokenization.

### Audit Logging

Admin student, fee-structure, and concession changes are written to `audit_logs`. Payment status transitions are also logged, including pending online payment creation and successful payment confirmation or offline collection.

### Real Health Check

The health endpoint checks database connectivity before reporting the service as healthy. This is better than only checking whether the web server is running.

## Database Schema Design

The schema is centered around students, fee assignment, concessions, and payments.

### Users

The users table stores login users, mainly admins. Each user has an email, hashed password, role, and creation time.

Roles are restricted to known values such as admin and parent. In the current flow, admins use this table for login. Parent access is mostly handled through student verification rather than permanent parent login.

### Students

The students table stores the main student profile:

- Admission number
- Roll number or student identifier
- Student name
- Parent names
- Mobile number
- Class and section
- Date of birth
- Student Aadhaar token
- Father Aadhaar token

Admission number and roll number are unique so that the same student cannot be created twice under conflicting identities.

### Parents

The parents table can link a user to a student. It supports a many-parent or many-student style relationship, although the current API keeps parent access simple by using direct student verification.

The table prevents duplicate links between the same user and student.

### Fee Structure

The fee structure table stores the assigned fees for one student in one academic year.

It separates the total fee into heads:

- Admission fee
- Term 1 fee
- Term 2 fee
- Term 3 fee
- Transport fee
- Books fee

There can be only one fee structure per student per academic year. All fee amounts must be non-negative.

This design makes it easy to calculate fee summaries by head and also prevents duplicate yearly fee assignments for the same student.

### Concessions

The concessions table stores discounts or reductions for one student in one academic year.

It currently supports:

- Transport concession
- Other concession

There can be only one concession record per student per academic year. Concession amounts must be non-negative.

Keeping concessions separate from the original fee structure is useful because the school can preserve the assigned fee while also tracking reductions clearly.

### Payments

The payments table stores both online and offline payments.

Each payment belongs to a student and an academic year. It also stores:

- Fee head being paid
- Amount paid
- Payment date
- Payment mode
- Payment status
- Online order identifier
- Gateway payment identifier
- Receipt number
- Collected-by information
- Remarks

Payment status is limited to pending, success, or failed. Only successful payments are counted as paid in fee summaries and balances.

The table has indexes for student, year, status, and fee head. These support common queries such as fee summary calculation, payment history, and balance checks.

### Audit Logs

The audit logs table stores durable records of sensitive operations. Each row includes actor information, action name, entity type and id, request IP address, sanitized JSON details, and timestamp.

## API Design

The API is organized by user role and responsibility.

### Authentication APIs

POST /auth/login

Used by admins to log in with email and password. It returns a bearer token for admin-only endpoints.

POST /auth/parent-access

Used by parents to verify access using roll number, date of birth, and Aadhaar number. It returns a bearer token scoped to that specific student.

### Admin APIs

GET /admin/me

Confirms that the current token belongs to an admin.

POST /admin/students

Creates a student profile. The backend checks for duplicate admission numbers and roll numbers.

POST /admin/fee-structure

Creates or updates the fee structure for a student and academic year. The backend validates that changes do not conflict with existing payments or concessions.

POST /admin/concessions

Creates or updates concessions for a student and academic year. The backend ensures concessions do not exceed valid fee limits.

POST /admin/payments/offline

Records an offline payment and immediately returns invoice details if the payment is valid.

POST /admin/payments/online/{payment_id}/confirm

Confirms a pending online payment after payment verification. Once confirmed, the payment becomes successful and receives invoice details.

### Parent APIs

GET /parent/me

Returns the student profile attached to the parent token.

GET /parent/fee-summary

Returns assigned fees, concessions, successful payments, and remaining balance for the selected academic year.

POST /parent/pay-online

Creates a pending online payment request. This does not create a successful invoice by itself.

GET /parent/payments

Shows the payment history for the student attached to the parent token.

GET /parent/invoices/{payment_id}

Returns invoice details only for successful payments that belong to the current parent token's student.

### Health API

GET /health

Checks whether the backend is running and whether the database connection is available.

## Security and Data Integrity Design

The backend uses bearer tokens for authenticated access. Admin tokens identify the admin user. Parent tokens identify the student they are allowed to access.

Passwords are stored as hashes, not plain text. Aadhaar values are stored as keyed HMAC tokens, not recoverable full numbers.

Financial operations use validation, uniqueness rules, and transaction-level checks to avoid invalid balances, duplicate receipts, and accidental overpayment.

## Current Production Considerations

This backend is suitable as a strong demo or small internal system, but a production deployment should still improve a few areas:

- Add real payment gateway signature or webhook verification.
- Store `SECRET_KEY` and `AADHAAR_TOKEN_KEY` in a managed secret store and rotate them through an explicit operational plan.
- Run Redis as managed shared infrastructure or move rate limiting to a gateway/WAF with equivalent shared counters.
