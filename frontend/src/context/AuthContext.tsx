'use client';

// frontend/context/AuthContext.tsx
import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

type User = {
  email: string;
  role: string; // e.g. 'org_admin' | 'team_manager' | 'employee'
} | null;

type AuthContextType = {
  user: User;
  login: (email: string, role: string) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User>(null);

  useEffect(() => {
    // Optional: restore user from localStorage
    try {
      const raw = localStorage.getItem('auth_user');
      if (raw) setUser(JSON.parse(raw));
    } catch {
      /* ignore */
    }
  }, []);

  function login(email: string, role: string) {
    const u = { email, role };
    setUser(u);
    try {
      localStorage.setItem('auth_user', JSON.stringify(u));
    } catch {}
  }

  function logout() {
    setUser(null);
    try {
      localStorage.removeItem('auth_user');
    } catch {}
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
