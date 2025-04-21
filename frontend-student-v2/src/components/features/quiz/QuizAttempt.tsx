import React, { useState, useEffect } from 'react';
// Importa useQuery e useMutation, e queryClient per invalidare
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
// Aggiorna import: aggiungi submitAnswer
import { startOrFetchQuizAttempt, fetchCurrentQuestion, submitAnswer } from '../../../services/quizService';
// Aggiorna tipi: aggiungi SubmitAnswerPayload
import type { AttemptQuestion, AttemptAnswerOption, StartAttemptResponse, SubmitAnswerPayload } from '../../../types/quiz';

interface QuizAttemptProps {
  quizId: number | string;
  onClose: () => void;
}

// Colori stile Kahoot
const answerColors = [
  'bg-red-500 hover:bg-red-600',
  'bg-blue-500 hover:bg-blue-600',
  'bg-yellow-400 hover:bg-yellow-500',
  'bg-green-500 hover:bg-green-600',
];

const QuizAttempt: React.FC<QuizAttemptProps> = ({ quizId, onClose }) => {
  const queryClient = useQueryClient(); // Ottieni il query client
  const [selectedOptionId, setSelectedOptionId] = useState<number | null>(null);

  // 1. Query per ottenere l'ID del tentativo
  const {
    data: startData,
    isLoading: isLoadingStart,
    isError: isErrorStart,
    error: errorStart,
  } = useQuery<StartAttemptResponse, Error>({
    queryKey: ['startQuizAttempt', quizId],
    queryFn: () => startOrFetchQuizAttempt(quizId),
    enabled: !!quizId,
    staleTime: 1000 * 60,
    gcTime: 1000 * 60 * 5,
    refetchOnWindowFocus: false,
  });

  const attemptId = startData?.id;

  // 2. Query per ottenere la domanda corrente
  const {
    data: currentQuestion,
    isLoading: isLoadingQuestion,
    isError: isErrorQuestion,
    error: errorQuestion,
    // Non serve refetch qui, lo faremo dopo la mutation
  } = useQuery<AttemptQuestion, Error>({
    queryKey: ['currentQuizQuestion', attemptId], // Chiave specifica
    queryFn: () => fetchCurrentQuestion(attemptId!),
    enabled: !!attemptId,
    staleTime: 0,
    gcTime: 1000 * 60 * 1,
    refetchOnWindowFocus: false, // Evita refetch che potrebbe sovrascrivere selezione
    // Rimuovi refetchOnMount/refetchOnReconnect se causano problemi con la selezione
  });

  // Effetto per resettare la selezione quando cambia la domanda
  useEffect(() => {
    setSelectedOptionId(null);
  }, [currentQuestion?.id]); // Resetta quando l'ID della domanda cambia

  // 3. Mutation per inviare la risposta
  const submitAnswerMutation = useMutation({
    mutationFn: (answerPayload: SubmitAnswerPayload) => submitAnswer(attemptId!, answerPayload),
    onSuccess: (data) => {
      console.log('Risposta inviata con successo:', data);
      // Invalida la query della domanda corrente per caricare la successiva
      queryClient.invalidateQueries({ queryKey: ['currentQuizQuestion', attemptId] });
      // Non resettare selectedOptionId qui, l'useEffect sopra lo farà quando arriva la nuova domanda
    },
    onError: (error) => {
      console.error('Errore durante invio risposta:', error);
      // TODO: Mostrare un messaggio di errore all'utente (es. con un toast)
    },
  });

  // Handler per selezionare una risposta
  const handleSelectAnswer = (optionId: number) => {
    setSelectedOptionId(optionId);
  };

  // Handler per inviare la risposta e passare alla prossima domanda
  const handleSubmitAnswer = () => {
    if (!selectedOptionId || !currentQuestion || !attemptId) {
      console.warn('Tentativo di invio senza selezione o dati mancanti.');
      return; // Non inviare se non c'è selezione o dati
    }

    const payload: SubmitAnswerPayload = {
      attempt_id: attemptId, // Anche se non richiesto dal backend, è buona norma averlo
      question_id: currentQuestion.id,
      // Adatta il payload in base al tipo di domanda se necessario
      // Per MC_SINGLE, inviamo solo l'ID selezionato
      selected_option_id: selectedOptionId,
      // answer_text: null, // Per altri tipi di domanda
    };

    submitAnswerMutation.mutate(payload);
  };


  // Determina lo stato di caricamento/errore combinato
  const isLoading = isLoadingStart || isLoadingQuestion;
  const isError = isErrorStart || isErrorQuestion;
  const error = errorQuestion || errorStart;

  return (
    <div className="quiz-attempt-container flex flex-col h-full p-4 md:p-6 bg-gray-100">
      <button
        onClick={onClose}
        className="absolute top-4 right-4 text-gray-600 hover:text-gray-900 text-2xl font-bold z-10"
        aria-label="Chiudi quiz"
      >
        &times;
      </button>

      {isLoading && <p className="text-center p-4 text-lg font-semibold text-gray-700">Caricamento domanda...</p>}
      {/* Mostra errore della mutation se presente, altrimenti errore di caricamento */}
      {(isError || submitAnswerMutation.isError) && (
         <p className="text-center p-4 text-red-600 font-semibold">
           Errore: {submitAnswerMutation.error?.message || error?.message || 'Si è verificato un errore.'}
         </p>
      )}


      {currentQuestion && !isLoading && !isError && (
        <>
          <div className="question-area mb-6 p-6 bg-white rounded-lg shadow-lg text-center flex-grow flex flex-col justify-center items-center relative">
            <p className="text-gray-500 text-sm mb-2 absolute top-2 left-2">Domanda {currentQuestion.order || 'corrente'}</p>
            <p className="text-2xl md:text-3xl font-bold text-gray-800">
              {currentQuestion.text}
            </p>
          </div>

          {currentQuestion.answer_options && Array.isArray(currentQuestion.answer_options) && currentQuestion.answer_options.length > 0 && (
            <div className="answers-grid grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4 mb-4 flex-shrink-0">
              {currentQuestion.answer_options.map((option: AttemptAnswerOption, index: number) => {
                const isSelected = selectedOptionId === option.id;
                return (
                  <button
                    key={option.id}
                    onClick={() => handleSelectAnswer(option.id)}
                    // Applica stile diverso se selezionato
                    className={`
                      ${answerColors[index % answerColors.length]}
                      text-white font-bold py-5 md:py-8 px-4 rounded-lg text-lg md:text-xl
                      transition duration-150 ease-in-out shadow-md transform hover:scale-105
                      ${isSelected ? 'ring-4 ring-offset-2 ring-yellow-400 scale-105' : ''}
                      ${submitAnswerMutation.isPending ? 'opacity-50 cursor-not-allowed' : ''}
                    `}
                    disabled={submitAnswerMutation.isPending} // Disabilita durante l'invio
                  >
                    {option.text}
                  </button>
                );
               })}
            </div>
          )}
           {(!currentQuestion.answer_options || currentQuestion.answer_options.length === 0) && (
              <p className="text-center text-gray-500 mb-4">Questa domanda non ha opzioni visualizzabili.</p>
           )}

          <div className="footer-actions text-center mt-4 flex-shrink-0">
             <button
               onClick={handleSubmitAnswer}
               disabled={!selectedOptionId || submitAnswerMutation.isPending} // Disabilita se nessuna selezione o durante invio
               className={`
                 bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-8 rounded-lg shadow-md
                 transition duration-150 ease-in-out
                 ${(!selectedOptionId || submitAnswerMutation.isPending) ? 'opacity-50 cursor-not-allowed' : ''}
               `}
             >
               {submitAnswerMutation.isPending ? 'Invio...' : 'Invia Risposta'}
               {/* TODO: Cambiare testo se è l'ultima domanda */}
             </button>
          </div>
        </>
      )}

       {!currentQuestion && !isLoading && !isError && !submitAnswerMutation.isPending && ( // Aggiungi controllo mutation
         <div className="text-center p-4">
            <p className="text-yellow-600 font-semibold">Nessuna domanda corrente disponibile.</p>
            <p className="text-sm text-gray-500 mt-1">(Quiz completato o errore nel caricamento).</p>
            <button
              onClick={onClose}
              className="mt-4 bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-6 rounded-lg"
            >
              Chiudi
            </button>
         </div>
       )}
    </div>
  );
};

export default QuizAttempt;