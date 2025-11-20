'use client';

import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

type User = {
  id: number;
  email: string;
  role: string;      // 'org_admin' | 'team_manager' | 'employee'
} | null;

type AuthContextType = {
  user: User;
  login: (email: string, role: string, id: number) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User>(null);

  // Load user from localStorage on mount
  useEffect(() => {
    try {
      const raw = localStorage.getItem('auth_user');
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && parsed.id && parsed.email && parsed.role) {
          setUser(parsed);
        } else {
          setUser(null);
        }
      }
    } catch {
      setUser(null);
    }
  }, []);

  function login(email: string, role: string, id: number) {
    if (!id) {
      console.warn("Login called without a valid user ID");
      return;
    }

    const u = { email, role, id };
    setUser(u);

    try {
      localStorage.setItem('auth_user', JSON.stringify(u));
    } catch {}
  }

  function logout() {
    setUser(null);
    try { localStorage.removeItem('auth_user'); } catch {}
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
