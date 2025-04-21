import React from 'react';
import { useParams } from 'react-router-dom'; // Per leggere l'ID del quiz dall'URL
import { motion } from 'framer-motion'; // Importa motion

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


const QuizAttemptPage: React.FC = () => {
  // Legge il parametro 'quizId' dall'URL
  const { quizId } = useParams<{ quizId: string }>();

  // TODO: Usare useQuery per fetchare i dettagli del quiz con ID quizId
  // const { data: quizDetails, isLoading, isError, error } = useQuery(...)

  return (
    // Usa motion.div come wrapper principale della pagina
    <motion.div
      initial="initial"
      animate="in"
      exit="out"
      variants={pageVariants}
      transition={pageTransition}
    >
      <h1 className="text-3xl font-bold mb-4">Tentativo Quiz</h1>
      <p className="mb-2">Stai eseguendo il quiz con ID: <span className="font-semibold">{quizId}</span></p>

      {/* Placeholder per caricamento/errore */}
      {/* {isLoading && <p>Caricamento domande...</p>} */}
      {/* {isError && <p className="text-red-500">Errore nel caricamento del quiz: {error?.message}</p>} */}

      {/* Placeholder per la visualizzazione delle domande */}
      <div className="mt-6 p-4 border rounded bg-gray-50">
        <h2 className="text-xl font-semibold mb-2">Domande del Quiz</h2>
        <p>Qui verranno visualizzate le domande e le opzioni di risposta.</p>
        {/* Esempio struttura domanda (da popolare con dati reali) */}
        <div className="mt-4 p-3 border rounded bg-white">
          <p className="font-medium">Domanda 1: Qual è la capitale d'Italia?</p>
          <div className="mt-2 space-y-1">
            <label className="flex items-center">
              <input type="radio" name="q1" value="a" className="mr-2" /> Roma
            </label>
            <label className="flex items-center">
              <input type="radio" name="q1" value="b" className="mr-2" /> Milano
            </label>
            {/* ... altre opzioni */}
          </div>
        </div>
      </div>

       {/* Placeholder per il bottone di invio */}
       <div className="mt-6 text-center">
          <button className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-6 rounded">
            Invia Risposte
          </button>
       </div>
    </motion.div>
  );
};

export default QuizAttemptPage;