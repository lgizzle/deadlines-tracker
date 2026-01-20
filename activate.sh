#!/bin/bash
# Quick activation script for deadlines-tracker
source /Users/lesgutches/Developer/venvs/business-general/bin/activate
echo "✓ Activated business-general venv"
echo "✓ Django $(python -c 'import django; print(django.get_version())')"
echo ""
echo "Common commands:"
echo "  python manage.py runserver        - Start dev server"
echo "  python manage.py createsuperuser  - Create admin user"
echo "  python manage.py migrate          - Run migrations"
echo "  python quick_import.py            - Import CSV data"
