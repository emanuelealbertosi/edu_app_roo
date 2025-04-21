import React, { useState } from 'react'; // Import useState
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion'; // Importa motion
import useAuthStore from '../stores/authStore';
import { fetchAssignedQuizzes, fetchAssignedPathways, fetchWalletInfo } from '../services/dashboardService';
import type { AssignedQuiz, AssignedPathway, Wallet } from '../types/dashboard';
import Modal from '../components/ui/Modal'; // Importa Modal
import QuizAttempt from '../components/features/quiz/QuizAttempt'; // Importa QuizAttempt
import Button from '../components/common/Button'; // Importa Button

// Componente per mostrare un messaggio di caricamento generico
const LoadingIndicator: React.FC = () => <div className="text-center p-4">Caricamento dati...</div>;

// Componente per mostrare un messaggio di errore generico
const ErrorDisplay: React.FC<{ message?: string }> = ({ message }) => ( // Rendi message opzionale
  <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
    <strong className="font-bold">Errore: </strong>
    <span className="block sm:inline">{message || 'Impossibile caricare i dati.'}</span>
  </div>
);


// Definisci le varianti per l'animazione (da mettere in un file condiviso idealmente)
const pageVariants = {
  initial: {
    opacity: 0,
    x: "-100vw",
    scale: 0.8
  },
  in: {
    opacity: 1,
    x: 0,
    scale: 1
  },
  out: {
    opacity: 0,
    x: "100vw",
    scale: 1.2
  }
};

// Definisci le proprietà di transizione
const pageTransition = {
  type: "tween",
  ease: "anticipate",
  duration: 0.5
};


