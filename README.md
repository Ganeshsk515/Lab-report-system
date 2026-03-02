# Lab Report System

A Flask-based diagnostics/lab report management system with role-based access for admin, staff, and patients.

## Features

- Admin and staff login workflow
- Security-question second-step verification during login
- Patient portal activation (using Patient ID + registered email)
- Patient record management (create, edit, search, delete)
- Diagnostic report publishing and viewing
- Role-based access control:
  - `admin`: manage users, full patient/report access
  - `staff`: manage patients and reports
  - `patient`: view only own reports
- Automatic default admin bootstrap from environment variables
- Supabase/PostgreSQL-ready (with SQLite fallback for local quick start)

## Tech Stack

- Python 3.11
- Flask 3.1
- Flask-Login
- Flask-WTF
- Flask-SQLAlchemy
- Gunicorn
- PostgreSQL (containerized option)

## Project Structure

```text
lab_report_system/
|- app/
|  |- __init__.py        # App factory, DB init, admin bootstrap, env loading
|  |- forms.py           # WTForms for auth, patient, and reports
|  |- models.py          # User, Patient, DiagnosticReport models
|  |- routes.py          # All web routes and role checks
|  `- templates/         # Jinja templates
|- config.py             # Flask + SQLAlchemy configuration
|- run.py                # Development entrypoint
|- wsgi.py               # Production WSGI entrypoint for gunicorn
|- requirements.txt
|- Dockerfile
|- docker-compose.yml
`- .env.example
```

## Local Development Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.env` from `.env.example` and update values.
4. Start the app:
   ```bash
   python run.py
   ```
5. Open `http://localhost:5000`.

Notes:
- If `DATABASE_URL` is not set, the app uses SQLite at `instance/database.db`.
- On startup, tables are auto-created (`db.create_all()`).

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `SECRET_KEY`: Flask secret key
- `DEFAULT_ADMIN_NAME`: seeded admin display name
- `DEFAULT_ADMIN_EMAIL`: seeded admin login email
- `DEFAULT_ADMIN_PASSWORD`: seeded admin login password
- `POSTGRES_DB`: PostgreSQL DB name (Docker)
- `POSTGRES_USER`: PostgreSQL user (Docker)
- `POSTGRES_PASSWORD`: PostgreSQL password (Docker)
- `DATABASE_URL` (optional locally, set automatically in Docker web service): SQLAlchemy database URL
- `SUPABASE_DB_URL` (optional): full Supabase Postgres URL
- `SUPABASE_PROJECT_REF` (optional): Supabase project reference, used with `SUPABASE_DB_PASSWORD`
- `SUPABASE_DB_PASSWORD` (optional): raw Supabase DB password (special chars supported)
- `ALLOW_SQLITE_RESET` (optional, default `true`): if `true`, app may reset outdated SQLite schema during migration checks

Example PostgreSQL URL:

```text
postgresql+psycopg2://diagnostics_user:diagnostics_password@localhost:5432/diagnostics
```

Example Supabase URL:

```text
postgresql://postgres:<db-password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require
```

## Supabase Setup

1. In Supabase, copy the Postgres connection details from `Project Settings -> Database`.
2. In `.env`, configure one of these:
   - `SUPABASE_DB_URL=<full-supabase-url>`
   - `SUPABASE_PROJECT_REF=<your-project-ref>` and `SUPABASE_DB_PASSWORD=<your-db-password>`
3. Start the app:
   ```bash
   python run.py
   ```

Resolution priority:
- `SUPABASE_DB_URL`
- `SUPABASE_PROJECT_REF` + `SUPABASE_DB_PASSWORD`
- `DATABASE_URL`
- local SQLite fallback

## Security Question Verification

- After password validation, users complete a second step by answering their security question.
- If a user has no configured question yet, they are prompted to set one at login.
- Forgot-password flow also uses the saved security question answer.

## Docker Setup

1. Create `.env` from `.env.example`.
2. Run:
   ```bash
   docker compose up --build
   ```
3. App: `http://localhost:5000`

Services:
- `db`: PostgreSQL 16
- `web`: Flask app served with Gunicorn

## Authentication and Roles

### Admin

- Log in through Admin section on `/auth`.
- Can view users and create staff/admin users.
- Can delete patients.

### Staff

- Log in through User section on `/auth`.
- Can create/edit/search patients and add reports.

### Patient

- Activates account on `/auth` (register section) using:
  - existing Patient ID
  - matching patient email
- Can log in and view only own reports via `/my-reports`.

## Main Routes

- `/auth`: unified admin/user login + patient activation
- `/dashboard`: staff/admin summary dashboard
- `/users`: admin user list
- `/users/new`: admin create user
- `/patients`: patient listing + search
- `/patients/new`: create patient
- `/patients/<patient_id>`: view patient and reports
- `/patients/<patient_id>/edit`: edit patient
- `/patients/<patient_id>/delete`: delete patient (admin)
- `/patients/<patient_id>/reports/new`: create report
- `/reports/<report_id>`: view a report
- `/my-reports`: patient self-service report list
- `/logout`: logout current user

## Data Model

### User

- Login identity and role (`admin`, `staff`, `patient`)
- Optional link to a `Patient` for portal users

### Patient

- Demographic/profile record
- Unique `patient_code` used for patient account activation

### DiagnosticReport

- Test details, interpretation, notes, verifier, reporter
- Linked to both patient and report creator

## Operational Notes

- Default admin is created only if `DEFAULT_ADMIN_EMAIL` and `DEFAULT_ADMIN_PASSWORD` are set.
- Patient portal registration is blocked unless Patient ID and email match an existing patient record.
- Patients are prevented from accessing other patients' records/reports.

## Production Notes

- Set a strong `SECRET_KEY`.
- Disable Flask debug mode (do not run `run.py` in production).
- Use `gunicorn wsgi:app` (already configured in `Dockerfile`).
- Use managed PostgreSQL and secure credentials.
