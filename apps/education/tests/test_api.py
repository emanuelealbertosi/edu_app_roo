import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from mixer.backend.django import mixer # Per creare dati di test

# Importa i modelli necessari
from apps.users.models import User, Student, UserRole
from apps.education.models import Pathway, Quiz, PathwayQuiz, PathwayAssignment, PathwayProgress

# Usa pytest.mark.django_db per accedere al database nei test
pytestmark = pytest.mark.django_db

@pytest.fixture
def api_client():
    """Fixture per creare un client API non autenticato."""
    return APIClient()

@pytest.fixture
def teacher_user():
    """Fixture per creare un utente Docente."""
    return mixer.blend(User, role=UserRole.TEACHER)

@pytest.fixture
def student_user(teacher_user):
    """Fixture per creare uno Studente associato a un Docente."""
    return mixer.blend(Student, teacher=teacher_user)

@pytest.fixture
def pathway(teacher_user):
    """Fixture per creare un Percorso."""
    return mixer.blend(Pathway, teacher=teacher_user)

@pytest.fixture
def quiz1(teacher_user):
    """Fixture per creare un Quiz."""
    return mixer.blend(Quiz, teacher=teacher_user, title="Quiz 1")

@pytest.fixture
def quiz2(teacher_user):
    """Fixture per creare un secondo Quiz."""
    return mixer.blend(Quiz, teacher=teacher_user, title="Quiz 2")

@pytest.fixture
def pathway_with_quizzes(pathway, quiz1, quiz2):
    """Fixture per creare un Percorso con due quiz."""
    mixer.blend(PathwayQuiz, pathway=pathway, quiz=quiz1, order=0)
    mixer.blend(PathwayQuiz, pathway=pathway, quiz=quiz2, order=1)
    return pathway

@pytest.fixture
def pathway_assignment(pathway_with_quizzes, student_user, teacher_user):
    """Fixture per assegnare un percorso a uno studente."""
    return mixer.blend(PathwayAssignment, pathway=pathway_with_quizzes, student=student_user, assigned_by=teacher_user)


class TestPathwayAttemptAPI:
    """
    Test per l'endpoint API di dettaglio del tentativo di percorso (/api/education/pathways/<pk>/attempt/).
    """

    def test_get_pathway_attempt_detail_unauthenticated(self, api_client, pathway_assignment):
        """
        Verifica che un utente non autenticato non possa accedere all'endpoint.
        """
        pathway = pathway_assignment.pathway
        url = reverse('student-pathway-attempt-detail', kwargs={'pk': pathway.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_pathway_attempt_detail_not_assigned(self, api_client, student_user, pathway_with_quizzes):
        """
        Verifica che uno studente non possa accedere a un percorso non assegnatogli.
        """
        # Autentica lo studente
        api_client.force_authenticate(user=student_user) # Usa lo studente per l'autenticazione
        
        pathway = pathway_with_quizzes
        url = reverse('student-pathway-attempt-detail', kwargs={'pk': pathway.pk})
        response = api_client.get(url)
        # Dovrebbe restituire 403 Forbidden perché non è assegnato
        assert response.status_code == status.HTTP_403_FORBIDDEN 

    def test_get_pathway_attempt_detail_first_time(self, api_client, student_user, pathway_assignment, quiz1):
        """
        Verifica che l'endpoint restituisca i dati corretti la prima volta che uno studente accede
        a un percorso assegnato (nessun progresso esistente, prossimo quiz è il primo).
        """
        api_client.force_authenticate(user=student_user)
        pathway = pathway_assignment.pathway
        url = reverse('student-pathway-attempt-detail', kwargs={'pk': pathway.pk})
        
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # Verifica dettagli percorso
        assert data['id'] == pathway.id
        assert data['title'] == pathway.title
        assert len(data['quiz_details']) == 2 # Ci sono due quiz nel percorso
        
        # Verifica progresso (dovrebbe essere stato creato e IN_PROGRESS)
        assert data['progress'] is not None
        assert data['progress']['status'] == PathwayProgress.ProgressStatus.IN_PROGRESS
        assert data['progress']['last_completed_quiz_order'] is None
        
        # Verifica prossimo quiz (dovrebbe essere quiz1)
        assert data['next_quiz'] is not None
        assert data['next_quiz']['id'] == quiz1.id
        assert data['next_quiz']['title'] == quiz1.title

    def test_get_pathway_attempt_detail_in_progress(self, api_client, student_user, pathway_assignment, quiz1, quiz2):
        """
        Verifica che l'endpoint restituisca i dati corretti quando lo studente ha completato
        il primo quiz ma non il secondo.
        """
        api_client.force_authenticate(user=student_user)
        pathway = pathway_assignment.pathway
        
        # Simula il completamento del primo quiz (ordine 0)
        progress = mixer.blend(PathwayProgress, pathway=pathway, student=student_user, last_completed_quiz_order=0, status=PathwayProgress.ProgressStatus.IN_PROGRESS)
        
        url = reverse('student-pathway-attempt-detail', kwargs={'pk': pathway.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # Verifica progresso
        assert data['progress'] is not None
        assert data['progress']['status'] == PathwayProgress.ProgressStatus.IN_PROGRESS
        assert data['progress']['last_completed_quiz_order'] == 0
        
        # Verifica prossimo quiz (dovrebbe essere quiz2)
        assert data['next_quiz'] is not None
        assert data['next_quiz']['id'] == quiz2.id
        assert data['next_quiz']['title'] == quiz2.title

    def test_get_pathway_attempt_detail_completed(self, api_client, student_user, pathway_assignment, quiz1, quiz2):
        """
        Verifica che l'endpoint restituisca i dati corretti quando lo studente ha completato
        tutti i quiz del percorso.
        """
        api_client.force_authenticate(user=student_user)
        pathway = pathway_assignment.pathway
        
        # Simula il completamento dell'ultimo quiz (ordine 1) e lo stato COMPLETED
        progress = mixer.blend(PathwayProgress, pathway=pathway, student=student_user, last_completed_quiz_order=1, status=PathwayProgress.ProgressStatus.COMPLETED)
        
        url = reverse('student-pathway-attempt-detail', kwargs={'pk': pathway.pk})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        
        # Verifica progresso
        assert data['progress'] is not None
        assert data['progress']['status'] == PathwayProgress.ProgressStatus.COMPLETED
        assert data['progress']['last_completed_quiz_order'] == 1
        
        # Verifica prossimo quiz (dovrebbe essere null)
        assert data['next_quiz'] is None

    # TODO: Aggiungere test per altri ruoli (es. Docente non dovrebbe accedere a questo endpoint studente)