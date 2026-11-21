import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { restoreSession } from '../api';
import { setUserListener } from '../api/client';
import type { User } from '../api/types';

interface AuthState {
  user: User | null;
  loading: boolean;
  setUser: (user: User | null) => void;
}

const AuthContext = createContext<AuthState>({ user: null, loading: true, setUser: () => undefined });

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setUserListener(setUser);
    restoreSession()
      .catch(() => null)
      .finally(() => setLoading(false));
    return () => setUserListener(null);
  }, []);

  const value = useMemo(() => ({ user, loading, setUser }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
