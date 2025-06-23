import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios'; // Import axios
import { API_URL } from '../config'; // Import API_URL
import { getCurrentUser } from '../api/authApi';

const AuthContext = createContext({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: () => {},
  logout: () => {},
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const isAuthenticated = !!user;

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await getCurrentUser();
        if (userData) {
          setUser({ email: userData.user });
        }
      } catch (error) {
        console.error('Auth check failed:', error);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  const login = async (userData) => {
    try {
      const response = await axios.post(`${API_URL}/auth/login`, userData);
      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        // Get the user data from the token or make a request to /protected
        const userResponse = await axios.get(`${API_URL}/auth/protected`, {
          headers: { Authorization: `Bearer ${response.data.access_token}` },
        });
        setUser({ email: userResponse.data.user });
        return true;
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        logout,
      }}
    >
      {!isLoading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
