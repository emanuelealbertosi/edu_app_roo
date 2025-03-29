from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal # Se usassimo DecimalField

# Importa modelli e factory da altre app
from apps.users.factories import UserFactory, StudentFactory
from apps.users.models import UserRole, User # Importa User

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
        Verifica che uno studente possa avere un solo wallet (OneToOne).
        La factory NON gestisce più l'unicità, quindi ci aspettiamo un errore DB.
        """
        student = StudentFactory()
        # Crea il primo wallet (potrebbe già esistere da altre parti del setup)
        Wallet.objects.get_or_create(student=student, defaults={'current_points': 100})
        # Tentare di creare un secondo wallet esplicitamente deve fallire
        with self.assertRaises(IntegrityError):
            Wallet.objects.create(student=student, current_points=50)
        # L'eccezione è sufficiente, il count fallisce in transazione atomica

    def test_add_points(self):
        """ Verifica il metodo add_points del Wallet. """
        # Usa get_or_create per assicurare un solo wallet
        wallet, _ = Wallet.objects.get_or_create(student=StudentFactory(), defaults={'current_points': 50})
        wallet.add_points(30, "Test add")
        wallet.refresh_from_db()
        self.assertEqual(wallet.current_points, 80)
        self.assertEqual(wallet.transactions.count(), 1)
        transaction = wallet.transactions.first()
        self.assertEqual(transaction.points_change, 30)
        self.assertEqual(transaction.reason, "Test add")

    def test_add_zero_or_negative_points(self):
        """ Verifica che aggiungere 0 o punti negativi non cambi il saldo. """
        wallet, _ = Wallet.objects.get_or_create(student=StudentFactory(), defaults={'current_points': 50})
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
        wallet, _ = Wallet.objects.get_or_create(student=StudentFactory(), defaults={'current_points': 100})
        wallet.subtract_points(40, "Test subtract")
        wallet.refresh_from_db()
        self.assertEqual(wallet.current_points, 60)
        self.assertEqual(wallet.transactions.count(), 1)
        transaction = wallet.transactions.first()
        self.assertEqual(transaction.points_change, -40)
        self.assertEqual(transaction.reason, "Test subtract")

    def test_subtract_points_insufficient(self):
        """ Verifica che subtract_points sollevi ValueError se i punti non bastano. """
        wallet, _ = Wallet.objects.get_or_create(student=StudentFactory(), defaults={'current_points': 30})
        with self.assertRaisesRegex(ValueError, "Insufficient points."):
            wallet.subtract_points(40, "Test insufficient")
        wallet.refresh_from_db()
        self.assertEqual(wallet.current_points, 30) # Saldo invariato
        self.assertEqual(wallet.transactions.count(), 0) # Nessuna transazione creata

    def test_subtract_zero_or_negative_points(self):
        """ Verifica che sottrarre 0 o punti negativi sollevi ValueError. """
        wallet, _ = Wallet.objects.get_or_create(student=StudentFactory(), defaults={'current_points': 50})
        with self.assertRaisesRegex(ValueError, "Points to subtract must be positive."):
            wallet.subtract_points(0, "Test zero subtract")
        with self.assertRaisesRegex(ValueError, "Points to subtract must be positive."):
            wallet.subtract_points(-10, "Test negative subtract")
        self.assertEqual(wallet.current_points, 50)
        self.assertEqual(wallet.transactions.count(), 0)


class PointTransactionModelTests(TestCase):

    def test_create_point_transaction(self):
        """ Verifica la creazione di una PointTransaction. """
        # Assicurati che il wallet esista prima di creare la transazione
        wallet, _ = Wallet.objects.get_or_create(student=StudentFactory())
        transaction = PointTransactionFactory(wallet=wallet, points_change=25, reason="Manual adjustment")
        self.assertEqual(transaction.wallet, wallet) # Verifica associazione corretta
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
             available_to_specific_students=[self.student1, self.other_teacher_student]
         )
         self.assertEqual(reward.available_to_specific_students.count(), 1)
         self.assertIn(self.student1, reward.available_to_specific_students.all())
         self.assertNotIn(self.other_teacher_student, reward.available_to_specific_students.all())

    def test_reward_student_availability_uniqueness(self):
        """ Verifica unique_together su RewardStudentSpecificAvailability. """
        # Crea reward con tipo specific, ma senza studenti iniziali
        reward = RewardFactory(teacher=self.teacher, availability_type=Reward.AvailabilityType.SPECIFIC_STUDENTS)
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
        # Imposta esplicitamente delivered_by perché il trait non lo fa più
        teacher = UserFactory(role=UserRole.TEACHER)
        reward = RewardFactory(teacher=teacher)
        student = StudentFactory(teacher=teacher)
        purchase = RewardPurchaseFactory(
            student=student,
            reward=reward,
            delivered=True,
            delivered_by=teacher # Imposta esplicitamente
        )
        self.assertEqual(purchase.status, RewardPurchase.PurchaseStatus.DELIVERED)
        self.assertEqual(purchase.delivered_by, teacher) # Verifica con il docente passato
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
# Importa anche i modelli necessari per i test API
from .models import RewardTemplate, Reward, RewardPurchase
from apps.users.models import UserRole # Importa UserRole

# Nota: I test API esistenti sono stati spostati qui sotto per coerenza

class RewardTemplateAPITests(APITestCase):
    """ Test per l'endpoint /api/rewards/reward-templates/ """

    def setUp(self):
        self.admin_user = UserFactory(admin=True, username='reward_admin')
        self.teacher1 = UserFactory(role=UserRole.TEACHER, username='reward_teacher1')
        self.teacher2 = UserFactory(role=UserRole.TEACHER, username='reward_teacher2')
        self.student = StudentFactory(teacher=self.teacher1) # Aggiunto studente per test permessi

        # Template globale e locali
        self.global_template = RewardTemplateFactory(global_template=True, creator=self.admin_user, name="Global T1")
        self.local_template_t1 = RewardTemplateFactory(creator=self.teacher1, name="Local T1")
        self.local_template_t2 = RewardTemplateFactory(creator=self.teacher2, name="Local T2")

        self.list_url = reverse('reward-template-list')
        self.detail_url = lambda pk: reverse('reward-template-detail', kwargs={'pk': pk})
        self.student_login_url = reverse('student-login') # Aggiunto per test studente

    def _login_student(self, student):
        """ Helper per fare il login dello studente e ottenere il token. """
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']

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
        data = {'name': 'New Local T1', 'type': RewardTemplate.RewardType.REAL_WORLD} # Già corretto qui
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_template = RewardTemplate.objects.get(pk=response.data['id'])
        self.assertEqual(new_template.scope, RewardTemplate.RewardScope.LOCAL)
        self.assertEqual(new_template.creator, self.teacher1)

    # --- Test Permessi Studente (Create/List) ---
    def test_student_cannot_list_templates(self):
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK) # Aspetta 200 OK
        self.assertEqual(len(response.data), 0) # ...con lista vuota

    def test_student_cannot_create_template(self):
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        data = {'name': 'Student Template', 'type': RewardTemplate.RewardType.DIGITAL} # Già corretto qui
        response = self.client.post(self.list_url, data)
        # perform_create solleva ValidationError -> 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Test Update ---
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

    def test_student_cannot_update_template(self):
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        data = {'description': 'Student update'}
        response = self.client.patch(self.detail_url(self.local_template_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Aspetta 404

    # --- Test Retrieve Specifici ---

    def test_admin_can_retrieve_any_template(self):
        """ Admin può recuperare qualsiasi template (globale o locale). """
        self.client.force_authenticate(user=self.admin_user)
        # Globale
        response_global = self.client.get(self.detail_url(self.global_template.pk))
        self.assertEqual(response_global.status_code, status.HTTP_200_OK)
        self.assertEqual(response_global.data['name'], self.global_template.name)
        # Locale (di teacher1)
        response_local = self.client.get(self.detail_url(self.local_template_t1.pk))
        self.assertEqual(response_local.status_code, status.HTTP_200_OK)
        self.assertEqual(response_local.data['name'], self.local_template_t1.name)

    def test_teacher_can_retrieve_own_local_template(self):
        """ Docente può recuperare il proprio template locale. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.local_template_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.local_template_t1.name)

    def test_teacher_can_retrieve_global_template(self):
        """ Docente può recuperare un template globale. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.global_template.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.global_template.name)

    def test_teacher_cannot_retrieve_other_local_template(self):
        """ Docente non può recuperare il template locale di un altro docente. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.local_template_t2.pk))
        # Il queryset filtra, quindi 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_cannot_retrieve_template(self):
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.detail_url(self.local_template_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Aspetta 404

    # --- Test DELETE ---

    def test_admin_can_delete_global_template(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url(self.global_template.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RewardTemplate.objects.filter(pk=self.global_template.pk).exists())

    def test_admin_can_delete_local_template(self):
        """ Admin può eliminare anche template locali. """
        local_pk = self.local_template_t1.pk
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url(local_pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RewardTemplate.objects.filter(pk=local_pk).exists())

    def test_teacher_can_delete_own_local_template(self):
        local_pk = self.local_template_t1.pk
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(local_pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RewardTemplate.objects.filter(pk=local_pk).exists())

    def test_teacher_cannot_delete_other_local_template(self):
        local_pk_t2 = self.local_template_t2.pk
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(local_pk_t2))
        # Il queryset filtra -> 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(RewardTemplate.objects.filter(pk=local_pk_t2).exists())

    def test_teacher_cannot_delete_global_template(self):
        global_pk = self.global_template.pk
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(global_pk))
        # Il permesso IsTemplateOwnerOrAdmin nega l'accesso
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(RewardTemplate.objects.filter(pk=global_pk).exists())

    def test_student_cannot_delete_template(self):
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.delete(self.detail_url(self.local_template_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Aspetta 404


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
            available_to_specific_students=[self.student1_t1] # Rimosso specific_availability
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
            'type': RewardTemplate.RewardType.DIGITAL, # Usa RewardTemplate.RewardType
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
            'type': RewardTemplate.RewardType.REAL_WORLD, # Usa RewardTemplate.RewardType
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
            'type': RewardTemplate.RewardType.DIGITAL, # Usa RewardTemplate.RewardType
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

    # --- Test CRUD aggiuntivi e Permessi ---

    def test_teacher_can_retrieve_own_reward(self):
        """ Verifica che un docente possa recuperare i dettagli della propria ricompensa. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.reward_t1_all.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.reward_t1_all.name)

    def test_teacher_cannot_retrieve_other_reward(self):
        """ Verifica che un docente non possa recuperare i dettagli della ricompensa di un altro. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.reward_t2.pk))
        # IsRewardOwner dovrebbe negare l'accesso (o queryset filtra -> 404)
        self.assertTrue(response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_admin_can_retrieve_any_reward(self):
        """ Verifica che un admin possa recuperare i dettagli di qualsiasi ricompensa. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.detail_url(self.reward_t2.pk)) # Ricompensa di teacher2
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.reward_t2.name)

    def test_teacher_can_update_own_reward_fields(self):
        """ Verifica che un docente possa aggiornare (PATCH) campi della propria ricompensa. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'name': 'Updated R1 Name', 'cost_points': 150, 'is_active': False}
        response = self.client.patch(self.detail_url(self.reward_t1_all.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reward_t1_all.refresh_from_db()
        self.assertEqual(self.reward_t1_all.name, 'Updated R1 Name')
        self.assertEqual(self.reward_t1_all.cost_points, 150)
        self.assertFalse(self.reward_t1_all.is_active)

    def test_teacher_cannot_update_other_reward(self):
        """ Verifica che un docente non possa aggiornare la ricompensa di un altro. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'name': 'Attempted Update'}
        response = self.client.patch(self.detail_url(self.reward_t2.pk), data, format='json')
        self.assertTrue(response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.reward_t2.refresh_from_db()
        self.assertNotEqual(self.reward_t2.name, 'Attempted Update')

    def test_admin_can_update_any_reward(self):
        """ Verifica che un admin possa aggiornare qualsiasi ricompensa. """
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'Admin Updated R2 Name', 'is_active': False}
        response = self.client.patch(self.detail_url(self.reward_t2.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reward_t2.refresh_from_db()
        self.assertEqual(self.reward_t2.name, 'Admin Updated R2 Name')
        self.assertFalse(self.reward_t2.is_active)

    def test_teacher_can_delete_own_reward(self):
        """ Verifica che un docente possa eliminare la propria ricompensa (se non acquistata). """
        # Assicurati che non ci siano acquisti per questa ricompensa
        RewardPurchase.objects.filter(reward=self.reward_t1_all).delete()
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(self.reward_t1_all.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Reward.objects.filter(pk=self.reward_t1_all.pk).exists())

    def test_teacher_cannot_delete_other_reward(self):
        """ Verifica che un docente non possa eliminare la ricompensa di un altro. """
        reward_t2_pk = self.reward_t2.pk
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(reward_t2_pk))
        self.assertTrue(response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.assertTrue(Reward.objects.filter(pk=reward_t2_pk).exists())

    def test_admin_can_delete_any_reward(self):
        """ Verifica che un admin possa eliminare qualsiasi ricompensa (se non acquistata). """
        reward_t2_pk = self.reward_t2.pk
        RewardPurchase.objects.filter(reward=self.reward_t2).delete()
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url(reward_t2_pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Reward.objects.filter(pk=reward_t2_pk).exists())

    def test_cannot_delete_reward_if_purchased(self):
        """ Verifica che la protezione on_delete impedisca l'eliminazione se ci sono acquisti. """
        RewardPurchaseFactory(reward=self.reward_t1_all, student=self.student1_t1)
        self.client.force_authenticate(user=self.teacher1) # O admin
        response = self.client.delete(self.detail_url(self.reward_t1_all.pk))
        # DRF solitamente restituisce 409 Conflict o 500 Internal Server Error in caso di ProtectedError
        # A seconda di come viene gestito l'errore a livello di view/eccezione
        self.assertTrue(response.status_code in [status.HTTP_409_CONFLICT, status.HTTP_500_INTERNAL_SERVER_ERROR, status.HTTP_400_BAD_REQUEST])
        self.assertTrue(Reward.objects.filter(pk=self.reward_t1_all.pk).exists())



class StudentShopAPITests(APITestCase):
    """ Test per /api/rewards/student/shop/ """
    def setUp(self):
        self.teacher1 = UserFactory(role=UserRole.TEACHER)
        self.teacher2 = UserFactory(role=UserRole.TEACHER) # Altro docente
        self.student1 = StudentFactory(teacher=self.teacher1)
        self.student2 = StudentFactory(teacher=self.teacher1) # Altro studente stesso docente
        self.student_t2 = StudentFactory(teacher=self.teacher2) # Studente altro docente

        # Wallet per gli studenti (creati esplicitamente)
        self.wallet1, _ = Wallet.objects.get_or_create(student=self.student1, defaults={'current_points': 200})
        self.wallet2, _ = Wallet.objects.get_or_create(student=self.student2, defaults={'current_points': 30})
        self.wallet_t2, _ = Wallet.objects.get_or_create(student=self.student_t2, defaults={'current_points': 500})

        # Ricompense
        self.reward_all_t1 = RewardFactory(teacher=self.teacher1, name="R All T1", cost_points=100, is_active=True)
        # Passa la lista direttamente a available_to_specific_students
        self.reward_spec_t1_s1 = RewardFactory(
            teacher=self.teacher1, name="R Spec T1 S1", cost_points=50, is_active=True,
            available_to_specific_students=[self.student1] # Rimosso specific_availability
        )
        self.reward_spec_t1_s2 = RewardFactory(
            teacher=self.teacher1, name="R Spec T1 S2", cost_points=20, is_active=True,
            available_to_specific_students=[self.student2] # Rimosso specific_availability
        )
        self.reward_inactive_t1 = RewardFactory(teacher=self.teacher1, name="R Inactive T1", cost_points=10, is_active=False)
        self.reward_all_t2 = RewardFactory(teacher=self.teacher2, name="R All T2", cost_points=150, is_active=True) # Ricompensa altro docente

        # URL Helpers
        self.shop_list_url = reverse('student-shop-list')
        self.purchase_url = lambda pk: reverse('student-shop-purchase', kwargs={'pk': pk})
        self.student_login_url = reverse('student-login') # Aggiunto URL login

        # Rimosso: Associazione User <-> Student (non più necessaria con login JWT)


    def _login_student(self, student): # Helper per login studente
        """ Helper per fare il login dello studente e ottenere il token. """
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']


    def test_student_sees_available_rewards_in_shop(self):
        """ Verifica che lo studente veda solo le ricompense attive e disponibili per lui. """
        # self.client.force_authenticate(user=self.student1_user) # Rimosso force_authenticate
        access_token = self._login_student(self.student1) # Usa login helper
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}') # Imposta token
        response = self.client.get(self.shop_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # R All T1, R Spec T1 S1
        reward_names = {r['name'] for r in response.data}
        self.assertEqual(reward_names, {"R All T1", "R Spec T1 S1"})
        # Verifica che non veda quelle inattive, quelle specifiche per altri, o quelle di altri docenti
        self.assertNotIn(self.reward_inactive_t1.pk, {r['id'] for r in response.data})
        self.assertNotIn(self.reward_spec_t1_s2.pk, {r['id'] for r in response.data})
        self.assertNotIn(self.reward_all_t2.pk, {r['id'] for r in response.data})
        self.client.credentials() # Pulisci token

    def test_teacher_cannot_access_student_shop(self):
        """ Verifica che un docente non possa accedere allo shop studente. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.shop_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_purchase_available_reward_with_sufficient_points(self):
        """ Verifica acquisto riuscito con punti sufficienti. """
        # self.client.force_authenticate(user=self.student1_user) # Rimosso
        access_token = self._login_student(self.student1) # Usa login
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}') # Imposta token
        initial_points = self.wallet1.current_points
        reward_cost = self.reward_all_t1.cost_points

        response = self.client.post(self.purchase_url(self.reward_all_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verifica creazione RewardPurchase
        self.assertTrue(RewardPurchase.objects.filter(student=self.student1, reward=self.reward_all_t1).exists())
        purchase = RewardPurchase.objects.get(student=self.student1, reward=self.reward_all_t1)
        self.assertEqual(purchase.points_spent, reward_cost)
        self.assertEqual(purchase.status, RewardPurchase.PurchaseStatus.PURCHASED)

        # Verifica aggiornamento Wallet
        self.wallet1.refresh_from_db()
        self.assertEqual(self.wallet1.current_points, initial_points - reward_cost)

        # Verifica creazione PointTransaction
        self.assertTrue(self.wallet1.transactions.filter(points_change=-reward_cost).exists())
        self.client.credentials() # Pulisci token

    def test_student_cannot_purchase_with_insufficient_points(self):
        """ Verifica errore acquisto con punti insufficienti. """
        # self.client.force_authenticate(user=self.student2_user) # Rimosso
        access_token = self._login_student(self.student2) # Usa login
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}') # Imposta token
        reward_cost = self.reward_all_t1.cost_points # Costa 100
        initial_points = self.wallet2.current_points

        response = self.client.post(self.purchase_url(self.reward_all_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Insufficient points', response.data.get('detail', ''))

        # Verifica che non sia stato creato l'acquisto e il saldo sia invariato
        self.assertFalse(RewardPurchase.objects.filter(student=self.student2, reward=self.reward_all_t1).exists())
        self.wallet2.refresh_from_db()
        self.assertEqual(self.wallet2.current_points, initial_points)
        self.client.credentials() # Pulisci token

    def test_student_cannot_purchase_unavailable_reward(self):
        """ Verifica errore acquisto per ricompensa non disponibile (specifica per altro studente). """
        # self.client.force_authenticate(user=self.student1_user) # Rimosso
        access_token = self._login_student(self.student1) # Usa login
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}') # Imposta token
        response = self.client.post(self.purchase_url(self.reward_spec_t1_s2.pk)) # Ricompensa per student2
        # La view dovrebbe dare 404 perché get_object_or_404 fallisce sul queryset filtrato
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(RewardPurchase.objects.filter(student=self.student1, reward=self.reward_spec_t1_s2).exists())
        self.client.credentials() # Pulisci token

    def test_student_cannot_purchase_inactive_reward(self):
        """ Verifica errore acquisto per ricompensa inattiva. """
        # self.client.force_authenticate(user=self.student1_user) # Rimosso
        access_token = self._login_student(self.student1) # Usa login
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}') # Imposta token
        response = self.client.post(self.purchase_url(self.reward_inactive_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(RewardPurchase.objects.filter(student=self.student1, reward=self.reward_inactive_t1).exists())
        self.client.credentials() # Pulisci token

    def test_student_cannot_purchase_other_teacher_reward(self):
        """ Verifica errore acquisto per ricompensa di altro docente. """
        # self.client.force_authenticate(user=self.student1_user) # Rimosso
        access_token = self._login_student(self.student1) # Usa login
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}') # Imposta token
        response = self.client.post(self.purchase_url(self.reward_all_t2.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(RewardPurchase.objects.filter(student=self.student1, reward=self.reward_all_t2).exists())
        self.client.credentials() # Pulisci token


# Importa i serializer necessari
from .serializers import WalletSerializer, PointTransactionSerializer

class StudentWalletAPITests(APITestCase):
    """ Test per /api/rewards/student/wallet/ """
    def setUp(self):
        self.teacher = UserFactory(role=UserRole.TEACHER)
        self.student = StudentFactory(teacher=self.teacher)
        self.wallet, _ = Wallet.objects.get_or_create(student=self.student, defaults={'current_points': 150})
        # Aggiungi alcune transazioni
        PointTransactionFactory(wallet=self.wallet, points_change=100, reason="Initial")
        PointTransactionFactory(wallet=self.wallet, points_change=75, reason="Quiz A")
        PointTransactionFactory(wallet=self.wallet, points_change=-25, reason="Purchase X") # Saldo: 150

        # URL Helper - Assumiamo che sia un retrieve su una risorsa singleton o custom view
        # Il nome potrebbe variare in base all'implementazione effettiva degli URL
        # CORRETTO: L'URL richiede il PK dello studente (che è il PK del wallet)
        self.wallet_url = lambda pk: reverse('student-wallet-detail', kwargs={'pk': pk})
        self.student_login_url = reverse('student-login') # Aggiunto URL login

        # Rimosso: Associazione User <-> Student


    def _login_student(self, student): # Helper per login studente
        """ Helper per fare il login dello studente e ottenere il token. """
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']


    def test_student_can_retrieve_own_wallet(self):
        """ Verifica che lo studente possa recuperare i dettagli del proprio wallet. """
        # self.client.force_authenticate(user=self.student_user) # Rimosso
        access_token = self._login_student(self.student) # Usa login
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}') # Imposta token
        response = self.client.get(self.wallet_url(pk=self.student.pk)) # Passa il PK come kwarg
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student'], self.student.pk)
        self.assertEqual(response.data['current_points'], 150)
        # Verifica che le transazioni siano incluse (se il serializer le include)
        # Il serializer di default potrebbe non includerle, dipende dall'implementazione
        # Se WalletSerializer include 'transactions' come nested:
        # self.assertTrue('transactions' in response.data)
        # self.assertEqual(len(response.data['transactions']), 3)
        self.client.credentials() # Pulisci token

    def test_teacher_cannot_retrieve_student_wallet(self):
        """ Verifica che un docente non possa accedere al wallet dello studente tramite questo endpoint. """
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(self.wallet_url(pk=self.student.pk)) # Passa il PK come kwarg
        # IsStudent dovrebbe negare l'accesso
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# Importa i serializer necessari
from .serializers import RewardPurchaseSerializer

class StudentPurchasesAPITests(APITestCase):
    """ Test per /api/rewards/student/purchases/ """
    def setUp(self):
        self.teacher = UserFactory(role=UserRole.TEACHER)
        self.student1 = StudentFactory(teacher=self.teacher)
        self.student2 = StudentFactory(teacher=self.teacher) # Altro studente

        # Ricompense
        self.reward1 = RewardFactory(teacher=self.teacher, cost_points=50)
        self.reward2 = RewardFactory(teacher=self.teacher, cost_points=100)

        # Acquisti per student1
        self.purchase1_s1 = RewardPurchaseFactory(student=self.student1, reward=self.reward1)
        self.purchase2_s1 = RewardPurchaseFactory(student=self.student1, reward=self.reward2, delivered=True, delivered_by=self.teacher) # Consegnato

        # Acquisto per student2
        self.purchase1_s2 = RewardPurchaseFactory(student=self.student2, reward=self.reward1)

        # URL Helper
        self.purchases_list_url = reverse('student-purchases-list')
        self.student_login_url = reverse('student-login') # Aggiunto URL login

        # Rimosso: Associazione User <-> Student


    def _login_student(self, student): # Helper per login studente
        """ Helper per fare il login dello studente e ottenere il token. """
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']


    def test_student_can_list_own_purchases(self):
        """ Verifica che lo studente veda solo i propri acquisti. """
        # self.client.force_authenticate(user=self.student1_user) # Rimosso
        access_token = self._login_student(self.student1) # Usa login
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}') # Imposta token
        response = self.client.get(self.purchases_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # student1 ha 2 acquisti
        purchase_ids = {p['id'] for p in response.data}
        self.assertIn(self.purchase1_s1.pk, purchase_ids)
        self.assertIn(self.purchase2_s1.pk, purchase_ids)
        self.assertNotIn(self.purchase1_s2.pk, purchase_ids) # Non vede acquisto di student2
        self.client.credentials() # Pulisci token

    def test_other_student_sees_own_purchases(self):
        """ Verifica che un altro studente veda i propri acquisti. """
        # self.client.force_authenticate(user=self.student2_user) # Rimosso
        access_token = self._login_student(self.student2) # Usa login
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}') # Imposta token
        response = self.client.get(self.purchases_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # student2 ha 1 acquisto
        self.assertEqual(response.data[0]['id'], self.purchase1_s2.pk)
        self.client.credentials() # Pulisci token

    def test_teacher_cannot_list_student_purchases(self):
        """ Verifica che un docente non possa accedere alla lista acquisti studente. """
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(self.purchases_list_url)
        # IsStudent dovrebbe negare l'accesso
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TeacherRewardDeliveryAPITests(APITestCase):
    """ Test per /api/rewards/teacher/pending-delivery/ e /api/rewards/teacher/purchases/{pk}/mark-delivered/ """
    def setUp(self):
        self.teacher1 = UserFactory(role=UserRole.TEACHER)
        self.teacher2 = UserFactory(role=UserRole.TEACHER) # Altro docente
        self.student1_t1 = StudentFactory(teacher=self.teacher1)
        self.student2_t1 = StudentFactory(teacher=self.teacher1)
        self.student1_t2 = StudentFactory(teacher=self.teacher2) # Studente altro docente

        # Ricompense reali e digitali
        self.real_reward_t1 = RewardFactory(teacher=self.teacher1, type=RewardTemplate.RewardType.REAL_WORLD, name="Real T1") # Usa RewardTemplate.RewardType
        self.digital_reward_t1 = RewardFactory(teacher=self.teacher1, type=RewardTemplate.RewardType.DIGITAL, name="Digital T1") # Usa RewardTemplate.RewardType
        self.real_reward_t2 = RewardFactory(teacher=self.teacher2, type=RewardTemplate.RewardType.REAL_WORLD, name="Real T2") # Usa RewardTemplate.RewardType

        # Acquisti in vari stati
        self.purchase_pending_t1_s1 = RewardPurchaseFactory(student=self.student1_t1, reward=self.real_reward_t1, status=RewardPurchase.PurchaseStatus.PURCHASED)
        self.purchase_pending_t1_s2 = RewardPurchaseFactory(student=self.student2_t1, reward=self.real_reward_t1, status=RewardPurchase.PurchaseStatus.PURCHASED)
        self.purchase_delivered_t1 = RewardPurchaseFactory(student=self.student1_t1, reward=self.real_reward_t1, delivered=True, delivered_by=self.teacher1) # Già consegnato
        self.purchase_digital_t1 = RewardPurchaseFactory(student=self.student1_t1, reward=self.digital_reward_t1, status=RewardPurchase.PurchaseStatus.PURCHASED) # Digitale, non dovrebbe apparire
        self.purchase_pending_t2 = RewardPurchaseFactory(student=self.student1_t2, reward=self.real_reward_t2, status=RewardPurchase.PurchaseStatus.PURCHASED) # Altro docente

        # URL Helpers
        self.list_pending_url = reverse('teacher-delivery-list-pending')
        self.mark_delivered_url = lambda pk: reverse('teacher-delivery-mark-delivered', kwargs={'pk': pk})
        self.student_login_url = reverse('student-login') # Aggiunto URL login

        # Associazione User <-> Student (necessaria solo se si testasse accesso studente)
        # ...

    def _login_student(self, student): # Helper per login studente
        """ Helper per fare il login dello studente e ottenere il token. """
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']


    def test_teacher_can_list_pending_real_world_deliveries(self):
        """ Verifica che il docente veda solo acquisti 'purchased' di tipo 'real_world' dei propri studenti. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.list_pending_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Solo i due pending di teacher1
        purchase_ids = {p['id'] for p in response.data}
        self.assertIn(self.purchase_pending_t1_s1.pk, purchase_ids)
        self.assertIn(self.purchase_pending_t1_s2.pk, purchase_ids)
        # Verifica che non veda quelli consegnati, digitali o di altri docenti
        self.assertNotIn(self.purchase_delivered_t1.pk, purchase_ids)
        self.assertNotIn(self.purchase_digital_t1.pk, purchase_ids)
        self.assertNotIn(self.purchase_pending_t2.pk, purchase_ids)

    def test_other_teacher_sees_own_pending_deliveries(self):
        """ Verifica che un altro docente veda i propri pending. """
        self.client.force_authenticate(user=self.teacher2)
        response = self.client.get(self.list_pending_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Solo quello di teacher2
        self.assertEqual(response.data[0]['id'], self.purchase_pending_t2.pk)

    def test_student_cannot_list_pending_deliveries(self):
        """ Verifica che uno studente non possa accedere a questo endpoint docente. """
        # Crea utente studente se necessario per autenticare
        if not hasattr(self.student1_t1, 'user') or not self.student1_t1.user:
             student1_user = UserFactory(username=f"student_{self.student1_t1.pk}")
             self.student1_t1.user = student1_user
             self.student1_t1.save()
        else:
             student1_user = self.student1_t1.user
        # Usa login studente invece di force_authenticate
        access_token = self._login_student(self.student1_t1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.list_pending_url)
        # Ci aspettiamo 403 perché IsTeacherUser blocca l'accesso
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials() # Pulisci token

    def test_teacher_can_mark_own_pending_delivery_as_delivered(self):
        """ Verifica che il docente possa marcare come consegnato un acquisto pending del proprio studente. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'delivery_notes': 'Consegnato a mano'}
        response = self.client.post(self.mark_delivered_url(self.purchase_pending_t1_s1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.purchase_pending_t1_s1.refresh_from_db()
        self.assertEqual(self.purchase_pending_t1_s1.status, RewardPurchase.PurchaseStatus.DELIVERED)
        self.assertEqual(self.purchase_pending_t1_s1.delivered_by, self.teacher1)
        self.assertIsNotNone(self.purchase_pending_t1_s1.delivered_at)
        self.assertEqual(self.purchase_pending_t1_s1.delivery_notes, 'Consegnato a mano')

    def test_teacher_cannot_mark_other_teacher_delivery(self):
        """ Verifica che un docente non possa marcare consegne di altri docenti. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.post(self.mark_delivered_url(self.purchase_pending_t2.pk)) # Acquisto di teacher2
        # Il queryset della view dovrebbe filtrare per docente -> 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.purchase_pending_t2.refresh_from_db()
        self.assertEqual(self.purchase_pending_t2.status, RewardPurchase.PurchaseStatus.PURCHASED) # Stato invariato

    def test_teacher_cannot_mark_already_delivered_purchase(self):
        """ Verifica che non si possa marcare come consegnato un acquisto già consegnato. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.post(self.mark_delivered_url(self.purchase_delivered_t1.pk))
        # La view dovrebbe verificare lo stato -> 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('già consegnato', response.data.get('detail', '').lower())

    def test_teacher_cannot_mark_digital_purchase(self):
        """ Verifica che non si possa marcare come consegnato un acquisto digitale. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.post(self.mark_delivered_url(self.purchase_digital_t1.pk))
        # Il queryset della view dovrebbe filtrare per tipo 'real_world' -> 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_cannot_mark_delivery(self):
        """ Verifica che uno studente non possa marcare consegne. """
        if not hasattr(self.student1_t1, 'user') or not self.student1_t1.user:
             student1_user = UserFactory(username=f"student_{self.student1_t1.pk}")
             self.student1_t1.user = student1_user
             self.student1_t1.save()
        else:
             student1_user = self.student1_t1.user
        # Usa login studente invece di force_authenticate
        access_token = self._login_student(self.student1_t1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.mark_delivered_url(self.purchase_pending_t1_s1.pk))
        # Ci aspettiamo 403 perché IsTeacherUser blocca l'accesso
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials() # Pulisci token
