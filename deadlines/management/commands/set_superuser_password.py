"""Management command to set superuser password from environment variable."""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Set password for superuser from DJANGO_SUPERUSER_PASSWORD env var"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin", help="Username to set password for")

    def handle(self, *args, **options):
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not password:
            self.stderr.write(self.style.ERROR("DJANGO_SUPERUSER_PASSWORD not set"))
            return

        User = get_user_model()
        username = options["username"]

        try:
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Password set for user: {username}"))
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"User {username} does not exist"))
