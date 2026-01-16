'use client';

import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { io } from "socket.io-client";

type User = {
  id: number;
  email: string;
  role: string;
} | null;

type AuthContextType = {
  user: User;
  login: (email: string, role: string, id: number) => void;
  logout: () => void;
  loading: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const socket = io("http://localhost:8000", {
  withCredentials: true,
  transports: ["websocket"],
  autoConnect: false,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    try {
      const raw = localStorage.getItem('auth_user');
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && parsed.id && parsed.email && parsed.role) setUser(parsed);
      }
    } catch {}
    setLoading(false);
  }, []);

  function login(email: string, role: string, id: number) {
    const u: User = { email, role, id };
    setUser(u);
    localStorage.setItem('auth_user', JSON.stringify(u));
  }

  function logout() {
    setUser(null);
    localStorage.removeItem('auth_user');
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
