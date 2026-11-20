import React, { createContext, useState, useEffect, useContext } from 'react';
import api from '../api/client';

const AuthContext = createContext();

const DEFAULT_ADMIN_USER = {
  id: 4,
  email: 'admin@village.gov.in',
  name: 'Divya Prasad',
  role: 'ADMIN'
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    try {
      const savedUser = localStorage.getItem('gis_user');
      if (savedUser) return JSON.parse(savedUser);
    } catch (e) {}
    return DEFAULT_ADMIN_USER;
  });

  const [token, setToken] = useState(() => localStorage.getItem('token') || '');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          const res = await api.get('/users/me');
          setUser(res.data);
          localStorage.setItem('gis_user', JSON.stringify(res.data));
        } catch (e) {
          // Token might have expired, re-login demo admin
          await autoLoginDemo();
        }
      } else {
        await autoLoginDemo();
      }
    };

    const autoLoginDemo = async () => {
      try {
        const res = await api.post('/auth/login', {
          email: 'admin@village.gov.in',
          password: 'Password123!'
        });
        const { access_token, role, user_id, name } = res.data;
        const userData = { id: user_id, email: 'admin@village.gov.in', name: name || 'Divya Prasad', role };
        localStorage.setItem('token', access_token);
        localStorage.setItem('gis_user', JSON.stringify(userData));
        setToken(access_token);
        setUser(userData);
      } catch (err) {
        console.log('Using fallback demo profile');
      }
    };

    initAuth();
  }, []);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const { access_token, role, user_id, name } = res.data;
    const userData = { id: user_id, email, name: name || 'Divya Prasad', role };
    localStorage.setItem('token', access_token);
    localStorage.setItem('gis_user', JSON.stringify(userData));
    setToken(access_token);
    setUser(userData);
    return res.data;
  };

  const register = async (userData) => {
    const res = await api.post('/auth/register', userData);
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('gis_user');
    setToken('');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, role: user?.role, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
