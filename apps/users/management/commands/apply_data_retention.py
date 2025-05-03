import logging
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.db.models import Max, Q

# Importa i modelli necessari (potrebbero servire aggiustamenti in base alla struttura esatta)
from apps.users.models import Student, User  # Assumendo che User sia qui
from apps.education.models import QuizAttempt, StudentAnswer
from apps.rewards.models import PointTransaction, RewardPurchase

logger = logging.getLogger(__name__)

# --- Costanti per la Policy ---
INACTIVE_STUDENT_YEARS = 2
DELETION_REQUEST_DAYS = 30
DATA_RETENTION_YEARS = 3 # Per tentativi, transazioni, acquisti

class Command(BaseCommand):
    help = 'Applica la policy di data retention cancellando o anonimizzando dati vecchi.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula le azioni senza modificare il database.',
        )
        parser.add_argument(
            '--force-user-model',
            action='store_true',
            help='Forza l\'uso del modello User di Django anche se non trovato in apps.users.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force_user_model = options['force_user_model']
        now = timezone.now()

        self.stdout.write(self.style.NOTICE(f"Inizio applicazione data retention policy ({'DRY RUN' if dry_run else 'LIVE RUN'})..."))

        # Determina il modello User da usare
        UserModel = User
        if force_user_model:
            try:
                from django.contrib.auth import get_user_model
                UserModel = get_user_model()
                self.stdout.write(self.style.NOTICE(f"Forzato l'uso del modello User: {UserModel}"))
            except Exception as e:
                 raise CommandError(f"Impossibile ottenere il modello User di Django: {e}")
        elif not hasattr(UserModel, 'is_deletion_requested'):
             self.stdout.write(self.style.WARNING(f"Il modello User ({UserModel}) non sembra avere 'is_deletion_requested'. La regola 2 potrebbe non funzionare come previsto."))


        # --- 1. Anonimizzazione Studenti Inattivi ---
        self.stdout.write(self.style.NOTICE("1. Anonimizzazione Studenti Inattivi..."))
        inactive_threshold_date = now - timedelta(days=365 * INACTIVE_STUDENT_YEARS)

        # Trova l'ultima attività per studente (questo può essere pesante, ottimizzare se necessario)
        # Consideriamo l'ultima data di completamento di un tentativo o l'ultimo acquisto
        active_students_ids = set()
        last_attempt_dates = QuizAttempt.objects.filter(
            completed_at__isnull=False
        ).values('student_id').annotate(last_activity=Max('completed_at'))

        last_purchase_dates = RewardPurchase.objects.values(
            'student_id'
        ).annotate(last_activity=Max('purchased_at'))

        for activity in last_attempt_dates:
            if activity['last_activity'] >= inactive_threshold_date:
                active_students_ids.add(activity['student_id'])

        for activity in last_purchase_dates:
             if activity['last_activity'] >= inactive_threshold_date:
                active_students_ids.add(activity['student_id'])

        # Identifica studenti attivi (is_active=True) che NON sono nel set degli attivi recenti
        # e che NON hanno una richiesta di cancellazione pendente (gestita dopo)
        students_to_anonymize_inactive = Student.objects.filter(
            is_active=True
        ).exclude(
            id__in=active_students_ids
        )

        # Escludi anche quelli con richiesta di cancellazione attiva sull'User associato (se possibile)
        try:
            # Assumiamo che Student abbia una ForeignKey 'user' a UserModel
            students_with_deletion_request = UserModel.objects.filter(is_deletion_requested=True).values_list('student__id', flat=True) # Adatta 'student__id' se la relazione è diversa
            students_to_anonymize_inactive = students_to_anonymize_inactive.exclude(id__in=students_with_deletion_request)
        except FieldError:
             self.stdout.write(self.style.WARNING("Impossibile filtrare per 'user.is_deletion_requested' su Student. La relazione potrebbe mancare o avere un nome diverso."))
        except AttributeError:
             self.stdout.write(self.style.WARNING("Il modello User non ha 'is_deletion_requested'. Salto il filtro."))


        count_inactive = students_to_anonymize_inactive.count()
        self.stdout.write(f"   Trovati {count_inactive} studenti potenzialmente inattivi da anonimizzare.")

        if not dry_run and count_inactive > 0:
            for student in students_to_anonymize_inactive.iterator():
                self.anonymize_student(student, UserModel, is_deletion_request=False)
            self.stdout.write(self.style.SUCCESS(f"   Anonimizzati {count_inactive} studenti inattivi."))
        elif dry_run:
            self.stdout.write(self.style.WARNING("   DRY RUN: Nessuna modifica applicata."))

        # --- 2. Anonimizzazione Richieste Cancellazione ---
        self.stdout.write(self.style.NOTICE("2. Anonimizzazione Richieste Cancellazione..."))
        deletion_threshold_date = now - timedelta(days=DELETION_REQUEST_DAYS)

        try:
            users_to_delete = UserModel.objects.filter(
                is_deletion_requested=True,
                # Assumiamo che esista un campo che traccia quando è stata fatta la richiesta
                # Se non esiste, potremmo basarci su un campo 'deletion_requested_at' o simile
                # Per ora, assumiamo che il flag sia sufficiente se il comando gira regolarmente
                # O potremmo usare un campo 'last_updated' se traccia il cambio del flag.
                # Qui usiamo solo il flag e la data soglia per semplicità, ma andrebbe raffinato.
                # Esempio con campo ipotetico: deletion_requested_at__lte=deletion_threshold_date
                is_active=True # Processa solo quelli ancora attivi
            )

            # Trova gli studenti associati a questi utenti
            # Adatta 'student' se la relazione inversa ha un nome diverso
            students_to_anonymize_deletion = Student.objects.filter(user__in=users_to_delete, is_active=True)

            count_deletion = students_to_anonymize_deletion.count()
            self.stdout.write(f"   Trovati {count_deletion} studenti associati a richieste di cancellazione da anonimizzare.")

            if not dry_run and count_deletion > 0:
                processed_users = set()
                for student in students_to_anonymize_deletion.iterator():
                     user = student.user # Assumendo relazione 'user'
                     self.anonymize_student(student, UserModel, is_deletion_request=True)
                     processed_users.add(user.pk)

                # Anonimizza anche gli utenti associati
                users_processed = UserModel.objects.filter(pk__in=processed_users)
                for user in users_processed:
                    self.anonymize_user(user)

                self.stdout.write(self.style.SUCCESS(f"   Anonimizzati {count_deletion} studenti e i loro utenti associati per richiesta cancellazione."))
            elif dry_run:
                self.stdout.write(self.style.WARNING("   DRY RUN: Nessuna modifica applicata."))

        except AttributeError:
             self.stdout.write(self.style.ERROR("   Errore: Il modello User non ha 'is_deletion_requested'. Impossibile processare le richieste di cancellazione."))
        except FieldError:
             self.stdout.write(self.style.ERROR("   Errore: Relazione tra User e Student non trovata o non nominata 'user'/'student'. Impossibile processare le richieste di cancellazione."))


        # --- 3. Cancellazione Tentativi Quiz e Risposte ---
        self.stdout.write(self.style.NOTICE("3. Cancellazione Tentativi Quiz e Risposte vecchi..."))
        retention_threshold_date = now - timedelta(days=365 * DATA_RETENTION_YEARS)

        # Trova ID studenti anonimizzati (is_active=False)
        anonymized_student_ids = Student.objects.filter(is_active=False).values_list('id', flat=True)

        attempts_to_delete = QuizAttempt.objects.filter(
            Q(completed_at__lte=retention_threshold_date) | Q(student_id__in=anonymized_student_ids),
            Q(status='completed') | Q(status='pending_manual_grading')
        )
        count_attempts = attempts_to_delete.count()
        # Nota: Cancellando QuizAttempt, le StudentAnswer associate dovrebbero essere cancellate
        # automaticamente se la ForeignKey ha on_delete=models.CASCADE. Verificare!
        # Se non è CASCADE, bisogna cancellare prima StudentAnswer.
        # student_answers_to_delete = StudentAnswer.objects.filter(quiz_attempt__in=attempts_to_delete)
        # count_answers = student_answers_to_delete.count()

        self.stdout.write(f"   Trovati {count_attempts} tentativi di quiz da cancellare.")
        # self.stdout.write(f"   Trovate {count_answers} risposte associate da cancellare.")

        if not dry_run and count_attempts > 0:
            # Prima le risposte se non c'è CASCADE
            # deleted_answers_count, _ = student_answers_to_delete.delete()
            deleted_attempts_count, _ = attempts_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f"   Cancellati {deleted_attempts_count} tentativi."))
            # self.stdout.write(self.style.SUCCESS(f"   Cancellate {deleted_answers_count} risposte."))
        elif dry_run:
            self.stdout.write(self.style.WARNING("   DRY RUN: Nessuna modifica applicata."))


        # --- 4. Cancellazione Transazioni Punti ---
        self.stdout.write(self.style.NOTICE("4. Cancellazione Transazioni Punti vecchie..."))
        # Assumiamo che PointTransaction abbia un campo 'timestamp'
        transactions_to_delete = PointTransaction.objects.filter(
             Q(timestamp__lte=retention_threshold_date) | Q(wallet__student_id__in=anonymized_student_ids) # Assumendo Wallet ha FK a Student
        )
        count_transactions = transactions_to_delete.count()
        self.stdout.write(f"   Trovate {count_transactions} transazioni punti da cancellare.")

        if not dry_run and count_transactions > 0:
            deleted_count, _ = transactions_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f"   Cancellate {deleted_count} transazioni."))
        elif dry_run:
            self.stdout.write(self.style.WARNING("   DRY RUN: Nessuna modifica applicata."))


        # --- 5. Cancellazione Acquisti Ricompense ---
        self.stdout.write(self.style.NOTICE("5. Cancellazione Acquisti Ricompense vecchi..."))
        purchases_to_delete = RewardPurchase.objects.filter(
            Q(purchased_at__lte=retention_threshold_date) | Q(student_id__in=anonymized_student_ids),
            Q(status='delivered') | Q(status='cancelled')
        )
        count_purchases = purchases_to_delete.count()
        self.stdout.write(f"   Trovati {count_purchases} acquisti ricompense da cancellare.")

        if not dry_run and count_purchases > 0:
            deleted_count, _ = purchases_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f"   Cancellati {deleted_count} acquisti."))
        elif dry_run:
            self.stdout.write(self.style.WARNING("   DRY RUN: Nessuna modifica applicata."))


        self.stdout.write(self.style.SUCCESS("Applicazione data retention policy completata."))

    def anonymize_student(self, student, UserModel, is_deletion_request=False):
        """Anonimizza un singolo oggetto Student."""
        student.is_active = False
        student.first_name = "Utente"
        student.last_name = "Anonimizzato"
        student.unique_identifier = f"anon_{student.id}"
        # Aggiungere qui altre eventuali cancellazioni/anonimizzazioni specifiche per Student
        student.save()
        logger.info(f"Anonimizzato Student ID: {student.id} (Richiesta Cancellazione: {is_deletion_request})")

        # Se è una richiesta di cancellazione, prova ad anonimizzare anche l'User associato
        if is_deletion_request:
            try:
                user = student.user # Assumendo relazione 'user'
                if user:
                    self.anonymize_user(user)
            except AttributeError:
                 logger.warning(f"Impossibile trovare/anonimizzare User associato a Student ID: {student.id}")
            except UserModel.DoesNotExist:
                 logger.warning(f"User associato a Student ID: {student.id} non trovato.")


    def anonymize_user(self, user):
        """Anonimizza un singolo oggetto User."""
        user.is_active = False
        user.email = f"anon_{user.id}@example.com" # Assumendo che User abbia 'email'
        user.first_name = "Utente" # Assumendo che User abbia 'first_name'
        user.last_name = "Anonimo" # Assumendo che User abbia 'last_name'
        user.set_password(None) # Imposta password non utilizzabile
        # Aggiungere qui altre eventuali cancellazioni/anonimizzazioni specifiche per User
        # Es: cancellare token, sessioni, ecc.
        user.save()
        logger.info(f"Anonimizzato User ID: {user.id}")