const DashboardPage: React.FC = () => {
  const student = useAuthStore((state) => state.student);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedQuizId, setSelectedQuizId] = useState<number | string | null>(null);

  // Funzioni per gestire la modale
  const handleOpenModal = (quizId: number | string) => {
    setSelectedQuizId(quizId);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedQuizId(null);
    // TODO: Potrebbe essere necessario invalidare/refetchare i dati della dashboard qui
    // queryClient.invalidateQueries({ queryKey: ['assignedQuizzes'] });
  };


  // Fetch dei quiz assegnati
  const {
    data: quizzes,
    isLoading: isLoadingQuizzes,
    isError: isErrorQuizzes,
    error: errorQuizzes,
  } = useQuery<AssignedQuiz[], Error>({
    queryKey: ['assignedQuizzes'], // Chiave univoca per questa query
    queryFn: fetchAssignedQuizzes, // Funzione che recupera i dati
    // enabled: !!student, // Esegui la query solo se lo studente è loggato (opzionale, gestito da auth)
  });

  // Fetch dei percorsi assegnati
  const {
    data: pathways,
    isLoading: isLoadingPathways,
    isError: isErrorPathways,
    error: errorPathways,
  } = useQuery<AssignedPathway[], Error>({
    queryKey: ['assignedPathways'],
    queryFn: fetchAssignedPathways,
    // enabled: !!student,
  });

  // Fetch del wallet
  const {
    data: wallet,
    isLoading: isLoadingWallet,
    isError: isErrorWallet,
    error: errorWallet,
  } = useQuery<Wallet, Error>({
    queryKey: ['walletInfo'],
    queryFn: fetchWalletInfo,
    // enabled: !!student,
  });

  // Determina lo stato di caricamento generale
  const isLoading = isLoadingQuizzes || isLoadingPathways || isLoadingWallet;

  return (
    <> {/* Fragment inizia qui */}
      {/* Usa motion.div come wrapper principale della pagina */}
      <motion.div
        initial="initial"
        animate="in"
        exit="out"
        variants={pageVariants}
        transition={pageTransition}
      >
        <h1 className="text-3xl font-bold mb-4">Dashboard Studente</h1>
        {student ? (
          <p className="mb-6">Benvenuto/a, <span className="font-semibold">{student.first_name || 'Studente'}</span>!</p>
      ) : (
        <p className="mb-6 text-gray-500">Caricamento dati utente...</p>
      )}

      {isLoading && <LoadingIndicator />}

      {/* Sezione Wallet */}
      <div className="mb-6 p-4 border rounded bg-blue-50 shadow-sm">
        <h2 className="text-xl font-semibold mb-2 text-blue-800">Il Tuo Saldo</h2>
        {isErrorWallet && <ErrorDisplay message={errorWallet?.message} />}
        {wallet && !isErrorWallet && (
          <p className="text-2xl font-bold text-blue-700">{wallet.current_points} Punti</p>
        )}
         {isLoadingWallet && !wallet && <p className="text-gray-500">Caricamento saldo...</p>}
      </div>

      {/* Sezione Quiz */}
      <div className="mb-6 p-4 border rounded bg-green-50 shadow-sm">
        <h2 className="text-xl font-semibold mb-2 text-green-800">Quiz Assegnati</h2>
        {isErrorQuizzes && <ErrorDisplay message={errorQuizzes?.message} />}
        {quizzes && quizzes.length > 0 && !isErrorQuizzes && (
          <ul className="space-y-3"> {/* Aggiunto space-y per spaziatura */}
            {quizzes.map((quiz) => (
              <li key={quiz.id} className="border-b pb-3 flex justify-between items-center">
                <div>
                  <span className="font-medium block">{quiz.title}</span>
                  <span className="text-sm text-gray-600">Stato: {quiz.status}</span>
                  {/* Aggiungere altri dettagli se necessario */}
                </div>
                {/* Bottone per avviare il quiz nella modale */}
                <Button
                  onClick={() => handleOpenModal(quiz.id)}
                  size="sm"
                  variant="primary"
                  // Disabilita se completato? O permetti di rivedere? Da decidere.
                  // disabled={quiz.status === 'completed'}
                >
                  Avvia Quiz
                </Button>
              </li>
            ))}
          </ul>
        )}
        {quizzes && quizzes.length === 0 && !isErrorQuizzes && (
           <p className="text-gray-500">Nessun quiz assegnato al momento.</p>
        )}
         {isLoadingQuizzes && !quizzes && <p className="text-gray-500">Caricamento quiz...</p>}
      </div>

      {/* Sezione Percorsi */}
      <div className="p-4 border rounded bg-yellow-50 shadow-sm">
        <h2 className="text-xl font-semibold mb-2 text-yellow-800">Percorsi Assegnati</h2>
        {isErrorPathways && <ErrorDisplay message={errorPathways?.message} />}
        {pathways && pathways.length > 0 && !isErrorPathways && (
           <ul>
            {pathways.map((pathway) => (
              <li key={pathway.id} className="border-b py-2">
                 <span className="font-medium">{pathway.title}</span> - <span className="text-sm text-gray-600">Stato: {pathway.status}</span>
              </li>
            ))}
          </ul>
        )}
         {pathways && pathways.length === 0 && !isErrorPathways && (
           <p className="text-gray-500">Nessun percorso assegnato al momento.</p>
        )}
         {isLoadingPathways && !pathways && <p className="text-gray-500">Caricamento percorsi...</p>}
      </div>

      </motion.div> {/* Chiusura del motion.div principale */}

      {/* Modale per il tentativo del Quiz (la modale stessa può avere le sue animazioni interne) */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={`Tentativo Quiz: ${quizzes?.find(q => q.id === selectedQuizId)?.title || ''}`} // Titolo dinamico
        size="full" // Usa 'full' per esperienza immersiva
      >
        {/* Renderizza il componente QuizAttempt solo se un quiz è selezionato */}
        {/* La condizione selectedQuizId && ... garantisce che quizId non sia null qui */}
        {selectedQuizId && (
          <QuizAttempt quizId={selectedQuizId} onClose={handleCloseModal} />
        )}
      </Modal>
    </> // Fragment finisce qui
  );
};

export default DashboardPage;