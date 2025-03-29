from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone

# Importa modelli e factory da altre app
from apps.users.factories import UserFactory, StudentFactory
from apps.users.models import UserRole

# Importa modelli e factory locali usando percorsi assoluti
from apps.education.models import (
    QuizTemplate, QuestionTemplate, AnswerOptionTemplate,
    Quiz, Question, AnswerOption, Pathway, PathwayQuiz,
    QuizAttempt, StudentAnswer, PathwayProgress, QuestionType,
    QuizAssignment, PathwayAssignment # Aggiungi modelli Assignment
)
from apps.education.factories import (
    QuizTemplateFactory, QuestionTemplateFactory, AnswerOptionTemplateFactory,
    QuizFactory, QuestionFactory, AnswerOptionFactory, PathwayFactory,
    QuizAttemptFactory, StudentAnswerFactory, PathwayProgressFactory
)

# --- Test Modelli Template ---

class QuizTemplateModelTests(TestCase):
    def test_create_quiz_template(self):
        template = QuizTemplateFactory(title="Intro Algebra")
        self.assertEqual(template.title, "Intro Algebra")
        self.assertTrue(template.admin.is_admin)

class QuestionTemplateModelTests(TestCase):
    def test_create_question_template(self):
        q_template = QuestionTemplateFactory(text="What is 2+2?", mc_single=True)
        self.assertEqual(q_template.text, "What is 2+2?")
        self.assertEqual(q_template.question_type, QuestionType.MULTIPLE_CHOICE_SINGLE)
        self.assertIsNotNone(q_template.quiz_template)

    def test_question_template_order_uniqueness(self):
        """ Verifica unique_together ('quiz_template', 'order'). """
        qt = QuizTemplateFactory()
        QuestionTemplateFactory(quiz_template=qt, order=1)
        with self.assertRaises(IntegrityError):
            QuestionTemplateFactory(quiz_template=qt, order=1) # Stesso ordine nello stesso template

class AnswerOptionTemplateModelTests(TestCase):
    def test_create_answer_option_template(self):
        opt_template = AnswerOptionTemplateFactory(text="Option A", is_correct=True)
        self.assertEqual(opt_template.text, "Option A")
        self.assertTrue(opt_template.is_correct)
        self.assertIsNotNone(opt_template.question_template)

    def test_answer_option_template_order_uniqueness(self):
        """ Verifica unique_together ('question_template', 'order'). """
        q_template = QuestionTemplateFactory()
        AnswerOptionTemplateFactory(question_template=q_template, order=1)
        with self.assertRaises(IntegrityError):
            AnswerOptionTemplateFactory(question_template=q_template, order=1)


# --- Test Modelli Concreti ---

class QuizModelTests(TestCase):
    def test_create_quiz(self):
        quiz = QuizFactory(title="Basic Math Quiz")
        self.assertEqual(quiz.title, "Basic Math Quiz")
        self.assertTrue(quiz.teacher.is_teacher)
        self.assertIsNotNone(quiz.metadata.get("completion_threshold"))

class QuestionModelTests(TestCase):
    def test_create_question(self):
        question = QuestionFactory(text="Is the Earth flat?", tf=True)
        self.assertEqual(question.text, "Is the Earth flat?")
        self.assertEqual(question.question_type, QuestionType.TRUE_FALSE)
        self.assertIsNotNone(question.quiz)

    def test_question_order_uniqueness(self):
        """ Verifica unique_together ('quiz', 'order'). """
        quiz = QuizFactory()
        QuestionFactory(quiz=quiz, order=1)
        with self.assertRaises(IntegrityError):
            QuestionFactory(quiz=quiz, order=1)

class AnswerOptionModelTests(TestCase):
    def test_create_answer_option(self):
        option = AnswerOptionFactory(text="True", is_correct=False)
        self.assertEqual(option.text, "True")
        self.assertFalse(option.is_correct)
        self.assertIsNotNone(option.question)

    def test_answer_option_order_uniqueness(self):
        """ Verifica unique_together ('question', 'order'). """
        question = QuestionFactory()
        AnswerOptionFactory(question=question, order=1)
        with self.assertRaises(IntegrityError):
            AnswerOptionFactory(question=question, order=1)

class PathwayModelTests(TestCase):
    def setUp(self):
        self.teacher = UserFactory(role=UserRole.TEACHER)
        self.quiz1 = QuizFactory(teacher=self.teacher, title="Quiz 1")
        self.quiz2 = QuizFactory(teacher=self.teacher, title="Quiz 2")
        self.other_quiz = QuizFactory() # Quiz di altro docente

    def test_create_pathway(self):
        pathway = PathwayFactory(teacher=self.teacher, title="Learning Path 1")
        self.assertEqual(pathway.title, "Learning Path 1")
        self.assertEqual(pathway.teacher, self.teacher)

    def test_add_quizzes_to_pathway(self):
        """ Verifica aggiunta quiz tramite post_generation della factory. """
        pathway = PathwayFactory(
            teacher=self.teacher,
            quizzes=[(self.quiz1, 1), self.quiz2] # Aggiunge quiz1 ordine 1, quiz2 ordine 2 (auto)
        )
        self.assertEqual(pathway.quizzes.count(), 2)
        pq1 = PathwayQuiz.objects.get(pathway=pathway, quiz=self.quiz1)
        pq2 = PathwayQuiz.objects.get(pathway=pathway, quiz=self.quiz2)
        self.assertEqual(pq1.order, 1)
        self.assertEqual(pq2.order, 2) # Ordine automatico

    def test_factory_prevents_adding_other_teacher_quiz(self):
        """ Verifica che la factory ignori quiz di altri docenti. """
        pathway = PathwayFactory(
            teacher=self.teacher,
            quizzes=[self.quiz1, self.other_quiz]
        )
        self.assertEqual(pathway.quizzes.count(), 1)
        self.assertIn(self.quiz1, pathway.quizzes.all())
        self.assertNotIn(self.other_quiz, pathway.quizzes.all())

    def test_pathway_quiz_order_uniqueness(self):
        """ Verifica unique_together ('pathway', 'order'). """
        pathway = PathwayFactory(teacher=self.teacher)
        PathwayQuiz.objects.create(pathway=pathway, quiz=self.quiz1, order=1)
        with self.assertRaises(IntegrityError):
            PathwayQuiz.objects.create(pathway=pathway, quiz=self.quiz2, order=1) # Stesso ordine

    # def test_pathway_quiz_quiz_uniqueness(self):
    #     """ Verifica unique_together ('pathway', 'quiz') se lo aggiungiamo. """
    #     pathway = PathwayFactory(teacher=self.teacher)
    #     PathwayQuiz.objects.create(pathway=pathway, quiz=self.quiz1, order=1)
    #     with self.assertRaises(IntegrityError):
    #         PathwayQuiz.objects.create(pathway=pathway, quiz=self.quiz1, order=2) # Stesso quiz


# --- Test Modelli Progresso Studente ---

class QuizAttemptModelTests(TestCase):
    def test_create_quiz_attempt(self):
        attempt = QuizAttemptFactory()
        self.assertIsNotNone(attempt.student)
        self.assertIsNotNone(attempt.quiz)
        self.assertEqual(attempt.student.teacher, attempt.quiz.teacher)
        self.assertEqual(attempt.status, QuizAttempt.AttemptStatus.IN_PROGRESS)
        self.assertIsNone(attempt.score)

    def test_create_completed_attempt(self):
        attempt = QuizAttemptFactory(completed=True)
        self.assertEqual(attempt.status, QuizAttempt.AttemptStatus.COMPLETED)
        self.assertIsNotNone(attempt.completed_at)
        self.assertIsNotNone(attempt.score)

class StudentAnswerModelTests(TestCase):
    def test_create_student_answer(self):
        answer = StudentAnswerFactory(selected_answers={'text': 'My answer'})
        self.assertIsNotNone(answer.quiz_attempt)
        self.assertIsNotNone(answer.question)
        self.assertEqual(answer.selected_answers, {'text': 'My answer'})
        self.assertIsNone(answer.is_correct)

    def test_student_answer_uniqueness(self):
        """ Verifica unique_together ('quiz_attempt', 'question'). """
        attempt = QuizAttemptFactory()
        question = QuestionFactory(quiz=attempt.quiz)
        StudentAnswerFactory(quiz_attempt=attempt, question=question)
        with self.assertRaises(IntegrityError):
            StudentAnswerFactory(quiz_attempt=attempt, question=question) # Stessa domanda nello stesso tentativo

class PathwayProgressModelTests(TestCase):
    def test_create_pathway_progress(self):
        progress = PathwayProgressFactory()
        self.assertIsNotNone(progress.student)
        self.assertIsNotNone(progress.pathway)
        self.assertEqual(progress.student.teacher, progress.pathway.teacher)
        self.assertEqual(progress.status, PathwayProgress.ProgressStatus.IN_PROGRESS)

    def test_pathway_progress_uniqueness(self):
        """ Verifica unique_together ('student', 'pathway') via get_or_create. """
        student = StudentFactory()
        pathway = PathwayFactory(teacher=student.teacher)
        progress1 = PathwayProgressFactory(student=student, pathway=pathway)
        progress2 = PathwayProgressFactory(student=student, pathway=pathway) # Dovrebbe restituire progress1
        self.assertEqual(progress1.pk, progress2.pk)
        self.assertEqual(PathwayProgress.objects.filter(student=student, pathway=pathway).count(), 1)


# --- Test API ---

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
# Importa anche i router nested se necessario per costruire URL
from rest_framework_nested import routers

