import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.users.models import UserRole # Import UserRole enum
# Import Factories (assuming they exist and are correctly set up)
from apps.users.factories import UserFactory, StudentFactory # Use UserFactory with traits and StudentFactory
from apps.education.factories import (
    QuizTemplateFactory, QuestionTemplateFactory, AnswerOptionTemplateFactory,
    QuizFactory, QuestionFactory, AnswerOptionFactory, PathwayFactory, # Rimosso PathwayQuizFactory
    QuizAssignmentFactory, PathwayAssignmentFactory
)
from apps.rewards.factories import (
    RewardTemplateFactory, RewardFactory # Rimosso WalletFactory dall'import delle factory
)
from apps.rewards.models import Wallet, RewardTemplate, Reward # Importa il modello Wallet
from apps.education.models import QuestionType, Quiz, Pathway
from apps.rewards.models import RewardTemplate, Reward, Badge, EarnedBadge # Import Badge and EarnedBadge

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with test data for students, education content, and rewards.'

    @transaction.atomic # Ensure all operations succeed or fail together
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))

        # --- Clean Slate (Optional but recommended for repeatable seeding) ---
        self.stdout.write('Deleting existing data...')
        # Importa i modelli necessari per la pulizia all'inizio del file o qui
        from apps.education.models import QuizTemplate, Quiz, Pathway, QuizAssignment, PathwayAssignment, QuizAttempt, PathwayProgress, StudentAnswer
        from apps.rewards.models import RewardTemplate, Reward, RewardPurchase, EarnedBadge
        from apps.users.models import Student

        # Elimina in ordine inverso per rispettare le dipendenze ForeignKey (o usa CASCADE)
        # Nota: L'ordine potrebbe dover essere aggiustato in base alle relazioni effettive
        self.stdout.write('Deleting Student Answers...')
        StudentAnswer.objects.all().delete()
        self.stdout.write('Deleting Quiz Attempts...')
        QuizAttempt.objects.all().delete()
        self.stdout.write('Deleting Pathway Progress...')
        PathwayProgress.objects.all().delete()
        self.stdout.write('Deleting Quiz Assignments...')
        QuizAssignment.objects.all().delete()
        self.stdout.write('Deleting Pathway Assignments...')
        PathwayAssignment.objects.all().delete()
        self.stdout.write('Deleting Earned Badges...')
        EarnedBadge.objects.all().delete()
        self.stdout.write('Deleting Reward Purchases...')
        RewardPurchase.objects.all().delete()
        self.stdout.write('Deleting Rewards...')
        Reward.objects.all().delete()
        self.stdout.write('Deleting Reward Templates...')
        RewardTemplate.objects.all().delete()
        self.stdout.write('Deleting Pathways...')
        Pathway.objects.all().delete() # Questo elimina anche PathwayQuiz tramite CASCADE (se impostato)
        self.stdout.write('Deleting Quizzes...')
        Quiz.objects.all().delete() # Questo elimina anche Question e AnswerOption tramite CASCADE
        self.stdout.write('Deleting Quiz Templates...')
        QuizTemplate.objects.all().delete() # Questo elimina anche QuestionTemplate e AnswerOptionTemplate
        self.stdout.write('Deleting Students and Wallets...')
        Student.objects.all().delete() # Questo elimina anche Wallet tramite CASCADE
        self.stdout.write('Deleting non-admin Users...')
        User.objects.filter(is_superuser=False, is_staff=False).delete() # Delete non-superusers/staff
        self.stdout.write(self.style.WARNING('Existing data deleted.'))

        # --- Create Users ---
        self.stdout.write('Creating users...')
        admin = UserFactory(admin=True, username='admin_test', email='admin@test.com') # Use UserFactory with admin trait
        teacher = UserFactory(role=UserRole.TEACHER, username='teacher_test', email='teacher@test.com') # Use UserFactory, explicitly set role
        students = StudentFactory.create_batch(3, teacher=teacher) # Use StudentFactory
        self.stdout.write(self.style.SUCCESS(f'Created: 1 Admin, 1 Teacher, {len(students)} Students'))

        # --- Create Wallets (if not handled automatically) ---
        # Check if wallets are created automatically (e.g., via signals on Student creation)
        # If not, create them explicitly:
        self.stdout.write('Ensuring wallets exist for students...')
        wallets_created = 0
        for student in students:
            # Usa il manager del modello Wallet per get_or_create
            wallet, created = Wallet.objects.get_or_create(student=student)
            if created:
                wallets_created += 1
        if wallets_created > 0:
             self.stdout.write(self.style.SUCCESS(f'Created {wallets_created} new wallets.'))
        else:
             self.stdout.write(self.style.NOTICE('Wallets already existed or are managed automatically.'))


        # --- Create Education Content Templates (Admin) ---
        self.stdout.write('Creating education templates (Admin)...')
        quiz_template = QuizTemplateFactory(admin=admin, title='Introduzione alla Storia Romana')
        qt1 = QuestionTemplateFactory(
            quiz_template=quiz_template, order=1, question_type=QuestionType.TRUE_FALSE,
            text='Roma è stata fondata nel 753 a.C.?'
        )
        AnswerOptionTemplateFactory(question_template=qt1, text='Vero', is_correct=True, order=1)
        AnswerOptionTemplateFactory(question_template=qt1, text='Falso', is_correct=False, order=2)

        qt2 = QuestionTemplateFactory(
            quiz_template=quiz_template, order=2, question_type=QuestionType.MULTIPLE_CHOICE_SINGLE,
            text='Chi fu il primo imperatore romano?'
        )
        AnswerOptionTemplateFactory(question_template=qt2, text='Giulio Cesare', is_correct=False, order=1)
        AnswerOptionTemplateFactory(question_template=qt2, text='Augusto', is_correct=True, order=2)
        AnswerOptionTemplateFactory(question_template=qt2, text='Nerone', is_correct=False, order=3)

        qt3 = QuestionTemplateFactory(
            quiz_template=quiz_template, order=3, question_type=QuestionType.FILL_BLANK,
            text='Il Colosseo è anche conosciuto come Anfiteatro _____.',
            metadata={'correct_answers': ['Flavio', 'flavio'], 'case_sensitive': False}
        )
        self.stdout.write(self.style.SUCCESS('Created 1 Quiz Template with 3 Question Templates.'))

        # --- Create Concrete Education Content (Teacher) ---
        self.stdout.write('Creating concrete education content (Teacher)...')
        # Create a Quiz based on the template
        quiz_romano = QuizFactory(
            teacher=teacher,
            source_template=quiz_template,
            title=quiz_template.title, # Inherit title
            description="Un quiz sulla fondazione e il primo impero.",
            metadata={'difficulty': 'easy', 'completion_threshold_percent': 70.0, 'points_on_completion': 15}
        )
        # Create Questions/Answers based on the template's questions
        # Note: Factories might need logic to handle cloning from templates if not already present
        # Manual creation for clarity here:
        q1 = QuestionFactory(
            quiz=quiz_romano, order=1, question_type=qt1.question_type, text=qt1.text
        )
        AnswerOptionFactory(question=q1, text='Vero', is_correct=True, order=1)
        AnswerOptionFactory(question=q1, text='Falso', is_correct=False, order=2)

        q2 = QuestionFactory(
            quiz=quiz_romano, order=2, question_type=qt2.question_type, text=qt2.text
        )
        AnswerOptionFactory(question=q2, text='Giulio Cesare', is_correct=False, order=1)
        AnswerOptionFactory(question=q2, text='Augusto', is_correct=True, order=2)
        AnswerOptionFactory(question=q2, text='Nerone', is_correct=False, order=3)

        q3 = QuestionFactory(
            quiz=quiz_romano, order=3, question_type=qt3.question_type, text=qt3.text, metadata=qt3.metadata
        )
        self.stdout.write(self.style.SUCCESS('Created 1 Quiz with 3 Questions based on template.'))

        # Create another Quiz (without template)
        quiz_egizio = QuizFactory(
            teacher=teacher,
            title='Antico Egitto: Dei e Faraoni',
            description='Domande sull\'antico Egitto.',
            metadata={'difficulty': 'medium', 'completion_threshold_percent': 80.0, 'points_on_completion': 25}
        )
        q_eg1 = QuestionFactory(quiz=quiz_egizio, order=1, question_type=QuestionType.MULTIPLE_CHOICE_SINGLE, text='Quale dio era associato al sole?')
        AnswerOptionFactory(question=q_eg1, text='Osiride', is_correct=False, order=1)
        AnswerOptionFactory(question=q_eg1, text='Ra', is_correct=True, order=2)
        AnswerOptionFactory(question=q_eg1, text='Anubi', is_correct=False, order=3)
        self.stdout.write(self.style.SUCCESS('Created 1 standalone Quiz.'))


        # Create a Pathway
        pathway = PathwayFactory(
            teacher=teacher,
            title='Introduzione alle Civiltà Antiche',
            description='Un percorso che copre Roma e l\'Egitto.',
            metadata={'points_on_completion': 50},
            # Passa i quiz (con ordine) direttamente alla factory
            quizzes=[(quiz_romano, 1), (quiz_egizio, 2)]
        )
        # Le righe seguenti non sono più necessarie, gestite da @post_generation
        # PathwayQuizFactory(pathway=pathway, quiz=quiz_romano, order=1)
        # PathwayQuizFactory(pathway=pathway, quiz=quiz_egizio, order=2)
        self.stdout.write(self.style.SUCCESS('Created 1 Pathway with 2 Quizzes.'))

        # --- Create Rewards ---
        self.stdout.write('Creating rewards...')
        # Global Reward Template (Admin)
        reward_template_global = RewardTemplateFactory(
            creator=admin, scope=RewardTemplate.RewardScope.GLOBAL,
            name='Buono Sconto Libri 5€', type=RewardTemplate.RewardType.DIGITAL,
            description='Un buono sconto digitale da usare in libreria.'
        )
        # Local Reward Template (Teacher)
        reward_template_local = RewardTemplateFactory(
            creator=teacher, scope=RewardTemplate.RewardScope.LOCAL,
            name='Figurina Speciale Classe', type=RewardTemplate.RewardType.REAL_WORLD,
            description='Una figurina speciale collezionabile.'
        )
        # Concrete Reward (Teacher, based on local template)
        reward_figurina = RewardFactory(
            teacher=teacher, template=reward_template_local,
            name=reward_template_local.name, # Inherit name
            cost_points=50,
            availability_type=Reward.AvailabilityType.ALL_STUDENTS, # Available to all teacher's students
            is_active=True
        )
        # Concrete Reward (Teacher, standalone)
        reward_bonus = RewardFactory(
            teacher=teacher,
            name='Bonus Compiti 1 Giorno',
            description='Salta i compiti per un giorno.',
            type=RewardTemplate.RewardType.REAL_WORLD,
            cost_points=100,
            availability_type=Reward.AvailabilityType.ALL_STUDENTS,
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS('Created 2 Reward Templates and 2 Rewards.'))

        # --- Create Badges ---
        self.stdout.write('Creating badges...')
        badge_first_quiz, created_bq = Badge.objects.get_or_create(
            name='Primo Quiz Completato!', # Usa 'name' invece di 'slug'
            defaults={
                'name': 'Primo Quiz Completato!',
                'description': 'Hai completato con successo il tuo primo quiz.',
                'image_url': '/badges/first_quiz.png', # Assumendo che l'immagine esista in static/badges/
                'trigger_type': 'AUTO', # O un altro tipo se definito
                'trigger_condition': {'event': 'first_quiz_passed'}, # Condizione simbolica
                'is_active': True
            }
        )
        if created_bq:
            self.stdout.write(self.style.SUCCESS(f'Created Badge: {badge_first_quiz.name}'))
        else:
            self.stdout.write(self.style.NOTICE(f'Badge "{badge_first_quiz.name}" already exists.'))

        # --- Assign Content to Students ---
        self.stdout.write('Assigning content to students...')
        assignments_created = 0
        due_date = timezone.now() + timezone.timedelta(days=7)
        for student in students:
            # Assign the first quiz
            QuizAssignmentFactory(
                student=student, quiz=quiz_romano, assigned_by=teacher, due_date=due_date
            )
            # Assign the pathway
            PathwayAssignmentFactory(
                student=student, pathway=pathway, assigned_by=teacher # Rimosso due_date
            )
            assignments_created += 2
        self.stdout.write(self.style.SUCCESS(f'Created {assignments_created} assignments.'))

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))