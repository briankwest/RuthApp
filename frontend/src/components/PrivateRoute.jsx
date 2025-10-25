import { Navigate } from 'react-router-dom';
import useAuthStore from '../stores/authStore';

export default function PrivateRoute({ children }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return isAuthenticated ? children : <Navigate to="/login" replace />;
}
