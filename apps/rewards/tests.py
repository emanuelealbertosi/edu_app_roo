from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal # Se usassimo DecimalField

# Importa modelli e factory da altre app
from apps.users.factories import UserFactory, StudentFactory
from apps.users.models import UserRole

# Importa modelli e factory locali usando percorsi assoluti
from apps.rewards.models import (
    Wallet, PointTransaction, RewardTemplate, Reward,
    RewardStudentSpecificAvailability, RewardPurchase
)
from apps.rewards.factories import (
    WalletFactory, PointTransactionFactory, RewardTemplateFactory,
    RewardFactory, RewardPurchaseFactory
)

class WalletModelTests(TestCase):

    def test_create_wallet(self):
        """ Verifica la creazione di un Wallet tramite factory (e implicitamente lo Studente). """
        wallet = WalletFactory(current_points=100)
        self.assertIsNotNone(wallet.student)
        self.assertEqual(wallet.current_points, 100)
        self.assertEqual(str(wallet), f"Wallet for {wallet.student.full_name} (100 points)")

    def test_wallet_student_unique(self):
        """
        Verifica che uno studente possa avere un solo wallet (OneToOne),
        considerando django_get_or_create = ('student',) nella factory.
        La factory restituirà l'oggetto esistente.
        """
        student = StudentFactory()
        wallet1 = WalletFactory(student=student, current_points=100)
        wallet2 = WalletFactory(student=student, current_points=50) # Dovrebbe restituire wallet1
        self.assertEqual(wallet1.pk, wallet2.pk) # Stesso oggetto
        # Verifichiamo che il saldo non sia stato sovrascritto (get_or_create non aggiorna)
        wallet1.refresh_from_db()
        self.assertEqual(wallet1.current_points, 100)
        self.assertEqual(Wallet.objects.filter(student=student).count(), 1)

    def test_add_points(self):
        """ Verifica il metodo add_points del Wallet. """
        wallet = WalletFactory(current_points=50)
        wallet.add_points(30, "Test add")
        wallet.refresh_from_db()
        self.assertEqual(wallet.current_points, 80)
        self.assertEqual(wallet.transactions.count(), 1)
        transaction = wallet.transactions.first()
        self.assertEqual(transaction.points_change, 30)
        self.assertEqual(transaction.reason, "Test add")

    def test_add_zero_or_negative_points(self):
        """ Verifica che aggiungere 0 o punti negativi non cambi il saldo. """
        wallet = WalletFactory(current_points=50)
        wallet.add_points(0, "Test zero")
        wallet.refresh_from_db()
        self.assertEqual(wallet.current_points, 50)
        self.assertEqual(wallet.transactions.count(), 0)

        # Il metodo add_points attuale ignora i negativi, non crea transazione
        wallet.add_points(-10, "Test negative add")
        wallet.refresh_from_db()
        self.assertEqual(wallet.current_points, 50)
        self.assertEqual(wallet.transactions.count(), 0)


    def test_subtract_points_sufficient(self):
        """ Verifica il metodo subtract_points con punti sufficienti. """
        wallet = WalletFactory(current_points=100)
        wallet.subtract_points(40, "Test subtract")
        wallet.refresh_from_db()
        self.assertEqual(wallet.current_points, 60)
        self.assertEqual(wallet.transactions.count(), 1)
        transaction = wallet.transactions.first()
        self.assertEqual(transaction.points_change, -40)
        self.assertEqual(transaction.reason, "Test subtract")

    def test_subtract_points_insufficient(self):
        """ Verifica che subtract_points sollevi ValueError se i punti non bastano. """
        wallet = WalletFactory(current_points=30)
        with self.assertRaisesRegex(ValueError, "Insufficient points."):
            wallet.subtract_points(40, "Test insufficient")
        wallet.refresh_from_db()
        self.assertEqual(wallet.current_points, 30) # Saldo invariato
        self.assertEqual(wallet.transactions.count(), 0) # Nessuna transazione creata

    def test_subtract_zero_or_negative_points(self):
        """ Verifica che sottrarre 0 o punti negativi sollevi ValueError. """
        wallet = WalletFactory(current_points=50)
        with self.assertRaisesRegex(ValueError, "Points to subtract must be positive."):
            wallet.subtract_points(0, "Test zero subtract")
        with self.assertRaisesRegex(ValueError, "Points to subtract must be positive."):
            wallet.subtract_points(-10, "Test negative subtract")
        self.assertEqual(wallet.current_points, 50)
        self.assertEqual(wallet.transactions.count(), 0)


