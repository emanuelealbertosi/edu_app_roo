import React from 'react';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-100 text-gray-600 text-center p-4 mt-8 border-t">
      <p>&copy; {currentYear} EduApp. Tutti i diritti riservati.</p>
      {/* Potremmo aggiungere altri link o informazioni qui */}
    </footer>
  );
};

export default Footer;