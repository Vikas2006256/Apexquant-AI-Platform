import { create } from "zustand";

interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  risk_limit_pct: number;
}

interface Position {
  id: string;
  ticker: string;
  quantity: number;
  side: string;
  entry_price: number;
  current_price: number;
  stop_loss: number | null;
  take_profit: number | null;
  status: string;
  pnl: number;
}

interface Portfolio {
  id: string;
  name: string;
  type: string;
  balance: number;
  initial_balance: number;
  positions: Position[];
}

interface AppState {
  token: string | null;
  user: User | null;
  activeSymbol: string;
  portfolios: Portfolio[];
  activePortfolio: Portfolio | null;
  isLoading: boolean;
  
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  setSymbol: (symbol: string) => void;
  setPortfolios: (portfolios: Portfolio[]) => void;
  setActivePortfolio: (portfolio: Portfolio | null) => void;
  setLoading: (loading: boolean) => void;
  
  initializeAuth: () => void;
  logout: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  token: null,
  user: null,
  activeSymbol: "AAPL",
  portfolios: [],
  activePortfolio: null,
  isLoading: false,

  setToken: (token) => set({ token }),
  setUser: (user) => set({ user }),
  setSymbol: (activeSymbol) => set({ activeSymbol }),
  setPortfolios: (portfolios) => set({ portfolios }),
  setActivePortfolio: (activePortfolio) => set({ activePortfolio }),
  setLoading: (isLoading) => set({ isLoading }),

  initializeAuth: () => {
    if (typeof window !== "undefined") {
      const savedToken = localStorage.getItem("apex_token");
      if (savedToken) {
        set({ token: savedToken });
      }
    }
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("apex_token");
    }
    set({ token: null, user: null, portfolios: [], activePortfolio: null });
  }
}));
