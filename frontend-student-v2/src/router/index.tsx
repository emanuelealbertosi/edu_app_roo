import React from 'react';
// Importa useLocation e Routes, Route
import { Routes, Route, useLocation } from 'react-router-dom';
// Importa AnimatePresence e motion da framer-motion
import { AnimatePresence, motion } from 'framer-motion';
import HomePage from '../pages/HomePage';
import LoginPage from '../pages/LoginPage';
import DashboardPage from '../pages/DashboardPage';
import QuizAttemptPage from '../pages/QuizAttemptPage'; // Import QuizAttemptPage
// Import other pages here as they are created
// import NotFoundPage from '../pages/NotFoundPage';

const AppRoutes: React.FC = () => {
  const location = useLocation(); // Ottieni la location corrente

  return (
    // Avvolgi le Routes con AnimatePresence
    <AnimatePresence mode="wait">
      {/* Passa location e key a Routes */}
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="/quiz/:quizId/attempt" element={<QuizAttemptPage />} /> {/* Add Quiz Attempt route */}
      {/* Add other routes here */}
      {/* Example for a 404 page */}
      {/* <Route path="*" element={<NotFoundPage />} /> */}
      </Routes>
    </AnimatePresence>
  );
};

export default AppRoutes;