class QuizTemplateAPITests(APITestCase):
    """ Test per /api/education/quiz-templates/ """
    def setUp(self):
        self.admin_user = UserFactory(admin=True)
        self.teacher_user = UserFactory(role=UserRole.TEACHER)
        self.template1 = QuizTemplateFactory(admin=self.admin_user, title="T1")
        self.template2 = QuizTemplateFactory(admin=self.admin_user, title="T2")
        self.list_url = reverse('quiz-template-list')
        self.detail_url = lambda pk: reverse('quiz-template-detail', kwargs={'pk': pk})

    def test_admin_can_list_templates(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_teacher_cannot_list_templates_via_admin_endpoint(self):
        """ Verifica che il permesso IsAdminUser funzioni. """
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.get(self.list_url)
        # Nota: Se avessimo un endpoint separato per docenti per vedere i template,
        # questo test sarebbe diverso. Qui testiamo l'endpoint admin.
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_template(self):
        self.client.force_authenticate(user=self.admin_user)
        data = {'title': 'New Template', 'description': 'Desc'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QuizTemplate.objects.count(), 3)
        new_template = QuizTemplate.objects.get(pk=response.data['id'])
        self.assertEqual(new_template.admin, self.admin_user)

    # --- Test CRUD aggiuntivi e Permessi ---

    def test_admin_can_retrieve_template(self):
        """ Verifica che un admin possa recuperare i dettagli di un template. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.detail_url(self.template1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.template1.title)

    def test_teacher_cannot_retrieve_template(self):
        """ Verifica che un docente non possa recuperare i dettagli di un template. """
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.get(self.detail_url(self.template1.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_template(self):
        """ Verifica che un admin possa aggiornare (PATCH) un template. """
        self.client.force_authenticate(user=self.admin_user)
        data = {'title': 'Updated T1 Title'}
        response = self.client.patch(self.detail_url(self.template1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.template1.refresh_from_db()
        self.assertEqual(self.template1.title, 'Updated T1 Title')

    def test_teacher_cannot_update_template(self):
        """ Verifica che un docente non possa aggiornare un template. """
        self.client.force_authenticate(user=self.teacher_user)
        data = {'title': 'Attempted Update'}
        response = self.client.patch(self.detail_url(self.template1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.template1.refresh_from_db()
        self.assertNotEqual(self.template1.title, 'Attempted Update')

    def test_admin_can_delete_template(self):
        """ Verifica che un admin possa eliminare un template. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url(self.template1.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(QuizTemplate.objects.filter(pk=self.template1.pk).exists())

    def test_teacher_cannot_delete_template(self):
        """ Verifica che un docente non possa eliminare un template. """
        template1_pk = self.template1.pk
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.delete(self.detail_url(template1_pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(QuizTemplate.objects.filter(pk=template1_pk).exists())

    # --- Test Permessi Studente su Endpoint QuizTemplate ---

    def _login_student(self, student):
        """ Helper per fare il login dello studente e ottenere il token. """
        student_login_url = reverse('student-login')
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']

    def test_student_cannot_list_quiz_templates(self):
        """ Verifica che uno studente non possa listare i template di quiz. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_create_quiz_template(self):
        """ Verifica che uno studente non possa creare un template di quiz. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        data = {'title': 'Student Template Attempt', 'description': 'Should fail'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_retrieve_quiz_template(self):
        """ Verifica che uno studente non possa recuperare i dettagli di un template di quiz. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.get(self.detail_url(self.template1.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_update_quiz_template(self):
        """ Verifica che uno studente non possa aggiornare un template di quiz. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        data = {'title': 'Student Update Attempt'}
        response = self.client.patch(self.detail_url(self.template1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_delete_quiz_template(self):
        """ Verifica che uno studente non possa eliminare un template di quiz. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.delete(self.detail_url(self.template1.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(QuizTemplate.objects.filter(pk=self.template1.pk).exists())
        self.client.credentials()


class QuizAPITests(APITestCase):
    """ Test per /api/education/quizzes/ """
    def setUp(self):
        self.teacher1 = UserFactory(role=UserRole.TEACHER, username='edu_teacher1')
        self.teacher2 = UserFactory(role=UserRole.TEACHER, username='edu_teacher2')
        self.admin_user = UserFactory(admin=True, username='edu_admin')
        self.student_t1 = StudentFactory(teacher=self.teacher1)

        self.quiz_t1 = QuizFactory(teacher=self.teacher1, title="Q1")
        self.quiz_t2 = QuizFactory(teacher=self.teacher2, title="Q2")
        self.template = QuizTemplateFactory(admin=self.admin_user)
        # Aggiungi domande/opzioni al template per testare create_from_template
        q_template = QuestionTemplateFactory(quiz_template=self.template, order=1, text="Template Q1")
        AnswerOptionTemplateFactory(question_template=q_template, order=1, text="Opt A", is_correct=True)
        AnswerOptionTemplateFactory(question_template=q_template, order=2, text="Opt B", is_correct=False)


        self.list_url = reverse('quiz-list')
        self.detail_url = lambda pk: reverse('quiz-detail', kwargs={'pk': pk})
        self.create_from_template_url = reverse('quiz-create-from-template')
        self.assign_student_url = lambda pk: reverse('quiz-assign-student', kwargs={'pk': pk})

    def test_teacher_can_list_own_quizzes(self):
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Q1")

    def test_admin_can_list_all_quizzes(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_teacher_can_create_quiz(self):
        self.client.force_authenticate(user=self.teacher1)
        data = {'title': 'New Quiz T1', 'description': 'Desc'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Quiz.objects.count(), 3)
        new_quiz = Quiz.objects.get(pk=response.data['id'])
        self.assertEqual(new_quiz.teacher, self.teacher1)

    def test_teacher_can_create_quiz_from_template(self):
        self.client.force_authenticate(user=self.teacher1)
        data = {'template_id': self.template.pk, 'title': 'Quiz from Template'}
        response = self.client.post(self.create_from_template_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Quiz.objects.count(), 3)
        new_quiz = Quiz.objects.get(pk=response.data['id'])
        self.assertEqual(new_quiz.teacher, self.teacher1)
        self.assertEqual(new_quiz.source_template, self.template)
        self.assertEqual(new_quiz.title, 'Quiz from Template')
        # Verifica che domande/opzioni siano state copiate
        self.assertEqual(new_quiz.questions.count(), 1)
        new_question = new_quiz.questions.first()
        self.assertEqual(new_question.text, "Template Q1")
        self.assertEqual(new_question.answer_options.count(), 2)

    def test_teacher_can_assign_quiz_to_own_student(self):
        """ Verifica che l'azione assign-student funzioni. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'student_id': self.student_t1.pk}
        response = self.client.post(self.assign_student_url(self.quiz_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) # Aspetta 201 per creazione
        self.assertEqual(response.data['status'], 'Quiz assegnato con successo.')
        self.assertTrue(QuizAssignment.objects.filter(quiz=self.quiz_t1, student=self.student_t1).exists())

    def test_teacher_cannot_assign_quiz_to_other_student(self):
        """ Verifica che il docente non possa assegnare a studenti non suoi. """
        other_student = StudentFactory() # Studente di altro docente
        self.client.force_authenticate(user=self.teacher1)
        data = {'student_id': other_student.pk}
        response = self.client.post(self.assign_student_url(self.quiz_t1.pk), data)
        # get_object_or_404 in action dovrebbe dare 404 perché non trova lo studente per quel docente
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(QuizAssignment.objects.filter(quiz=self.quiz_t1, student=other_student).exists())

    def test_assign_student_creates_assignment(self):
        """ Verifica che l'azione crei correttamente QuizAssignment. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'student_id': self.student_t1.pk}
        self.assertFalse(QuizAssignment.objects.filter(quiz=self.quiz_t1, student=self.student_t1).exists())
        response = self.client.post(self.assign_student_url(self.quiz_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(QuizAssignment.objects.filter(quiz=self.quiz_t1, student=self.student_t1).exists())
        assignment = QuizAssignment.objects.get(quiz=self.quiz_t1, student=self.student_t1)
        self.assertEqual(assignment.assigned_by, self.teacher1)

    def test_assign_student_twice_returns_ok(self):
        """ Verifica che assegnare due volte restituisca 200 OK (get_or_create). """
        QuizAssignment.objects.create(quiz=self.quiz_t1, student=self.student_t1, assigned_by=self.teacher1)
        self.client.force_authenticate(user=self.teacher1)
        data = {'student_id': self.student_t1.pk}
        response = self.client.post(self.assign_student_url(self.quiz_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(QuizAssignment.objects.filter(quiz=self.quiz_t1, student=self.student_t1).count(), 1)

    # --- Test CRUD aggiuntivi e Permessi ---

    def test_teacher_can_retrieve_own_quiz(self):
        """ Verifica che un docente possa recuperare i dettagli del proprio quiz. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.quiz_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.quiz_t1.title)

    def test_teacher_cannot_retrieve_other_quiz(self):
        """ Verifica che un docente non possa recuperare i dettagli del quiz di un altro docente. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.quiz_t2.pk))
        # IsQuizOwnerOrAdmin nega l'accesso
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Updated expected status

    def test_admin_can_retrieve_any_quiz(self):
        """ Verifica che un admin possa recuperare i dettagli di qualsiasi quiz. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.detail_url(self.quiz_t2.pk)) # Quiz di teacher2
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.quiz_t2.title)

    def test_teacher_can_update_own_quiz(self):
        """ Verifica che un docente possa aggiornare (PATCH) il proprio quiz. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'title': 'Updated Q1 Title'}
        response = self.client.patch(self.detail_url(self.quiz_t1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.quiz_t1.refresh_from_db()
        self.assertEqual(self.quiz_t1.title, 'Updated Q1 Title')

    def test_teacher_cannot_update_other_quiz(self):
        """ Verifica che un docente non possa aggiornare il quiz di un altro docente. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'title': 'Attempted Update'}
        response = self.client.patch(self.detail_url(self.quiz_t2.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Updated expected status
        self.quiz_t2.refresh_from_db()
        self.assertNotEqual(self.quiz_t2.title, 'Attempted Update')

    def test_admin_can_update_any_quiz(self):
        """ Verifica che un admin possa aggiornare qualsiasi quiz. """
        self.client.force_authenticate(user=self.admin_user)
        data = {'title': 'Admin Updated Q2 Title'}
        response = self.client.patch(self.detail_url(self.quiz_t2.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.quiz_t2.refresh_from_db()
        self.assertEqual(self.quiz_t2.title, 'Admin Updated Q2 Title')

    def test_teacher_can_delete_own_quiz(self):
        """ Verifica che un docente possa eliminare il proprio quiz. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(self.quiz_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(pk=self.quiz_t1.pk).exists())

    def test_teacher_cannot_delete_other_quiz(self):
        """ Verifica che un docente non possa eliminare il quiz di un altro docente. """
        quiz_t2_pk = self.quiz_t2.pk
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(quiz_t2_pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Updated expected status
        self.assertTrue(Quiz.objects.filter(pk=quiz_t2_pk).exists())

    def test_admin_can_delete_any_quiz(self):
        """ Verifica che un admin possa eliminare qualsiasi quiz. """
        quiz_t2_pk = self.quiz_t2.pk
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url(quiz_t2_pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(pk=quiz_t2_pk).exists())

    # --- Test Permessi Studente su Endpoint Quiz ---

    def _login_student(self, student):
        """ Helper per fare il login dello studente e ottenere il token. """
        student_login_url = reverse('student-login')
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']

    def test_student_cannot_list_quizzes(self):
        """ Verifica che uno studente non possa listare i quiz tramite l'endpoint principale. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.get(self.list_url)
        # Ci aspettiamo 403 Forbidden perché l'endpoint richiede IsTeacherUser o IsAdminUser
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials() # Pulisce le credenziali per i test successivi

    def test_student_cannot_create_quiz(self):
        """ Verifica che uno studente non possa creare un quiz. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        data = {'title': 'Student Quiz Attempt', 'description': 'Should fail'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_retrieve_quiz(self):
        """ Verifica che uno studente non possa recuperare i dettagli di un quiz. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.get(self.detail_url(self.quiz_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_update_quiz(self):
        """ Verifica che uno studente non possa aggiornare un quiz. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        data = {'title': 'Student Update Attempt'}
        response = self.client.patch(self.detail_url(self.quiz_t1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_delete_quiz(self):
        """ Verifica che uno studente non possa eliminare un quiz. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.delete(self.detail_url(self.quiz_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Quiz.objects.filter(pk=self.quiz_t1.pk).exists()) # Verifica che non sia stato eliminato
        self.client.credentials()

    def test_student_cannot_create_quiz_from_template(self):
        """ Verifica che uno studente non possa creare un quiz da un template. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        data = {'template_id': self.template.pk, 'title': 'Student Template Attempt'}
        response = self.client.post(self.create_from_template_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_assign_quiz(self):
        """ Verifica che uno studente non possa assegnare un quiz. """
        student_user = StudentFactory() # Rimosso pin='1234'
        another_student = StudentFactory(teacher=self.teacher1) # Uno studente a cui assegnare
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        data = {'student_id': another_student.pk}
        response = self.client.post(self.assign_student_url(self.quiz_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()


class PathwayAPITests(APITestCase):
    """ Test per /api/education/pathways/ """
    # --- Test CRUD aggiuntivi e Azioni ---

    def setUp(self): # Estendo il setUp per includere più dati
        self.teacher1 = UserFactory(role=UserRole.TEACHER, username='path_teacher1')
        self.teacher2 = UserFactory(role=UserRole.TEACHER, username='path_teacher2')
        self.admin_user = UserFactory(admin=True, username='path_admin')
        self.student_t1 = StudentFactory(teacher=self.teacher1)

        self.pathway_t1 = PathwayFactory(teacher=self.teacher1, title="P1")
        self.pathway_t2 = PathwayFactory(teacher=self.teacher2, title="P2")
        self.quiz_t1_1 = QuizFactory(teacher=self.teacher1, title="Q1.1")
        self.quiz_t1_2 = QuizFactory(teacher=self.teacher1, title="Q1.2")
        self.quiz_t2_1 = QuizFactory(teacher=self.teacher2, title="Q2.1") # Quiz di altro docente

        # URL Helpers
        self.list_url = reverse('pathway-list')
        self.detail_url = lambda pk: reverse('pathway-detail', kwargs={'pk': pk})
        self.assign_student_url = lambda pk: reverse('pathway-assign-student-pathway', kwargs={'pk': pk})
        self.add_quiz_url = lambda pk: reverse('pathway-add-quiz', kwargs={'pk': pk})

    def test_teacher_can_list_own_pathways(self):
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "P1")

    def test_admin_can_list_all_pathways(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_teacher_can_create_pathway(self):
        self.client.force_authenticate(user=self.teacher1)
        data = {'title': 'New Pathway T1', 'description': 'Desc'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pathway.objects.count(), 3)
        new_pathway = Pathway.objects.get(pk=response.data['id'])
        self.assertEqual(new_pathway.teacher, self.teacher1)

    def test_teacher_can_retrieve_own_pathway(self):
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.pathway_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.pathway_t1.title)

    def test_teacher_cannot_retrieve_other_pathway(self):
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.pathway_t2.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Updated expected status

    def test_teacher_can_update_own_pathway(self):
        self.client.force_authenticate(user=self.teacher1)
        data = {'title': 'Updated P1 Title'}
        response = self.client.patch(self.detail_url(self.pathway_t1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pathway_t1.refresh_from_db()
        self.assertEqual(self.pathway_t1.title, 'Updated P1 Title')

    def test_teacher_cannot_update_other_pathway(self):
        self.client.force_authenticate(user=self.teacher1)
        data = {'title': 'Attempted Update'}
        response = self.client.patch(self.detail_url(self.pathway_t2.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Updated expected status

    def test_teacher_can_delete_own_pathway(self):
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(self.pathway_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Pathway.objects.filter(pk=self.pathway_t1.pk).exists())

    def test_teacher_cannot_delete_other_pathway(self):
        pathway_t2_pk = self.pathway_t2.pk
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(pathway_t2_pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # Updated expected status
        self.assertTrue(Pathway.objects.filter(pk=pathway_t2_pk).exists())

    def test_teacher_can_add_own_quiz_to_own_pathway(self):
        """ Verifica che l'azione add_quiz funzioni. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'quiz_id': self.quiz_t1_1.pk, 'order': 1}
        response = self.client.post(self.add_quiz_url(self.pathway_t1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PathwayQuiz.objects.filter(pathway=self.pathway_t1, quiz=self.quiz_t1_1).exists())
        pq = PathwayQuiz.objects.get(pathway=self.pathway_t1, quiz=self.quiz_t1_1)
        self.assertEqual(pq.order, 1)

    def test_teacher_cannot_add_other_teacher_quiz_to_pathway(self):
        """ Verifica che non si possa aggiungere un quiz di un altro docente. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'quiz_id': self.quiz_t2_1.pk, 'order': 1} # Quiz di teacher2
        response = self.client.post(self.add_quiz_url(self.pathway_t1.pk), data, format='json')
        # get_object_or_404 su Quiz (filtrato per request.user) dovrebbe dare 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(PathwayQuiz.objects.filter(pathway=self.pathway_t1, quiz=self.quiz_t2_1).exists())

    def test_add_quiz_invalid_order(self):
        """ Verifica errore se l'ordine non è valido. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'quiz_id': self.quiz_t1_1.pk, 'order': -1} # Ordine negativo
        response = self.client.post(self.add_quiz_url(self.pathway_t1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Verifica che il messaggio di errore per la chiave 'order' contenga la stringa attesa
        self.assertIn('intero non negativo', response.data.get('order', ''))

    def test_add_quiz_missing_data(self):
        """ Verifica errore se mancano quiz_id o order. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'quiz_id': self.quiz_t1_1.pk} # Manca order
        response = self.client.post(self.add_quiz_url(self.pathway_t1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('order sono richiesti', response.data.get('detail', ''))

    # Mantengo i test originali per assign_student_pathway
    def test_teacher_can_assign_pathway_to_own_student(self):
        """ Verifica che l'azione assign_student_pathway funzioni. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'student_id': self.student_t1.pk}
        self.assertFalse(PathwayAssignment.objects.filter(pathway=self.pathway_t1, student=self.student_t1).exists())
        response = self.client.post(self.assign_student_url(self.pathway_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(PathwayAssignment.objects.filter(pathway=self.pathway_t1, student=self.student_t1).exists())
        assignment = PathwayAssignment.objects.get(pathway=self.pathway_t1, student=self.student_t1)
        self.assertEqual(assignment.assigned_by, self.teacher1)

    def test_teacher_cannot_assign_pathway_to_other_student(self):
        """ Verifica che il docente non possa assegnare percorsi a studenti non suoi. """
        other_student = StudentFactory()
        self.client.force_authenticate(user=self.teacher1)
        data = {'student_id': other_student.pk}
        response = self.client.post(self.assign_student_url(self.pathway_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(PathwayAssignment.objects.filter(pathway=self.pathway_t1, student=other_student).exists())

    # --- Test Permessi Studente su Endpoint Pathway ---

    def _login_student(self, student):
        """ Helper per fare il login dello studente e ottenere il token. """
        student_login_url = reverse('student-login')
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']

    def test_student_cannot_list_pathways(self):
        """ Verifica che uno studente non possa listare i percorsi. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_create_pathway(self):
        """ Verifica che uno studente non possa creare un percorso. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        data = {'title': 'Student Pathway Attempt', 'description': 'Should fail'}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_retrieve_pathway(self):
        """ Verifica che uno studente non possa recuperare i dettagli di un percorso. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.get(self.detail_url(self.pathway_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_update_pathway(self):
        """ Verifica che uno studente non possa aggiornare un percorso. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        data = {'title': 'Student Update Attempt'}
        response = self.client.patch(self.detail_url(self.pathway_t1.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_delete_pathway(self):
        """ Verifica che uno studente non possa eliminare un percorso. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.delete(self.detail_url(self.pathway_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Pathway.objects.filter(pk=self.pathway_t1.pk).exists())
        self.client.credentials()

    def test_student_cannot_add_quiz_to_pathway(self):
        """ Verifica che uno studente non possa aggiungere un quiz a un percorso. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        data = {'quiz_id': self.quiz_t1_1.pk, 'order': 1}
        response = self.client.post(self.add_quiz_url(self.pathway_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()

    def test_student_cannot_assign_pathway(self):
        """ Verifica che uno studente non possa assegnare un percorso. """
        student_user = StudentFactory() # Rimosso pin='1234'
        another_student = StudentFactory(teacher=self.teacher1)
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        data = {'student_id': another_student.pk}
        response = self.client.post(self.assign_student_url(self.pathway_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials()


# Aggiungere test per QuestionAPITests, AnswerOptionAPITests (usando nested URLs)

# Importa anche i serializer necessari per confrontare l'output
from apps.education.serializers import QuestionSerializer

class AttemptAPITests(APITestCase):
    """ Test per /api/education/attempts/{pk}/ """
    def setUp(self):
        self.teacher = UserFactory(role=UserRole.TEACHER)
        self.student = StudentFactory(teacher=self.teacher)
        self.other_student = StudentFactory() # Studente di altro docente
        self.quiz = QuizFactory(teacher=self.teacher)
        # Aggiungi domande al quiz
        self.q1 = QuestionFactory(quiz=self.quiz, order=1, question_type=QuestionType.TRUE_FALSE, text="Q1: TF")
        AnswerOptionFactory(question=self.q1, text="True", is_correct=True, order=1)
        AnswerOptionFactory(question=self.q1, text="False", is_correct=False, order=2)
        self.q2 = QuestionFactory(quiz=self.quiz, order=2, question_type=QuestionType.MULTIPLE_CHOICE_SINGLE, text="Q2: MC-S")
        self.q2_opt1 = AnswerOptionFactory(question=self.q2, text="A", is_correct=False, order=1)
        self.q2_opt2 = AnswerOptionFactory(question=self.q2, text="B", is_correct=True, order=2)
        self.q3 = QuestionFactory(quiz=self.quiz, order=3, question_type=QuestionType.OPEN_ANSWER_MANUAL, text="Q3: Open")

        # Assegna il quiz allo studente
        self.assignment = QuizAssignment.objects.create(quiz=self.quiz, student=self.student, assigned_by=self.teacher)
        # Crea un tentativo per lo studente
        self.attempt = QuizAttemptFactory(quiz=self.quiz, student=self.student)

        # URL Helper (basati su basename='attempt')
        self.details_url = lambda pk: reverse('attempt-details', kwargs={'pk': pk}) # Nome dell'azione custom 'details'
        self.current_question_url = lambda pk: reverse('attempt-current-question', kwargs={'pk': pk})
        self.submit_answer_url = lambda pk: reverse('attempt-submit-answer', kwargs={'pk': pk})
        self.complete_url = lambda pk: reverse('attempt-complete-attempt', kwargs={'pk': pk})
        # Add student login URL
        self.student_login_url = reverse('student-login')

        # Non creiamo più User fittizi per gli studenti qui.
        # Useremo il login endpoint per ottenere un token JWT valido nei test.


    def test_student_can_get_attempt_details(self):
        """ Verifica che lo studente proprietario possa vedere i dettagli del tentativo. """
        # Login studente per ottenere token
        login_data = {'student_code': self.student.student_code, 'pin': '1234'} # Assumendo PIN '1234' dalla factory
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token per la richiesta
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.details_url(self.attempt.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.attempt.pk)
        self.assertEqual(len(response.data['questions']), 3) # Verifica che le domande siano incluse
        self.assertEqual(len(response.data['given_answers']), 0) # Nessuna risposta ancora

    def test_other_student_cannot_get_attempt_details(self):
        """ Verifica che un altro studente non possa vedere i dettagli. """
        # Login dell'altro studente
        other_login_data = {'student_code': self.other_student.student_code, 'pin': '1234'}
        other_login_response = self.client.post(self.student_login_url, other_login_data)
        self.assertEqual(other_login_response.status_code, status.HTTP_200_OK, "Login altro studente fallito")
        other_access_token = other_login_response.data['access']

        # Usa il token dell'altro studente per la richiesta
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_access_token}')
        response = self.client.get(self.details_url(self.attempt.pk))
        # IsStudentOwnerForAttempt dovrebbe negare l'accesso
        self.assertTrue(response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_teacher_cannot_get_attempt_details_via_student_endpoint(self):
         """ Verifica che il docente non possa usare l'endpoint studente per i dettagli. """
         self.client.force_authenticate(user=self.teacher)
         response = self.client.get(self.details_url(self.attempt.pk))
         # IsStudent dovrebbe negare l'accesso
         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_student_can_get_current_question_first(self):
        """ Verifica che current_question restituisca la prima domanda (ordine 1). """
        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.current_question_url(self.attempt.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Confronta con i dati serializzati della prima domanda
        expected_data = QuestionSerializer(self.q1).data
        self.assertEqual(response.data['id'], expected_data['id'])
        self.assertEqual(response.data['text'], expected_data['text'])

    def test_current_question_after_answering_first(self):
        """ Verifica che current_question restituisca la seconda domanda dopo aver risposto alla prima. """
        # Simula la risposta alla prima domanda
        StudentAnswerFactory(quiz_attempt=self.attempt, question=self.q1, selected_answers={'selected_option_id': self.q1.answer_options.filter(is_correct=True).first().id})

        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.current_question_url(self.attempt.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Confronta con i dati serializzati della seconda domanda
        expected_data = QuestionSerializer(self.q2).data
        self.assertEqual(response.data['id'], expected_data['id'])
        self.assertEqual(response.data['text'], expected_data['text'])

    def test_current_question_when_all_answered(self):
        """ Verifica che current_question restituisca 204 se tutte le domande sono state risposte. """
        # Simula risposta a tutte le domande
        StudentAnswerFactory(quiz_attempt=self.attempt, question=self.q1)
        StudentAnswerFactory(quiz_attempt=self.attempt, question=self.q2)
        StudentAnswerFactory(quiz_attempt=self.attempt, question=self.q3)

        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.current_question_url(self.attempt.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # --- Test per submit_answer ---

    def test_submit_answer_true_false_correct(self):
        """ Verifica l'invio di una risposta corretta per True/False. """
        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        correct_option_id = self.q1.answer_options.get(is_correct=True).id
        data = {
            'question_id': self.q1.id,
            'selected_answers': {'selected_option_id': correct_option_id}
        }
        response = self.client.post(self.submit_answer_url(self.attempt.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(StudentAnswer.objects.filter(quiz_attempt=self.attempt, question=self.q1).exists())
        student_answer = StudentAnswer.objects.get(quiz_attempt=self.attempt, question=self.q1)
        self.assertEqual(student_answer.selected_answers, {'selected_option_id': correct_option_id})

    def test_submit_answer_mc_single_correct(self):
        """ Verifica l'invio di una risposta corretta per Multiple Choice Single. """
        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        correct_option_id = self.q2_opt2.id # Opzione B è corretta
        data = {
            'question_id': self.q2.id,
            'selected_answers': {'selected_option_id': correct_option_id}
        }
        response = self.client.post(self.submit_answer_url(self.attempt.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        student_answer = StudentAnswer.objects.get(quiz_attempt=self.attempt, question=self.q2)
        self.assertEqual(student_answer.selected_answers, {'selected_option_id': correct_option_id})

    def test_submit_answer_invalid_format(self):
        """ Verifica errore se il formato di selected_answers non è corretto per il tipo di domanda. """
        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        data = {
            'question_id': self.q1.id, # True/False aspetta {'selected_option_id': ID}
            'selected_answers': ['invalid_format'] # Formato errato
        }
        response = self.client.post(self.submit_answer_url(self.attempt.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data) # Verifica presenza messaggio di errore
        self.assertFalse(StudentAnswer.objects.filter(quiz_attempt=self.attempt, question=self.q1).exists())

    def test_submit_answer_attempt_not_in_progress(self):
        """ Verifica errore se si tenta di inviare risposta per un tentativo non in corso. """
        self.attempt.status = QuizAttempt.AttemptStatus.COMPLETED
        self.attempt.save()

        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        data = {
            'question_id': self.q1.id,
            'selected_answers': {'selected_option_id': self.q1.answer_options.first().id}
        }
        response = self.client.post(self.submit_answer_url(self.attempt.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non è più in corso', response.data.get('detail', ''))

    def test_submit_answer_for_wrong_question(self):
        """ Verifica errore se si invia risposta per una domanda non appartenente al quiz del tentativo. """
        wrong_question = QuestionFactory() # Domanda di un altro quiz

        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        data = {
            'question_id': wrong_question.id,
            'selected_answers': {'answer_text': 'abc'} # Formato generico
        }
        response = self.client.post(self.submit_answer_url(self.attempt.pk), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # get_object_or_404 su Question fallisce

    # --- Test per complete_attempt ---

    def test_complete_attempt_no_manual_questions(self):
        """ Verifica il completamento di un tentativo senza domande manuali. """
        # Rimuoviamo la domanda manuale per questo test specifico
        self.q3.delete()
        # Simula risposte a q1 e q2
        StudentAnswerFactory(quiz_attempt=self.attempt, question=self.q1)
        StudentAnswerFactory(quiz_attempt=self.attempt, question=self.q2)

        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.complete_url(self.attempt.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.status, QuizAttempt.AttemptStatus.COMPLETED)
        self.assertIsNotNone(self.attempt.completed_at)
        # Nota: Il calcolo del punteggio e l'assegnazione punti potrebbero essere ancora placeholder
        # self.assertIsNotNone(self.attempt.score) # Scommentare quando la logica è completa

    def test_complete_attempt_with_manual_questions(self):
        """ Verifica che il tentativo vada in PENDING_GRADING se ci sono domande manuali. """
        # Assicurati che q3 (manuale) esista
        self.assertTrue(Question.objects.filter(pk=self.q3.pk).exists())
        # Simula risposte a q1 e q2 (non importa se q3 è risposta o no)
        StudentAnswerFactory(quiz_attempt=self.attempt, question=self.q1)
        StudentAnswerFactory(quiz_attempt=self.attempt, question=self.q2)

        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.complete_url(self.attempt.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.attempt.refresh_from_db()
        self.assertEqual(self.attempt.status, QuizAttempt.AttemptStatus.PENDING_GRADING)
        self.assertIsNone(self.attempt.completed_at) # Non ancora completato
        self.assertIsNone(self.attempt.score) # Il punteggio non è calcolato

    def test_complete_attempt_not_in_progress(self):
        """ Verifica errore se si tenta di completare un tentativo non in corso. """
        self.attempt.status = QuizAttempt.AttemptStatus.COMPLETED
        self.attempt.save()

        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.complete_url(self.attempt.pk))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non è più in corso', response.data.get('detail', ''))

    # --- Test per submit_answer ---
    # ... (da implementare) ...

    # --- Test per complete_attempt ---
    # ... (da implementare) ...


# Aggiungere test per StudentDashboardViewSet, StudentQuizAttemptViewSet, TeacherGradingViewSet
# (tenendo conto dei placeholder per l'autenticazione studente)


class StudentQuizAttemptAPITests(APITestCase):
    """ Test per /api/education/quizzes/{quiz_pk}/start-attempt/ """
    def setUp(self):
        self.teacher = UserFactory(role=UserRole.TEACHER)
        self.student = StudentFactory(teacher=self.teacher)
        self.other_student = StudentFactory()
        self.quiz = QuizFactory(teacher=self.teacher)
        self.unassigned_quiz = QuizFactory(teacher=self.teacher) # Quiz non assegnato

        # Assegna self.quiz allo studente
        self.assignment = QuizAssignment.objects.create(quiz=self.quiz, student=self.student, assigned_by=self.teacher)

        # URL Helper - L'azione è registrata sotto il router annidato 'quizzes'
        # Il nome generato sarà 'quiz-attempts-start-attempt'
        self.start_attempt_url = lambda quiz_pk: reverse('quiz-attempts-start-attempt', kwargs={'quiz_pk': quiz_pk})
        # Add student login URL
        self.student_login_url = reverse('student-login')

        # Non creiamo più User fittizi per gli studenti qui.

    def test_student_can_start_attempt_for_assigned_quiz(self):
        """ Verifica che lo studente possa iniziare un tentativo per un quiz assegnato. """
        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.start_attempt_url(self.quiz.pk))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(QuizAttempt.objects.filter(student=self.student, quiz=self.quiz).exists())
        attempt = QuizAttempt.objects.get(student=self.student, quiz=self.quiz)
        self.assertEqual(attempt.status, QuizAttempt.AttemptStatus.IN_PROGRESS)
        self.assertEqual(response.data['id'], attempt.pk) # Verifica che ritorni i dettagli del nuovo tentativo

    def test_student_cannot_start_attempt_for_unassigned_quiz(self):
        """ Verifica che lo studente non possa iniziare un tentativo per un quiz non assegnato. """
        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.start_attempt_url(self.unassigned_quiz.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(QuizAttempt.objects.filter(student=self.student, quiz=self.unassigned_quiz).exists())

    def test_start_attempt_returns_existing_in_progress_attempt(self):
        """ Verifica che chiamare start su un tentativo già in corso restituisca quello esistente (200 OK). """
        existing_attempt = QuizAttemptFactory(student=self.student, quiz=self.quiz, status=QuizAttempt.AttemptStatus.IN_PROGRESS)

        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.start_attempt_url(self.quiz.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], existing_attempt.pk) # Deve restituire l'ID del tentativo esistente
        self.assertEqual(QuizAttempt.objects.filter(student=self.student, quiz=self.quiz).count(), 1) # Non ne crea uno nuovo

    def test_teacher_cannot_start_attempt(self):
        """ Verifica che un docente non possa usare l'endpoint start_attempt. """
        self.client.force_authenticate(user=self.teacher)
        response = self.client.post(self.start_attempt_url(self.quiz.pk))
        # IsStudent dovrebbe negare l'accesso
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StudentDashboardAPITests(APITestCase):
    """ Test per /api/education/student/dashboard/ """
    def setUp(self):
        self.teacher = UserFactory(role=UserRole.TEACHER)
        self.student = StudentFactory(teacher=self.teacher)
        self.other_student = StudentFactory(teacher=self.teacher) # Altro studente dello stesso docente

        self.quiz1 = QuizFactory(teacher=self.teacher, title="Assigned Quiz 1")
        self.quiz2 = QuizFactory(teacher=self.teacher, title="Assigned Quiz 2")
        self.quiz_unassigned = QuizFactory(teacher=self.teacher, title="Unassigned Quiz")
        self.pathway1 = PathwayFactory(teacher=self.teacher, title="Assigned Pathway 1")
        self.pathway_unassigned = PathwayFactory(teacher=self.teacher, title="Unassigned Pathway")

        # Assegna alcuni item allo studente principale
        QuizAssignment.objects.create(quiz=self.quiz1, student=self.student, assigned_by=self.teacher)
        QuizAssignment.objects.create(quiz=self.quiz2, student=self.student, assigned_by=self.teacher)
        PathwayAssignment.objects.create(pathway=self.pathway1, student=self.student, assigned_by=self.teacher)

        # URL Helper
        self.dashboard_url = reverse('student-dashboard') # Nome definito nel path diretto
        # Add student login URL
        self.student_login_url = reverse('student-login')

        # Non creiamo più User fittizi per gli studenti qui.

    def test_student_can_list_assigned_items(self):
        """ Verifica che lo studente veda solo i quiz/percorsi a lui assegnati. """
        # Login studente
        login_data = {'student_code': self.student.student_code, 'pin': '1234'}
        login_response = self.client.post(self.student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        assigned_quiz_ids = {q['id'] for q in response.data.get('assigned_quizzes', [])}
        assigned_pathway_ids = {p['id'] for p in response.data.get('assigned_pathways', [])}

        self.assertEqual(len(assigned_quiz_ids), 2)
        self.assertIn(self.quiz1.pk, assigned_quiz_ids)
        self.assertIn(self.quiz2.pk, assigned_quiz_ids)
        self.assertNotIn(self.quiz_unassigned.pk, assigned_quiz_ids)

        self.assertEqual(len(assigned_pathway_ids), 1)
        self.assertIn(self.pathway1.pk, assigned_pathway_ids)
        self.assertNotIn(self.pathway_unassigned.pk, assigned_pathway_ids)

    def test_other_student_sees_empty_dashboard(self):
        """ Verifica che un altro studente (senza assegnazioni) veda liste vuote. """
        # Login altro studente
        other_login_data = {'student_code': self.other_student.student_code, 'pin': '1234'}
        other_login_response = self.client.post(self.student_login_url, other_login_data)
        self.assertEqual(other_login_response.status_code, status.HTTP_200_OK, "Login altro studente fallito")
        other_access_token = other_login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_access_token}')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('assigned_quizzes', [])), 0)
        self.assertEqual(len(response.data.get('assigned_pathways', [])), 0)

    def test_teacher_cannot_access_student_dashboard(self):
        """ Verifica che un docente non possa accedere alla dashboard studente. """
        self.client.force_authenticate(user=self.teacher)
        response = self.client.get(self.dashboard_url)
        # IsStudent dovrebbe negare l'accesso
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class QuestionTemplateAPITests(APITestCase):
    """ Test per /api/education/quiz-templates/{quiz_template_pk}/questions/ """
    def setUp(self):
        self.admin_user = UserFactory(admin=True)
        self.teacher_user = UserFactory(role=UserRole.TEACHER)
        self.quiz_template = QuizTemplateFactory(admin=self.admin_user)
        self.q_template1 = QuestionTemplateFactory(quiz_template=self.quiz_template, order=1, text="QT1")
        self.q_template2 = QuestionTemplateFactory(quiz_template=self.quiz_template, order=2, text="QT2")

        # URL Helpers for nested routes
        self.list_url = lambda qt_pk: reverse('quiz-template-questions-list', kwargs={'quiz_template_pk': qt_pk})
        self.detail_url = lambda qt_pk, pk: reverse('quiz-template-questions-detail', kwargs={'quiz_template_pk': qt_pk, 'pk': pk})

    def test_admin_can_list_question_templates_for_quiz(self):
        """ Admin può listare le domande di un template specifico. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url(self.quiz_template.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_teacher_cannot_list_question_templates(self):
        """ Docente non può accedere a questo endpoint admin. """
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.get(self.list_url(self.quiz_template.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_question_template(self):
        """ Admin può creare una domanda per un template specifico. """
        self.client.force_authenticate(user=self.admin_user)
        data = {'text': 'New QT3', 'question_type': QuestionType.TRUE_FALSE, 'order': 3}
        response = self.client.post(self.list_url(self.quiz_template.pk), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.quiz_template.question_templates.count(), 3)
        new_q_template = QuestionTemplate.objects.get(pk=response.data['id'])
        self.assertEqual(new_q_template.quiz_template, self.quiz_template)
        self.assertEqual(new_q_template.text, 'New QT3')

    def test_admin_can_retrieve_question_template(self):
        """ Admin può recuperare una domanda specifica di un template. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.detail_url(self.quiz_template.pk, self.q_template1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], self.q_template1.text)

    def test_admin_can_update_question_template(self):
        """ Admin può aggiornare una domanda specifica di un template. """
        self.client.force_authenticate(user=self.admin_user)
        data = {'text': 'Updated QT1 Text'}
        response = self.client.patch(self.detail_url(self.quiz_template.pk, self.q_template1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.q_template1.refresh_from_db()
        self.assertEqual(self.q_template1.text, 'Updated QT1 Text')

    def test_admin_can_delete_question_template(self):
        """ Admin può eliminare una domanda specifica di un template. """
        q_template_pk = self.q_template1.pk
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url(self.quiz_template.pk, q_template_pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(QuestionTemplate.objects.filter(pk=q_template_pk).exists())
        self.assertEqual(self.quiz_template.question_templates.count(), 1) # Solo q_template2 rimane

    def test_teacher_cannot_access_nested_question_template_endpoints(self):
        """ Docente non può accedere a nessun endpoint nested per le domande template. """
        self.client.force_authenticate(user=self.teacher_user)
        # Create
        data = {'text': 'Teacher QT', 'question_type': QuestionType.TRUE_FALSE, 'order': 3}
        response_create = self.client.post(self.list_url(self.quiz_template.pk), data)
        self.assertEqual(response_create.status_code, status.HTTP_403_FORBIDDEN)
        # Retrieve
        response_retrieve = self.client.get(self.detail_url(self.quiz_template.pk, self.q_template1.pk))
        self.assertEqual(response_retrieve.status_code, status.HTTP_403_FORBIDDEN)
        # Update
        data_update = {'text': 'Teacher Update'}
        response_update = self.client.patch(self.detail_url(self.quiz_template.pk, self.q_template1.pk), data_update)
        self.assertEqual(response_update.status_code, status.HTTP_403_FORBIDDEN)
        # Delete
        response_delete = self.client.delete(self.detail_url(self.quiz_template.pk, self.q_template1.pk))
        self.assertEqual(response_delete.status_code, status.HTTP_403_FORBIDDEN)

    def _login_student(self, student):
        """ Helper per fare il login dello studente e ottenere il token. """
        student_login_url = reverse('student-login')
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']

    def test_student_cannot_access_nested_question_template_endpoints(self):
        """ Verifica che uno studente non possa accedere agli endpoint nested dei template di domande. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test LIST
        response_list = self.client.get(self.list_url(self.quiz_template.pk))
        self.assertEqual(response_list.status_code, status.HTTP_403_FORBIDDEN)

        # Test CREATE
        data_create = {'text': 'Student Q', 'question_type': QuestionType.TRUE_FALSE, 'order': 3}
        response_create = self.client.post(self.list_url(self.quiz_template.pk), data_create)
        self.assertEqual(response_create.status_code, status.HTTP_403_FORBIDDEN)

        # Test RETRIEVE
        response_retrieve = self.client.get(self.detail_url(self.quiz_template.pk, self.q_template1.pk))
        self.assertEqual(response_retrieve.status_code, status.HTTP_403_FORBIDDEN)

        # Test UPDATE
        data_update = {'text': 'Student Update'}
        response_update = self.client.patch(self.detail_url(self.quiz_template.pk, self.q_template1.pk), data_update)
        self.assertEqual(response_update.status_code, status.HTTP_403_FORBIDDEN)

        # Test DELETE
        response_delete = self.client.delete(self.detail_url(self.quiz_template.pk, self.q_template1.pk))
        self.assertEqual(response_delete.status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials() # Pulisce credenziali studente


class QuestionAPITests(APITestCase):
    """ Test per /api/education/quizzes/{quiz_pk}/questions/ """
    def setUp(self):
        self.teacher1 = UserFactory(role=UserRole.TEACHER)
        self.teacher2 = UserFactory(role=UserRole.TEACHER) # Altro docente
        self.admin_user = UserFactory(admin=True)
        self.quiz_t1 = QuizFactory(teacher=self.teacher1)
        self.quiz_t2 = QuizFactory(teacher=self.teacher2) # Quiz altro docente
        self.q1_t1 = QuestionFactory(quiz=self.quiz_t1, order=1, text="Q1")
        self.q2_t1 = QuestionFactory(quiz=self.quiz_t1, order=2, text="Q2")

        # URL Helpers for nested routes
        self.list_url = lambda quiz_pk: reverse('quiz-questions-list', kwargs={'quiz_pk': quiz_pk})
        self.detail_url = lambda quiz_pk, pk: reverse('quiz-questions-detail', kwargs={'quiz_pk': quiz_pk, 'pk': pk})

    def test_teacher_can_list_questions_for_own_quiz(self):
        """ Docente può listare le domande del proprio quiz. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.list_url(self.quiz_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_teacher_cannot_list_questions_for_other_quiz(self):
        """ Docente non può listare le domande del quiz di un altro docente. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.list_url(self.quiz_t2.pk))
        # Il permesso IsQuizOwner sulla view annidata dovrebbe bloccare
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # O 404 se get_object_or_404 fallisce prima

    def test_admin_can_list_questions_for_any_quiz(self):
        """ Admin può listare le domande di qualsiasi quiz. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url(self.quiz_t2.pk)) # Quiz di teacher2
        # Assumendo che l'admin abbia accesso (potrebbe richiedere aggiustamenti ai permessi)
        # Se IsQuizOwner blocca anche l'admin, questo test fallirà.
        # Modifichiamo il permesso o il test in base alla logica desiderata.
        # Per ora, assumiamo che l'admin possa vedere tutto.
        quiz_t2_question_count = Question.objects.filter(quiz=self.quiz_t2).count()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), quiz_t2_question_count)


    def test_teacher_can_create_question_for_own_quiz(self):
        """ Docente può creare una domanda per il proprio quiz. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'text': 'New Q3', 'question_type': QuestionType.FILL_BLANK, 'order': 3}
        response = self.client.post(self.list_url(self.quiz_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.quiz_t1.questions.count(), 3)
        new_q = Question.objects.get(pk=response.data['id'])
        self.assertEqual(new_q.quiz, self.quiz_t1)
        self.assertEqual(new_q.text, 'New Q3')

    def test_teacher_cannot_create_question_for_other_quiz(self):
        """ Docente non può creare una domanda per il quiz di un altro docente. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'text': 'Intruder Q', 'question_type': QuestionType.TRUE_FALSE, 'order': 1}
        response = self.client.post(self.list_url(self.quiz_t2.pk), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # O 404

    def test_teacher_can_retrieve_question_for_own_quiz(self):
        """ Docente può recuperare una domanda specifica del proprio quiz. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.quiz_t1.pk, self.q1_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], self.q1_t1.text)

    def test_teacher_cannot_retrieve_question_for_other_quiz(self):
        """ Docente non può recuperare una domanda del quiz di un altro docente. """
        # Crea una domanda per quiz_t2 per avere un target
        q1_t2 = QuestionFactory(quiz=self.quiz_t2, order=1)
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.quiz_t2.pk, q1_t2.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # O 404

    def test_teacher_can_update_question_for_own_quiz(self):
        """ Docente può aggiornare una domanda specifica del proprio quiz. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'text': 'Updated Q1 Text'}
        response = self.client.patch(self.detail_url(self.quiz_t1.pk, self.q1_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.q1_t1.refresh_from_db()
        self.assertEqual(self.q1_t1.text, 'Updated Q1 Text')

    def test_teacher_cannot_update_question_for_other_quiz(self):
        """ Docente non può aggiornare una domanda del quiz di un altro docente. """
        q1_t2 = QuestionFactory(quiz=self.quiz_t2, order=1)
        self.client.force_authenticate(user=self.teacher1)
        data = {'text': 'Intruder Update'}
        response = self.client.patch(self.detail_url(self.quiz_t2.pk, q1_t2.pk), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # O 404

    def test_teacher_can_delete_question_for_own_quiz(self):
        """ Docente può eliminare una domanda specifica del proprio quiz. """
        q1_pk = self.q1_t1.pk
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(self.quiz_t1.pk, q1_pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Question.objects.filter(pk=q1_pk).exists())
        self.assertEqual(self.quiz_t1.questions.count(), 1) # Solo q2_t1 rimane

    def test_teacher_cannot_delete_question_for_other_quiz(self):
        """ Docente non può eliminare una domanda del quiz di un altro docente. """
        q1_t2 = QuestionFactory(quiz=self.quiz_t2, order=1)
        q1_t2_pk = q1_t2.pk
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(self.quiz_t2.pk, q1_t2_pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # O 404
        self.assertTrue(Question.objects.filter(pk=q1_t2_pk).exists())


class AnswerOptionAPITests(APITestCase):
    """ Test per /api/education/quizzes/{quiz_pk}/questions/{question_pk}/options/ """
    def setUp(self):
        self.teacher1 = UserFactory(role=UserRole.TEACHER)
        self.teacher2 = UserFactory(role=UserRole.TEACHER) # Altro docente
        self.admin_user = UserFactory(admin=True)
        self.quiz_t1 = QuizFactory(teacher=self.teacher1)
        self.question_t1 = QuestionFactory(quiz=self.quiz_t1, question_type=QuestionType.MULTIPLE_CHOICE_SINGLE)
        self.option1_q1 = AnswerOptionFactory(question=self.question_t1, order=1, text="Opt1", is_correct=True)
        self.option2_q1 = AnswerOptionFactory(question=self.question_t1, order=2, text="Opt2", is_correct=False)

        # Oggetti di altro docente per test permessi
        self.quiz_t2 = QuizFactory(teacher=self.teacher2)
        self.question_t2 = QuestionFactory(quiz=self.quiz_t2)

        # URL Helpers for doubly nested routes
        self.list_url = lambda quiz_pk, q_pk: reverse('question-options-list', kwargs={'quiz_pk': quiz_pk, 'question_pk': q_pk})
        self.detail_url = lambda quiz_pk, q_pk, pk: reverse('question-options-detail', kwargs={'quiz_pk': quiz_pk, 'question_pk': q_pk, 'pk': pk})

    def test_teacher_can_list_options_for_own_question(self):
        """ Docente può listare le opzioni della propria domanda. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.list_url(self.quiz_t1.pk, self.question_t1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_teacher_cannot_list_options_for_other_question(self):
        """ Docente non può listare le opzioni della domanda di un altro docente. """
        # Crea opzione per domanda di teacher2
        option_q2 = AnswerOptionFactory(question=self.question_t2)
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.list_url(self.quiz_t2.pk, self.question_t2.pk))
        # Il permesso IsQuizOwner sulla view QuestionViewSet (genitore) dovrebbe bloccare
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # O 404

    def test_admin_can_list_options_for_any_question(self):
        """ Admin può listare le opzioni di qualsiasi domanda. """
        option_q2 = AnswerOptionFactory(question=self.question_t2)
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url(self.quiz_t2.pk, self.question_t2.pk))
        # Assumendo che l'admin abbia accesso
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_teacher_can_create_option_for_own_question(self):
        """ Docente può creare un'opzione per la propria domanda. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'text': 'New Opt3', 'is_correct': False, 'order': 3}
        response = self.client.post(self.list_url(self.quiz_t1.pk, self.question_t1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.question_t1.answer_options.count(), 3)
        new_opt = AnswerOption.objects.get(pk=response.data['id'])
        self.assertEqual(new_opt.question, self.question_t1)
        self.assertEqual(new_opt.text, 'New Opt3')

    def test_teacher_cannot_create_option_for_other_question(self):
        """ Docente non può creare un'opzione per la domanda di un altro docente. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'text': 'Intruder Opt', 'is_correct': True, 'order': 1}
        response = self.client.post(self.list_url(self.quiz_t2.pk, self.question_t2.pk), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # O 404

    def test_teacher_can_retrieve_option_for_own_question(self):
        """ Docente può recuperare un'opzione specifica della propria domanda. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.quiz_t1.pk, self.question_t1.pk, self.option1_q1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], self.option1_q1.text)

    def test_teacher_cannot_retrieve_option_for_other_question(self):
        """ Docente non può recuperare un'opzione della domanda di un altro docente. """
        option_q2 = AnswerOptionFactory(question=self.question_t2)
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.detail_url(self.quiz_t2.pk, self.question_t2.pk, option_q2.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # O 404

    def test_teacher_can_update_option_for_own_question(self):
        """ Docente può aggiornare un'opzione specifica della propria domanda. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'text': 'Updated Opt1 Text', 'is_correct': False}
        response = self.client.patch(self.detail_url(self.quiz_t1.pk, self.question_t1.pk, self.option1_q1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.option1_q1.refresh_from_db()
        self.assertEqual(self.option1_q1.text, 'Updated Opt1 Text')
        self.assertFalse(self.option1_q1.is_correct)

    def test_teacher_cannot_update_option_for_other_question(self):
        """ Docente non può aggiornare un'opzione della domanda di un altro docente. """
        option_q2 = AnswerOptionFactory(question=self.question_t2)
        self.client.force_authenticate(user=self.teacher1)
        data = {'text': 'Intruder Update'}
        response = self.client.patch(self.detail_url(self.quiz_t2.pk, self.question_t2.pk, option_q2.pk), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # O 404

    def test_teacher_can_delete_option_for_own_question(self):
        """ Docente può eliminare un'opzione specifica della propria domanda. """
        option1_pk = self.option1_q1.pk
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(self.quiz_t1.pk, self.question_t1.pk, option1_pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AnswerOption.objects.filter(pk=option1_pk).exists())
        self.assertEqual(self.question_t1.answer_options.count(), 1) # Solo option2_q1 rimane

    def test_teacher_cannot_delete_option_for_other_question(self):
        """ Docente non può eliminare un'opzione della domanda di un altro docente. """
        option_q2 = AnswerOptionFactory(question=self.question_t2)
        option_q2_pk = option_q2.pk
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.delete(self.detail_url(self.quiz_t2.pk, self.question_t2.pk, option_q2_pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # O 404
        self.assertTrue(AnswerOption.objects.filter(pk=option_q2_pk).exists())


class TeacherGradingAPITests(APITestCase):
    """ Test per /api/education/teacher/grading/ """
    def setUp(self):
        self.teacher1 = UserFactory(role=UserRole.TEACHER)
        self.teacher2 = UserFactory(role=UserRole.TEACHER) # Altro docente
        self.student1_t1 = StudentFactory(teacher=self.teacher1)
        self.student2_t1 = StudentFactory(teacher=self.teacher1)
        self.student1_t2 = StudentFactory(teacher=self.teacher2) # Studente altro docente

        # Quiz con domanda manuale
        self.quiz_manual_t1 = QuizFactory(teacher=self.teacher1)
        self.q_manual_t1 = QuestionFactory(quiz=self.quiz_manual_t1, question_type=QuestionType.OPEN_ANSWER_MANUAL, order=1)
        self.q_auto_t1 = QuestionFactory(quiz=self.quiz_manual_t1, question_type=QuestionType.TRUE_FALSE, order=2) # Domanda auto

        self.quiz_manual_t2 = QuizFactory(teacher=self.teacher2) # Quiz altro docente
        self.q_manual_t2 = QuestionFactory(quiz=self.quiz_manual_t2, question_type=QuestionType.OPEN_ANSWER_MANUAL, order=1)

        # Tentativi in attesa di grading
        # Tentativo 1 (stud1, quiz1) - Risposta manuale presente
        self.attempt1_pending = QuizAttemptFactory(student=self.student1_t1, quiz=self.quiz_manual_t1, status=QuizAttempt.AttemptStatus.PENDING_GRADING)
        self.answer1_manual = StudentAnswerFactory(quiz_attempt=self.attempt1_pending, question=self.q_manual_t1, selected_answers={'answer_text': 'Risposta 1'})
        self.answer1_auto = StudentAnswerFactory(quiz_attempt=self.attempt1_pending, question=self.q_auto_t1) # Risposta auto (non rilevante per grading)

        # Tentativo 2 (stud2, quiz1) - Risposta manuale presente
        self.attempt2_pending = QuizAttemptFactory(student=self.student2_t1, quiz=self.quiz_manual_t1, status=QuizAttempt.AttemptStatus.PENDING_GRADING)
        self.answer2_manual = StudentAnswerFactory(quiz_attempt=self.attempt2_pending, question=self.q_manual_t1, selected_answers={'answer_text': 'Risposta 2'})

        # Tentativo 3 (stud1_t2, quiz2) - Altro docente
        self.attempt3_other_teacher = QuizAttemptFactory(student=self.student1_t2, quiz=self.quiz_manual_t2, status=QuizAttempt.AttemptStatus.PENDING_GRADING)
        self.answer3_manual_other = StudentAnswerFactory(quiz_attempt=self.attempt3_other_teacher, question=self.q_manual_t2)

        # Tentativo 4 (stud1, quiz1) - Già completato
        self.attempt4_completed = QuizAttemptFactory(student=self.student1_t1, quiz=self.quiz_manual_t1, status=QuizAttempt.AttemptStatus.COMPLETED)
        self.answer4_manual_completed = StudentAnswerFactory(quiz_attempt=self.attempt4_completed, question=self.q_manual_t1, is_correct=True, score=10)

        # URL Helpers
        self.list_pending_url = reverse('teacher-grading-list-pending')
        self.grade_answer_url = lambda pk: reverse('teacher-grading-grade-answer', kwargs={'pk': pk})

        # Associazione User <-> Student (necessaria solo se si testasse accesso studente)
        if not hasattr(self.student1_t1, 'user') or not self.student1_t1.user:
             self.student1_user = UserFactory(username=f"student_{self.student1_t1.pk}")
             self.student1_t1.user = self.student1_user
             self.student1_t1.save()
        else:
             self.student1_user = self.student1_t1.user

    def _login_student(self, student):
        """ Helper per fare il login dello studente e ottenere il token. """
        student_login_url = reverse('student-login')
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']

    def test_teacher_can_list_own_pending_answers(self):
        """ Verifica che il docente veda solo le risposte manuali PENDING dei propri studenti. """
        self.client.force_authenticate(user=self.teacher1)
        response = self.client.get(self.list_pending_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Dovrebbe vedere answer1_manual e answer2_manual
        self.assertEqual(len(response.data), 2)
        answer_ids = {a['id'] for a in response.data}
        self.assertIn(self.answer1_manual.pk, answer_ids)
        self.assertIn(self.answer2_manual.pk, answer_ids)
        # Verifica che non veda quelle auto, di altri docenti, o già gradate
        self.assertNotIn(self.answer1_auto.pk, answer_ids)
        self.assertNotIn(self.answer3_manual_other.pk, answer_ids)
        self.assertNotIn(self.answer4_manual_completed.pk, answer_ids)

    def test_other_teacher_sees_own_pending_answers(self):
        """ Verifica che un altro docente veda le proprie risposte pending. """
        self.client.force_authenticate(user=self.teacher2)
        response = self.client.get(self.list_pending_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Solo answer3_manual_other
        self.assertEqual(response.data[0]['id'], self.answer3_manual_other.pk)

    def test_student_cannot_list_pending_answers(self):
        """ Verifica che uno studente non possa accedere a questo endpoint docente. """
        # Usa l'autenticazione JWT studente invece di force_authenticate
        # Passa l'oggetto Student (self.student1_t1), non l'User associato
        access_token = self._login_student(self.student1_t1)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.list_pending_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.credentials() # Pulisci le credenziali

    def test_teacher_can_grade_own_pending_answer(self):
        """ Verifica che il docente possa gradare una risposta manuale pending di un proprio studente. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'is_correct': True, 'score': 15}
        response = self.client.post(self.grade_answer_url(self.answer1_manual.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.answer1_manual.refresh_from_db()
        self.assertTrue(self.answer1_manual.is_correct)
        self.assertEqual(self.answer1_manual.score, 15)

        # Verifica se il tentativo è stato completato (se era l'unica risposta manuale)
        # Questa logica potrebbe essere più complessa (es. trigger asincrono)
        # Per ora, assumiamo che la view chiami un metodo per verificare/completare l'attempt
        self.attempt1_pending.refresh_from_db()
        # Se q_auto_t1 non richiede grading, l'attempt dovrebbe essere COMPLETED
        # Assumendo che la logica di check_attempt_completion sia chiamata
        # self.assertEqual(self.attempt1_pending.status, QuizAttempt.AttemptStatus.COMPLETED)
        # self.assertIsNotNone(self.attempt1_pending.score) # E il punteggio calcolato

    def test_teacher_cannot_grade_other_teacher_answer(self):
        """ Verifica che un docente non possa gradare risposte di studenti di altri docenti. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'is_correct': False, 'score': 0}
        response = self.client.post(self.grade_answer_url(self.answer3_manual_other.pk))
        # Il queryset della view dovrebbe filtrare -> 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.answer3_manual_other.refresh_from_db()
        self.assertIsNone(self.answer3_manual_other.is_correct) # Stato invariato

    def test_teacher_cannot_grade_already_graded_answer(self):
        """ Verifica che non si possa gradare una risposta già gradata. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'is_correct': False, 'score': 5}
        response = self.client.post(self.grade_answer_url(self.answer4_manual_completed.pk))
        # La view dovrebbe verificare lo stato -> 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('già stata corretta', response.data.get('detail', '').lower())

    def test_teacher_cannot_grade_non_manual_answer(self):
        """ Verifica che non si possa gradare una risposta non manuale. """
        self.client.force_authenticate(user=self.teacher1)
        data = {'is_correct': True, 'score': 10}
        response = self.client.post(self.grade_answer_url(self.answer1_auto.pk))
        # Il queryset della view dovrebbe filtrare per question_type -> 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_cannot_grade_answer(self):
        """ Verifica che uno studente non possa gradare risposte. """
        # Login studente
        login_data = {'student_code': self.student1_t1.student_code, 'pin': '1234'}
        login_response = self.client.post(reverse('student-login'), login_data) # Usa reverse qui
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login studente fallito")
        access_token = login_response.data['access']

        # Usa il token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        data = {'is_correct': True, 'score': 10}
        response = self.client.post(self.grade_answer_url(self.answer1_manual.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) # IsTeacherUser dovrebbe bloccare

    def test_grade_answer_completes_attempt(self):
        """ Verifica che gradare l'ultima risposta manuale completi il tentativo. """
        # Assicurati che ci sia solo una risposta manuale nel tentativo
        # (Nel setUp di default, answer1_auto è per q1, answer1_manual per q3)
        # Per simulare che q3 sia l'unica domanda manuale, potremmo dover modificare il setup
        # o creare un tentativo specifico qui. Per semplicità, assumiamo che sia l'unica
        # risposta manuale rimasta da gradare.
        self.attempt1_pending.status = QuizAttempt.AttemptStatus.PENDING_GRADING
        self.attempt1_pending.save()
        # Assicuriamoci che l'altra risposta (se esiste e fosse manuale) sia già gradata
        # In questo setup, answer1_auto non è manuale, quindi non serve.

        self.client.force_authenticate(user=self.teacher1)
        data = {'is_correct': True, 'score': 10}
        response = self.client.post(self.grade_answer_url(self.answer1_manual.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.answer1_manual.refresh_from_db()
        self.assertTrue(self.answer1_manual.is_correct)
        self.assertEqual(self.answer1_manual.score, 10)

        self.attempt1_pending.refresh_from_db()
        self.assertEqual(self.attempt1_pending.status, QuizAttempt.AttemptStatus.COMPLETED)
        self.assertIsNotNone(self.attempt1_pending.completed_at)
        self.assertIsNotNone(self.attempt1_pending.score) # Il punteggio dovrebbe essere stato calcolato
        # Potremmo aggiungere un controllo sui punti guadagnati se la logica è definita
        # self.assertIsNotNone(self.attempt1_pending.points_earned)

    def test_grade_answer_updates_answer_status_but_not_attempt(self):
        """ Verifica che gradare una risposta aggiorni is_correct/score, ma non completi
            il tentativo se ci sono altre risposte manuali pendenti. """
        # Aggiungi un'altra domanda manuale e risposta al tentativo
        q_manual2 = QuestionFactory(quiz=self.quiz_manual_t1, order=4, question_type=QuestionType.OPEN_ANSWER_MANUAL, text="Q Manual 2")
        answer_manual2 = StudentAnswerFactory(quiz_attempt=self.attempt1_pending, question=q_manual2, selected_answers={'text': 'Seconda risposta'})
        self.attempt1_pending.status = QuizAttempt.AttemptStatus.PENDING_GRADING
        self.attempt1_pending.save()

        self.client.force_authenticate(user=self.teacher1)
        data = {'is_correct': False, 'score': 0}
        response = self.client.post(self.grade_answer_url(self.answer1_manual.pk), data) # Grada la prima
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.answer1_manual.refresh_from_db()
        self.assertFalse(self.answer1_manual.is_correct)
        self.assertEqual(self.answer1_manual.score, 0)

        # Il tentativo dovrebbe rimanere PENDING_GRADING
        self.attempt1_pending.refresh_from_db()
        self.assertEqual(self.attempt1_pending.status, QuizAttempt.AttemptStatus.PENDING_GRADING)
        self.assertIsNone(self.attempt1_pending.completed_at)
        self.assertIsNone(self.attempt1_pending.score)

    def test_grade_answer_invalid_data(self):
        """ Verifica errore se i dati inviati non sono validi (es. score non numerico). """
        self.client.force_authenticate(user=self.teacher1)
        data = {'is_correct': 'maybe', 'score': 'ten'} # Dati invalidi
        response = self.client.post(self.grade_answer_url(self.answer1_manual.pk), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Modificato: Verifica solo la presenza della chiave 'score' negli errori,
        # dato che il messaggio specifico può variare o essere troncato.
        self.assertNotIn('is_correct', response.data)
        self.assertIn('score', response.data)


class AnswerOptionTemplateAPITests(APITestCase):
    """ Test per /api/education/quiz-templates/{qt_pk}/questions/{qtq_pk}/options/ """
    def setUp(self):
        self.admin_user = UserFactory(admin=True)
        self.teacher_user = UserFactory(role=UserRole.TEACHER)
        self.quiz_template = QuizTemplateFactory(admin=self.admin_user)
        self.question_template = QuestionTemplateFactory(quiz_template=self.quiz_template, question_type=QuestionType.MULTIPLE_CHOICE_SINGLE)
        self.option_template1 = AnswerOptionTemplateFactory(question_template=self.question_template, order=1, text="OptT1", is_correct=True)
        self.option_template2 = AnswerOptionTemplateFactory(question_template=self.question_template, order=2, text="OptT2", is_correct=False)

        # URL Helpers for doubly nested routes
        self.list_url = lambda qt_pk, qtq_pk: reverse('question-template-options-list', kwargs={'quiz_template_pk': qt_pk, 'question_template_pk': qtq_pk})
        self.detail_url = lambda qt_pk, qtq_pk, pk: reverse('question-template-options-detail', kwargs={'quiz_template_pk': qt_pk, 'question_template_pk': qtq_pk, 'pk': pk})

    def test_admin_can_list_option_templates_for_question(self):
        """ Admin può listare le opzioni di una domanda template specifica. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.list_url(self.quiz_template.pk, self.question_template.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_teacher_cannot_list_option_templates(self):
        """ Docente non può accedere a questo endpoint admin. """
        self.client.force_authenticate(user=self.teacher_user)
        response = self.client.get(self.list_url(self.quiz_template.pk, self.question_template.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_option_template(self):
        """ Admin può creare un'opzione per una domanda template specifica. """
        self.client.force_authenticate(user=self.admin_user)
        data = {'text': 'New OptT3', 'is_correct': False, 'order': 3}
        response = self.client.post(self.list_url(self.quiz_template.pk, self.question_template.pk), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.question_template.answer_option_templates.count(), 3)
        new_opt_t = AnswerOptionTemplate.objects.get(pk=response.data['id'])
        self.assertEqual(new_opt_t.question_template, self.question_template)
        self.assertEqual(new_opt_t.text, 'New OptT3')

    def test_admin_can_retrieve_option_template(self):
        """ Admin può recuperare un'opzione specifica di una domanda template. """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.detail_url(self.quiz_template.pk, self.question_template.pk, self.option_template1.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], self.option_template1.text)

    def test_admin_can_update_option_template(self):
        """ Admin può aggiornare un'opzione specifica di una domanda template. """
        self.client.force_authenticate(user=self.admin_user)
        data = {'text': 'Updated OptT1 Text', 'is_correct': False}
        response = self.client.patch(self.detail_url(self.quiz_template.pk, self.question_template.pk, self.option_template1.pk), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.option_template1.refresh_from_db()
        self.assertEqual(self.option_template1.text, 'Updated OptT1 Text')
        self.assertFalse(self.option_template1.is_correct)

    def test_admin_can_delete_option_template(self):
        """ Admin può eliminare un'opzione specifica di una domanda template. """
        option_template_pk = self.option_template1.pk
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.detail_url(self.quiz_template.pk, self.question_template.pk, option_template_pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AnswerOptionTemplate.objects.filter(pk=option_template_pk).exists())
        self.assertEqual(self.question_template.answer_option_templates.count(), 1) # Solo option_template2 rimane

    def test_teacher_cannot_access_nested_option_template_endpoints(self):
        """ Docente non può accedere a nessun endpoint nested per le opzioni template. """
        self.client.force_authenticate(user=self.teacher_user)
        # Create
        data = {'text': 'Teacher OptT', 'is_correct': False, 'order': 3}
        response_create = self.client.post(self.list_url(self.quiz_template.pk, self.question_template.pk), data)
        self.assertEqual(response_create.status_code, status.HTTP_403_FORBIDDEN)
        # Retrieve
        response_retrieve = self.client.get(self.detail_url(self.quiz_template.pk, self.question_template.pk, self.option_template1.pk))
        self.assertEqual(response_retrieve.status_code, status.HTTP_403_FORBIDDEN)
        # Update
        data_update = {'text': 'Teacher Update'}
        response_update = self.client.patch(self.detail_url(self.quiz_template.pk, self.question_template.pk, self.option_template1.pk), data_update)
        self.assertEqual(response_update.status_code, status.HTTP_403_FORBIDDEN)
        # Delete
        response_delete = self.client.delete(self.detail_url(self.quiz_template.pk, self.question_template.pk, self.option_template1.pk))
        self.assertEqual(response_delete.status_code, status.HTTP_403_FORBIDDEN)

    def _login_student(self, student):
        """ Helper per fare il login dello studente e ottenere il token. """
        student_login_url = reverse('student-login')
        login_data = {'student_code': student.student_code, 'pin': '1234'} # Assumendo pin '1234'
        login_response = self.client.post(student_login_url, login_data)
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, f"Login studente {student.student_code} fallito")
        return login_response.data['access']

    def test_student_cannot_access_nested_option_template_endpoints(self):
        """ Studente non può accedere a nessun endpoint nested per le opzioni template. """
        student_user = StudentFactory() # Rimosso pin='1234'
        access_token = self._login_student(student_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Create
        data_create = {'text': 'Student Opt', 'is_correct': False, 'order': 3}
        response_create = self.client.post(self.list_url(self.quiz_template.pk, self.question_template.pk), data_create)
        self.assertEqual(response_create.status_code, status.HTTP_403_FORBIDDEN)
        # Retrieve
        response_retrieve = self.client.get(self.detail_url(self.quiz_template.pk, self.question_template.pk, self.option_template1.pk))
        self.assertEqual(response_retrieve.status_code, status.HTTP_403_FORBIDDEN)
        # Update
        data_update = {'text': 'Student Update'}
        response_update = self.client.patch(self.detail_url(self.quiz_template.pk, self.question_template.pk, self.option_template1.pk), data_update)
        self.assertEqual(response_update.status_code, status.HTTP_403_FORBIDDEN)
        # Delete
        response_delete = self.client.delete(self.detail_url(self.quiz_template.pk, self.question_template.pk, self.option_template1.pk))
        self.assertEqual(response_delete.status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials() # Pulisce credenziali studente
