import factory
from factory.django import DjangoModelFactory

# Importa modelli locali
from .models import RewardTemplate, Reward, RewardPurchase, PointTransaction, Wallet

# Importa factory da altre app (causa ciclo se non gestito)
# from apps.users.factories import UserFactory, StudentFactory

class WalletFactory(DjangoModelFactory):
    class Meta:
        model = Wallet

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
    creator = factory.SubFactory('apps.users.factories.UserFactory') # Può essere Admin o Docente
    scope = factory.Faker('random_element', elements=['global', 'local'])
    name = factory.Sequence(lambda n: f'Reward Template {n}')
    description = factory.Faker('sentence')
    type = factory.Faker('random_element', elements=['digital', 'real_world_tracked'])
    metadata = factory.LazyFunction(dict)

class RewardFactory(DjangoModelFactory):
    class Meta:
        model = Reward

    # Usa stringa per riferirsi a UserFactory
    teacher = factory.SubFactory('apps.users.factories.UserFactory', role='TEACHER') # Creato da Docente
    template = None
    name = factory.Sequence(lambda n: f'Reward {n}')
    description = factory.Faker('sentence')
    type = factory.Faker('random_element', elements=['digital', 'real_world_tracked'])
    cost_points = factory.Faker('pyint', min_value=10, max_value=1000)
    availability_type = 'all_students'
    metadata = factory.LazyFunction(dict)
    is_active = True

    # Gestione M2M per disponibilità specifica (se availability_type == 'specific_students')
    @factory.post_generation
    def specific_students(obj, create, extracted, **kwargs):
        if not create or not extracted:
            return
        if obj.availability_type == 'specific_students':
            # extracted è una lista di oggetti Student
            obj.specific_students.set(extracted)


class RewardPurchaseFactory(DjangoModelFactory):
    class Meta:
        model = RewardPurchase

    # Usa stringa per riferirsi a StudentFactory
    student = factory.SubFactory('apps.users.factories.StudentFactory')
    # Usa stringa per riferirsi a RewardFactory (anche se nello stesso file, per coerenza)
    reward = factory.SubFactory('apps.rewards.factories.RewardFactory', teacher=factory.SelfAttribute('..student.teacher'))
    points_spent = factory.LazyAttribute(lambda o: o.reward.cost_points)
    status = 'purchased'
    # delivered_by, delivered_at, delivery_notes sono null di default