import { createContext, useCallback, useContext, useEffect, useMemo, useState, ReactNode } from 'react';
import type { Business } from '../types';
import { businessApi } from '../services/api';

interface AuthContextValue {
  currentBusiness: Business | null;
  initializing: boolean;
  savedBusinesses: Array<{ id: number; name: string }>;
  setActiveBusiness: (business: Business) => void;
  clearBusiness: () => void;
  refreshBusiness: (id?: number) => Promise<Business | null>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const ACTIVE_BUSINESS_KEY = 'bizgenie.activeBusinessId';
const SAVED_BUSINESSES_KEY = 'bizgenie.savedBusinesses';

interface AuthProviderProps {
  children: ReactNode;
}

const parseSavedBusinesses = (): Array<{ id: number; name: string }> => {
  try {
    const raw = localStorage.getItem(SAVED_BUSINESSES_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch {
    return [];
  }
};

export function AuthProvider({ children }: AuthProviderProps) {
  const [currentBusiness, setCurrentBusiness] = useState<Business | null>(null);
  const [initializing, setInitializing] = useState(true);
  const [savedBusinesses, setSavedBusinesses] = useState<Array<{ id: number; name: string }>>(parseSavedBusinesses);

  const persistSavedBusinesses = useCallback((businesses: Array<{ id: number; name: string }>) => {
    setSavedBusinesses(businesses);
    localStorage.setItem(SAVED_BUSINESSES_KEY, JSON.stringify(businesses));
  }, []);

  const setActiveBusiness = useCallback((business: Business) => {
    setCurrentBusiness(business);
    localStorage.setItem(ACTIVE_BUSINESS_KEY, String(business.id));

    const exists = savedBusinesses.some((entry) => entry.id === business.id);
    if (!exists) {
      persistSavedBusinesses([{ id: business.id, name: business.name }, ...savedBusinesses].slice(0, 5));
    } else {
      const updated = savedBusinesses
        .filter((entry) => entry.id !== business.id)
        .map((entry) => entry);
      persistSavedBusinesses([{ id: business.id, name: business.name }, ...updated]);
    }
  }, [persistSavedBusinesses, savedBusinesses]);

  const clearBusiness = useCallback(() => {
    setCurrentBusiness(null);
    localStorage.removeItem(ACTIVE_BUSINESS_KEY);
  }, []);

  const refreshBusiness = useCallback(async (id?: number) => {
    const businessId = id ?? (currentBusiness?.id || Number(localStorage.getItem(ACTIVE_BUSINESS_KEY)));
    if (!businessId) {
      return null;
    }
    try {
      const business = await businessApi.get(businessId);
      setActiveBusiness(business);
      return business;
    } catch (error) {
      console.error('Failed to refresh business session', error);
      if (id === undefined) {
        clearBusiness();
      }
      return null;
    }
  }, [clearBusiness, currentBusiness?.id, setActiveBusiness]);

  useEffect(() => {
    const bootstrap = async () => {
      const storedId = localStorage.getItem(ACTIVE_BUSINESS_KEY);
      if (!storedId) {
        setInitializing(false);
        return;
      }
      await refreshBusiness(Number(storedId));
      setInitializing(false);
    };
    bootstrap();
  }, [refreshBusiness]);

  const value = useMemo<AuthContextValue>(() => ({
    currentBusiness,
    initializing,
    savedBusinesses,
    setActiveBusiness,
    clearBusiness,
    refreshBusiness,
  }), [currentBusiness, initializing, savedBusinesses, setActiveBusiness, clearBusiness, refreshBusiness]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/* eslint-disable-next-line react-refresh/only-export-components */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}


