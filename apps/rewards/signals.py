import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.education.models import QuizAttempt # Importa il modello che triggera
from .models import Badge, EarnedBadge, Student # Importa modelli Badge e Studente

logger = logging.getLogger(__name__)

@receiver(post_save, sender=QuizAttempt)
def check_for_quiz_completion_badges(sender, instance: QuizAttempt, created, **kwargs):
    """
    Controlla se lo studente ha guadagnato badge relativi al completamento di un quiz.
    Triggerato dopo il salvataggio di un QuizAttempt.
    """
    # Esegui solo se il tentativo è stato completato (non in creazione o aggiornamento intermedio)
    # e se lo stato è COMPLETED o FAILED (potremmo avere badge anche per tentativi falliti?)
    if instance.status in [QuizAttempt.Status.COMPLETED, QuizAttempt.Status.FAILED] and instance.student:
        student = instance.student
        quiz = instance.quiz
        score = instance.score # Percentuale

        # 1. Trova i badge attivi relativi al completamento di quiz
        quiz_badges = Badge.objects.filter(
            is_active=True,
            trigger_type=Badge.TriggerType.QUIZ_COMPLETED
        )

        # Ottieni gli ID dei badge già guadagnati dallo studente per evitare duplicati
        earned_badge_ids = set(EarnedBadge.objects.filter(student=student).values_list('badge_id', flat=True))

        badges_to_award = []

        for badge in quiz_badges:
            if badge.id in earned_badge_ids:
                continue # Già guadagnato

            conditions = badge.trigger_condition or {}
            quiz_id_condition = conditions.get('quiz_id')
            min_score_condition = conditions.get('min_score') # Percentuale
            max_score_condition = conditions.get('max_score') # Percentuale
            status_condition = conditions.get('status', QuizAttempt.Status.COMPLETED) # Default a COMPLETED

            # Verifica condizioni
            conditions_met = True

            # Condizione sullo stato (es. deve essere COMPLETED)
            if status_condition and instance.status != status_condition:
                conditions_met = False

            # Condizione sull'ID specifico del quiz (se presente)
            if conditions_met and quiz_id_condition and quiz.id != quiz_id_condition:
                conditions_met = False
            
            # Condizione sul punteggio minimo (se presente e se il punteggio esiste)
            if conditions_met and min_score_condition is not None and (score is None or score < min_score_condition):
                 conditions_met = False

            # Condizione sul punteggio massimo (se presente e se il punteggio esiste)
            if conditions_met and max_score_condition is not None and (score is None or score > max_score_condition):
                 conditions_met = False

            # Se tutte le condizioni sono soddisfatte, aggiungi alla lista
            if conditions_met:
                logger.info(f"Studente {student.id} ha soddisfatto le condizioni per il badge '{badge.name}' (ID: {badge.id}) completando il quiz {quiz.id}.")
                badges_to_award.append(EarnedBadge(student=student, badge=badge))

        # Crea i record EarnedBadge in bulk se ce ne sono
        if badges_to_award:
            try:
                EarnedBadge.objects.bulk_create(badges_to_award, ignore_conflicts=True) # ignore_conflicts per sicurezza
                logger.info(f"Assegnati {len(badges_to_award)} badge allo studente {student.id}.")
                # Qui potremmo inviare una notifica (se avessimo un sistema di notifiche)
            except Exception as e:
                 logger.error(f"Errore durante bulk_create di EarnedBadge per studente {student.id}: {e}", exc_info=True)

    # TODO: Implementare segnali simili per altri trigger (PATHWAY_COMPLETED, CORRECT_STREAK, POINTS_THRESHOLD)
    # Per CORRECT_STREAK, potrebbe essere necessario un segnale su StudentAnswer.
    # Per POINTS_THRESHOLD, potrebbe essere necessario un segnale su Wallet o PointTransaction.