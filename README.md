## School Fee Portal (FastAPI)

### Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Set your database URL (PostgreSQL recommended):

```powershell
$env:DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/school_fee"
```

Set JWT secret (important):

```powershell
$env:SECRET_KEY="change-this-to-a-long-random-secret"
```

Set an Aadhaar token key. Keep this stable, because existing Aadhaar tokens cannot be matched if it changes:

```powershell
$env:AADHAAR_TOKEN_KEY="change-this-to-a-long-random-value"
```

Set Redis for shared login and parent-access rate limiting:

```powershell
$env:REDIS_URL="redis://localhost:6379/0"
```

Apply database migrations:

```bash
python -m app.db.init_db
```

Seed demo data (admin + 1 student):

```bash
python -m app.scripts.seed_demo
```

Seeded demo access:

- Admin: `admin@school.com` / `Admin@12345`
- Parent verification:
  - Roll number: `S0001`
  - Date of birth: `2010-05-15`
  - Aadhaar number: `123412341234`

Run the API:

```bash
python -m uvicorn app.main:app --reload
```

The app also applies pending database migrations on startup. It does not use ORM `create_all` table creation.

### Authentication

- **Admin login**: `POST /auth/login` (OAuth2 password flow)
  - username = email
  - password = password
- **Parent access**: `POST /auth/parent-access`
  - JSON body:

```json
{
  "roll_number": "S0001",
  "date_of_birth": "2010-05-15",
  "aadhaar_number": "123412341234"
}
```

- **Admin token payload**: `{ user_id, email, role, exp }`
- **Parent token payload**: `{ role, student_id, roll_number, exp }` (scoped to exactly 1 student)

You can authorize in Swagger UI at `/docs` using the returned bearer token.

### Main API flow

- `POST /admin/students`: school administration creates the student profile
- `POST /admin/fee-structure`: assign annual fee structure
- `POST /admin/concessions`: apply concessions if needed
- `POST /auth/parent-access`: parent verifies using child roll number, DOB, and Aadhaar
- `GET /parent/fee-summary?academic_year=2024-2025`: parent checks dues
- `POST /parent/pay-online`: parent creates a pending online payment intent
- `POST /admin/payments/online/{payment_id}/confirm`: admin/gateway-confirmed online payment becomes successful and receives invoice data
- `GET /parent/invoices/{payment_id}`: fetch invoice after the payment is successful
- `POST /admin/payments/offline`: admin records an offline payment and receives invoice data

Online parent payments are intentionally not marked successful at creation time. A pending online payment must be confirmed through the admin confirmation endpoint after external gateway verification.

### Schemas (ORM models)

The database schemas you provided are implemented in:

- `app/db/models.py`

Runtime schema changes are implemented as versioned migrations in:

- `app/db/migrations.py`

