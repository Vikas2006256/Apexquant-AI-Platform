import type { Metadata } from "next";
import "./globals.css";
import React from "react";

import { ApexQuantLogo } from "@/components/ApexQuantLogo";

export const metadata: Metadata = {
  title: "ApexQuant AI | Institutional Trading Intelligence",
  description: "Institutional-grade AI Trading Research, Multi-Agent Consensus Engine, Risk Management and Real-Time Decision Support.",
  keywords: "quantitative trading, AI trading, institutional terminal, algo trading, market analysis",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Outfit:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-darkBg text-gray-100 min-h-screen flex flex-col font-sans">
        {/* Animated Glassmorphism Background Layer */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden z-0" aria-hidden="true">
          <div className="absolute inset-0 bg-grid opacity-100" />
          <div className="glass-orb-1 absolute -top-20 left-1/4 w-[700px] h-[700px] rounded-full opacity-[0.12] bg-gradient-to-br from-indigoAccent via-purpleAccent to-transparent blur-[140px]" />
          <div className="glass-orb-2 absolute -bottom-20 right-1/4 w-[650px] h-[650px] rounded-full opacity-[0.10] bg-gradient-to-tr from-cyanAccent via-emeraldGreen to-transparent blur-[140px]" />
          <div className="absolute top-1/3 -left-20 w-[450px] h-[450px] rounded-full opacity-[0.08] bg-gradient-to-r from-goldAccent to-roseRed blur-[120px]" />
        </div>

        {/* Main Header */}
        <header className="sticky top-0 z-50 flex items-center justify-between border-b border-darkBorder/60 bg-darkBg/80 backdrop-blur-xl px-4 sm:px-6 lg:px-8 py-3">
          {/* Brand */}
          <ApexQuantLogo size="md" />

          {/* Navigation */}
          <nav className="flex items-center space-x-1">
            <a
              href="/"
              id="nav-terminal"
              className="flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold text-white transition-all duration-200"
              style={{ background: 'linear-gradient(135deg, rgba(108,99,255,0.2) 0%, rgba(0,212,255,0.08) 100%)', border: '1px solid rgba(108,99,255,0.2)' }}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Terminal
            </a>
            <a
              href="/backtest"
              id="nav-backtest"
              className="flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold text-gray-400 hover:text-white transition-all duration-200 hover:bg-darkCard2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Strategy Sandbox
            </a>
          </nav>

          {/* Right side status */}
          <div className="flex items-center gap-3">
            <div className="badge-live">LIVE</div>
            <div className="hidden md:flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-mono" style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.06)' }}>
              <span className="text-gray-500">Markets</span>
              <span className="text-emeraldGreen font-bold">OPEN</span>
            </div>
          </div>
        </header>

        {/* Dashboard Area */}
        <main className="relative flex-1 w-full max-w-[1600px] mx-auto p-4 md:p-6 animate-fade-in">
          {children}
        </main>

        {/* Footer */}
        <footer className="relative border-t border-darkBorder/40 bg-darkBg/60 backdrop-blur-sm px-6 py-3">
          <div className="max-w-[1600px] mx-auto flex items-center justify-between">
            <p className="text-[10px] font-mono text-gray-600">
              ApexQuant AI Platform v2.0 — Institutional Decision Support Engine
            </p>
            <p className="text-[10px] text-gray-600">
              ⚠ Probabilistic signals only. Not financial advice. Capital preservation is priority #1.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
