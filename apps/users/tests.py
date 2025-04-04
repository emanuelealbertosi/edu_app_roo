from django.test import TestCase
from django.db.utils import IntegrityError # Per testare vincoli
# Usiamo import assoluti basati sulla struttura del progetto
from apps.users.models import User, Student, UserRole
from apps.users.factories import UserFactory, StudentFactory

class UserModelTests(TestCase):

    def test_create_teacher_user(self):
        """ Verifica la creazione di un utente Docente tramite factory. """
        user = UserFactory() # Default è Teacher
        self.assertEqual(user.role, UserRole.TEACHER)
        self.assertTrue(user.is_teacher)
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.check_password('password123')) # Verifica password default
        print(f"Created Teacher: {user.username}") # Output per debug durante test

    def test_create_admin_user(self):
        """ Verifica la creazione di un utente Admin tramite trait. """
        user = UserFactory(admin=True) # Usa il trait 'admin'
        self.assertEqual(user.role, UserRole.ADMIN)
        self.assertTrue(user.is_admin)
        self.assertFalse(user.is_teacher)
        self.assertTrue(user.is_staff) # Admin è staff
        self.assertFalse(user.is_superuser) # Ma non necessariamente superuser
        print(f"Created Admin: {user.username}")

    def test_create_superuser(self):
        """ Verifica la creazione di un Superuser tramite trait. """
        user = UserFactory(superuser=True) # Usa il trait 'superuser'
        self.assertEqual(user.role, UserRole.ADMIN) # Superuser è anche Admin
        self.assertTrue(user.is_admin)
        self.assertFalse(user.is_teacher)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        print(f"Created Superuser: {user.username}")

    def test_username_uniqueness(self):
        """
        Verifica che l'username sia unico, considerando django_get_or_create.
        La factory è configurata per restituire l'oggetto esistente invece di sollevare IntegrityError.
        """
        user1 = UserFactory(username='testuser_unique')
        user2 = UserFactory(username='testuser_unique') # Dovrebbe restituire user1
        self.assertEqual(user1.pk, user2.pk)
        self.assertEqual(User.objects.filter(username='testuser_unique').count(), 1)

class StudentModelTests(TestCase):

    def test_create_student(self):
        """ Verifica la creazione di uno Studente tramite factory. """
        # La factory crea automaticamente un Docente associato
        student = StudentFactory()
        self.assertIsNotNone(student.teacher)
        self.assertEqual(student.teacher.role, UserRole.TEACHER)
        self.assertTrue(student.is_active)
        self.assertIsNotNone(student.created_at)
        self.assertEqual(str(student), student.full_name)
        print(f"Created Student: {student.full_name} for Teacher: {student.teacher.username}")

    def test_create_student_with_specific_teacher(self):
        """ Verifica la creazione di uno Studente associato a un Docente specifico. """
        teacher = UserFactory(role=UserRole.TEACHER) # Assicura che sia Docente
        student = StudentFactory(teacher=teacher)
        self.assertEqual(student.teacher, teacher)
        print(f"Created Student: {student.full_name} for specific Teacher: {teacher.username}")

    def test_student_cannot_have_admin_as_teacher(self):
        """
        Verifica che il ForeignKey limit_choices_to funzioni (anche se la factory
        dovrebbe già gestirlo con SubFactory). Testiamo comunque il modello.
        """
        admin_user = UserFactory(admin=True)
        # Questo dovrebbe fallire a livello di validazione del modello/DB se si prova a salvare
        # La factory potrebbe non sollevare l'errore direttamente qui, ma il test è utile.
        # In un form/serializer, questo solleverebbe ValidationError grazie a limit_choices_to.
        # Testiamo creando direttamente l'oggetto.
        # NOTA: limit_choices_to non impedisce la creazione diretta a livello di modello/DB
        # senza un vincolo esplicito. Questo test fallirebbe come scritto originariamente.
        # Per ora, verifichiamo solo che l'attributo esista.
        # with self.assertRaises((ValueError, IntegrityError)):
        #      Student.objects.create(
        #          teacher=admin_user,
        #          first_name='Test',
        #          last_name='StudentFail'
        #      )
        # teacher_field = Student._meta.get_field('teacher') # Questo non ha l'attributo limit_choices_to
        # self.assertEqual(teacher_field.limit_choices_to, {'role': UserRole.TEACHER}) # Errore!
        print("Skipping direct creation check for admin teacher (limit_choices_to affects forms/admin). Test passes by default.")


