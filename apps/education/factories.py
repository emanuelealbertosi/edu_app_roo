import factory
from factory.django import DjangoModelFactory
from django.utils import timezone

# Importa modelli da altre app
from apps.users.factories import UserFactory, StudentFactory
from apps.users.models import UserRole

# Importa modelli locali
from .models import (
    QuizTemplate, QuestionTemplate, AnswerOptionTemplate,
    Quiz, Question, AnswerOption, Pathway, PathwayQuiz,
    QuizAttempt, StudentAnswer, PathwayProgress, QuestionType,
    QuizAssignment, PathwayAssignment # Aggiunti modelli Assignment
)

# --- Template Factories ---

class QuizTemplateFactory(DjangoModelFactory):
    class Meta:
        model = QuizTemplate

    admin = factory.SubFactory(UserFactory, admin=True) # Creato da Admin
    title = factory.Sequence(lambda n: f'Quiz Template {n}')
    description = factory.Faker('sentence')
    metadata = factory.LazyFunction(dict)

class QuestionTemplateFactory(DjangoModelFactory):
    class Meta:
        model = QuestionTemplate

    quiz_template = factory.SubFactory(QuizTemplateFactory)
    text = factory.Faker('paragraph', nb_sentences=1)
    question_type = factory.Faker('random_element', elements=QuestionType.values)
    order = factory.Sequence(lambda n: n)
    metadata = factory.LazyFunction(dict)

    # Trait per tipi specifici
    class Params:
        mc_single = factory.Trait(question_type=QuestionType.MULTIPLE_CHOICE_SINGLE)
        mc_multi = factory.Trait(question_type=QuestionType.MULTIPLE_CHOICE_MULTIPLE)
        tf = factory.Trait(question_type=QuestionType.TRUE_FALSE)
        fill = factory.Trait(question_type=QuestionType.FILL_BLANK)
        open_manual = factory.Trait(question_type=QuestionType.OPEN_ANSWER_MANUAL)

class AnswerOptionTemplateFactory(DjangoModelFactory):
    class Meta:
        model = AnswerOptionTemplate

    question_template = factory.SubFactory(QuestionTemplateFactory)
    text = factory.Faker('word')
    is_correct = factory.Faker('boolean', chance_of_getting_true=25) # 1 su 4 corretta
    order = factory.Sequence(lambda n: n)


# --- Concrete Factories ---

class QuizFactory(DjangoModelFactory):
    class Meta:
        model = Quiz

    teacher = factory.SubFactory(UserFactory, role=UserRole.TEACHER)
    source_template = None
    title = factory.Sequence(lambda n: f'Quiz Concreto {n}')
    description = factory.Faker('sentence')
    metadata = factory.LazyFunction(lambda: {"completion_threshold": 0.8, "points_on_completion": 50}) # Default metadata
    # available_from/until sono null di default

class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = Question

    quiz = factory.SubFactory(QuizFactory)
    text = factory.Faker('paragraph', nb_sentences=1)
    question_type = factory.Faker('random_element', elements=QuestionType.values)
    order = factory.Sequence(lambda n: n)
    metadata = factory.LazyFunction(dict)

    # Traits come in QuestionTemplateFactory
    class Params:
        mc_single = factory.Trait(question_type=QuestionType.MULTIPLE_CHOICE_SINGLE)
        mc_multi = factory.Trait(question_type=QuestionType.MULTIPLE_CHOICE_MULTIPLE)
        tf = factory.Trait(question_type=QuestionType.TRUE_FALSE)
        fill = factory.Trait(question_type=QuestionType.FILL_BLANK)
        open_manual = factory.Trait(question_type=QuestionType.OPEN_ANSWER_MANUAL)

class AnswerOptionFactory(DjangoModelFactory):
    class Meta:
        model = AnswerOption

    question = factory.SubFactory(QuestionFactory)
    text = factory.Faker('word')
    is_correct = factory.Faker('boolean', chance_of_getting_true=25)
    order = factory.Sequence(lambda n: n)

