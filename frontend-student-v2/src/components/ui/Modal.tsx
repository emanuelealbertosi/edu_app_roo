import React, { ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Button from '../common/Button'; // Per il bottone di chiusura

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'; // Aggiunta opzione 'full'
}

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
}) => {
  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    full: 'max-w-full h-full', // Classe per full screen/height
  };

  // Variazioni per animazione overlay e modale
  const backdropVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  };

  const modalVariants = {
    hidden: { y: "-50px", opacity: 0 },
    visible: { y: "0", opacity: 1, transition: { duration: 0.3 } },
    exit: { y: "50px", opacity: 0, transition: { duration: 0.2 } },
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 backdrop-blur-sm p-4"
          variants={backdropVariants}
          initial="hidden"
          animate="visible"
          exit="hidden"
          onClick={onClose} // Chiudi cliccando sullo sfondo
        >
          <motion.div
            className={`bg-white rounded-lg shadow-xl overflow-hidden w-full ${sizeClasses[size]} ${size === 'full' ? 'flex flex-col' : ''}`}
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={(e) => e.stopPropagation()} // Impedisce la chiusura cliccando sulla modale stessa
          >
            {/* Header della Modale */}
            <div className={`flex justify-between items-center p-4 border-b ${size === 'full' ? 'flex-shrink-0' : ''}`}>
              {title && <h2 className="text-xl font-semibold">{title}</h2>}
              <Button onClick={onClose} variant="ghost" size="sm" className="text-gray-500 hover:text-gray-800">
                {/* Icona X (placeholder) */}
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </Button>
            </div>

            {/* Contenuto della Modale */}
            <div className={`p-6 ${size === 'full' ? 'flex-grow overflow-y-auto' : ''}`}>
              {children}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default Modal;