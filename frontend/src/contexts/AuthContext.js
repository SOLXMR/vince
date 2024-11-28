import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      console.log('Setting token in axios defaults:', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setIsAuthenticated(true);
      // Get user profile
      fetchProfile();
    }
    setLoading(false);
  }, []);

  const setAuthToken = (token) => {
    if (token) {
      localStorage.setItem('token', token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      console.log('Token set in axios defaults:', axios.defaults.headers.common['Authorization']);
    } else {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    }
  };

  const fetchProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('Token from localStorage:', token);
      console.log('Current axios headers:', axios.defaults.headers.common);
      
      const response = await axios.get('/api/auth/profile');
      setUser(response.data.user);
    } catch (error) {
      console.error('Error fetching profile:', error);
      console.error('Request config:', error.config);
      if (error.response) {
        console.error('Response data:', error.response.data);
        console.error('Response status:', error.response.status);
        console.error('Response headers:', error.response.headers);
      }
      logout();
    }
  };

  const login = async (username, password) => {
    try {
      console.log('Sending login request...');
      const response = await axios.post('/api/auth/login', {
        username,
        password
      });
      console.log('Login response:', response.data);
      
      const { token } = response.data;
      setAuthToken(token);
      setIsAuthenticated(true);
      await fetchProfile();
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    }
  };

  const register = async (username, email, password) => {
    try {
      console.log('Sending registration request...');
      const response = await axios.post('/api/auth/register', {
        username,
        email,
        password
      });
      console.log('Registration response:', response.data);
      
      const { token } = response.data;
      setAuthToken(token);
      console.log('Token set in localStorage and axios defaults');
      setIsAuthenticated(true);
      await fetchProfile();
      return { success: true };
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: error.message };
    }
  };

  const logout = () => {
    setAuthToken(null);
    setIsAuthenticated(false);
    setUser(null);
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext); 