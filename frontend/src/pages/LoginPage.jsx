import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../stores/authStore';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [tagline, setTagline] = useState('');
  const { login, isLoading, error, clearError, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    // Load tagline
    fetch('/tagline.txt')
      .then((res) => res.text())
      .then((text) => setTagline(text.trim()))
      .catch(() => setTagline('Raise Up The Heard'));
  }, []);

  useEffect(() => {
    return () => clearError();
  }, [clearError]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await login(email, password);
    if (success) {
      navigate('/');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-ruth-navy to-ruth-blue flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Logo */}
        <div className="text-center mb-8">
          <img
            src="/ruth_logo.png"
            alt="Ruth Logo"
            className="h-96 mx-auto mb-4"
          />
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-lg shadow-xl p-8">
          <h2 className="text-2xl font-bold text-center mb-6 text-gray-900">
            Sign In
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" autoComplete="on">
            <div>
              <label htmlFor="email" className="label">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                required
                autoComplete="username"
              />
            </div>

            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                required
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn btn-primary"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-gray-600">
            Don't have an account?{' '}
            <Link
              to="/register"
              className="text-ruth-blue hover:text-blue-700 font-medium"
            >
              Register
            </Link>
          </p>

          {/* Version and Policy Links */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="flex flex-col items-center gap-2 text-xs text-gray-500">
              <div>Ruth v{import.meta.env.VITE_APP_VERSION || 'unknown'}</div>
              <div className="flex gap-4">
                <Link
                  to="/terms"
                  className="hover:text-ruth-blue transition-colors"
                >
                  Terms of Service
                </Link>
                <Link
                  to="/privacy"
                  className="hover:text-ruth-blue transition-colors"
                >
                  Privacy Policy
                </Link>
              </div>
              <div>© 2025 Brian West</div>
            </div>
          </div>
        </div>

        {/* Tagline */}
        <div className="mt-8 text-center">
          <p className="text-white text-sm">{tagline}</p>
        </div>
      </div>
    </div>
  );
}
