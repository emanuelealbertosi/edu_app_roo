from django.urls import path, include
from rest_framework_nested import routers # Import nested routers
from .views import (
    QuizTemplateViewSet, QuestionTemplateViewSet, AnswerOptionTemplateViewSet,
    QuizViewSet, QuestionViewSet, AnswerOptionViewSet, PathwayViewSet,
    StudentDashboardViewSet, StudentQuizAttemptViewSet, TeacherGradingViewSet,
    AttemptViewSet, # Importa la nuova viewset
    StudentAssignedQuizzesView, StudentAssignedPathwaysView, # Importa le nuove view
    PathwayAttemptDetailView, # Importa la nuova view per i dettagli del tentativo percorso
    StudentQuizDetailView, # Importa la nuova vista per i dettagli del quiz studente
    # Nuovi ViewSet per Template Percorsi
    PathwayTemplateViewSet, PathwayQuizTemplateViewSet, TeacherQuizTemplateViewSet,
    TeacherQuestionTemplateViewSet, TeacherAnswerOptionTemplateViewSet # Aggiungo i nuovi ViewSet nidificati
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
router.register(r'pathway-templates', PathwayTemplateViewSet, basename='pathway-template') # Gestione Template Percorsi (Docente)
router.register(r'teacher/quiz-templates', TeacherQuizTemplateViewSet, basename='teacher-quiz-template') # Gestione Template Quiz (Docente)

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
# Registra StudentQuizAttemptViewSet qui per l'azione start_attempt
quizzes_router.register(r'attempts', StudentQuizAttemptViewSet, basename='quiz-attempts')

# /quizzes/{quiz_pk}/questions/{question_pk}/options/
questions_router = routers.NestedDefaultRouter(quizzes_router, r'questions', lookup='question')
questions_router.register(r'options', AnswerOptionViewSet, basename='question-options')

# /pathway-templates/{pathway_template_pk}/quiz-templates/
pathway_templates_router = routers.NestedDefaultRouter(router, r'pathway-templates', lookup='pathway_template')
pathway_templates_router.register(r'quiz-templates', PathwayQuizTemplateViewSet, basename='pathway-template-quiz-templates')
# Router nidificati per i template quiz del docente
# /teacher/quiz-templates/{quiz_template_pk}/questions/
teacher_quiz_templates_router = routers.NestedDefaultRouter(router, r'teacher/quiz-templates', lookup='quiz_template')
teacher_quiz_templates_router.register(r'questions', TeacherQuestionTemplateViewSet, basename='teacher-quiz-template-questions')

# /teacher/quiz-templates/{quiz_template_pk}/questions/{question_template_pk}/options/
teacher_question_templates_router = routers.NestedDefaultRouter(teacher_quiz_templates_router, r'questions', lookup='question_template')
teacher_question_templates_router.register(r'options', TeacherAnswerOptionTemplateViewSet, basename='teacher-question-template-options')



# Combina tutti gli URL
urlpatterns = [
    # URLs specifici per lo studente (devono precedere il router principale per matching corretto)
    # Il prefisso 'student/' verrà aggiunto in config/urls.py
    path('dashboard/quizzes/', StudentAssignedQuizzesView.as_view(), name='student-dashboard-quizzes'),
    path('dashboard/pathways/', StudentAssignedPathwaysView.as_view(), name='student-dashboard-pathways'),
    path('quizzes/<int:pk>/', StudentQuizDetailView.as_view(), name='student-quiz-detail'),
    path('pathways/<int:pk>/attempt/', PathwayAttemptDetailView.as_view(), name='student-pathway-attempt-detail'),

    # Router principale (include ViewSet per admin/docenti e azioni generiche)
    path('', include(router.urls)),

    # Include i router annidati (devono seguire il router principale a cui si agganciano)
    path('', include(quiz_templates_router.urls)),
    path('', include(question_templates_router.urls)),
    path('', include(quizzes_router.urls)),
    path('', include(questions_router.urls)),
    path('', include(pathway_templates_router.urls)),
    path('', include(teacher_quiz_templates_router.urls)),
    path('', include(teacher_question_templates_router.urls)),

    # URL per Student Dashboard (non basato su router standard) - Rimosso perché gestito da view specifiche sopra
    # path('student/dashboard/', StudentDashboardViewSet.as_view({'get': 'list'}), name='student-dashboard'),
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
# /api/education/quizzes/{quiz_pk}/attempts/start-attempt/
# /api/education/pathways/
# /api/education/pathways/{pk}/
# /api/education/pathways/{pk}/attempt/  <- NUOVO URL per studente
# /api/education/teacher/grading/pending/
# /api/education/teacher/grading/{pk}/grade/
# /api/education/dashboard/quizzes/
# /api/education/dashboard/pathways/