import { createContext, useCallback, useEffect, useState } from "react";
import { authApi, tokenStorage } from "../services/api";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadUser = useCallback(async () => {
    if (!tokenStorage.getAccess()) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const { data } = await authApi.me();
      setUser(data);
    } catch {
      tokenStorage.clear();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (username, password) => {
    const { data } = await authApi.login(username, password);
    tokenStorage.set(data.access, data.refresh);
    await loadUser();
  };

  const logout = () => {
    tokenStorage.clear();
    setUser(null);
  };

  const canWrite = user?.role === "ADMIN" || user?.role === "OPERATOR";
  const isAdmin = user?.role === "ADMIN";

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, canWrite, isAdmin }}>
      {children}
    </AuthContext.Provider>
  );
}
