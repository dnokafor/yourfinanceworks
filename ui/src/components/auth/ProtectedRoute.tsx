import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');

    if (!token || !user) {
      // No authentication data, redirect to login
      navigate('/login');
      return;
    }

    try {
      // Validate that user data is valid JSON
      JSON.parse(user);
    } catch (error) {
      // Invalid user data, clear and redirect
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      navigate('/login');
    }
  }, [navigate]);

  // Check if user is authenticated
  const token = localStorage.getItem('token');
  const user = localStorage.getItem('user');

  if (!token || !user) {
    return null; // Don't render anything while redirecting
  }

  return <>{children}</>;
} 