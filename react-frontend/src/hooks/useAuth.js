import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { authFetch, clearTokens } from '../utils/apiClient';

export function useAuth() {
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  const handleLogout = useCallback(() => {
    clearTokens();
    navigate('/login');
  }, [navigate]);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await authFetch('/auth/users/me');
        if (response.ok) {
          setUser(await response.json());
        } else {
          handleLogout();
        }
      } catch {
        handleLogout();
      }
    };
    fetchUser();
  }, [handleLogout]);

  return { user, handleLogout };
}
