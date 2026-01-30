"""
Import sensitive financial data from SSOT into encrypted fields.

NOTE: This script was used for initial data import. Sensitive data has been
removed from this file for security reasons. The data now lives encrypted
in the database.

To re-import data, update the SSOT markdown files and modify this script
to read from them at runtime rather than hardcoding values.
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Import sensitive data from SSOT (one-time import - data removed for security)"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                "This import script has been disabled for security.\n"
                "Sensitive data was removed from the codebase.\n"
                "The data has already been imported to the database.\n"
                "If you need to re-import, modify this script to read from SSOT files."
            )
        )
