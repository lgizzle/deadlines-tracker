# Handoff: Business Deadlines Tracker

**Date**: January 19, 2026  
**Status**: ✅ Scaffolding complete, ready for admin setup  
**Location**: `/Users/lesgutches/Developer/websites/deadlines-tracker`

## What This Is

A **Django web application** to replace SharePoint/Power Apps for tracking business deadlines. Built with:
- Django 5.2 admin interface
- 8 data models (Entity, Deadline, BankAccount, CreditCard, Insurance, License, Loan, Contact)
- Microsoft SSO configuration (needs Azure setup)
- Railway deployment ready
- SQLite database with **14 entities & 63 deadlines** already imported

## Current State

### ✅ Complete
- Django project scaffolded (`bizops/` settings)
- All models created and migrated
- Professional admin interface configured
- CSV data imported (14 entities, 63 deadlines)
- Moved to standard location with shared venv
- Railway deployment config ready
- Documentation created (README.md, QUICKSTART.md, START-HERE.md)

### 🔄 Next Action Required
**CREATE ADMIN USER** - You need a login to access the admin interface

## Environment Setup

**Virtual Environment**: `/Users/lesgutches/Developer/venvs/business-general` (shared)

**Activate**:
```bash
cd ~/Developer/websites/deadlines-tracker
source activate.sh
# OR
source /Users/lesgutches/Developer/venvs/business-general/bin/activate
```

**Dependencies Installed**:
- Django 5.2.3
- django-allauth (Microsoft SSO)
- django-extensions
- dj-database-url
- gunicorn
- whitenoise
- python-decouple
- python-dateutil

## Admin User Creation

**Action Item**: Create admin credentials

```bash
# Option 1: Interactive (prompts for username, email, password)
python manage.py createsuperuser

# Option 2: Set password for existing 'admin' user
python manage.py changepassword admin
```

**Recommended Credentials**:
- Username: `admin`
- Email: `les@ngbsolutions.com` 
- Password: (set securely during creation)

## Quick Start Commands

```bash
# Activate environment
source activate.sh

# Start development server
python manage.py runserver

# Access admin interface
open http://127.0.0.1:8000/admin/

# Re-import CSV data (if needed)
python quick_import.py

# Django shell
python manage.py shell
```

## Key Files

- **manage.py** - Django management command
- **activate.sh** - Quick venv activation helper
- **quick_import.py** - CSV import script
- **.env** - Environment variables (SECRET_KEY, DEBUG, DATABASE_URL, etc.)
- **db.sqlite3** - Local SQLite database with imported data
- **bizops/settings.py** - Django configuration
- **deadlines/models.py** - All data models
- **deadlines/admin.py** - Admin interface customization

## Data Imported

### Entities (14)
CHEERS, PATLIQ, GXM, TIMBER, NWNINTH, FOURWEST, FIRS, HUCKBERRY, NC1105, NCPIC, NGB, PERSONAL, XBIZ, RETREAT

### Deadlines (63)
- Sales tax filings
- Utility payments
- Insurance renewals
- License renewals
- Loan payments
- Various recurring obligations

## Admin Interface Features

Once you create an admin user, you'll see:

### Deadlines View
- **Color-coded badges**:
  - 🔴 Red = Overdue
  - 🟡 Yellow = Due within reminder window
  - 🟢 Green = Upcoming (shows days until due)
- **Filters**: By entity, category, frequency, autopay, status
- **Search**: Title, account number, notes
- **Date hierarchy**: Browse by next due date
- **Autopay indicator**: Shows which items auto-pay

### Entities View
- Complete business information
- Organized fieldsets (Basic, Classification, Location, Contact, SOS info)
- Filter by status, entity type, tax filing type
- Search across codes, names, EINs

## Microsoft SSO Setup (Optional)

To enable Microsoft authentication:

1. **Azure App Registration**:
   - Go to Azure Portal → Entra ID → App registrations
   - Create new registration
   - Set redirect URI: `http://127.0.0.1:8000/accounts/microsoft/login/callback/`
   - Generate client secret

2. **Update .env**:
   ```
   MICROSOFT_CLIENT_ID=<your-client-id>
   MICROSOFT_CLIENT_SECRET=<your-client-secret>
   MICROSOFT_TENANT_ID=common
   ```

3. **Restart server** and visit `/accounts/login/`

## Deployment to Railway

When ready to deploy:

1. Push to GitHub repository
2. Create Railway project → Deploy from GitHub
3. Railway auto-detects Django via `Procfile`
4. Add Postgres database (Railway provides DATABASE_URL)
5. Set environment variables:
   - `SECRET_KEY` (generate new for production)
   - `DEBUG=False`
   - `ALLOWED_HOSTS=your-app.up.railway.app`
   - Microsoft SSO credentials (if using)
6. Deploy runs migrations automatically via `Procfile`

See [README.md](README.md) for detailed deployment steps.

## CSV Import Details

Data imported from:
- `../csv-exports/Entities.csv` → Entity model
- `../csv-exports/BusinessDeadlines.csv` → Deadline model

Other CSV files available but not yet imported (different schemas):
- BankAccounts.csv
- CreditCards.csv
- InsurancePolicies.csv
- Licenses.csv
- Loans.csv
- Contacts.csv

Use `python manage.py import_csv --csv-dir=../csv-exports` for full import (needs schema fixes).

## Project Structure

```
deadlines-tracker/
├── activate.sh              # Quick venv activation
├── manage.py                # Django management
├── quick_import.py          # Fast CSV import
├── .env                     # Environment variables
├── db.sqlite3               # SQLite database
├── requirements.txt         # Python dependencies
├── Procfile                 # Railway deployment
├── railway.json             # Railway config
├── nixpacks.toml            # Build config
├── bizops/                  # Django project
│   ├── settings.py          # Configuration
│   ├── urls.py              # URL routing
│   └── wsgi.py              # WSGI entry point
├── deadlines/               # Main app
│   ├── models.py            # 8 data models
│   ├── admin.py             # Admin customization
│   ├── views.py             # Views (empty for now)
│   ├── migrations/          # Database migrations
│   └── management/
│       └── commands/
│           └── import_csv.py
└── staticfiles/             # Collected static files
```

## Context for Next Session

When you open this directory:

1. **First action**: Create admin user (command provided above)
2. **Test**: Start server and login to admin
3. **Explore**: Look at Entities and Deadlines in admin interface
4. **Verify**: Color-coded deadline badges work correctly
5. **Optional**: Configure Microsoft SSO for production use

## Why Django Instead of Power Apps

✅ **Free hosting** (Railway free tier)  
✅ **Full Python control** (no formula debugging)  
✅ **Fast performance** (instant vs. slow Power Apps loading)  
✅ **Git version control** (proper change tracking)  
✅ **Unlimited extensibility** (add any feature you want)  
✅ **Professional admin UI** (Django admin is battle-tested)  
✅ **Real development workflow** (test locally, deploy confidently)

## Questions to Consider

- Do you want Microsoft SSO or stick with Django auth?
- Should we add email reminders for upcoming deadlines?
- Need custom dashboard beyond admin interface?
- Want mobile-optimized views or just use responsive admin?
- Deploy to Railway or another platform?

## Resources

- Full documentation: [README.md](README.md)
- Quick guide: [QUICKSTART.md](QUICKSTART.md)  
- Simple start: [START-HERE.md](START-HERE.md)
- Django docs: https://docs.djangoproject.com
- Railway docs: https://docs.railway.app

---

**Next Step**: Create admin user with `python manage.py createsuperuser`

**Context Preserved**: All project details, imported data, and next actions documented here for when you switch to this directory.
