import factory
from factory.django import DjangoModelFactory
from decimal import Decimal # Se usassimo DecimalField per i punti
from django.utils import timezone

# Importa modelli da altre app
from apps.users.factories import UserFactory, StudentFactory
from apps.users.models import UserRole

# Importa modelli locali
from .models import (
    Wallet, PointTransaction, RewardTemplate, Reward,
    RewardStudentSpecificAvailability, RewardPurchase
)

class WalletFactory(DjangoModelFactory):
    class Meta:
        model = Wallet
        # Usiamo student come chiave primaria, quindi get_or_create su di esso
        django_get_or_create = ('student',)

    student = factory.SubFactory(StudentFactory)
    current_points = factory.Faker('random_int', min=0, max=1000)

class PointTransactionFactory(DjangoModelFactory):
    class Meta:
        model = PointTransaction

    wallet = factory.SubFactory(WalletFactory)
    points_change = factory.Faker('random_int', min=-100, max=100)
    reason = factory.Faker('sentence', nb_words=6)
    # timestamp è auto_now_add

class RewardTemplateFactory(DjangoModelFactory):
    class Meta:
        model = RewardTemplate

    # Default a template locale creato da un Docente
    creator = factory.SubFactory(UserFactory, role=UserRole.TEACHER)
    scope = RewardTemplate.RewardScope.LOCAL
    name = factory.Sequence(lambda n: f'Template Ricompensa {n}')
    description = factory.Faker('paragraph', nb_sentences=2)
    type = factory.Faker('random_element', elements=RewardTemplate.RewardType.values)
    metadata = factory.LazyFunction(dict) # Default a dict vuoto

    # Traits
    class Params:
        global_template = factory.Trait(
            creator=factory.SubFactory(UserFactory, admin=True), # Creato da Admin
            scope=RewardTemplate.RewardScope.GLOBAL
        )
        real_world = factory.Trait(type=RewardTemplate.RewardType.REAL_WORLD)
        digital = factory.Trait(type=RewardTemplate.RewardType.DIGITAL)

class RewardFactory(DjangoModelFactory):
    class Meta:
        model = Reward

    teacher = factory.SubFactory(UserFactory, role=UserRole.TEACHER)
    template = None # Default a nessuna derivazione da template
    name = factory.Sequence(lambda n: f'Ricompensa Specifica {n}')
    description = factory.Faker('paragraph', nb_sentences=3)
    type = factory.Faker('random_element', elements=RewardTemplate.RewardType.values)
    cost_points = factory.Faker('random_int', min=10, max=500)
    availability_type = Reward.AvailabilityType.ALL_STUDENTS # Default
    metadata = factory.LazyFunction(dict)
    is_active = True

    # Traits
    class Params:
        from_template = factory.Trait(
            # Associa a un template e copia alcuni campi (la logica di copia vera è nella view)
            template=factory.SubFactory(RewardTemplateFactory),
            # name=factory.SelfAttribute('template.name'), # Potrebbe causare conflitti di sequence
            description=factory.SelfAttribute('template.description'),
            type=factory.SelfAttribute('template.type'),
            metadata=factory.SelfAttribute('template.metadata')
        )
        specific_availability = factory.Trait(
            availability_type=Reward.AvailabilityType.SPECIFIC_STUDENTS
        )

    # Gestione M2M per specific_availability
    # Usiamo RelatedFactoryList per creare le associazioni DOPO che Reward è stato creato
    @factory.post_generation
    def available_to_specific_students(obj, create, extracted, **kwargs):
        if not create or not extracted:
            # Non fare nulla se non stiamo creando o se non sono stati passati studenti
            return

        if obj.availability_type != Reward.AvailabilityType.SPECIFIC_STUDENTS:
             # Non aggiungere se il tipo non è SPECIFIC
             return

        # 'extracted' è la lista di studenti passata alla factory, es: RewardFactory(specific_availability=True, available_to_specific_students=[s1, s2])
        for student in extracted:
             # Assicuriamoci che lo studente appartenga al docente della ricompensa
             if student.teacher == obj.teacher:
                 RewardStudentSpecificAvailability.objects.create(reward=obj, student=student)
             else:
                 print(f"Attenzione (Factory): Studente {student.id} non appartiene al docente {obj.teacher.id}, non aggiunto a Reward {obj.id}")


class RewardPurchaseFactory(DjangoModelFactory):
    class Meta:
        model = RewardPurchase

    # Crea uno studente e una ricompensa associati allo stesso docente
    # Questo è un po' complesso, potremmo dover passare student/reward esplicitamente nei test
    @factory.lazy_attribute
    def student(self):
        # Crea uno studente con un docente
        return StudentFactory()

    @factory.lazy_attribute
    def reward(self):
        # Crea una ricompensa con lo stesso docente dello studente creato sopra
        # Assicurati che sia disponibile per lo studente!
        teacher = self.student.teacher
        # Crea una ricompensa disponibile a tutti per semplicità
        return RewardFactory(teacher=teacher, availability_type=Reward.AvailabilityType.ALL_STUDENTS)

    points_spent = factory.SelfAttribute('reward.cost_points') # Usa il costo della ricompensa
    status = RewardPurchase.PurchaseStatus.PURCHASED # Default
    # delivered_by, delivered_at, delivery_notes sono null/blank di default

    # Traits
    class Params:
        delivered = factory.Trait(
            status=RewardPurchase.PurchaseStatus.DELIVERED,
            delivered_by=factory.SelfAttribute('reward.teacher'), # Consegnato dal docente della ricompensa
            delivered_at=factory.LazyFunction(timezone.now)
        )
        cancelled = factory.Trait(status=RewardPurchase.PurchaseStatus.CANCELLED)