"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

const API_KEY_STORAGE_KEY = "forma3d_api_key";
const AuthContext = createContext(null);

function loadInitialKey() {
  if (typeof window === "undefined") return process.env.NEXT_PUBLIC_API_KEY || null;
  const stored = window.localStorage.getItem(API_KEY_STORAGE_KEY);
  return stored || process.env.NEXT_PUBLIC_API_KEY || null;
}

export function AuthProvider({ children }) {
  const [apiKey, setApiKey] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setApiKey(loadInitialKey());
    setReady(true);
  }, []);

  const updateKey = (value) => {
    setApiKey(value);
    if (typeof window !== "undefined") {
      if (value) {
        window.localStorage.setItem(API_KEY_STORAGE_KEY, value);
      } else {
        window.localStorage.removeItem(API_KEY_STORAGE_KEY);
      }
    }
  };

  const value = useMemo(
    () => ({ apiKey, setApiKey: updateKey, clearApiKey: () => updateKey(null), ready }),
    [apiKey]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

