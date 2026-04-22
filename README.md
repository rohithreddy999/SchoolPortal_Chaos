# School Fee Portal

Full-stack school administration portal built with FastAPI, PostgreSQL, and React.

## What it does

- Username/password login for a small admin team
- Create and edit student records by academic year
- Store fee setup for admission, term fees, transport, books, and transport concession
- Search students by admission number, academic year, student name, or class
- Record offline payments against one or more fee components
- Automatically calculate paid totals, component balances, adjusted total, and pending balance
- Generate a PDF fee statement for the selected student showing paid and pending components
- Prevent duplicate student Aadhaar records across the database

## Project structure

- `backend/` FastAPI API, authentication, PostgreSQL models, and fee calculation logic
- `frontend/` React app for login, student entry, search, and payment updates
- `docker-compose.yml` local PostgreSQL database

## Backend setup

1. Copy `backend/.env.example` to `backend/.env`
2. Create and activate a virtual environment inside `backend/`
3. Install dependencies:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

4. Start PostgreSQL:

```powershell
cd ..
docker compose up -d
```

5. Apply database migrations:

```powershell
cd backend
.\.venv\Scripts\python -m alembic upgrade head
```

6. Start the API:

```powershell
cd backend
uvicorn app.main:app --reload
```

The backend expects Alembic migrations to be applied and then seeds a default admin user from the environment variables.

Default login from `.env.example`:

- Username: `admin`
- Password: `admin123`

## Frontend setup

1. Copy `frontend/.env.example` to `frontend/.env`
2. Install dependencies and start the React app:

```powershell
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173` and calls the backend at `http://localhost:8000/api` by default.

Note: this project maps PostgreSQL to host port `5433` to avoid conflicts with an existing local PostgreSQL service on `5432`.

## Main workflow

1. Log in as admin
2. Create a student record with academic year, class/section, IDs, and fee amounts
3. Search the student later using admission number and academic year
4. Enter offline payments for one or more fee components
5. Review updated balances and payment history immediately after each entry

## One-command start and stop

From the project root:

```powershell
.\start.ps1
```

That script will:

- create missing `.env` files from the examples
- create the backend virtual environment if needed
- install backend packages again only when `backend/requirements.txt` changes
- install frontend packages if needed
- start the project PostgreSQL cluster on port `5433`
- apply Alembic migrations automatically
- open separate PowerShell windows for the backend and frontend

To stop everything:

```powershell
.\stop.ps1
```

## Backups

Create a PostgreSQL backup:

```powershell
.\backup.ps1
```

This creates a timestamped dump in `backups/` and removes old dumps beyond the retention window.

For operational guidance on migrations, recovery, and backup strategy, see `OPERATIONS.md`.

## Migration workflow

Create a new migration after model changes:

```powershell
cd backend
.\.venv\Scripts\python -m alembic revision --autogenerate -m "describe change"
```

Apply all pending migrations:

```powershell
cd backend
.\.venv\Scripts\python -m alembic upgrade head
```

Show the currently applied revision:

```powershell
cd backend
.\.venv\Scripts\python -m alembic current
```