class PointTransactionModelTests(TestCase):

    def test_create_point_transaction(self):
        """ Verifica la creazione di una PointTransaction. """
        transaction = PointTransactionFactory(points_change=25, reason="Manual adjustment")
        self.assertIsNotNone(transaction.wallet)
        self.assertEqual(transaction.points_change, 25)
        self.assertEqual(transaction.reason, "Manual adjustment")
        self.assertIsNotNone(transaction.timestamp)
        self.assertTrue("Added 25 points" in str(transaction))


class RewardTemplateModelTests(TestCase):

    def test_create_local_template(self):
        """ Verifica creazione template locale (default factory). """
        template = RewardTemplateFactory()
        self.assertEqual(template.scope, RewardTemplate.RewardScope.LOCAL)
        self.assertTrue(template.creator.is_teacher)
        self.assertEqual(str(template), f"{template.name} (Local)")

    def test_create_global_template(self):
        """ Verifica creazione template globale tramite trait. """
        template = RewardTemplateFactory(global_template=True)
        self.assertEqual(template.scope, RewardTemplate.RewardScope.GLOBAL)
        self.assertTrue(template.creator.is_admin)
        self.assertEqual(str(template), f"{template.name} (Global)")


class RewardModelTests(TestCase):

    def setUp(self):
        self.teacher = UserFactory(role=UserRole.TEACHER)
        self.student1 = StudentFactory(teacher=self.teacher)
        self.student2 = StudentFactory(teacher=self.teacher)
        self.other_teacher_student = StudentFactory() # Studente di altro docente

    def test_create_reward_all_students(self):
        """ Verifica creazione ricompensa disponibile a tutti. """
        reward = RewardFactory(teacher=self.teacher, availability_type=Reward.AvailabilityType.ALL_STUDENTS)
        self.assertEqual(reward.teacher, self.teacher)
        self.assertEqual(reward.availability_type, Reward.AvailabilityType.ALL_STUDENTS)
        self.assertFalse(reward.available_to_specific_students.exists()) # M2M vuota

    def test_create_reward_specific_students(self):
        """ Verifica creazione ricompensa per studenti specifici usando post_generation. """
        reward = RewardFactory(
            teacher=self.teacher,
            specific_availability=True, # Usa il trait
            available_to_specific_students=[self.student1, self.student2] # Passa studenti
        )
        self.assertEqual(reward.teacher, self.teacher)
        self.assertEqual(reward.availability_type, Reward.AvailabilityType.SPECIFIC_STUDENTS)
        self.assertEqual(reward.available_to_specific_students.count(), 2)
        self.assertIn(self.student1, reward.available_to_specific_students.all())
        self.assertIn(self.student2, reward.available_to_specific_students.all())

    def test_factory_prevents_adding_other_teacher_student(self):
         """ Verifica che la factory ignori studenti di altri docenti in post_generation. """
         reward = RewardFactory(
             teacher=self.teacher,
             specific_availability=True,
             available_to_specific_students=[self.student1, self.other_teacher_student]
         )
         self.assertEqual(reward.available_to_specific_students.count(), 1)
         self.assertIn(self.student1, reward.available_to_specific_students.all())
         self.assertNotIn(self.other_teacher_student, reward.available_to_specific_students.all())

    def test_reward_student_availability_uniqueness(self):
        """ Verifica unique_together su RewardStudentSpecificAvailability. """
        reward = RewardFactory(teacher=self.teacher, specific_availability=True)
        RewardStudentSpecificAvailability.objects.create(reward=reward, student=self.student1)
        with self.assertRaises(IntegrityError):
            RewardStudentSpecificAvailability.objects.create(reward=reward, student=self.student1)


class RewardPurchaseModelTests(TestCase):

    def test_create_reward_purchase(self):
        """ Verifica creazione acquisto tramite factory. """
        purchase = RewardPurchaseFactory()
        self.assertIsNotNone(purchase.student)
        self.assertIsNotNone(purchase.reward)
        self.assertEqual(purchase.student.teacher, purchase.reward.teacher) # Stesso docente
        self.assertEqual(purchase.points_spent, purchase.reward.cost_points)
        self.assertEqual(purchase.status, RewardPurchase.PurchaseStatus.PURCHASED)
        self.assertIsNone(purchase.delivered_by)
        self.assertIsNone(purchase.delivered_at)

    def test_create_delivered_purchase(self):
        """ Verifica creazione acquisto consegnato tramite trait. """
        purchase = RewardPurchaseFactory(delivered=True)
        self.assertEqual(purchase.status, RewardPurchase.PurchaseStatus.DELIVERED)
        self.assertEqual(purchase.delivered_by, purchase.reward.teacher)
        self.assertIsNotNone(purchase.delivered_at)
        self.assertTrue(timezone.now() - purchase.delivered_at < timezone.timedelta(seconds=5)) # Check recente

    def test_protect_reward_on_purchase_delete(self):
        """ Verifica che on_delete=PROTECT impedisca eliminazione Reward se acquistata. """
        purchase = RewardPurchaseFactory()
        reward = purchase.reward
        with self.assertRaises(IntegrityError): # O ProtectedError? IntegrityError è più generico
            reward.delete()


