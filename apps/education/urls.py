from django.urls import path, include
from rest_framework_nested import routers # Import nested routers
from .views import (
    QuizTemplateViewSet, QuestionTemplateViewSet, AnswerOptionTemplateViewSet,
    QuizViewSet, QuestionViewSet, AnswerOptionViewSet, PathwayViewSet,
    StudentDashboardViewSet, StudentQuizAttemptViewSet, TeacherGradingViewSet,
    AttemptViewSet # Importa la nuova viewset
)

# Router principale per le risorse top-level dell'app education
router = routers.DefaultRouter()
router.register(r'quiz-templates', QuizTemplateViewSet, basename='quiz-template') # Admin
router.register(r'quizzes', QuizViewSet, basename='quiz') # Gestione Quiz (Docente/Admin)
router.register(r'pathways', PathwayViewSet, basename='pathway') # Gestione Percorsi (Docente/Admin)
router.register(r'attempts', AttemptViewSet, basename='attempt') # Gestione Tentativi Specifici (Studente)
# Endpoint specifici Studente/Docente
# router.register(r'student/dashboard', StudentDashboardViewSet, basename='student-dashboard') # Usare APIView semplice? -> Usiamo path diretto sotto
router.register(r'teacher/grading', TeacherGradingViewSet, basename='teacher-grading') # Gestione Correzioni (Docente)

# --- Router Annidati ---

# /quiz-templates/{quiz_template_pk}/questions/
quiz_templates_router = routers.NestedDefaultRouter(router, r'quiz-templates', lookup='quiz_template')
quiz_templates_router.register(r'questions', QuestionTemplateViewSet, basename='quiz-template-questions')

# /quiz-templates/{quiz_template_pk}/questions/{question_template_pk}/options/
question_templates_router = routers.NestedDefaultRouter(quiz_templates_router, r'questions', lookup='question_template')
question_templates_router.register(r'options', AnswerOptionTemplateViewSet, basename='question-template-options')

# /quizzes/{quiz_pk}/questions/
quizzes_router = routers.NestedDefaultRouter(router, r'quizzes', lookup='quiz')
quizzes_router.register(r'questions', QuestionViewSet, basename='quiz-questions')
# L'azione start_attempt è ora gestita da StudentQuizAttemptViewSet registrato nel router principale
# quizzes_router.register(r'attempts', StudentQuizAttemptViewSet, basename='quiz-attempts') # Rimosso

# /quizzes/{quiz_pk}/questions/{question_pk}/options/
questions_router = routers.NestedDefaultRouter(quizzes_router, r'questions', lookup='question')
questions_router.register(r'options', AnswerOptionViewSet, basename='question-options')


# Combina tutti gli URL
urlpatterns = [
    path('', include(router.urls)),
    path('', include(quiz_templates_router.urls)),
    path('', include(question_templates_router.urls)),
    path('', include(quizzes_router.urls)),
    path('', include(questions_router.urls)),
    # URL per Student Dashboard (non basato su router standard)
    path('student/dashboard/', StudentDashboardViewSet.as_view({'get': 'list'}), name='student-dashboard'),
]

# Esempi URL generati:
# /api/education/quiz-templates/
# /api/education/quiz-templates/{pk}/
# /api/education/quiz-templates/{quiz_template_pk}/questions/
# /api/education/quiz-templates/{quiz_template_pk}/questions/{pk}/
# /api/education/quiz-templates/{quiz_template_pk}/questions/{question_template_pk}/options/
# /api/education/quizzes/
# /api/education/quizzes/{pk}/
# /api/education/quizzes/{quiz_pk}/questions/
# /api/education/quizzes/{quiz_pk}/questions/{pk}/
# /api/education/quizzes/{quiz_pk}/questions/{question_pk}/options/
# /api/education/quizzes/{quiz_pk}/attempts/start-attempt/  <- Corretto da StudentQuizAttemptViewSet
# /api/education/pathways/
# /api/education/teacher/grading/pending/
# /api/education/teacher/grading/{pk}/grade/