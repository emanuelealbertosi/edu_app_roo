import apiClient from './apiClient';
import type { AssignedQuiz, AssignedPathway, Wallet } from '../types/dashboard';

// Funzione per recuperare i quiz assegnati
export const fetchAssignedQuizzes = async (): Promise<AssignedQuiz[]> => {
  try {
    const response = await apiClient.get<AssignedQuiz[]>('/student/dashboard/quizzes/');
    // Assumiamo che l'API restituisca direttamente un array di AssignedQuiz
    return response.data;
  } catch (error) {
    console.error('Error fetching assigned quizzes:', error);
    // Rilancia l'errore per gestirlo con React Query
    throw error;
  }
};

// Funzione per recuperare i percorsi assegnati
export const fetchAssignedPathways = async (): Promise<AssignedPathway[]> => {
  try {
    const response = await apiClient.get<AssignedPathway[]>('/student/dashboard/pathways/');
    // Assumiamo che l'API restituisca direttamente un array di AssignedPathway
    return response.data;
  } catch (error) {
    console.error('Error fetching assigned pathways:', error);
    throw error;
  }
};

// Funzione per recuperare le informazioni del wallet
export const fetchWalletInfo = async (): Promise<Wallet> => {
  try {
    const response = await apiClient.get<Wallet>('/student/dashboard/wallet/');
    // Assumiamo che l'API restituisca direttamente l'oggetto Wallet
    return response.data;
  } catch (error) {
    console.error('Error fetching wallet info:', error);
    throw error;
  }
};

// Potremmo anche creare una funzione che chiama tutte e tre in parallelo
// export const fetchAllDashboardData = async (): Promise<{quizzes: AssignedQuiz[], pathways: AssignedPathway[], wallet: Wallet}> => {
//   try {
//     const [quizzesResponse, pathwaysResponse, walletResponse] = await Promise.all([
//       apiClient.get<AssignedQuiz[]>('/student/dashboard/quizzes/'),
//       apiClient.get<AssignedPathway[]>('/student/dashboard/pathways/'),
//       apiClient.get<Wallet>('/student/dashboard/wallet/')
//     ]);
//     return {
//       quizzes: quizzesResponse.data,
//       pathways: pathwaysResponse.data,
//       wallet: walletResponse.data
//     };
//   } catch (error) {
//     console.error('Error fetching all dashboard data:', error);
//     throw error;
//   }
// };