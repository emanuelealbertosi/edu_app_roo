import React from 'react';
import { motion } from 'framer-motion'; // Importa motion

// Definisci le varianti per l'animazione
const pageVariants = {
  initial: {
    opacity: 0,
    x: "-100vw", // Inizia fuori schermo a sinistra
    scale: 0.8
  },
  in: {
    opacity: 1,
    x: 0, // Entra al centro
    scale: 1
  },
  out: {
    opacity: 0,
    x: "100vw", // Esce verso destra
    scale: 1.2
  }
};

// Definisci le proprietà di transizione
const pageTransition = {
  type: "tween", // Tipo di animazione (tween, spring, etc.)
  ease: "anticipate", // Effetto di easing (es. easeInOut, anticipate)
  duration: 0.5 // Durata dell'animazione
};


const HomePage: React.FC = () => {
  return (
    // Usa motion.div come wrapper principale della pagina
    <motion.div
      initial="initial"
      animate="in"
      exit="out"
      variants={pageVariants}
      transition={pageTransition}
    >
      <h1 className="text-2xl font-bold text-center p-4">Home Page</h1>
      <p className="text-center">Contenuto della home page...</p>
    </motion.div>
  );
};

export default HomePage;