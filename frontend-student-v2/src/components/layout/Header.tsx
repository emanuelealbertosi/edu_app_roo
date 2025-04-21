import React from 'react';
import { Link, useNavigate } from 'react-router-dom'; // Aggiunto useNavigate
import useAuthStore from '../../stores/authStore'; // Importa lo store di autenticazione
import Button from '../common/Button'; // Importa il componente Button

const Header: React.FC = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const logout = useAuthStore((state) => state.logout);
  const student = useAuthStore((state) => state.student); // Prendi anche i dati studente
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login'); // Reindirizza al login dopo il logout
  };

  return (
    <header className="bg-gray-800 text-white shadow-md sticky top-0 z-50"> {/* Aggiunto sticky e z-index */}
      <nav className="container mx-auto px-4 py-3 flex justify-between items-center">
        {/* Logo/Title */}
        <Link to={isAuthenticated ? "/dashboard" : "/"} className="text-xl font-bold hover:text-gray-300">
          EduApp Studenti V2
        </Link>

        {/* Navigation Links / User Info */}
        <div className="flex items-center space-x-4">
          {isAuthenticated ? (
            <>
              {/* Mostra il nome utente se disponibile */}
              {student && <span className="text-sm hidden sm:inline">Ciao, {student.first_name || 'Studente'}</span>}
              <Link to="/dashboard" className="hover:text-gray-300">Dashboard</Link>
              {/* Aggiungere altri link per utenti loggati qui (es. Profilo) */}
              <Button onClick={handleLogout} variant="secondary" size="sm">
                Logout
              </Button>
            </>
          ) : (
            <>
              <Link to="/" className="hover:text-gray-300">Home</Link>
              <Link to="/login" className="hover:text-gray-300">Login</Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
};

export default Header;