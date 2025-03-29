import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import UserFactory, StudentFactory
from apps.users.models import UserRole
from .factories import QuizFactory, PathwayFactory, QuestionFactory, AnswerOptionFactory
from .models import Quiz, Pathway, Question, AnswerOption

# Mark all tests in this module to use the Django database
pytestmark = pytest.mark.django_db

class AdminAccessPermissionTests(APITestCase):
    """
    Test per verificare che gli Admin abbiano accesso appropriato
    alle risorse dei Docenti (Quiz, Percorsi, etc.).
    """
    def setUp(self):
        self.admin_user = UserFactory(admin=True, username='perm_admin')
        self.teacher1 = UserFactory(role=UserRole.TEACHER, username='perm_teacher1')
        self.teacher2 = UserFactory(role=UserRole.TEACHER, username='perm_teacher2') # Added for cross-teacher tests

        self.quiz_t1 = QuizFactory(teacher=self.teacher1, title="Admin Test Quiz T1")
        self.pathway_t1 = PathwayFactory(teacher=self.teacher1, title="Admin Test Pathway T1")

        # URLs
        self.quiz_detail_url = lambda pk: reverse('quiz-detail', kwargs={'pk': pk})
        self.pathway_detail_url = lambda pk: reverse('pathway-detail', kwargs={'pk': pk})

    def test_admin_can_retrieve_other_teacher_quiz(self):
        """ Verifica che l'admin possa vedere il quiz di un altro docente. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.quiz_detail_url(self.quiz_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.quiz_t1.title)

    def test_admin_can_update_other_teacher_quiz(self):
        """ Verifica che l'admin possa modificare il quiz di un altro docente. """
        self.client.force_authenticate(user=self.admin_user)
        new_title = "Admin Updated Title"
        data = {'title': new_title}
        response = self.client.patch(self.quiz_detail_url(self.quiz_t1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.quiz_t1.refresh_from_db()
        self.assertEqual(self.quiz_t1.title, new_title)

    def test_admin_can_delete_other_teacher_quiz(self):
        """ Verifica che l'admin possa eliminare il quiz di un altro docente. """
        self.client.force_authenticate(user=self.admin_user)
        quiz_pk = self.quiz_t1.pk
        response = self.client.delete(self.quiz_detail_url(quiz_pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(pk=quiz_pk).exists())

    def test_admin_can_retrieve_other_teacher_pathway(self):
        """ Verifica che l'admin possa vedere il percorso di un altro docente. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.pathway_detail_url(self.pathway_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.pathway_t1.title)

    def test_admin_can_update_other_teacher_pathway(self):
        """ Verifica che l'admin possa modificare il percorso di un altro docente. """
        self.client.force_authenticate(user=self.admin_user)
        new_title = "Admin Updated Pathway Title"
        data = {'title': new_title}
        response = self.client.patch(self.pathway_detail_url(self.pathway_t1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pathway_t1.refresh_from_db()
        self.assertEqual(self.pathway_t1.title, new_title)

    def test_admin_can_delete_other_teacher_pathway(self):
        """ Verifica che l'admin possa eliminare il percorso di un altro docente. """
        self.client.force_authenticate(user=self.admin_user)
        pathway_pk = self.pathway_t1.pk
        response = self.client.delete(self.pathway_detail_url(pathway_pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Pathway.objects.filter(pk=pathway_pk).exists())


class TeacherAccessPermissionTests(APITestCase):
    """
    Test per verificare che un Docente NON possa accedere/modificare
    risorse di un altro Docente.
    """
    def setUp(self):
        self.teacher1 = UserFactory(role=UserRole.TEACHER, username='cross_teacher1')
        self.teacher2 = UserFactory(role=UserRole.TEACHER, username='cross_teacher2')

        # Risorse create da teacher2
        self.quiz_t2 = QuizFactory(teacher=self.teacher2, title="T2 Quiz")
        self.pathway_t2 = PathwayFactory(teacher=self.teacher2, title="T2 Pathway")
        self.question_t2 = QuestionFactory(quiz=self.quiz_t2, text="T2 Question")
        self.option_t2 = AnswerOptionFactory(question=self.question_t2, text="T2 Option")

        # URLs
        self.quiz_detail_url = lambda pk: reverse('quiz-detail', kwargs={'pk': pk})
        self.pathway_detail_url = lambda pk: reverse('pathway-detail', kwargs={'pk': pk})
        # URLs per risorse annidate (richiedono setup router annidato se non già fatto)
        # Assumiamo che gli URL siano configurati correttamente per questi test
        self.question_detail_url = lambda q_pk, pk: reverse('question-detail', kwargs={'quiz_pk': q_pk, 'pk': pk})
        self.option_detail_url = lambda q_pk, ques_pk, pk: reverse('answeroption-detail', kwargs={'quiz_pk': q_pk, 'question_pk': ques_pk, 'pk': pk})


    def test_teacher_cannot_retrieve_other_teacher_quiz(self):
        """ Verifica che teacher1 non possa vedere il quiz di teacher2. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.quiz_detail_url(self.quiz_t2.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_update_other_teacher_quiz(self):
        """ Verifica che teacher1 non possa modificare il quiz di teacher2. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'title': 'Attempt Update'}
        response = self.client.patch(self.quiz_detail_url(self.quiz_t2.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_delete_other_teacher_quiz(self):
        """ Verifica che teacher1 non possa eliminare il quiz di teacher2. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.quiz_detail_url(self.quiz_t2.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_retrieve_other_teacher_pathway(self):
        """ Verifica che teacher1 non possa vedere il percorso di teacher2. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.pathway_detail_url(self.pathway_t2.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_update_other_teacher_pathway(self):
        """ Verifica che teacher1 non possa modificare il percorso di teacher2. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'title': 'Attempt Update'}
        response = self.client.patch(self.pathway_detail_url(self.pathway_t2.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_teacher_cannot_delete_other_teacher_pathway(self):
        """ Verifica che teacher1 non possa eliminare il percorso di teacher2. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.pathway_detail_url(self.pathway_t2.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Aggiungere test simili per Question e AnswerOption se necessario


class StudentAccessPermissionTests(APITestCase):
    """
    Test per verificare che uno Studente NON possa accedere/modificare
    risorse dei Docenti (Quiz, Percorsi, etc.).
    """
    def setUp(self):
        self.teacher = UserFactory(role=UserRole.TEACHER, username='student_perm_teacher')
        self.student = StudentFactory(teacher=self.teacher) # Studente associato al docente

        # Risorse create dal docente
        self.quiz = QuizFactory(teacher=self.teacher, title="Student Test Quiz")
        self.pathway = PathwayFactory(teacher=self.teacher, title="Student Test Pathway")

        # URLs
        self.quiz_list_url = reverse('quiz-list')
        self.quiz_detail_url = lambda pk: reverse('quiz-detail', kwargs={'pk': pk})
        self.pathway_list_url = reverse('pathway-list')
        self.pathway_detail_url = lambda pk: reverse('pathway-detail', kwargs={'pk': pk})
        self.student_login_url = reverse('student-login')

    def _login_student(self, student):
        """ Helper per fare il login dello studente e ottenere il token. """
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']

    def test_student_cannot_list_quizzes(self):
        """ Verifica che uno studente non possa listare i quiz tramite l'endpoint docente. """
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.quiz_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_retrieve_quiz(self):
        """ Verifica che uno studente non possa vedere i dettagli di un quiz tramite l'endpoint docente. """
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.quiz_detail_url(self.quiz.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_create_quiz(self):
        """ Verifica che uno studente non possa creare un quiz. """
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        data = {'title': 'Student Quiz Attempt'}
        response = self.client.post(self.quiz_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_update_quiz(self):
        """ Verifica che uno studente non possa modificare un quiz. """
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        data = {'title': 'Student Update Attempt'}
        response = self.client.patch(self.quiz_detail_url(self.quiz.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_delete_quiz(self):
        """ Verifica che uno studente non possa eliminare un quiz. """
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.delete(self.quiz_detail_url(self.quiz.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_list_pathways(self):
        """ Verifica che uno studente non possa listare i percorsi tramite l'endpoint docente. """
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.pathway_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_retrieve_pathway(self):
        """ Verifica che uno studente non possa vedere i dettagli di un percorso tramite l'endpoint docente. """
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.pathway_detail_url(self.pathway.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_create_pathway(self):
        """ Verifica che uno studente non possa creare un percorso. """
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        data = {'title': 'Student Pathway Attempt'}
        response = self.client.post(self.pathway_list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_update_pathway(self):
        """ Verifica che uno studente non possa modificare un percorso. """
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        data = {'title': 'Student Update Attempt'}
        response = self.client.patch(self.pathway_detail_url(self.pathway.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_delete_pathway(self):
        """ Verifica che uno studente non possa eliminare un percorso. """
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.delete(self.pathway_detail_url(self.pathway.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

# Aggiungere qui altre classi di test per permessi studenti su altre risorse (es. grading)