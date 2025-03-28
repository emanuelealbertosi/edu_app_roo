import pytest
from django.urls import reverse
from django.utils import timezone # Import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.factories import UserFactory, StudentFactory
from apps.users.models import UserRole, User # Import User
from apps.rewards.models import PointTransaction, Wallet # Import PointTransaction e Wallet
from .factories import (
    QuizFactory, PathwayFactory, QuestionFactory, AnswerOptionFactory,
    QuizAssignmentFactory, PathwayAssignmentFactory, QuizAttemptFactory, StudentAnswerFactory
)
from .models import ( # Import models
    Quiz, Pathway, Question, AnswerOption, QuizAttempt, PathwayProgress,
    QuestionType # Import QuestionType
)

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
        # self.question_detail_url = lambda q_pk, pk: reverse('question-detail', kwargs={'quiz_pk': q_pk, 'pk': pk})
        # self.option_detail_url = lambda q_pk, ques_pk, pk: reverse('answeroption-detail', kwargs={'quiz_pk': q_pk, 'question_pk': ques_pk, 'pk': pk})


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


class PathwayPointsLogicTests(APITestCase):
    """ Test per la logica di assegnazione punti dei Percorsi. """
    def setUp(self):
        self.teacher = UserFactory(role=UserRole.TEACHER)
        self.student = StudentFactory(teacher=self.teacher)
        # Crea esplicitamente il wallet per lo studente
        Wallet.objects.get_or_create(student=self.student)

        # Crea un percorso con punti assegnati al completamento
        self.pathway_points = 50
        self.pathway = PathwayFactory(
            teacher=self.teacher,
            title="Pathway with Points",
            metadata={'points_on_completion': self.pathway_points}
        )

        # Crea due quiz per il percorso, ognuno con una domanda TF
        self.quiz1 = QuizFactory(teacher=self.teacher, title="P Quiz 1", metadata={'completion_threshold_percent': 80.0, 'points_on_completion': 10})
        self.q1_1 = QuestionFactory(quiz=self.quiz1, question_type=QuestionType.TRUE_FALSE, order=1)
        AnswerOptionFactory(question=self.q1_1, text='True', is_correct=True, order=1)
        AnswerOptionFactory(question=self.q1_1, text='False', is_correct=False, order=2)

        self.quiz2 = QuizFactory(teacher=self.teacher, title="P Quiz 2", metadata={'completion_threshold_percent': 80.0, 'points_on_completion': 15})
        self.q2_1 = QuestionFactory(quiz=self.quiz2, question_type=QuestionType.TRUE_FALSE, order=1)
        AnswerOptionFactory(question=self.q2_1, text='True', is_correct=True, order=1)
        AnswerOptionFactory(question=self.q2_1, text='False', is_correct=False, order=2)

        # Aggiungi un terzo quiz con domanda manuale
        self.quiz3_manual = QuizFactory(teacher=self.teacher, title="P Quiz 3 Manual", metadata={'completion_threshold_percent': 50.0, 'points_on_completion': 20})
        self.q3_manual = QuestionFactory(quiz=self.quiz3_manual, question_type=QuestionType.OPEN_ANSWER_MANUAL, order=1)

        self.pathway.quizzes.add(self.quiz1, through_defaults={'order': 1})
        self.pathway.quizzes.add(self.quiz2, through_defaults={'order': 2})
        self.pathway.quizzes.add(self.quiz3_manual, through_defaults={'order': 3}) # Aggiunto terzo quiz

        # Assegna il percorso allo studente
        PathwayAssignmentFactory(pathway=self.pathway, student=self.student, assigned_by=self.teacher)

        # Crea il progresso iniziale per lo studente
        self.progress = PathwayProgress.objects.create(student=self.student, pathway=self.pathway)

        # URL per completare un tentativo (assumendo che la logica pathway sia lì)
        self.complete_attempt_url = lambda pk: reverse('attempt-complete-attempt', kwargs={'pk': pk})
        self.student_login_url = reverse('student-login')

    def _login_student(self, student):
        """ Helper per fare il login dello studente e ottenere il token. """
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']

    def _complete_quiz_attempt_api(self, quiz, student, correct=True):
        """ Helper per completare un quiz tramite API, rispondendo correttamente o meno. """
        attempt = QuizAttemptFactory(quiz=quiz, student=student)
        question = quiz.questions.first() # Assume una sola domanda per semplicità
        option = AnswerOption.objects.get(question=question, is_correct=correct)
        StudentAnswerFactory(
            quiz_attempt=attempt,
            question=question,
            selected_answers={'selected_option_id': option.pk}
        )
        response = self.client.post(self.complete_attempt_url(attempt.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Errore completamento attempt: {response.data}")
        attempt.refresh_from_db()
        return attempt

    def test_points_awarded_on_first_pathway_completion(self):
        """ Verifica che i punti siano assegnati al primo completamento corretto del percorso. """
        initial_points = self.student.wallet.current_points
        quiz1_points = self.quiz1.metadata.get('points_on_completion', 0)
        quiz2_points = self.quiz2.metadata.get('points_on_completion', 0)

        # Login studente
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # --- Completa il primo quiz CORRETTAMENTE ---
        attempt1 = self._complete_quiz_attempt_api(self.quiz1, self.student, correct=True)
        self.assertEqual(attempt1.status, QuizAttempt.AttemptStatus.COMPLETED)
        self.assertGreaterEqual(attempt1.score, 80.0)

        # Verifica che il progresso sia aggiornato (last_completed_quiz_order = 1)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.last_completed_quiz_order, 1, "last_completed_quiz_order non aggiornato dopo quiz 1")
        self.assertEqual(self.progress.status, PathwayProgress.ProgressStatus.IN_PROGRESS)

        # --- Completa il secondo quiz CORRETTAMENTE ---
        attempt2 = self._complete_quiz_attempt_api(self.quiz2, self.student, correct=True)
        self.assertEqual(attempt2.status, QuizAttempt.AttemptStatus.COMPLETED)
        self.assertGreaterEqual(attempt2.score, 80.0)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.last_completed_quiz_order, 2) # Verifica ordine dopo quiz 2

        # --- Completa il terzo quiz (manuale) ---
        # Dobbiamo creare l'attempt, rispondere, completare (va in PENDING), poi gradare
        attempt3 = QuizAttemptFactory(quiz=self.quiz3_manual, student=self.student)
        manual_answer = StudentAnswerFactory(
            quiz_attempt=attempt3,
            question=self.q3_manual,
            selected_answers={'answer_text': 'Risposta per test completamento'}
        )
        # Login studente necessario per completare
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response_complete3 = self.client.post(self.complete_attempt_url(attempt3.pk))
        self.assertEqual(response_complete3.status_code, status.HTTP_200_OK)
        attempt3.refresh_from_db()
        self.assertEqual(attempt3.status, QuizAttempt.AttemptStatus.PENDING_GRADING)

        # --- Grada la risposta manuale (come docente) ---
        self.client.credentials() # Logout studente
        self.client.force_authenticate(user=self.teacher)
        grade_answer_url = lambda pk: reverse('teacher-grading-grade-answer', kwargs={'pk': pk})
        grading_data = {'is_correct': True, 'score': 100} # Assicura superamento soglia 50%
        response_grade = self.client.post(grade_answer_url(manual_answer.pk), grading_data)
        self.assertEqual(response_grade.status_code, status.HTTP_200_OK)
        attempt3.refresh_from_db()
        self.assertEqual(attempt3.status, QuizAttempt.AttemptStatus.COMPLETED)

        # --- Verifica lo stato finale del progresso e i punti ---
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, PathwayProgress.ProgressStatus.COMPLETED, "Il progresso del percorso non è COMPLETED dopo grading")
        self.assertTrue(self.progress.first_correct_completion, "first_correct_completion non è True dopo grading")
        self.assertIsNotNone(self.progress.completed_at, "completed_at non è impostato dopo grading")

        # Verifica la transazione punti per il PERCORSO
        pathway_transaction_exists = PointTransaction.objects.filter(
            wallet=self.student.wallet,
            points_change=self.pathway_points,
            reason=f"Completamento Percorso: {self.pathway.title}"
        ).exists()
        self.assertTrue(pathway_transaction_exists, "La transazione punti per il percorso non è stata creata.")

        # Verifica il saldo finale (considerando punti quiz + punti percorso)
        self.student.wallet.refresh_from_db()
        quiz3_points = self.quiz3_manual.metadata.get('points_on_completion', 0) # Recupera punti quiz 3
        expected_points = initial_points + quiz1_points + quiz2_points + quiz3_points + self.pathway_points # Includi punti quiz 3
        self.assertEqual(self.student.wallet.current_points, expected_points, "Il saldo punti finale non è corretto.")

        self.client.credentials() # Pulisci credenziali

    def test_no_pathway_points_if_quiz_failed(self):
        """ Verifica che i punti percorso non siano assegnati se un quiz non è superato. """
        initial_points = self.student.wallet.current_points
        quiz1_points = self.quiz1.metadata.get('points_on_completion', 0)

        # Login studente
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # --- Completa il primo quiz CORRETTAMENTE ---
        attempt1 = self._complete_quiz_attempt_api(self.quiz1, self.student, correct=True)
        self.assertEqual(attempt1.status, QuizAttempt.AttemptStatus.COMPLETED)
        self.assertGreaterEqual(attempt1.score, 80.0)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.last_completed_quiz_order, 1)

        # --- Completa il secondo quiz ERRONEAMENTE ---
        attempt2 = self._complete_quiz_attempt_api(self.quiz2, self.student, correct=False)
        self.assertEqual(attempt2.status, QuizAttempt.AttemptStatus.COMPLETED)
        self.assertLess(attempt2.score, 80.0) # Punteggio sotto soglia

        # --- Verifica lo stato finale del progresso e i punti ---
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, PathwayProgress.ProgressStatus.IN_PROGRESS, "Il progresso del percorso non dovrebbe essere COMPLETED")
        self.assertFalse(self.progress.first_correct_completion, "first_correct_completion dovrebbe essere False")
        self.assertIsNone(self.progress.completed_at, "completed_at non dovrebbe essere impostato")

        # Verifica che NON ci sia la transazione punti per il PERCORSO
        pathway_transaction_exists = PointTransaction.objects.filter(
            wallet=self.student.wallet,
            reason=f"Completamento Percorso: {self.pathway.title}"
        ).exists()
        self.assertFalse(pathway_transaction_exists, "La transazione punti per il percorso è stata creata erroneamente.")

        # Verifica il saldo finale (solo punti del primo quiz)
        self.student.wallet.refresh_from_db()
        expected_points = initial_points + quiz1_points
        self.assertEqual(self.student.wallet.current_points, expected_points, "Il saldo punti finale non è corretto.")

        self.client.credentials()

    def test_no_pathway_points_on_second_completion(self):
        """ Verifica che i punti percorso non siano assegnati al secondo completamento. """
        # --- Primo completamento (come nel test precedente) ---
        initial_points = self.student.wallet.current_points
        quiz1_points = self.quiz1.metadata.get('points_on_completion', 0)
        quiz2_points = self.quiz2.metadata.get('points_on_completion', 0)
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        self._complete_quiz_attempt_api(self.quiz1, self.student, correct=True)
        self._complete_quiz_attempt_api(self.quiz2, self.student, correct=True)
        # Completa e grada anche il terzo quiz
        attempt3_first = QuizAttemptFactory(quiz=self.quiz3_manual, student=self.student)
        manual_answer_first = StudentAnswerFactory(quiz_attempt=attempt3_first, question=self.q3_manual, selected_answers={'answer_text': 'Primo giro'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}') # Login studente
        self.client.post(self.complete_attempt_url(attempt3_first.pk))
        self.client.credentials() # Logout studente
        self.client.force_authenticate(user=self.teacher) # Login docente
        grade_answer_url = lambda pk: reverse('teacher-grading-grade-answer', kwargs={'pk': pk})
        self.client.post(grade_answer_url(manual_answer_first.pk), {'is_correct': True, 'score': 100})
        attempt3_first.refresh_from_db()
        self.assertEqual(attempt3_first.status, QuizAttempt.AttemptStatus.COMPLETED)

        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, PathwayProgress.ProgressStatus.COMPLETED)
        self.student.wallet.refresh_from_db() # Refresh first
        points_after_first_completion = self.student.wallet.current_points # Then get attribute
        quiz3_points = self.quiz3_manual.metadata.get('points_on_completion', 0) # Prendi punti quiz 3
        expected_first_completion_points = initial_points + quiz1_points + quiz2_points + quiz3_points + self.pathway_points # Correggi punti attesi
        self.assertEqual(points_after_first_completion, expected_first_completion_points)
        pathway_transactions_count = PointTransaction.objects.filter(reason=f"Completamento Percorso: {self.pathway.title}").count()
        self.assertEqual(pathway_transactions_count, 1)

        self.assertEqual(pathway_transactions_count, 1)

        # --- Secondo tentativo e completamento del percorso ---
        # Nota: La logica attuale non permette di "ricominciare" un percorso completato in questo modo.
        # Il test verifica che *rifacendo i quiz* non si ottengano di nuovo i punti percorso.

        print("\n--- Inizio Secondo Completamento ---")
        # Assicurati che l'autenticazione forzata del docente sia rimossa
        self.client.force_authenticate(user=None)
        # Login studente per il secondo giro
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        attempt_q1_second = self._complete_quiz_attempt_api(self.quiz1, self.student, correct=True) # Secondo tentativo quiz 1
        attempt_q2_second = self._complete_quiz_attempt_api(self.quiz2, self.student, correct=True) # Secondo tentativo quiz 2
        # Completa e grada anche il terzo quiz per il secondo giro
        attempt_q3_second = QuizAttemptFactory(quiz=self.quiz3_manual, student=self.student)
        manual_answer_second = StudentAnswerFactory(quiz_attempt=attempt_q3_second, question=self.q3_manual, selected_answers={'answer_text': 'Secondo giro'})
        self.client.post(self.complete_attempt_url(attempt_q3_second.pk)) # Studente completa
        self.client.credentials() # Logout studente
        self.client.force_authenticate(user=self.teacher) # Login docente
        self.client.post(grade_answer_url(manual_answer_second.pk), {'is_correct': True, 'score': 100}) # Docente grada
        attempt_q3_second.refresh_from_db()
        self.assertEqual(attempt_q3_second.status, QuizAttempt.AttemptStatus.COMPLETED)


        # --- Verifica punti dopo secondo completamento ---
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, PathwayProgress.ProgressStatus.COMPLETED) # Rimane completato
        # first_correct_completion dovrebbe rimanere True dal primo completamento

        # Verifica che NON sia stata creata una NUOVA transazione punti per il PERCORSO
        pathway_transactions_count_after = PointTransaction.objects.filter(reason=f"Completamento Percorso: {self.pathway.title}").count()
        self.assertEqual(pathway_transactions_count_after, pathway_transactions_count, "È stata creata una nuova transazione punti per il percorso al secondo completamento.")

        # Verifica il saldo finale (non dovrebbe essere cambiato rispetto al primo completamento)
        self.student.wallet.refresh_from_db()
        self.assertEqual(self.student.wallet.current_points, points_after_first_completion, "Il saldo punti è cambiato dopo il secondo completamento.")

        self.client.credentials()

    def test_pathway_progress_not_updated_if_quiz_below_threshold(self):
        """ Verifica che last_completed_quiz_order non venga aggiornato se il quiz è sotto soglia. """
        initial_points = self.student.wallet.current_points

        # Login studente
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # --- Completa il primo quiz ERRONEAMENTE (sotto soglia 80%) ---
        attempt1 = self._complete_quiz_attempt_api(self.quiz1, self.student, correct=False)
        self.assertEqual(attempt1.status, QuizAttempt.AttemptStatus.COMPLETED)
        self.assertLess(attempt1.score, 80.0)

        # Verifica che il progresso NON sia aggiornato
        self.progress.refresh_from_db()
        self.assertIsNone(self.progress.last_completed_quiz_order, "last_completed_quiz_order è stato aggiornato erroneamente.")
        self.assertEqual(self.progress.status, PathwayProgress.ProgressStatus.IN_PROGRESS)

        # Verifica che non siano stati assegnati punti per il quiz (la logica punti quiz è separata)
        # e che il saldo sia invariato
        self.student.wallet.refresh_from_db()
        self.assertEqual(self.student.wallet.current_points, initial_points)

        self.client.credentials()

    def test_pathway_completion_with_manual_grading(self):
        """ Verifica il completamento del percorso dopo il grading manuale dell'ultimo quiz. """
        initial_points = self.student.wallet.current_points
        quiz1_points = self.quiz1.metadata.get('points_on_completion', 0)
        quiz2_points = self.quiz2.metadata.get('points_on_completion', 0)
        # quiz3_manual non assegna punti quiz, solo il percorso

        # URL per il grading (necessario per il docente)
        grade_answer_url = lambda pk: reverse('teacher-grading-grade-answer', kwargs={'pk': pk})

        # --- Login Studente ---
        access_token = self._login_student(self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # --- Completa i primi due quiz CORRETTAMENTE ---
        attempt1 = self._complete_quiz_attempt_api(self.quiz1, self.student, correct=True)
        self.assertEqual(attempt1.status, QuizAttempt.AttemptStatus.COMPLETED)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.last_completed_quiz_order, 1)

        attempt2 = self._complete_quiz_attempt_api(self.quiz2, self.student, correct=True)
        self.assertEqual(attempt2.status, QuizAttempt.AttemptStatus.COMPLETED)
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.last_completed_quiz_order, 2)

        # --- Inizia e rispondi al terzo quiz (manuale) ---
        attempt3 = QuizAttemptFactory(quiz=self.quiz3_manual, student=self.student)
        manual_answer = StudentAnswerFactory(
            quiz_attempt=attempt3,
            question=self.q3_manual,
            selected_answers={'answer_text': 'Risposta manuale dello studente'}
        )
        # Completa il tentativo (dovrebbe andare in PENDING_GRADING)
        response_complete = self.client.post(self.complete_attempt_url(attempt3.pk))
        self.assertEqual(response_complete.status_code, status.HTTP_200_OK)
        attempt3.refresh_from_db()
        self.assertEqual(attempt3.status, QuizAttempt.AttemptStatus.PENDING_GRADING)

        # Verifica che il percorso NON sia ancora completo
        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, PathwayProgress.ProgressStatus.IN_PROGRESS)
        self.assertFalse(self.progress.first_correct_completion)
        pathway_transactions_before_grading = PointTransaction.objects.filter(reason=f"Completamento Percorso: {self.pathway.title}").count()

        # --- Logout Studente, Login Docente ---
        self.client.credentials() # Pulisce token studente
        self.client.force_authenticate(user=self.teacher)

        # --- Grada la risposta manuale CORRETTAMENTE ---
        grading_data = {'is_correct': True, 'score': 10} # Score > soglia 50%
        response_grade = self.client.post(grade_answer_url(manual_answer.pk), grading_data)
        self.assertEqual(response_grade.status_code, status.HTTP_200_OK, f"Errore grading: {response_grade.data}")

        # --- Verifica lo stato finale ---
        attempt3.refresh_from_db()
        self.assertEqual(attempt3.status, QuizAttempt.AttemptStatus.COMPLETED, "Il tentativo manuale non è COMPLETED dopo il grading")
        self.assertGreaterEqual(attempt3.score, 50.0) # Verifica che il punteggio sia stato calcolato e sia sopra soglia

        self.progress.refresh_from_db()
        self.assertEqual(self.progress.status, PathwayProgress.ProgressStatus.COMPLETED, "Il percorso non è COMPLETED dopo il grading")
        self.assertTrue(self.progress.first_correct_completion)
        self.assertIsNotNone(self.progress.completed_at)

        # Verifica che la transazione punti PERCORSO sia stata creata
        pathway_transactions_after_grading = PointTransaction.objects.filter(reason=f"Completamento Percorso: {self.pathway.title}").count()
        self.assertEqual(pathway_transactions_after_grading, pathway_transactions_before_grading + 1, "La transazione punti percorso non è stata creata dopo il grading.")

        # Verifica saldo finale
        self.student.wallet.refresh_from_db()
        quiz3_points = self.quiz3_manual.metadata.get('points_on_completion', 0) # Recupera punti quiz 3
        expected_points = initial_points + quiz1_points + quiz2_points + quiz3_points + self.pathway_points # Includi punti quiz 3
        self.assertEqual(self.student.wallet.current_points, expected_points)


# Aggiungere test per:
# - Gestione corretta di last_completed_quiz_order (es. quiz completato fuori ordine)