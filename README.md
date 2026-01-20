# Business Deadlines Tracker - Django App

A Django-based business deadlines tracking system with Microsoft SSO authentication, built for easy deployment to Railway.

## Features

- **Complete Business Data Management**: Entities, deadlines, bank accounts, credit cards, insurance, licenses, loans, contacts
- **Smart Deadline Tracking**: Color-coded admin interface with overdue/due-soon indicators
- **Microsoft SSO**: Secure authentication via Microsoft Entra ID (formerly Azure AD)
- **Professional Admin Interface**: Django admin with organized fieldsets and filtering
- **CSV Import**: One-command data import from your existing CSV files
- **Railway Ready**: One-click deployment with automatic PostgreSQL provisioning

## Quick Start (Local Development)

### 1. Install Dependencies

```bash
cd webapp
source venv/bin/activate  # venv already created
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings (SECRET_KEY generated, DEBUG=True for local)
```

### 3. Run Migrations

```bash
python manage.py migrate
python manage.py createsuperuser  # Create admin account
```

### 4. Import Your Data

```bash
python manage.py import_csv --csv-dir=../csv-exports
```

### 5. Run Development Server

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/admin/ and login with your superuser account.

## Deploy to Railway (Recommended)

### Step 1: Create Railway Project

1. Go to [Railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select this repository
4. Railway auto-detects Django and provisions PostgreSQL

### Step 2: Add PostgreSQL Database

1. In your Railway project, click **New** → **Database** → **PostgreSQL**
2. Railway automatically sets `DATABASE_URL` environment variable

### Step 3: Set Environment Variables

In Railway project settings, add:

```
SECRET_KEY=<generate-a-long-random-string>
DEBUG=False
ALLOWED_HOSTS=your-app-name.up.railway.app
MICROSOFT_CLIENT_ID=<from-azure-app-registration>
MICROSOFT_CLIENT_SECRET=<from-azure-app-registration>
MICROSOFT_TENANT_ID=common
```

### Step 4: Deploy

Railway automatically deploys on git push. After first deploy:

```bash
# SSH into Railway container (via Railway CLI or dashboard)
python manage.py createsuperuser
python manage.py import_csv --csv-dir=/app/csv-exports
```

## Microsoft SSO Setup

### Create Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations**
2. Click **New registration**:
   - Name: "Business Deadlines Tracker"
   - Supported account types: "Accounts in this organizational directory only"
   - Redirect URI: `https://your-app.up.railway.app/accounts/microsoft/login/callback/`
3. After creation:
   - Copy **Application (client) ID** → `MICROSOFT_CLIENT_ID`
   - Copy **Directory (tenant) ID** → `MICROSOFT_TENANT_ID`
   - Go to **Certificates & secrets** → **New client secret** → Copy value → `MICROSOFT_CLIENT_SECRET`

### Configure Permissions

In your app registration:

- Go to **API permissions** → **Add a permission** → **Microsoft Graph** → **Delegated permissions**
- Add: `User.Read`
- Click **Grant admin consent**

## Project Structure

```
webapp/
├── bizops/              # Django project settings
│   ├── settings.py      # Config with Railway, SSO, DB setup
│   └── urls.py          # URL routing
├── deadlines/           # Main app
│   ├── models.py        # Data models (Entity, Deadline, etc.)
│   ├── admin.py         # Admin interface customization
│   └── management/
│       └── commands/
│           └── import_csv.py  # CSV import command
├── requirements.txt     # Python dependencies
├── Procfile            # Railway deployment config
├── railway.json        # Railway settings
└── .env.example        # Environment template
```

## Models

- **Entity**: Business entities (CHEERS, TIMBER, GXM, etc.)
- **Deadline**: Recurring obligations with due date tracking
- **BankAccount**: Bank account information
- **CreditCard**: Credit card details
- **InsurancePolicy**: Insurance policies and renewals
- **License**: Business licenses and permits
- **Loan**: Loan and financing details
- **Contact**: Business contacts

## CSV Import

The `import_csv` command reads from `csv-exports/` and imports all data:

```bash
python manage.py import_csv --csv-dir=../csv-exports
```

Supported files:

- `Entities.csv`
- `BusinessDeadlines.csv`
- `BankAccounts.csv`
- `CreditCards.csv`
- `InsurancePolicies.csv`
- `Licenses.csv`
- `Loans.csv`
- `Contacts.csv`

## Admin Interface Features

### Deadline Management

- **Color-coded status badges**: Red (overdue), yellow (due soon), green (upcoming)
- **Days until due counter**
- **Autopay indicator**
- **Filter by entity, category, status**
- **Date hierarchy navigation**

### Entity Management

- **Organized fieldsets**: Basic info, location, contacts, SOS info
- **Filter by status, entity type**
- **Search across codes, names, EINs**

## Security Notes

- Never commit `.env` file
- Use strong `SECRET_KEY` in production
- Set `DEBUG=False` in production
- Railway automatically provides SSL/HTTPS
- Microsoft SSO ensures authenticated access only

## Next Steps

### Optional Enhancements

1. **Custom dashboard**: Build front-end views instead of just admin
2. **Email reminders**: Use Celery + Railway Redis for scheduled deadline notifications
3. **Mobile responsive UI**: Add Tailwind CSS dashboard
4. **API endpoints**: Add Django REST framework for mobile app integration

## Support

- **Railway Docs**: https://docs.railway.app
- **Django Admin**: https://docs.djangoproject.com/en/stable/ref/contrib/admin/
- **django-allauth**: https://django-allauth.readthedocs.io/

## Why This Beats Power Apps

✓ Full control - no formula debugging hell  
✓ Free Railway tier (way better than SharePoint costs)  
✓ Professional admin UI out of the box  
✓ Easy to extend with custom features  
✓ Works on any device with a browser  
✓ Microsoft SSO just like Power Apps  
✓ Git-based deployment (proper version control)
