import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion'; // Importa motion
import useAuthStore from '../stores/authStore'; // Importa lo store
import Button from '../components/common/Button'; // Importa il componente Button

// Definisci le varianti per l'animazione (puoi metterle in un file separato)
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


const LoginPage: React.FC = () => {
  const [studentCode, setStudentCode] = useState('');
  const [pin, setPin] = useState('');
  const navigate = useNavigate();

  // Accedi allo stato e alle azioni dello store
  const login = useAuthStore((state) => state.login);
  const isLoading = useAuthStore((state) => state.loading);
  const error = useAuthStore((state) => state.error);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault(); // Previene il ricaricamento della pagina
    console.log('[LoginPage] Attempting login with:', { studentCode, pin });

    const success = await login({ studentCode, pin });

    if (success) {
      console.log('[LoginPage] Login successful, navigating to home.');
      navigate('/'); // Reindirizza alla home page dopo login riuscito
    } else {
      console.log('[LoginPage] Login failed.');
      // L'errore verrà mostrato tramite lo stato 'error' dello store
    }
  };

  return (
    // Usa motion.div come wrapper principale della pagina
    <motion.div
      initial="initial"
      animate="in"
      exit="out"
      variants={pageVariants}
      transition={pageTransition}
      className="flex flex-col items-center justify-center min-h-[calc(100vh-150px)]" // Mantieni le classi di layout
    >
      <h1 className="text-3xl font-bold mb-6">Accedi</h1>
      <form onSubmit={handleSubmit} className="w-full max-w-sm bg-white p-8 rounded shadow-md">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
            <strong className="font-bold">Errore: </strong>
            <span className="block sm:inline">{error}</span>
          </div>
        )}
        <div className="mb-4">
          <label htmlFor="studentCode" className="block text-gray-700 text-sm font-bold mb-2">
            Codice Studente
          </label>
          <input
            id="studentCode"
            type="text"
            placeholder="Il tuo codice studente"
            value={studentCode}
            onChange={(e) => setStudentCode(e.target.value)}
            disabled={isLoading}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline disabled:bg-gray-100"
            required
          />
        </div>
        <div className="mb-6">
          <label htmlFor="pin" className="block text-gray-700 text-sm font-bold mb-2">
            PIN
          </label>
          <input
            id="pin"
            type="password"
            placeholder="Il tuo PIN"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            disabled={isLoading}
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline disabled:bg-gray-100"
            required
          />
        </div>
        <div className="flex items-center justify-between">
          <Button type="submit" variant="primary" isLoading={isLoading} disabled={isLoading} className="w-full">
            {isLoading ? 'Accesso in corso...' : 'Accedi'}
          </Button>
        </div>
      </form>
    </motion.div>
  );
};

export default LoginPage;