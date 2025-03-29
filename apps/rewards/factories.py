import factory
from factory.django import DjangoModelFactory
from django.utils import timezone # Aggiunto import

# Importa modelli locali
from .models import RewardTemplate, Reward, RewardPurchase, PointTransaction, Wallet

# Importa factory da altre app (causa ciclo se non gestito)
# from apps.users.factories import UserFactory, StudentFactory

class WalletFactory(DjangoModelFactory):
    class Meta:
        model = Wallet
        # Rimosso: django_get_or_create = ('student',) # Causa conflitti con RelatedFactory

    # Usa stringa per riferirsi a StudentFactory
    student = factory.SubFactory('apps.users.factories.StudentFactory')
    current_points = 0

class PointTransactionFactory(DjangoModelFactory):
    class Meta:
        model = PointTransaction

    wallet = factory.SubFactory(WalletFactory)
    points_change = factory.Faker('pyint', min_value=-100, max_value=100)
    reason = factory.Faker('sentence')

class RewardTemplateFactory(DjangoModelFactory):
    class Meta:
        model = RewardTemplate

    # Usa stringa per riferirsi a UserFactory
    # Default a Docente
    creator = factory.SubFactory('apps.users.factories.UserFactory', role='TEACHER')
    scope = RewardTemplate.RewardScope.LOCAL # Usa enum, default a LOCAL
    name = factory.Sequence(lambda n: f'Reward Template {n}')
    description = factory.Faker('sentence')
    type = factory.Faker('random_element', elements=[RewardTemplate.RewardType.DIGITAL, RewardTemplate.RewardType.REAL_WORLD]) # Usa enum
    metadata = factory.LazyFunction(dict)

    class Params:
        global_template = factory.Trait(
            creator=factory.SubFactory('apps.users.factories.UserFactory', admin=True), # Associa Admin
            scope=RewardTemplate.RewardScope.GLOBAL # Imposta scope a GLOBAL
        )


class RewardFactory(DjangoModelFactory):
    class Meta:
        model = Reward

    # Usa stringa per riferirsi a UserFactory
    teacher = factory.SubFactory('apps.users.factories.UserFactory', role='TEACHER') # Creato da Docente
    template = None
    name = factory.Sequence(lambda n: f'Reward {n}')
    description = factory.Faker('sentence')
    type = factory.Faker('random_element', elements=[RewardTemplate.RewardType.DIGITAL, RewardTemplate.RewardType.REAL_WORLD]) # Usa enum
    cost_points = factory.Faker('pyint', min_value=10, max_value=1000)
    availability_type = Reward.AvailabilityType.ALL_STUDENTS # Usa enum
    metadata = factory.LazyFunction(dict)
    is_active = True

    # Rimosso Params e Trait specific_availability
    # Rimosso parametro available_to

    # Gestione M2M per disponibilità specifica
    @factory.post_generation
    def available_to_specific_students(obj, create, extracted, **kwargs):
        if not create:
            return

        # 'extracted' conterrà la lista passata come 'available_to_specific_students'
        if extracted:
            # Imposta availability_type a SPECIFIC se vengono passati studenti
            obj.availability_type = Reward.AvailabilityType.SPECIFIC_STUDENTS
            # Filtra studenti per assicurarsi che appartengano allo stesso docente della ricompensa
            valid_students = [s for s in extracted if s.teacher == obj.teacher]
            obj.available_to_specific_students.set(valid_students)
            obj.save() # Salva le modifiche a availability_type e M2M


class RewardPurchaseFactory(DjangoModelFactory):
    class Meta:
        model = RewardPurchase

    # Usa stringa per riferirsi a StudentFactory
    student = factory.SubFactory('apps.users.factories.StudentFactory')
    # Usa stringa per riferirsi a RewardFactory (anche se nello stesso file, per coerenza)
    reward = factory.SubFactory('apps.rewards.factories.RewardFactory', teacher=factory.SelfAttribute('..student.teacher'))
    points_spent = factory.LazyAttribute(lambda o: o.reward.cost_points)
    status = RewardPurchase.PurchaseStatus.PURCHASED # Usa enum
    # delivered_by, delivered_at, delivery_notes sono null di default

    class Params:
        delivered = factory.Trait(
            status=RewardPurchase.PurchaseStatus.DELIVERED,
            delivered_at=factory.LazyFunction(timezone.now)
            # Rimosso: delivered_by=factory.SelfAttribute('..reward.teacher')
            # Questo causava IndexError. Lo imposteremo nei test se necessario.
        )