// src/api/mockAuth.ts
interface LoginCredentials {
  email: string;
  password: string;
}

interface LoginResponse {
  token: string;
  user: {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
  };
}

const mockAuth = {
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (credentials.email === 'test@example.com' && credentials.password === 'password') {
          resolve({
            token: 'mocked_jwt_token',
            user: {
              id: 1,
              email: 'test@example.com',
              first_name: 'Test',
              last_name: 'User',
            },
          });
        } else {
          reject({
            response: {
              status: 401,
              data: { message: 'Invalid credentials' },
            },
          });
        }
      }, 500); // Simula un ritardo di 500ms
    });
  },
};

export default mockAuth;