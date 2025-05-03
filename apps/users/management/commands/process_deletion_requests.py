import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

logger = logging.getLogger(__name__)

User = get_user_model()

class Command(BaseCommand):
    help = 'Processes user deletion requests by anonymizing their data.'

    def handle(self, *args, **options):
        users_to_process = User.objects.filter(is_deletion_requested=True, is_active=True)
        processed_count = 0
        skipped_count = 0

        if not users_to_process.exists():
            self.stdout.write(self.style.SUCCESS('No pending user deletion requests found.'))
            return

        self.stdout.write(f'Found {users_to_process.count()} user(s) marked for deletion. Processing...')

        for user in users_to_process:
            try:
                with transaction.atomic():
                    user_id = user.id
                    self.stdout.write(f'Processing user ID: {user_id} ({user.email})...')

                    # Anonymize identifying information
                    user.email = f'deleted_user_{user_id}@example.com'
                    user.first_name = 'Utente'
                    user.last_name = 'Cancellato'
                    user.username = f'deleted_user_{user_id}' # Assuming username is used and unique

                    # Clear potentially identifying optional fields (add others as needed)
                    # user.profile_picture = None # Example if you have profile pictures
                    # user.phone_number = None # Example

                    # Mark as inactive and note deletion processing time
                    user.is_active = False
                    user.is_deletion_requested = False # Reset flag after processing
                    user.date_joined = timezone.now() # Optional: Overwrite join date or add a specific 'anonymized_at' field

                    # Ensure password is unusable
                    user.set_unusable_password()

                    user.save()

                    # TODO: Consider related data - should it be deleted or anonymized?
                    # Example: Delete related student profile if it exists
                    # if hasattr(user, 'student_profile'):
                    #     user.student_profile.delete()

                    self.stdout.write(self.style.SUCCESS(f'Successfully anonymized user ID: {user_id}'))
                    processed_count += 1

            except Exception as e:
                logger.error(f"Error processing deletion for user ID {user.id}: {e}", exc_info=True)
                self.stderr.write(self.style.ERROR(f'Failed to process user ID: {user.id}. Error: {e}'))
                skipped_count += 1
                # Optionally, you might want to keep is_deletion_requested=True for retry

        self.stdout.write(self.style.SUCCESS(f'Processing complete. Anonymized: {processed_count}, Skipped: {skipped_count}'))