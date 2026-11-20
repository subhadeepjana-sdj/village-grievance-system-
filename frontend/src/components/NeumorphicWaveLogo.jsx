import React from 'react';

/**
 * 3D Layered Glass Flame / Wave Emblem
 * Exact match to the reference image logo
 */
const NeumorphicWaveLogo = ({ className = 'w-16 h-16', size = 64 }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={{ filter: 'drop-shadow(0px 8px 14px rgba(29, 78, 216, 0.38))' }}
    >
      <defs>
        {/* Top Frosted White/Ice-Blue Flame */}
        <linearGradient id="topFlameGrad" x1="20%" y1="0%" x2="80%" y2="100%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.98" />
          <stop offset="45%" stopColor="#f0f7ff" stopOpacity="0.92" />
          <stop offset="100%" stopColor="#b9d6fe" stopOpacity="0.82" />
        </linearGradient>

        {/* Middle Royal Blue Flame */}
        <linearGradient id="midFlameGrad" x1="0%" y1="10%" x2="100%" y2="90%">
          <stop offset="0%" stopColor="#60a5fa" />
          <stop offset="35%" stopColor="#3b82f6" />
          <stop offset="100%" stopColor="#1d4ed8" />
        </linearGradient>

        {/* Bottom Sapphire Electric Blue Flame */}
        <linearGradient id="botFlameGrad" x1="0%" y1="0%" x2="90%" y2="100%">
          <stop offset="0%" stopColor="#38bdf8" />
          <stop offset="25%" stopColor="#2563eb" />
          <stop offset="80%" stopColor="#1e40af" />
          <stop offset="100%" stopColor="#172554" />
        </linearGradient>

        {/* Gloss Sheen Reflection */}
        <linearGradient id="glossSheen" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.8" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>

        {/* Inner Soft Shadow Filter */}
        <filter id="flameShadow" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="4" stdDeviation="4" floodColor="#0f172a" floodOpacity="0.25" />
        </filter>
      </defs>

      {/* ─── 1. Top Translucent Frosted Wave / Flame ─── */}
      <path
        d="M52 14 C56 12, 60 18, 62 25 C66 33, 68 40, 62 47 C57 53, 50 51, 47 45 C43 37, 46 22, 52 14 Z"
        fill="url(#topFlameGrad)"
        style={{ backdropFilter: 'blur(4px)' }}
      />
      {/* Top Flame Highlight Sheen */}
      <path
        d="M52 16 C55 18, 58 24, 59 31 C57 33, 53 28, 51 22 Z"
        fill="url(#glossSheen)"
      />

      {/* ─── 2. Middle Vivid Azure Flame Swoosh ─── */}
      <path
        d="M44 31 C49 28, 56 34, 58 43 C61 54, 56 65, 48 69 C41 73, 35 68, 37 59 C38 49, 40 37, 44 31 Z"
        fill="url(#midFlameGrad)"
        filter="url(#flameShadow)"
      />
      {/* Middle Crest Highlight */}
      <path
        d="M44 34 C47 36, 52 43, 53 50 C51 52, 47 46, 44 40 Z"
        fill="#93c5fd"
        opacity="0.6"
      />

      {/* ─── 3. Bottom Sapphire Curved Swoosh Ribbon ─── */}
      <path
        d="M34 49 C39 46, 46 51, 48 60 C51 72, 44 82, 36 84 C28 86, 23 79, 25 70 C27 59, 29 53, 34 49 Z"
        fill="url(#botFlameGrad)"
        filter="url(#flameShadow)"
      />
      {/* Bottom Glow Sheen */}
      <path
        d="M34 52 C37 54, 42 61, 43 68 C40 70, 36 64, 34 58 Z"
        fill="#60a5fa"
        opacity="0.75"
      />

      {/* ─── 4. Sleek Connecting Right Crest ─── */}
      <path
        d="M48 68 C52 64, 57 60, 56 55 C54 52, 49 55, 46 60 Z"
        fill="#3b82f6"
        opacity="0.9"
      />
    </svg>
  );
};

export default NeumorphicWaveLogo;
