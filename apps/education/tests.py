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

    # Aggiungere test per retrieve, update, delete, permessi


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

    # Aggiungere test per retrieve, update, delete, permessi


class PathwayAPITests(APITestCase):
    """ Test per /api/education/pathways/ """
    def setUp(self):
        self.teacher1 = UserFactory(role=UserRole.TEACHER, username='path_teacher1')
        self.student_t1 = StudentFactory(teacher=self.teacher1)
        self.pathway_t1 = PathwayFactory(teacher=self.teacher1, title="P1")
        self.assign_student_url = lambda pk: reverse('pathway-assign-student-pathway', kwargs={'pk': pk}) # Usa il nome corretto dell'azione

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

    # Aggiungere altri test per PathwayViewSet (list, create, add_quiz, etc.)


# Aggiungere test per QuestionAPITests, AnswerOptionAPITests (usando nested URLs)
# Aggiungere test per StudentDashboardViewSet, StudentQuizAttemptViewSet, TeacherGradingViewSet
# (tenendo conto dei placeholder per l'autenticazione studente)
