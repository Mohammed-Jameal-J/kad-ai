"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import * as api from "@/services/authApi";

type AuthContextValue = {
  user: api.User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<api.User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.me()
      .then(setUser)
      .catch(() => setUser(null)) // backend down: behave as a guest
      .finally(() => setLoading(false));
  }, []);

  const value: AuthContextValue = {
    user,
    loading,
    login: useCallback(async (email, password) => setUser(await api.login(email, password)), []),
    register: useCallback(async (name, email, password) => setUser(await api.register(name, email, password)), []),
    logout: useCallback(async () => {
      await api.logout();
      setUser(null);
    }, []),
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
