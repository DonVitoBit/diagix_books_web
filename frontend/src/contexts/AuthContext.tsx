import React, { createContext, useContext, useState, useCallback } from "react";

export type UserRole = "admin" | "moderator" | "guest";

export interface User {
  username: string;
  name: string;
  role: UserRole;
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  isAdmin: boolean;
  isModerator: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

// Mock auth - replace with real API calls
const MOCK_USERS: Record<string, { password: string; user: User }> = {
  admin: {
    password: "admin123",
    user: { username: "admin", name: "Администратор", role: "admin" },
  },
  moderator: {
    password: "mod123",
    user: { username: "moderator", name: "Иван Петров", role: "moderator" },
  },
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = sessionStorage.getItem("tr_user");
    return saved ? JSON.parse(saved) : null;
  });

  const login = useCallback(async (username: string, password: string) => {
    // Mock login - replace with POST /auth/login
    const entry = MOCK_USERS[username];
    if (entry && entry.password === password) {
      setUser(entry.user);
      sessionStorage.setItem("tr_user", JSON.stringify(entry.user));
      return true;
    }
    return false;
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    sessionStorage.removeItem("tr_user");
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        isAdmin: user?.role === "admin",
        isModerator: user?.role === "moderator",
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
