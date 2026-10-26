import React from "react";

interface ApexQuantLogoProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function ApexQuantLogo({ size = "md", className = "" }: ApexQuantLogoProps) {
  const iconSize = size === "sm" ? "w-6 h-6" : size === "lg" ? "w-10 h-10" : "w-8 h-8";
  const titleSize = size === "sm" ? "text-base" : size === "lg" ? "text-2xl" : "text-xl";
  const subSize = size === "sm" ? "text-[9px]" : "text-[10px]";

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <div className={`relative ${iconSize} flex items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-purple-600 to-cyan-400 p-[1.5px] shadow-lg shadow-indigo-500/25`}>
        <div className="w-full h-full bg-[#0d1117] rounded-[10px] flex items-center justify-center">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            className="w-3/5 h-3/5 text-cyan-400"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12 2L2 19.5H22L12 2Z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M12 9V14"
              stroke="#6366f1"
              strokeWidth="2"
              strokeLinecap="round"
            />
            <circle cx="12" cy="17" r="1" fill="#10b981" />
          </svg>
        </div>
      </div>
      <div>
        <div className={`font-outfit font-extrabold tracking-tight ${titleSize} bg-gradient-to-r from-white via-gray-100 to-gray-400 bg-clip-text text-transparent flex items-center gap-1.5`}>
          <span>ApexQuant</span>
          <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 font-mono font-medium">AI</span>
        </div>
        <p className={`font-mono text-gray-500 font-medium tracking-wider uppercase ${subSize}`}>
          Institutional Engine
        </p>
      </div>
    </div>
  );
}
