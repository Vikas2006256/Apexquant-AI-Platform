import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: "#070711",
        darkCard: "#0d0d1a",
        darkCard2: "#111128",
        darkBorder: "#1e1e3a",
        darkBorder2: "#252545",
        emeraldGreen: "#00d68f",
        emeraldGreenDark: "#00b377",
        roseRed: "#ff3366",
        roseRedDark: "#cc0044",
        indigoAccent: "#6c63ff",
        indigoLight: "#8b83ff",
        indigoDark: "#4a42d4",
        cyanAccent: "#00d4ff",
        goldAccent: "#f5a623",
        purpleAccent: "#a855f7",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        display: ["Outfit", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "grid-pattern":
          "linear-gradient(rgba(108,99,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(108,99,255,0.03) 1px, transparent 1px)",
        "glow-indigo": "radial-gradient(circle at 50% 50%, rgba(108,99,255,0.15) 0%, transparent 70%)",
        "glow-emerald": "radial-gradient(circle at 50% 50%, rgba(0,214,143,0.12) 0%, transparent 70%)",
        "glow-cyan": "radial-gradient(circle at 50% 50%, rgba(0,212,255,0.1) 0%, transparent 70%)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
        "slide-up": "slideUp 0.3s ease-out",
        "fade-in": "fadeIn 0.4s ease-out",
        "shimmer": "shimmer 2s infinite",
        "float": "float 3s ease-in-out infinite",
        "scan": "scan 2s linear infinite",
      },
      keyframes: {
        glow: {
          "0%": { boxShadow: "0 0 5px rgba(108,99,255,0.3), 0 0 10px rgba(108,99,255,0.1)" },
          "100%": { boxShadow: "0 0 20px rgba(108,99,255,0.6), 0 0 40px rgba(108,99,255,0.2)" },
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" },
        },
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100vh)" },
        },
      },
      boxShadow: {
        "neon-indigo": "0 0 20px rgba(108,99,255,0.4), 0 0 60px rgba(108,99,255,0.1)",
        "neon-emerald": "0 0 20px rgba(0,214,143,0.3), 0 0 60px rgba(0,214,143,0.08)",
        "neon-rose": "0 0 20px rgba(255,51,102,0.3), 0 0 60px rgba(255,51,102,0.08)",
        "neon-cyan": "0 0 20px rgba(0,212,255,0.3), 0 0 60px rgba(0,212,255,0.08)",
        "card": "0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)",
        "card-hover": "0 8px 40px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.06)",
        "inner-glow": "inset 0 1px 0 rgba(255,255,255,0.05), inset 0 -1px 0 rgba(0,0,0,0.2)",
      },
      backdropBlur: {
        xs: "2px",
      },
    },
  },
  plugins: [],
};
export default config;
