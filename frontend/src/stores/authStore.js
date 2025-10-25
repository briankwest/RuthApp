import { create } from 'zustand';
import { authAPI } from '../services/api';

const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authAPI.login(email, password);
      const { user, tokens } = response.data;

      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);

      set({ user, isAuthenticated: true, isLoading: false });
      return true;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Login failed',
        isLoading: false
      });
      return false;
    }
  },

  register: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authAPI.register(data);
      const { user, tokens } = response.data;

      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);

      set({ user, isAuthenticated: true, isLoading: false });
      return true;
    } catch (error) {
      set({
        error: error.response?.data?.detail || 'Registration failed',
        isLoading: false
      });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, isAuthenticated: false });
  },

  loadUser: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isAuthenticated: false, isLoading: false });
      return;
    }

    try {
      const response = await authAPI.getProfile();
      set({ user: response.data, isAuthenticated: true, isLoading: false });
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  clearError: () => set({ error: null }),
}));

export default useAuthStore;