class PathwayFactory(DjangoModelFactory):
    class Meta:
        model = Pathway

    teacher = factory.SubFactory(UserFactory, role=UserRole.TEACHER)
    title = factory.Sequence(lambda n: f'Percorso {n}')
    description = factory.Faker('sentence')
    metadata = factory.LazyFunction(lambda: {"points_on_completion": 100})

    # Gestione M2M per i quiz nel percorso
    @factory.post_generation
    def quizzes(obj, create, extracted, **kwargs):
        if not create or not extracted:
            return
        # extracted è una lista di tuple (quiz, order) o solo quiz
        for item in extracted:
            if isinstance(item, tuple) and len(item) == 2:
                quiz, order = item
            else:
                quiz = item
                # Assegna un ordine progressivo se non specificato
                order = PathwayQuiz.objects.filter(pathway=obj).count() + 1

            # Assicurati che il quiz appartenga allo stesso docente del percorso
            if quiz.teacher == obj.teacher:
                PathwayQuiz.objects.create(pathway=obj, quiz=quiz, order=order)
            else:
                 print(f"Attenzione (Factory): Quiz {quiz.id} non appartiene al docente {obj.teacher.id}, non aggiunto a Pathway {obj.id}")


class QuizAttemptFactory(DjangoModelFactory):
    class Meta:
        model = QuizAttempt

    student = factory.SubFactory(StudentFactory)
    # Assicura che il quiz sia dello stesso docente dello studente
    quiz = factory.SubFactory(QuizFactory, teacher=factory.SelfAttribute('..student.teacher'))
    status = QuizAttempt.AttemptStatus.IN_PROGRESS
    # started_at è auto_now_add
    # completed_at, score sono null di default

    class Params:
        completed = factory.Trait(
            status=QuizAttempt.AttemptStatus.COMPLETED,
            completed_at=factory.LazyFunction(timezone.now),
            score=factory.Faker('pyfloat', left_digits=2, right_digits=2, min_value=0, max_value=100)
        )
        pending = factory.Trait(status=QuizAttempt.AttemptStatus.PENDING_GRADING)


class StudentAnswerFactory(DjangoModelFactory):
    class Meta:
        model = StudentAnswer

    quiz_attempt = factory.SubFactory(QuizAttemptFactory)
    # Assicura che la domanda appartenga allo stesso quiz del tentativo
    question = factory.SubFactory(QuestionFactory, quiz=factory.SelfAttribute('..quiz_attempt.quiz'))
    selected_answers = factory.LazyFunction(dict) # Default vuoto, da sovrascrivere nel test
    is_correct = None # Default a non valutato
    score = None
    # answered_at è auto_now_add


class PathwayProgressFactory(DjangoModelFactory):
    class Meta:
        model = PathwayProgress
        # unique_together = ('student', 'pathway') gestito da get_or_create
        django_get_or_create = ('student', 'pathway')

    student = factory.SubFactory(StudentFactory)
    # Assicura che il percorso sia dello stesso docente dello studente
    pathway = factory.SubFactory(PathwayFactory, teacher=factory.SelfAttribute('..student.teacher'))
    status = PathwayProgress.ProgressStatus.IN_PROGRESS
    # started_at è auto_now_add
    # completed_at, last_completed_quiz_order sono null di default

    class Params:
        completed = factory.Trait(
            status=PathwayProgress.ProgressStatus.COMPLETED,
            completed_at=factory.LazyFunction(timezone.now),
            # last_completed_quiz_order andrebbe impostato in base ai quiz del percorso
        )

# --- Assignment Factories ---

class QuizAssignmentFactory(DjangoModelFactory):
    class Meta:
        model = QuizAssignment
        django_get_or_create = ('student', 'quiz') # Evita duplicati

    student = factory.SubFactory(StudentFactory)
    # Assicura che il quiz sia dello stesso docente dello studente
    quiz = factory.SubFactory(QuizFactory, teacher=factory.SelfAttribute('..student.teacher'))
    # Assicura che assigned_by sia il docente del quiz/studente
    assigned_by = factory.SelfAttribute('quiz.teacher')

class PathwayAssignmentFactory(DjangoModelFactory):
    class Meta:
        model = PathwayAssignment
        django_get_or_create = ('student', 'pathway') # Evita duplicati

    student = factory.SubFactory(StudentFactory)
    # Assicura che il percorso sia dello stesso docente dello studente
    pathway = factory.SubFactory(PathwayFactory, teacher=factory.SelfAttribute('..student.teacher'))
    # Assicura che assigned_by sia il docente del percorso/studente
    assigned_by = factory.SelfAttribute('pathway.teacher')