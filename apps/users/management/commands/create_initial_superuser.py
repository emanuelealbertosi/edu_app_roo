import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Creates a superuser non-interactively if it does not exist.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not all([username, email, password]):
            self.stderr.write(self.style.ERROR(
                "Missing environment variables: DJANGO_SUPERUSER_USERNAME, "
                "DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD"
            ))
            return

        if not User.objects.filter(username=username).exists():
            self.stdout.write(f"Creating superuser '{username}'...")
            try:
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created successfully."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error creating superuser: {e}"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists. Skipping creation."))