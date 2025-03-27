import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.hashers import make_password # Per hashare password di default
from .models import User, Student, UserRole

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',) # Evita duplicati per username

    # Usiamo sequence per generare valori univoci
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda o: f'{o.username}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    # Imposta una password predefinita hashata (non sicura per produzione!)
    password = factory.LazyFunction(lambda: make_password('password123'))
    role = UserRole.TEACHER # Default a Docente
    is_active = True
    is_staff = False # Default a non staff
    is_superuser = False # Default a non superuser

    # Traits per creare tipi specifici di utenti facilmente
    class Params:
        admin = factory.Trait(
            role=UserRole.ADMIN,
            is_staff=True, # Gli admin dovrebbero poter accedere all'admin Django
            is_superuser=False # Non necessariamente superuser
        )
        superuser = factory.Trait(
            role=UserRole.ADMIN, # Superuser è anche Admin
            is_staff=True,
            is_superuser=True
        )

class StudentFactory(DjangoModelFactory):
    class Meta:
        model = Student

    # Associa a una TeacherFactory per default
    # Se non viene passata una 'teacher', ne crea una nuova
    teacher = factory.SubFactory(UserFactory, role=UserRole.TEACHER)
    # Genera un codice studente univoco
    student_code = factory.Sequence(lambda n: f'STUDENT{1000+n}')
    # Imposta un PIN predefinito (hashato)
    pin_hash = factory.LazyFunction(lambda: make_password('1234')) # Usa make_password importato
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True