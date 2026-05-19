# HomeFinder

HomeFinder is a real estate marketplace web app for browsing listings, saving properties, sending inquiries, comparing homes, and managing admin/owner workflows.

## Run The App

1. Open PowerShell in the project folder:

```powershell
cd \homefinderapp-main
```

2. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install Python dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

4. Create local environment settings:

```powershell
copy .env.example .env
```

5. Start the app:

```powershell
python scripts/dev_server.py
```

6. Open the site:

```text
http://127.0.0.1:8000
```

If port `8000` is busy, the dev server will try another local port and print the URL.

## Demo Accounts

The first admin login may require a password change.

Current demo users in the local database:

| Username | Email | Role | Verified |
| --- | --- | --- | --- |
| admin | admin@homefinder.com | admin | yes |
| MasterAdmin | master_admin@homefinder.local | admin | yes |
| LuxuryRep | luxury_rep@estatemax.com | property_owner | yes |
| JohnRenter | john_renter@gmail.com | regular_user | yes |
| seeduser | seed@example.com | admin | no |
| tcilipass | TCILIP@gmail.com | regular_user | no |
| tcilipp | tcilipp@gmail.com | regular_user | no |

Only the default seeded admin password is guaranteed by the project setup. Other local demo users may have passwords created during testing.

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- Alembic
- SQLite locally, PostgreSQL-ready for production
- Jinja2 server-rendered pages
- React + Vite + TypeScript frontend folder
- HTML, CSS, JavaScript
- Docker / Docker Compose


## Main Features

- Listing search and filters
- Real listing photos
- User registration and login
- Email verification
- Favorites / saved listings
- Property inquiries and threaded messages
- Owner inbox and admin inbox
- Listing comparison and comparison analysis
- Admin user/listing management
- Monthly reports and dashboard metrics
- Payment logs and reservation/viewing models

