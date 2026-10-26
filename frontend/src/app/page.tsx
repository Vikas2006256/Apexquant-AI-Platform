"use client";

import React, { useEffect, useState } from "react";
import { useAppStore } from "@/store";
import { TradingViewChart } from "@/components/TradingViewChart";
import { getApiUrl } from "@/config";
import { MultiAgentConsole } from "@/components/MultiAgentConsole";
import {
  Cpu,
  CreditCard,
  Lock,
  Mail,
  User as UserIcon,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Shield,
  Activity,
  BarChart2,
  LogOut,
  Search,
  ChevronRight,
  AlertCircle,
  CheckCircle2,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Settings,
  X,
  Save,
} from "lucide-react";

export default function TerminalDashboard() {
  const {
    token, setToken, user, setUser,
    portfolios, setPortfolios,
    activePortfolio, setActivePortfolio,
    activeSymbol, setSymbol,
  } = useAppStore();

  // Auth Form State
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("trader@apexquant.ai");
  const [password, setPassword] = useState("password123");
  const [fullName, setFullName] = useState("Vikas Quant");
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);

  // API settings state
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [openaiKey, setOpenaiKey] = useState("");
  const [geminiKey, setGeminiKey] = useState("");
  const [savingSettings, setSavingSettings] = useState(false);

  const fetchSettings = async () => {
    try {
      const response = await fetch(getApiUrl("/api/v1/settings"));
      if (response.ok) {
        const data = await response.json();
        setOpenaiKey(data.openai_api_key || "");
        setGeminiKey(data.gemini_api_key || "");
      }
    } catch (err) {
      console.error("Failed to load settings:", err);
    }
  };

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingSettings(true);
    try {
      const response = await fetch(getApiUrl("/api/v1/settings"), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          openai_api_key: openaiKey,
          gemini_api_key: geminiKey
        })
      });
      if (response.ok) {
        setShowSettingsModal(false);
      } else {
        alert("Failed to save settings. Please try again.");
      }
    } catch (err) {
      console.error("Failed to save settings:", err);
      alert("Failed to connect to backend server.");
    } finally {
      setSavingSettings(false);
    }
  };

  useEffect(() => {
    if (showSettingsModal) {
      fetchSettings();
    }
  }, [showSettingsModal]);

  // Market & Order State
  const [ticker, setTicker] = useState("AAPL");
  const [selectedPeriod, setSelectedPeriod] = useState("max");
  const [selectedInterval, setSelectedInterval] = useState("1d");
  const [ohlcvData, setOhlcvData] = useState<any[]>([]);
  const [orderQty, setOrderQty] = useState("10");
  const [orderAction, setOrderAction] = useState("buy");
  const [stopLossVal, setStopLossVal] = useState("");
  const [takeProfitVal, setTakeProfitVal] = useState("");
  const [orderMessage, setOrderMessage] = useState("");
  const [orderMessageType, setOrderMessageType] = useState<"success" | "error">("success");

  // Analysis State
  const [report, setReport] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isMarketLoading, setIsMarketLoading] = useState(false);

  // Live Global Search State
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);

  useEffect(() => {
    if (!ticker || ticker.trim().length < 1) {
      setSearchResults([]);
      setShowSearchDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await fetch(getApiUrl(`/api/v1/market/search?q=${encodeURIComponent(ticker.trim())}`));
        if (res.ok) {
          const data = await res.json();
          setSearchResults(data || []);
          setShowSearchDropdown(true);
        }
      } catch (e) {
        console.error("Live ticker search error:", e);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [ticker]);

  const selectSearchSymbol = (sym: string) => {
    setTicker(sym);
    setSymbol(sym);
    setShowSearchDropdown(false);
  };

  // Initialize auth token & auto demo login
  useEffect(() => {
    const savedToken = localStorage.getItem("apex_token");
    if (savedToken) {
      setToken(savedToken);
    } else {
      autoDemoLogin();
    }
  }, [setToken]);

  const autoDemoLogin = async () => {
    try {
      const formData = new URLSearchParams();
      formData.append("username", "trader@apexquant.ai");
      formData.append("password", "password123");
      const res = await fetch(getApiUrl("/api/v1/auth/login"), {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("apex_token", data.access_token);
        setToken(data.access_token);
      }
    } catch (e) {
      console.error("Auto demo login error:", e);
    }
  };

  useEffect(() => {
    if (token) fetchUserData();
  }, [token]);

  useEffect(() => {
    loadMarketData(activeSymbol, selectedPeriod, selectedInterval);
    // Refresh full historical dataset every 60 seconds (real-time ticks handle instant updates)
    const intervalId = setInterval(() => {
      loadMarketData(activeSymbol, selectedPeriod, selectedInterval);
    }, 60000);
    return () => clearInterval(intervalId);
  }, [activeSymbol, selectedPeriod, selectedInterval]);

  useEffect(() => {
    setTicker(activeSymbol);
  }, [activeSymbol]);

  const fetchUserData = async () => {
    try {
      const profileRes = await fetch(getApiUrl("/api/v1/auth/me"), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (profileRes.ok) {
        const profile = await profileRes.json();
        setUser(profile);
      } else {
        logoutUser();
        return;
      }

      const portfoliosRes = await fetch(getApiUrl("/api/v1/portfolios/"), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (portfoliosRes.ok) {
        let list = await portfoliosRes.json();
        if (list.length === 0) {
          const createRes = await fetch(getApiUrl("/api/v1/portfolios/"), {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify({ name: "Main Paper Account", type: "paper", balance: 100000.0 }),
          });
          if (createRes.ok) {
            const newP = await createRes.json();
            list = [newP];
          }
        }
        setPortfolios(list);
        setActivePortfolio(list[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadMarketData = async (
    targetTicker = activeSymbol,
    pVal = selectedPeriod,
    iVal = selectedInterval
  ) => {
    setIsMarketLoading(true);
    try {
      const res = await fetch(
        getApiUrl(`/api/v1/market/ohlcv?ticker=${encodeURIComponent(targetTicker)}&period=${pVal}&interval=${iVal}`)
      );
      if (res.ok) {
        const data = await res.json();
        setOhlcvData(data || []);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsMarketLoading(false);
    }
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    setAuthLoading(true);
    try {
      if (authMode === "login") {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);
        const res = await fetch(getApiUrl("/api/v1/auth/login"), {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: formData,
        });
        if (res.ok) {
          const data = await res.json();
          localStorage.setItem("apex_token", data.access_token);
          setToken(data.access_token);
        } else {
          const err = await res.json();
          setAuthError(err.detail || "Authentication failed");
        }
      } else {
        const res = await fetch(getApiUrl("/api/v1/auth/register"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password, full_name: fullName, risk_limit_pct: 2.0 }),
        });
        if (res.ok) {
          setAuthMode("login");
          setAuthError("Registration successful — please sign in.");
        } else {
          const err = await res.json();
          setAuthError(err.detail || "Registration failed");
        }
      }
    } catch {
      setAuthError("Cannot connect to backend server");
    } finally {
      setAuthLoading(false);
    }
  };

  const logoutUser = () => {
    localStorage.removeItem("apex_token");
    setToken(null);
    setUser(null);
    setPortfolios([]);
    setActivePortfolio(null);
    setReport(null);
  };

  const handleSymbolChange = (e: React.FormEvent) => {
    e.preventDefault();
    if (ticker.trim()) setSymbol(ticker.toUpperCase().trim());
  };

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setOrderMessage("");

    let currentPortfolio = activePortfolio;
    if (!currentPortfolio && portfolios.length > 0) {
      currentPortfolio = portfolios[0];
      setActivePortfolio(portfolios[0]);
    }

    if (!currentPortfolio) {
      setOrderMessage("Initializing portfolio account...");
      setOrderMessageType("error");
      await fetchUserData();
      return;
    }

    try {
      const payload: any = {
        ticker: activeSymbol,
        quantity: parseFloat(orderQty) || 1,
        action: orderAction,
        side: "long",
      };
      if (stopLossVal && !isNaN(parseFloat(stopLossVal))) payload.stop_loss = parseFloat(stopLossVal);
      if (takeProfitVal && !isNaN(parseFloat(takeProfitVal))) payload.take_profit = parseFloat(takeProfitVal);

      let authToken = token || localStorage.getItem("apex_token");
      if (!authToken) {
        await autoDemoLogin();
        authToken = localStorage.getItem("apex_token");
      }

      const res = await fetch(
        getApiUrl(`/api/v1/portfolios/${currentPortfolio.id}/order`),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify(payload),
        }
      );

      if (res.ok) {
        setOrderMessage(`Order Executed: ${orderAction.toUpperCase()} ${orderQty} ${activeSymbol}`);
        setOrderMessageType("success");
        await fetchUserData();
      } else {
        const err = await res.json();
        setOrderMessage(`Execution Error: ${err.detail || "Failed to fill order"}`);
        setOrderMessageType("error");
      }
    } catch (e: any) {
      setOrderMessage(`Order Error: ${e.message || "Failed to communicate with backend"}`);
      setOrderMessageType("error");
    }
  };

  const handleClosePosition = async (pos: any) => {
    if (!activePortfolio) return;
    try {
      const payload = {
        ticker: pos.ticker,
        quantity: pos.quantity,
        action: "sell",
        side: pos.side,
      };
      let authToken = token || localStorage.getItem("apex_token");
      const res = await fetch(
        getApiUrl(`/api/v1/portfolios/${activePortfolio.id}/order`),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${authToken}`,
          },
          body: JSON.stringify(payload),
        }
      );
      if (res.ok) {
        setOrderMessage(`Position Closed: SOLD ${pos.quantity} ${pos.ticker}`);
        setOrderMessageType("success");
        await fetchUserData();
      } else {
        const err = await res.json();
        setOrderMessage(`Close Error: ${err.detail || "Failed to close position"}`);
        setOrderMessageType("error");
      }
    } catch (e: any) {
      setOrderMessage(`Error: ${e.message}`);
      setOrderMessageType("error");
    }
  };

  const runAgentConsensus = async (userQuery: string) => {
    setIsAnalyzing(true);
    try {
      const res = await fetch(getApiUrl("/api/v1/agents/analyze"), {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          ticker: activeSymbol,
          user_query: userQuery,
          portfolio_id: activePortfolio?.id,
        }),
      });
      if (res.ok) {
        const r = await res.json();
        setReport(r);
        return r;
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // ───────────────────────────────────────────────
  // AUTH SCREEN
  // ───────────────────────────────────────────────
  if (!token) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center px-4 animate-fade-in">
        {/* Background glow */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full bg-indigoAccent/5 blur-[80px]" />
        </div>

        <div className="relative w-full max-w-md">
          {/* Card */}
          <div className="glass-card p-8 animate-slide-up">
            {/* Header */}
            <div className="mb-8 text-center">
              <div className="mx-auto mb-4 relative w-16 h-16 flex items-center justify-center">
                <div className="absolute inset-0 rounded-2xl bg-indigoAccent/20 blur-md animate-pulse-slow" />
                <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-indigoAccent to-purpleAccent flex items-center justify-center shadow-neon-indigo">
                  <Cpu className="h-8 w-8 text-white" />
                </div>
              </div>
              <h2 className="font-display text-2xl font-black text-white tracking-tight">
                {authMode === "login" ? "Welcome Back" : "Create Account"}
              </h2>
              <p className="mt-1.5 text-xs text-gray-500">
                {authMode === "login"
                  ? "Access your institutional trading terminal"
                  : "Register for quantitative decision support"}
              </p>
            </div>

            {/* Toggle tabs */}
            <div className="mb-6 flex rounded-xl p-1" style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <button
                onClick={() => { setAuthMode("login"); setAuthError(""); }}
                id="tab-login"
                className={`flex-1 rounded-lg py-2 text-sm font-bold transition-all duration-200 ${
                  authMode === "login" ? "bg-indigoAccent text-white shadow-neon-indigo" : "text-gray-500 hover:text-gray-300"
                }`}
              >
                Sign In
              </button>
              <button
                onClick={() => { setAuthMode("register"); setAuthError(""); }}
                id="tab-register"
                className={`flex-1 rounded-lg py-2 text-sm font-bold transition-all duration-200 ${
                  authMode === "register" ? "bg-indigoAccent text-white shadow-neon-indigo" : "text-gray-500 hover:text-gray-300"
                }`}
              >
                Register
              </button>
            </div>

            {/* Alert */}
            {authError && (
              <div className={`mb-4 flex items-center gap-2 rounded-xl p-3 text-xs animate-slide-up ${
                authError.includes("successful")
                  ? "bg-emeraldGreen/10 border border-emeraldGreen/20 text-emeraldGreen"
                  : "bg-roseRed/10 border border-roseRed/20 text-roseRed"
              }`}>
                {authError.includes("successful") ? (
                  <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                ) : (
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                )}
                {authError}
              </div>
            )}

            <form onSubmit={handleAuthSubmit} className="space-y-4">
              {authMode === "register" && (
                <div className="animate-slide-up">
                  <label className="section-label mb-1.5 block">Full Name</label>
                  <div className="relative">
                    <UserIcon className="absolute left-3.5 top-3.5 h-4 w-4 text-gray-500" />
                    <input
                      type="text"
                      id="input-full-name"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="terminal-input py-3 pl-10 pr-4"
                      placeholder="Your full name"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="section-label mb-1.5 block">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-3.5 h-4 w-4 text-gray-500" />
                  <input
                    type="email"
                    id="input-email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="terminal-input py-3 pl-10 pr-4"
                    placeholder="trader@apexquant.ai"
                  />
                </div>
              </div>

              <div>
                <label className="section-label mb-1.5 block">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3.5 top-3.5 h-4 w-4 text-gray-500" />
                  <input
                    type="password"
                    id="input-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="terminal-input py-3 pl-10 pr-4"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <button
                type="submit"
                id="btn-auth-submit"
                disabled={authLoading}
                className="neon-btn-indigo w-full py-3 text-sm flex items-center justify-center gap-2 disabled:opacity-60"
              >
                {authLoading ? (
                  <>
                    <Cpu className="h-4 w-4 animate-spin" />
                    Authenticating...
                  </>
                ) : (
                  <>
                    {authMode === "login" ? "Enter Terminal" : "Create Account"}
                    <ChevronRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </form>

            {/* Decorative bottom text */}
            <div className="mt-6 pt-4 border-t border-darkBorder text-center">
              <p className="text-[10px] font-mono text-gray-600">
                Protected by institutional-grade encryption
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Compute portfolio stats
  const openPositions = activePortfolio?.positions?.filter((p: any) => p.status === "open") ?? [];
  const totalPnl = openPositions.reduce((acc: number, p: any) => acc + (p.pnl || 0), 0);

  // ───────────────────────────────────────────────
  // MAIN DASHBOARD
  // ───────────────────────────────────────────────
  return (
    <div className="space-y-5 animate-fade-in">
      {/* ── Institutional Live Ticker Tape Marquee ── */}
      <div className="glass-card p-2 px-4 rounded-xl flex items-center justify-between gap-4 overflow-x-auto no-scrollbar text-xs font-mono text-gray-300 border-indigoAccent/20">
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="h-2 w-2 rounded-full bg-emeraldGreen animate-pulse" />
          <span className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Global Markets:</span>
        </div>
        <div className="flex items-center gap-6 overflow-x-auto no-scrollbar shrink-0">
          <div className="flex items-center gap-1.5">
            <span className="text-gray-400 font-bold">S&P 500</span>
            <span className="font-bold text-white">5,432.10</span>
            <span className="text-emeraldGreen font-bold flex items-center text-[10px]"><ArrowUpRight className="h-3 w-3" />+0.65%</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-gray-400 font-bold">NASDAQ</span>
            <span className="font-bold text-white">17,210.40</span>
            <span className="text-emeraldGreen font-bold flex items-center text-[10px]"><ArrowUpRight className="h-3 w-3" />+1.12%</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-gray-400 font-bold">BTC/USD</span>
            <span className="font-bold text-white">$94,250.00</span>
            <span className="text-emeraldGreen font-bold flex items-center text-[10px]"><ArrowUpRight className="h-3 w-3" />+3.40%</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-gray-400 font-bold">ETH/USD</span>
            <span className="font-bold text-white">$3,480.00</span>
            <span className="text-emeraldGreen font-bold flex items-center text-[10px]"><ArrowUpRight className="h-3 w-3" />+2.85%</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-gray-400 font-bold">AAPL</span>
            <span className="font-bold text-white">$330.90</span>
            <span className="text-roseRed font-bold flex items-center text-[10px]"><ArrowDownRight className="h-3 w-3" />-0.42%</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-gray-400 font-bold">NVDA</span>
            <span className="font-bold text-white">$128.50</span>
            <span className="text-emeraldGreen font-bold flex items-center text-[10px]"><ArrowUpRight className="h-3 w-3" />+4.18%</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-gray-400 font-bold">VIX</span>
            <span className="font-bold text-white">14.20</span>
            <span className="text-emeraldGreen font-bold text-[10px]">-3.10%</span>
          </div>
        </div>
      </div>

      {/* ── Top Bar ── */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        {/* Left: Title */}
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="section-label">Institutional Terminal</span>
            <span className="text-[10px] font-mono text-gray-500">/ 15-agent consensus engine</span>
          </div>
          <h2 className="font-display text-2xl font-black text-white leading-none">
            Market Intelligence{" "}
            <span className="gradient-text-indigo">Dashboard</span>
          </h2>
        </div>

        {/* Right: Controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Symbol Search */}
          <div className="relative">
            <form
              onSubmit={(e) => {
                handleSymbolChange(e);
                setShowSearchDropdown(false);
              }}
              className="flex items-center gap-2 glass-card px-3 py-2 rounded-xl border border-indigoAccent/30 focus-within:border-indigoAccent transition-all"
            >
              <Search className="h-4 w-4 text-indigoAccent" />
              <input
                type="text"
                id="input-ticker"
                value={ticker}
                onChange={(e) => {
                  setTicker(e.target.value);
                  setShowSearchDropdown(true);
                }}
                onFocus={() => {
                  if (searchResults.length > 0) setShowSearchDropdown(true);
                }}
                className="bg-transparent border-none text-sm font-mono font-bold text-white focus:outline-none w-36 sm:w-48 md:w-60 uppercase placeholder-gray-500"
                placeholder="Search any stock, company, crypto..."
              />
              {isSearching && <Cpu className="h-3.5 w-3.5 text-indigoAccent animate-spin" />}
              <button
                type="submit"
                id="btn-go-symbol"
                className="rounded-lg bg-gradient-to-r from-indigoAccent to-purpleAccent px-3 py-1.5 text-xs font-bold text-white shadow-neon-indigo hover:opacity-90 transition-all shrink-0"
              >
                Search
              </button>
            </form>

            {/* Live Autocomplete Results Dropdown */}
            {showSearchDropdown && searchResults.length > 0 && (
              <div
                className="absolute top-full left-0 right-0 mt-2 z-50 rounded-2xl glass-card border border-indigoAccent/30 p-2 shadow-2xl backdrop-blur-2xl max-h-80 overflow-y-auto min-w-[300px]"
                style={{ background: "rgba(13, 13, 26, 0.96)" }}
              >
                <div className="text-[10px] font-mono text-gray-500 uppercase px-3 py-1 border-b border-darkBorder mb-1 flex justify-between">
                  <span>Global Market Matches</span>
                  <span>{searchResults.length} results</span>
                </div>
                {searchResults.map((item, idx) => (
                  <button
                    key={`${item.symbol}-${idx}`}
                    onClick={() => selectSearchSymbol(item.symbol)}
                    className="w-full text-left flex items-center justify-between p-2.5 rounded-xl hover:bg-indigoAccent/20 transition-all group border border-transparent hover:border-indigoAccent/30"
                  >
                    <div className="truncate mr-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-sm text-indigoLight group-hover:text-white">
                          {item.symbol}
                        </span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigoAccent/20 text-indigoAccent font-mono uppercase">
                          {item.type || "EQUITY"}
                        </span>
                      </div>
                      <div className="text-xs text-gray-400 truncate group-hover:text-gray-200">
                        {item.name}
                      </div>
                    </div>
                    {item.exchange && (
                      <span className="text-[10px] font-mono text-gray-500 bg-darkBorder/60 px-2 py-1 rounded-lg shrink-0">
                        {item.exchange}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Portfolio chip */}
          {activePortfolio && (
            <div className="glass-card flex items-center gap-2.5 px-3.5 py-2 rounded-xl">
              <CreditCard className="h-4 w-4 text-emeraldGreen" />
              <div className="text-xs">
                <span className="text-gray-500 font-semibold">{activePortfolio.name} </span>
                <span className="font-mono font-bold text-white">
                  ${activePortfolio.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          )}

          {/* User chip */}
          {user && (
            <div className="hidden lg:flex glass-card items-center gap-2 px-3 py-2 rounded-xl">
              <div className="h-6 w-6 rounded-full bg-gradient-to-br from-indigoAccent to-purpleAccent flex items-center justify-center text-[10px] font-bold text-white">
                {user.full_name?.[0] ?? "U"}
              </div>
              <span className="text-xs font-semibold text-gray-300">{user.full_name}</span>
            </div>
          )}

          <button
            onClick={fetchUserData}
            id="btn-refresh"
            className="glass-card p-2.5 rounded-xl text-gray-400 hover:text-white transition-all hover:border-indigoAccent/30"
            title="Refresh data"
          >
            <RefreshCw className="h-4 w-4" />
          </button>

          <button
            onClick={() => setShowSettingsModal(true)}
            id="btn-settings"
            className="glass-card p-2.5 rounded-xl text-gray-400 hover:text-white transition-all hover:border-indigoAccent/30"
            title="Configure API Keys"
          >
            <Settings className="h-4 w-4" />
          </button>

          <button
            onClick={logoutUser}
            id="btn-logout"
            className="neon-btn-rose flex items-center gap-1.5 px-3 py-2.5 text-xs rounded-xl"
          >
            <LogOut className="h-3.5 w-3.5" />
            Logout
          </button>
        </div>
      </div>

      {/* ── Popular Stock Shortcut Strip ── */}
      <div className="glass-card p-2.5 rounded-2xl flex items-center gap-2 overflow-x-auto no-scrollbar">
        <span className="text-[10px] font-mono font-bold text-gray-400 uppercase tracking-wider pl-2 shrink-0 flex items-center gap-1">
          <TrendingUp className="h-3.5 w-3.5 text-indigoAccent" /> Watchlist:
        </span>
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          {["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "AMZN", "META", "SPY", "QQQ", "BTC-USD", "ETH-USD"].map((sym) => (
            <button
              key={sym}
              onClick={() => {
                setTicker(sym);
                setSymbol(sym);
              }}
              className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition-all shrink-0 ${
                activeSymbol === sym
                  ? "bg-gradient-to-r from-indigoAccent to-purpleAccent text-white shadow-neon-indigo border border-indigoAccent/50 scale-105"
                  : "bg-darkBorder/40 text-gray-400 hover:text-white hover:bg-darkBorder border border-transparent"
              }`}
            >
              {sym}
            </button>
          ))}
        </div>
      </div>

      {/* ── Portfolio Stats Row ── */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {/* Stat Card 1: Balance */}
        <div className="stat-card group">
          <div className="flex items-center justify-between">
            <div className="section-label">Portfolio Balance</div>
            <span className="text-[9px] font-mono font-bold text-emeraldGreen bg-emeraldGreen/10 border border-emeraldGreen/30 px-1.5 py-0.5 rounded-md">
              +11.8% All-Time
            </span>
          </div>
          <div className="font-mono text-2xl font-black text-white mt-1">
            ${activePortfolio ? activePortfolio.balance.toLocaleString(undefined, { maximumFractionDigits: 0 }) : "—"}
          </div>
          <div className="flex items-center justify-between mt-2 pt-1 border-t border-darkBorder/40">
            <div className="flex items-center gap-1 text-[10px] text-gray-400 font-mono">
              <Activity className="h-3 w-3 text-indigoAccent" />
              Paper Cash Balance
            </div>
            {/* Sparkline SVG */}
            <svg className="w-16 h-5 stroke-indigoLight fill-none" viewBox="0 0 60 20">
              <path d="M0 15 Q 15 18, 30 10 T 60 4" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
        </div>

        {/* Stat Card 2: Open Positions */}
        <div className="stat-card group">
          <div className="flex items-center justify-between">
            <div className="section-label">Open Positions</div>
            <span className="text-[9px] font-mono font-bold text-cyanAccent bg-cyanAccent/10 border border-cyanAccent/30 px-1.5 py-0.5 rounded-md">
              {openPositions.length} Active Trades
            </span>
          </div>
          <div className="font-mono text-2xl font-black text-white mt-1">
            {openPositions.length} <span className="text-xs font-normal text-gray-400">Assets</span>
          </div>
          <div className="flex items-center justify-between mt-2 pt-1 border-t border-darkBorder/40">
            <div className="flex items-center gap-1 text-[10px] text-gray-400 font-mono">
              <BarChart2 className="h-3 w-3 text-cyanAccent" />
              Allocated Exposure
            </div>
            {/* Sparkline SVG */}
            <svg className="w-16 h-5 stroke-cyanAccent fill-none" viewBox="0 0 60 20">
              <path d="M0 18 Q 15 8, 30 14 T 60 6" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
        </div>

        {/* Stat Card 3: Unrealized PnL */}
        <div className="stat-card group">
          <div className="flex items-center justify-between">
            <div className="section-label">Unrealized PnL</div>
            <span className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded-md border ${
              totalPnl >= 0
                ? "bg-emeraldGreen/10 text-emeraldGreen border-emeraldGreen/30"
                : "bg-roseRed/10 text-roseRed border-roseRed/30"
            }`}>
              {totalPnl >= 0 ? "+11.79%" : "-2.10%"} Return
            </span>
          </div>
          <div className={`font-mono text-2xl font-black mt-1 ${totalPnl >= 0 ? "text-emeraldGreen" : "text-roseRed"}`}>
            {totalPnl >= 0 ? "+" : ""}${totalPnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className="flex items-center justify-between mt-2 pt-1 border-t border-darkBorder/40">
            <div className="flex items-center gap-1 text-[10px] text-gray-400 font-mono">
              {totalPnl >= 0 ? <ArrowUpRight className="h-3 w-3 text-emeraldGreen" /> : <ArrowDownRight className="h-3 w-3 text-roseRed" />}
              Live Portfolio Yield
            </div>
            {/* Sparkline SVG */}
            <svg className={`w-16 h-5 fill-none ${totalPnl >= 0 ? "stroke-emeraldGreen" : "stroke-roseRed"}`} viewBox="0 0 60 20">
              <path d="M0 16 Q 15 12, 30 6 T 60 2" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
        </div>

        {/* Stat Card 4: Risk Enforcer */}
        <div className="stat-card group">
          <div className="flex items-center justify-between">
            <div className="section-label">Risk Protocol</div>
            <span className="text-[9px] font-mono font-bold text-goldAccent bg-goldAccent/10 border border-goldAccent/30 px-1.5 py-0.5 rounded-md">
              Enforced Active
            </span>
          </div>
          <div className="font-mono text-2xl font-black text-white mt-1">
            {user?.risk_limit_pct ?? 2}% <span className="text-xs font-normal text-gray-400">/ Trade Max</span>
          </div>
          <div className="flex items-center justify-between mt-2 pt-1 border-t border-darkBorder/40">
            <div className="flex items-center gap-1 text-[10px] text-gray-400 font-mono">
              <Shield className="h-3 w-3 text-goldAccent" />
              Capital Preservation
            </div>
            {/* Sparkline SVG */}
            <svg className="w-16 h-5 stroke-goldAccent fill-none" viewBox="0 0 60 20">
              <path d="M0 10 Q 20 14, 40 8 T 60 10" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
        </div>
      </div>

      {/* ── Main Grid: Chart + Order Panel ── */}
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-4">
        {/* Chart */}
        <div className="xl:col-span-3 relative">
          {isMarketLoading && ohlcvData.length === 0 ? (
            <div className="glass-card flex h-[500px] items-center justify-center gap-3">
              <div className="relative">
                <Cpu className="h-8 w-8 text-indigoAccent animate-spin" />
                <div className="absolute inset-0 rounded-full bg-indigoAccent/20 blur-md animate-pulse" />
              </div>
              <div>
                <div className="text-sm font-bold text-white">Fetching Market Data</div>
                <div className="text-xs text-gray-500 font-mono">{activeSymbol} · 60d · 1D</div>
              </div>
            </div>
          ) : (
            <div className="relative">
              {isMarketLoading && (
                <div className="absolute top-3 right-3 z-20 flex items-center gap-2 bg-darkCard/80 backdrop-blur-md px-3 py-1.5 rounded-lg border border-indigoAccent/30 text-xs font-mono text-indigoLight shadow-lg">
                  <Cpu className="h-3.5 w-3.5 text-indigoAccent animate-spin" />
                  Updating...
                </div>
              )}
              <TradingViewChart
                data={ohlcvData}
                symbol={activeSymbol}
                selectedPeriod={selectedPeriod}
                onPeriodChange={(period, defaultInterval) => {
                  setSelectedPeriod(period);
                  setSelectedInterval(defaultInterval);
                }}
                selectedInterval={selectedInterval}
                onIntervalChange={(interval) => {
                  setSelectedInterval(interval);
                }}
              />
            </div>
          )}
        </div>

        {/* Order Execution Panel */}
        <div className="glass-card p-5 xl:col-span-1 flex flex-col gap-5">
          {/* Header */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="section-label">Order Execution</span>
              <div className="flex items-center gap-1 text-[10px] font-mono text-emeraldGreen">
                <Zap className="h-3 w-3" />
                Paper
              </div>
            </div>
            <div className="h-px bg-gradient-to-r from-indigoAccent/30 via-cyanAccent/20 to-transparent" />
          </div>

          {/* Order Message */}
          {orderMessage && (
            <div className={`flex items-start gap-2 rounded-xl p-3 text-xs animate-slide-up ${
              orderMessageType === "success"
                ? "bg-emeraldGreen/10 border border-emeraldGreen/20 text-emeraldGreen"
                : "bg-roseRed/10 border border-roseRed/20 text-roseRed"
            }`}>
              {orderMessageType === "success" ? (
                <CheckCircle2 className="h-3.5 w-3.5 mt-0.5 shrink-0" />
              ) : (
                <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
              )}
              {orderMessage}
            </div>
          )}

          <form onSubmit={handlePlaceOrder} className="space-y-4 flex-1">
            {/* Direction Toggle */}
            <div>
              <label className="section-label mb-2 block">Direction</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  id="btn-buy"
                  onClick={() => setOrderAction("buy")}
                  className={`flex items-center justify-center gap-1.5 rounded-xl py-2.5 text-xs font-bold transition-all duration-200 ${
                    orderAction === "buy"
                      ? "bg-emeraldGreen text-darkBg shadow-neon-emerald"
                      : "bg-darkBg border border-darkBorder text-gray-500 hover:border-emeraldGreen/30 hover:text-emeraldGreen"
                  }`}
                >
                  <TrendingUp className="h-3.5 w-3.5" />
                  Buy
                </button>
                <button
                  type="button"
                  id="btn-sell"
                  onClick={() => setOrderAction("sell")}
                  className={`flex items-center justify-center gap-1.5 rounded-xl py-2.5 text-xs font-bold transition-all duration-200 ${
                    orderAction === "sell"
                      ? "bg-roseRed text-white shadow-neon-rose"
                      : "bg-darkBg border border-darkBorder text-gray-500 hover:border-roseRed/30 hover:text-roseRed"
                  }`}
                >
                  <TrendingDown className="h-3.5 w-3.5" />
                  Sell
                </button>
              </div>
            </div>

            {/* Instrument */}
            <div>
              <label className="section-label mb-1.5 block">Instrument</label>
              <div className="terminal-input py-2.5 px-3.5 font-mono font-bold text-sm text-indigoLight flex items-center gap-2">
                <BarChart2 className="h-3.5 w-3.5 text-indigoAccent" />
                {activeSymbol}
              </div>
            </div>

            {/* Quantity */}
            <div>
              <label className="section-label mb-1.5 block">Quantity (Shares)</label>
              <input
                id="input-quantity"
                type="number"
                value={orderQty}
                onChange={(e) => setOrderQty(e.target.value)}
                className="terminal-input py-2.5 px-3.5 font-mono"
                required
                min="1"
              />
            </div>

            {/* Stop Loss / Take Profit */}
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="section-label mb-1.5 block text-roseRed/80">Stop Loss</label>
                <input
                  id="input-stop-loss"
                  type="number"
                  step="0.01"
                  value={stopLossVal}
                  onChange={(e) => setStopLossVal(e.target.value)}
                  className="terminal-input py-2 px-3 font-mono text-xs"
                  placeholder="Price"
                />
              </div>
              <div>
                <label className="section-label mb-1.5 block text-emeraldGreen/80">Take Profit</label>
                <input
                  id="input-take-profit"
                  type="number"
                  step="0.01"
                  value={takeProfitVal}
                  onChange={(e) => setTakeProfitVal(e.target.value)}
                  className="terminal-input py-2 px-3 font-mono text-xs"
                  placeholder="Price"
                />
              </div>
            </div>

            <button
              type="submit"
              id="btn-execute-order"
              className={`w-full py-3 text-sm font-bold rounded-xl flex items-center justify-center gap-2 transition-all duration-200 ${
                orderAction === "buy" ? "neon-btn-emerald text-darkBg" : "bg-roseRed text-white hover:bg-roseRedDark shadow-neon-rose"
              }`}
            >
              <Zap className="h-4 w-4" />
              Execute {orderAction === "buy" ? "Buy" : "Sell"} Order
            </button>
          </form>

          {/* Risk footer */}
          <div className="pt-3 border-t border-darkBorder">
            <div className="flex items-center justify-between text-[10px]">
              <span className="flex items-center gap-1 text-gray-600">
                <Shield className="h-3 w-3 text-goldAccent" />
                Risk enforced
              </span>
              <span className="font-mono font-bold text-goldAccent">{user?.risk_limit_pct ?? 2}% / trade</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── AI Agent Console ── */}
      <MultiAgentConsole
        onAnalyze={runAgentConsensus}
        isLoading={isAnalyzing}
        analysisReport={report}
        symbol={activeSymbol}
        onApplyTradePlan={(plan) => {
          if (plan.stopLoss) {
            const num = plan.stopLoss.replace(/[^0-9.]/g, "");
            if (num) setStopLossVal(num);
          }
          if (plan.takeProfit) {
            const num = plan.takeProfit.replace(/[^0-9.]/g, "");
            if (num) setTakeProfitVal(num);
          }
        }}
      />

      {/* ── Positions Table ── */}
      {activePortfolio && (
        <div className="glass-card p-5 animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <div>
              <span className="section-label block mb-1">Portfolio Positions</span>
              <h3 className="text-base font-bold text-white">
                Open Trades
                <span className="ml-2 text-xs font-mono text-gray-600">({openPositions.length} active)</span>
              </h3>
            </div>
            {openPositions.length > 0 && (
              <div className={`flex items-center gap-1.5 text-sm font-mono font-black ${totalPnl >= 0 ? "text-emeraldGreen" : "text-roseRed"}`}>
                {totalPnl >= 0 ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}
                ${Math.abs(totalPnl).toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </div>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="data-table w-full text-left">
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Side</th>
                  <th className="text-right">Qty</th>
                  <th className="text-right">Entry</th>
                  <th className="text-right">Current</th>
                  <th className="text-right">Stop</th>
                  <th className="text-right">Target</th>
                  <th className="text-right">Unrealized PnL</th>
                  <th className="text-center">Action</th>
                </tr>
              </thead>
              <tbody>
                {openPositions.length > 0 ? (
                  openPositions.map((pos: any) => (
                    <tr key={pos.id}>
                      <td className="font-mono font-bold text-white uppercase">{pos.ticker}</td>
                      <td>
                        <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase ${
                          pos.side === "long"
                            ? "bg-emeraldGreen/10 border border-emeraldGreen/20 text-emeraldGreen"
                            : "bg-roseRed/10 border border-roseRed/20 text-roseRed"
                        }`}>
                          {pos.side === "long" ? <TrendingUp className="h-2.5 w-2.5" /> : <TrendingDown className="h-2.5 w-2.5" />}
                          {pos.side}
                        </span>
                      </td>
                      <td className="text-right font-mono text-gray-300">{pos.quantity}</td>
                      <td className="text-right font-mono text-gray-300">${pos.entry_price.toLocaleString()}</td>
                      <td className="text-right font-mono text-white font-semibold">${pos.current_price.toLocaleString()}</td>
                      <td className="text-right font-mono text-roseRed text-xs">
                        {pos.stop_loss ? `$${pos.stop_loss.toLocaleString()}` : "—"}
                      </td>
                      <td className="text-right font-mono text-emeraldGreen text-xs">
                        {pos.take_profit ? `$${pos.take_profit.toLocaleString()}` : "—"}
                      </td>
                      <td className={`text-right font-mono font-bold ${pos.pnl >= 0 ? "text-emeraldGreen" : "text-roseRed"}`}>
                        {pos.pnl >= 0 ? "+" : ""}${pos.pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </td>
                      <td className="text-center">
                        <button
                          type="button"
                          onClick={() => handleClosePosition(pos)}
                          className="px-2.5 py-1 text-[11px] font-bold rounded-lg bg-roseRed/20 text-roseRed border border-roseRed/30 hover:bg-roseRed hover:text-white transition-all shadow-sm"
                          title="Close / Sell position"
                        >
                          Close / Sell
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={9} className="py-10 text-center">
                      <div className="flex flex-col items-center gap-2">
                        <BarChart2 className="h-8 w-8 text-darkBorder2" />
                        <p className="text-sm font-semibold text-gray-600">No open positions</p>
                        <p className="text-xs text-gray-700">Execute a Buy or Sell order above to start trading</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {/* API Settings Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md animate-fade-in">
          <div className="glass-card max-w-md w-full p-6 mx-4 relative overflow-hidden border border-indigoAccent/30 shadow-2xl flex flex-col gap-4 animate-scale-in" style={{ background: "rgba(13, 13, 26, 0.95)" }}>
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold text-indigoLight tracking-wide flex items-center gap-2">
                  <Settings className="h-4 w-4 text-indigoAccent" />
                  API Settings Configuration
                </span>
                <button
                  type="button"
                  onClick={() => setShowSettingsModal(false)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <div className="h-px bg-gradient-to-r from-indigoAccent/40 via-cyanAccent/20 to-transparent" />
            </div>

            <p className="text-xs text-gray-400">
              Configure your API keys for institutional AI market analysis. The application works completely offline using fallback heuristics if keys are unconfigured.
            </p>

            <form onSubmit={handleSaveSettings} className="space-y-4">
              <div>
                <label className="section-label mb-2 block">OpenAI API Key</label>
                <input
                  type="password"
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  className="w-full bg-darkBg/60 border border-darkBorder hover:border-indigoAccent/30 focus:border-indigoAccent rounded-xl px-4 py-2.5 text-xs text-white placeholder-gray-500 font-mono transition-all focus:outline-none"
                  placeholder="sk-or-your-openai-api-key..."
                />
              </div>

              <div>
                <label className="section-label mb-2 block">Gemini API Key</label>
                <input
                  type="password"
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  className="w-full bg-darkBg/60 border border-darkBorder hover:border-indigoAccent/30 focus:border-indigoAccent rounded-xl px-4 py-2.5 text-xs text-white placeholder-gray-500 font-mono transition-all focus:outline-none"
                  placeholder="AIzaSy...your-gemini-api-key..."
                />
              </div>

              <div className="flex items-center gap-2 pt-2 justify-end">
                <button
                  type="button"
                  onClick={() => setShowSettingsModal(false)}
                  className="glass-card px-4 py-2 text-xs font-semibold text-gray-400 hover:text-white transition-all hover:bg-darkBorder/20"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingSettings}
                  className="neon-btn-indigo px-4 py-2 text-xs rounded-xl flex items-center gap-2"
                >
                  {savingSettings ? <Cpu className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                  {savingSettings ? "Saving..." : "Save Configuration"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