# --- Test API ---

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class RewardTemplateAPITests(APITestCase):
    """ Test per l'endpoint /api/rewards/reward-templates/ """

    def setUp(self):
        self.admin_user = UserFactory(admin=True, username='reward_admin')
        self.teacher1 = UserFactory(role=UserRole.TEACHER, username='reward_teacher1')
        self.teacher2 = UserFactory(role=UserRole.TEACHER, username='reward_teacher2')

        # Template globale e locali
        self.global_template = RewardTemplateFactory(global_template=True, creator=self.admin_user, name="Global T1")
        self.local_template_t1 = RewardTemplateFactory(creator=self.teacher1, name="Local T1")
        self.local_template_t2 = RewardTemplateFactory(creator=self.teacher2, name="Local T2")

        self.list_url = reverse('reward-template-list')
        self.detail_url = lambda pk: reverse('reward-template-detail', kwargs={'pk': pk})

    def test_admin_can_list_all_templates(self):
        """ Admin vede tutti i template (globali e locali). """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_teacher_can_list_own_and_global_templates(self):
        """ Docente vede i propri template locali e quelli globali. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Globale + Locale T1
        template_names = {t['name'] for t in response.data}
        self.assertEqual(template_names, {"Global T1", "Local T1"})

    def test_admin_can_create_global_template(self):
        """ Admin crea un template (forzato a globale). """
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'New Global', 'type': RewardTemplate.RewardType.DIGITAL}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_template = RewardTemplate.objects.get(pk=response.data['id'])
        self.assertEqual(new_template.scope, RewardTemplate.RewardScope.GLOBAL)
        self.assertEqual(new_template.creator, self.admin_user)

    def test_teacher_can_create_local_template(self):
        """ Docente crea un template (forzato a locale). """
        self.client.force_authenticate(user=self.teacher1)
        data = {'name': 'New Local T1', 'type': RewardTemplate.RewardType.REAL_WORLD}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_template = RewardTemplate.objects.get(pk=response.data['id'])
        self.assertEqual(new_template.scope, RewardTemplate.RewardScope.LOCAL)
        self.assertEqual(new_template.creator, self.teacher1)

    def test_admin_can_update_global_template(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {'description': 'Updated global desc'}
        response = self.client.patch(self.detail_url(self.global_template.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.global_template.refresh_from_db()
        self.assertEqual(self.global_template.description, 'Updated global desc')

    def test_admin_can_update_local_template(self):
        """ Admin può modificare anche template locali (come deciso). """
        self.client.force_authenticate(user=self.admin_user)
        data = {'description': 'Updated local desc by admin'}
        response = self.client.patch(self.detail_url(self.local_template_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.local_template_t1.refresh_from_db()
        self.assertEqual(self.local_template_t1.description, 'Updated local desc by admin')

    def test_teacher_can_update_own_local_template(self):
        self.client.force_authenticate(user=self.teacher1)
        data = {'description': 'Updated local desc by owner'}
        response = self.client.patch(self.detail_url(self.local_template_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.local_template_t1.refresh_from_db()
        self.assertEqual(self.local_template_t1.description, 'Updated local desc by owner')

    def test_teacher_cannot_update_other_local_template(self):
        self.client.force_authenticate(user=self.teacher1)
        data = {'description': 'Trying to update'}
        response = self.client.patch(self.detail_url(self.local_template_t2.pk), data)
        # Il queryset filtra, quindi il docente non trova l'oggetto -> 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_teacher_cannot_update_global_template(self):
        self.client.force_authenticate(user=self.teacher1)
        data = {'description': 'Trying to update global'}
        response = self.client.patch(self.detail_url(self.global_template.pk), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Aggiungere test per DELETE


class RewardAPITests(APITestCase):
    """ Test per l'endpoint /api/rewards/rewards/ """

    def setUp(self):
        self.teacher1 = UserFactory(role=UserRole.TEACHER, username='reward_teacher1')
        self.teacher2 = UserFactory(role=UserRole.TEACHER, username='reward_teacher2')
        self.admin_user = UserFactory(admin=True, username='reward_admin')
        self.student1_t1 = StudentFactory(teacher=self.teacher1)
        self.student2_t1 = StudentFactory(teacher=self.teacher1)
        self.student1_t2 = StudentFactory(teacher=self.teacher2)

        self.reward_t1_all = RewardFactory(teacher=self.teacher1, name="R1 T1 All", cost_points=100)
        self.reward_t1_spec = RewardFactory(
            teacher=self.teacher1, name="R1 T1 Spec", cost_points=50,
            specific_availability=True, available_to_specific_students=[self.student1_t1]
        )
        self.reward_t2 = RewardFactory(teacher=self.teacher2, name="R2 T2 All", cost_points=200)

        self.list_url = reverse('reward-list')
        self.detail_url = lambda pk: reverse('reward-detail', kwargs={'pk': pk})

    def test_teacher_can_list_own_rewards(self):
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        names = {r['name'] for r in response.data}
        self.assertEqual(names, {"R1 T1 All", "R1 T1 Spec"})

    def test_admin_can_list_all_rewards(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_teacher_can_create_reward_all(self):
        self.client.force_authenticate(user=self.teacher1)
        data = {
            'name': 'New Reward All',
            'cost_points': 75,
            'type': RewardTemplate.RewardType.DIGITAL,
            'availability_type': Reward.AvailabilityType.ALL_STUDENTS
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_reward = Reward.objects.get(pk=response.data['id'])
        self.assertEqual(new_reward.teacher, self.teacher1)
        self.assertEqual(new_reward.availability_type, Reward.AvailabilityType.ALL_STUDENTS)

    def test_teacher_can_create_reward_specific(self):
        self.client.force_authenticate(user=self.teacher1)
        data = {
            'name': 'New Reward Spec',
            'cost_points': 120,
            'type': RewardTemplate.RewardType.REAL_WORLD,
            'availability_type': Reward.AvailabilityType.SPECIFIC_STUDENTS,
            'specific_student_ids': [self.student1_t1.pk, self.student2_t1.pk]
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_reward = Reward.objects.get(pk=response.data['id'])
        self.assertEqual(new_reward.teacher, self.teacher1)
        self.assertEqual(new_reward.availability_type, Reward.AvailabilityType.SPECIFIC_STUDENTS)
        self.assertEqual(new_reward.available_to_specific_students.count(), 2)

    def test_teacher_cannot_create_reward_for_other_student(self):
        """ Verifica che la validazione nella view impedisca di aggiungere studenti non propri. """
        self.client.force_authenticate(user=self.teacher1)
        data = {
            'name': 'Invalid Reward Spec',
            'cost_points': 10,
            'type': RewardTemplate.RewardType.DIGITAL,
            'availability_type': Reward.AvailabilityType.SPECIFIC_STUDENTS,
            'specific_student_ids': [self.student1_t1.pk, self.student1_t2.pk] # student1_t2 non è di teacher1
        }
        response = self.client.post(self.list_url, data)
        # Ci aspettiamo un errore di validazione dalla perform_create
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non appartiene a questo docente', str(response.data))

    def test_teacher_can_update_own_reward_availability(self):
        """ Verifica cambio disponibilità da ALL a SPECIFIC e viceversa. """
        self.client.force_authenticate(user=self.teacher1)
        # 1. Da ALL a SPECIFIC
        data1 = {
            'availability_type': Reward.AvailabilityType.SPECIFIC_STUDENTS,
            'specific_student_ids': [self.student1_t1.pk]
        }
        response1 = self.client.patch(self.detail_url(self.reward_t1_all.pk), data1)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.reward_t1_all.refresh_from_db()
        self.assertEqual(self.reward_t1_all.availability_type, Reward.AvailabilityType.SPECIFIC_STUDENTS)
        self.assertEqual(self.reward_t1_all.available_to_specific_students.count(), 1)

        # 2. Da SPECIFIC a ALL (assicura che M2M venga pulita)
        data2 = {'availability_type': Reward.AvailabilityType.ALL_STUDENTS}
        response2 = self.client.patch(self.detail_url(self.reward_t1_all.pk), data2)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.reward_t1_all.refresh_from_db()
        self.assertEqual(self.reward_t1_all.availability_type, Reward.AvailabilityType.ALL_STUDENTS)
        self.assertEqual(self.reward_t1_all.available_to_specific_students.count(), 0)

    # Aggiungere test per retrieve, update (altri campi), delete, permessi admin/altri docenti


# Aggiungere test per StudentShopViewSet, StudentWalletViewSet, StudentPurchasesViewSet
# (tenendo conto dei placeholder per l'autenticazione studente)

# Aggiungere test per TeacherRewardDeliveryViewSet