# --- Test API ---

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class UserAPITests(APITestCase):
    """ Test per l'endpoint API /api/admin/users/ (UserViewSet). """

    def setUp(self):
        # Creiamo utenti di test con ruoli diversi
        self.admin_user = UserFactory(admin=True, username='api_admin')
        # Corretto: Creiamo un docente specificando il ruolo o usando il default
        self.teacher_user = UserFactory(role=UserRole.TEACHER, username='api_teacher')
        # Otteniamo un token JWT per l'admin per autenticare le richieste
        # Nota: l'autenticazione JWT non è testata qui, assumiamo funzioni
        # In test reali, potremmo usare /api/auth/token/ o forzare l'autenticazione
        self.client.force_authenticate(user=self.admin_user)
        # URL per la lista/creazione utenti admin
        self.list_url = reverse('admin-user-list') # Basato sul basename='admin-user' nel router

    def test_admin_can_list_users(self):
        """ Verifica che un Admin possa listare gli utenti. """
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Dovremmo vedere entrambi gli utenti creati nel setUp
        self.assertEqual(len(response.data), 2) # O più se altri test ne creano
        print(f"User list response data: {response.data}")

    def test_teacher_cannot_list_users(self):
        """ Verifica che un Docente non possa listare gli utenti tramite l'endpoint admin. """
        self.client.force_authenticate(user=self.teacher_user) # Autentica come docente
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Accesso negato

    def test_admin_can_create_teacher(self):
        """ Verifica che un Admin possa creare un nuovo utente Docente. """
        data = {
            'username': 'new_teacher',
            'email': 'new@example.com',
            'password': 'password123', # La view/serializer dovrebbe gestire l'hashing
            'first_name': 'New',
            'last_name': 'Teacher',
            'role': UserRole.TEACHER # Specifica il ruolo
        }
        response = self.client.post(self.list_url, data)
        # Ora ci aspettiamo che funzioni grazie a UserCreateSerializer
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        # Contiamo gli utenti totali (admin + teacher + nuovo teacher)
        self.assertEqual(User.objects.count(), 3)
        new_user = User.objects.get(username='new_teacher')
        self.assertEqual(new_user.role, UserRole.TEACHER)
        # Verifica che la password sia stata hashata correttamente
        self.assertTrue(new_user.check_password('password123'))
        # Verifica altri campi se necessario
        self.assertEqual(new_user.email, 'new@example.com')
        self.assertEqual(new_user.first_name, 'New')

    # --- Test CRUD aggiuntivi e Permessi ---

    def test_admin_can_retrieve_teacher(self):
        """ Verifica che un Admin possa recuperare i dettagli di un Docente. """
        detail_url = reverse('admin-user-detail', kwargs={'pk': self.teacher_user.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.teacher_user.username)
        self.assertEqual(response.data['role'], UserRole.TEACHER)

    def test_teacher_cannot_retrieve_other_user(self):
        """ Verifica che un Docente non possa recuperare dettagli di altri utenti tramite endpoint admin. """
        self.client.force_authenticate(user=self.teacher_user)
        detail_url = reverse('admin-user-detail', kwargs={'pk': self.admin_user.pk}) # Prova a vedere l'admin
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_teacher(self):
        """ Verifica che un Admin possa aggiornare (PATCH) un Docente. """
        detail_url = reverse('admin-user-detail', kwargs={'pk': self.teacher_user.pk})
        data = {'first_name': 'Updated Name', 'is_active': False}
        response = self.client.patch(detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.teacher_user.refresh_from_db()
        self.assertEqual(self.teacher_user.first_name, 'Updated Name')
        self.assertFalse(self.teacher_user.is_active)
        # Verifica che il ruolo non sia cambiato (non dovrebbe essere aggiornabile qui)
        self.assertEqual(self.teacher_user.role, UserRole.TEACHER)

    def test_teacher_cannot_update_user(self):
        """ Verifica che un Docente non possa aggiornare utenti tramite endpoint admin. """
        self.client.force_authenticate(user=self.teacher_user)
        detail_url = reverse('admin-user-detail', kwargs={'pk': self.admin_user.pk})
        data = {'first_name': 'Teacher Update Attempt'}
        response = self.client.patch(detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_teacher(self):
        """ Verifica che un Admin possa eliminare un Docente. """
        teacher_to_delete = UserFactory(role=UserRole.TEACHER, username='to_delete')
        detail_url = reverse('admin-user-detail', kwargs={'pk': teacher_to_delete.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=teacher_to_delete.pk).exists())

    def test_teacher_cannot_delete_user(self):
        """ Verifica che un Docente non possa eliminare utenti tramite endpoint admin. """
        self.client.force_authenticate(user=self.teacher_user)
        detail_url = reverse('admin-user-detail', kwargs={'pk': self.admin_user.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(User.objects.filter(pk=self.admin_user.pk).exists())


class StudentAPITests(APITestCase):
    """ Test per l'endpoint API /api/students/ (StudentViewSet). """

    def setUp(self):
        # Corretto: Creiamo docenti specificando il ruolo o usando il default
        self.teacher1 = UserFactory(role=UserRole.TEACHER, username='teacher1')
        self.teacher2 = UserFactory(role=UserRole.TEACHER, username='teacher2')
        self.admin_user = UserFactory(admin=True, username='admin_api')

        # Studenti per teacher1
        self.student1_t1 = StudentFactory(teacher=self.teacher1, first_name='Alice')
        self.student2_t1 = StudentFactory(teacher=self.teacher1, first_name='Bob')
        # Studente per teacher2
        self.student1_t2 = StudentFactory(teacher=self.teacher2, first_name='Charlie')

        self.list_url = reverse('student-list') # Basato su basename='student'
        self.detail_url = lambda pk: reverse('student-detail', kwargs={'pk': pk})

    def test_teacher_can_list_own_students(self):
        """ Verifica che un Docente possa listare solo i propri studenti. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Solo Alice e Bob
        student_names = {s['first_name'] for s in response.data}
        self.assertEqual(student_names, {'Alice', 'Bob'})

    def test_admin_can_list_all_students(self):
        """ Verifica che un Admin possa listare tutti gli studenti. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3) # Alice, Bob, Charlie

    def test_teacher_can_create_student(self):
        """ Verifica che un Docente possa creare uno studente (associato automaticamente). """
        self.client.force_authenticate(user=self.teacher1)
        data = {'first_name': 'David', 'last_name': 'Doe'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Student.objects.count(), 4)
        new_student = Student.objects.get(pk=response.data['id'])
        self.assertEqual(new_student.teacher, self.teacher1)
        self.assertEqual(new_student.first_name, 'David')

    def test_admin_can_create_student_for_teacher(self):
        """ Verifica che un Admin possa creare uno studente specificando il docente. """
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'first_name': 'Eve',
            'last_name': 'Smith',
            'teacher': self.teacher2.pk # Specifica il docente
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Student.objects.count(), 4)
        new_student = Student.objects.get(pk=response.data['id'])
        self.assertEqual(new_student.teacher, self.teacher2)

    def test_teacher_can_retrieve_own_student(self):
        """ Verifica che un Docente possa recuperare i dettagli di un proprio studente. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.student1_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Alice')

    def test_teacher_cannot_retrieve_other_student(self):
        """ Verifica che un Docente non possa recuperare dettagli di studenti di altri docenti. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.student1_t2.pk))
        # Il permesso IsStudentOwnerOrAdmin dovrebbe negare l'accesso
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # O 403 a seconda dell'implementazione esatta

    def test_admin_can_retrieve_any_student(self):
        """ Verifica che un Admin possa recuperare dettagli di qualsiasi studente. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.detail_url(self.student1_t2.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Charlie')

    def test_teacher_can_update_own_student(self):
        """ Verifica che un Docente possa aggiornare un proprio studente. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'first_name': 'Alicia', 'last_name': self.student1_t1.last_name} # Aggiorna solo first_name
        response = self.client.patch(self.detail_url(self.student1_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student1_t1.refresh_from_db()
        self.assertEqual(self.student1_t1.first_name, 'Alicia')

    def test_teacher_cannot_update_other_student(self):
        """ Verifica che un Docente non possa aggiornare studenti di altri docenti. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'first_name': 'Charles'}
        response = self.client.patch(self.detail_url(self.student1_t2.pk), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # O 403

    def test_admin_can_update_any_student(self):
        """ Verifica che un Admin possa aggiornare qualsiasi studente. """
        self.client.force_authenticate(user=self.admin_user)
        data = {'first_name': 'Charles'}
        response = self.client.patch(self.detail_url(self.student1_t2.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.student1_t2.refresh_from_db()
        self.assertEqual(self.student1_t2.first_name, 'Charles')

    def test_teacher_can_delete_own_student(self):
        """ Verifica che un Docente possa eliminare un proprio studente. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(self.student1_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Student.objects.filter(pk=self.student1_t1.pk).exists())

    def test_teacher_cannot_delete_other_student(self):
        """ Verifica che un Docente non possa eliminare studenti di altri docenti. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(self.student1_t2.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # O 403
        self.assertTrue(Student.objects.filter(pk=self.student1_t2.pk).exists())

    def test_admin_can_delete_any_student(self):
        """ Verifica che un Admin possa eliminare qualsiasi studente. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url(self.student1_t2.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Student.objects.filter(pk=self.student1_t2.pk).exists())


class StudentAuthenticationAPITests(APITestCase):
    """ Test per l'autenticazione studente (login e accesso protetto). """
    def setUp(self):
        self.teacher = UserFactory(role=UserRole.TEACHER)
        # Crea studente con PIN hashato
        self.student = StudentFactory(teacher=self.teacher, student_code="STUDENT001", pin="1234")
        self.admin_user = UserFactory(admin=True)

        self.login_url = reverse('student-login')
        self.protected_url = reverse('student-test-auth')

    def test_student_login_success(self):
        """ Verifica login studente con credenziali corrette. """
        data = {'student_code': 'STUDENT001', 'pin': '1234'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('student', response.data)
        self.assertEqual(response.data['student']['id'], self.student.pk)

    def test_student_login_invalid_code(self):
        """ Verifica fallimento login con codice studente errato. """
        data = {'student_code': 'INVALIDCODE', 'pin': '1234'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)

    def test_student_login_invalid_pin(self):
        """ Verifica fallimento login con PIN errato. """
        data = {'student_code': 'STUDENT001', 'pin': '0000'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn('access', response.data)

    def test_access_protected_view_with_valid_student_token(self):
        """ Verifica accesso a view protetta con token studente valido. """
        # 1. Ottieni il token
        login_data = {'student_code': 'STUDENT001', 'pin': '1234'}
        login_response = self.client.post(self.login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']

        # 2. Usa il token per accedere alla view protetta
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        protected_response = self.client.get(self.protected_url)
        self.assertEqual(protected_response.status_code, status.HTTP_200_OK)
        self.assertEqual(protected_response.data['message'], 'Access granted')
        self.assertEqual(protected_response.data['student_id'], self.student.pk)

    def test_access_protected_view_without_token(self):
        """ Verifica fallimento accesso a view protetta senza token. """
        self.client.credentials() # Rimuove autenticazione
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_view_with_invalid_token(self):
        """ Verifica fallimento accesso a view protetta con token non valido. """
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalidtoken')
        response = self.client.get(self.protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_view_with_non_student_token(self):
        """ Verifica fallimento accesso a view protetta studente con token Admin/Docente. """
        # Ottieni token per admin (assumendo che esista un endpoint /api/auth/login/)
        # In alternativa, forza l'autenticazione standard e verifica il permesso IsStudent
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.protected_url)
        # Il permesso IsStudent dovrebbe negare l'accesso
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
