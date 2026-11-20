import React from 'react';

export const GeoCivicLogo = ({ className = "w-10 h-10" }) => {
  return (
    <svg 
      viewBox="0 0 64 64" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <radialGradient id="geoGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.8" />
          <stop offset="60%" stopColor="#00A3E0" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#0047BA" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="pinGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#38BDF8" />
          <stop offset="50%" stopColor="#00A3E0" />
          <stop offset="100%" stopColor="#0047BA" />
        </linearGradient>
        <linearGradient id="goldRing" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FCD34D" />
          <stop offset="100%" stopColor="#F59E0B" />
        </linearGradient>
        <filter id="glowEffect" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      {/* Outer ambient glow */}
      <circle cx="32" cy="28" r="24" fill="url(#geoGlow)" />

      {/* Orbital Gold/Cyan rings */}
      <ellipse cx="32" cy="28" rx="20" ry="8" stroke="url(#goldRing)" strokeWidth="1.2" transform="rotate(-20 32 28)" opacity="0.75" />
      <ellipse cx="32" cy="28" rx="19" ry="7" stroke="#38BDF8" strokeWidth="0.8" strokeDasharray="3 2" transform="rotate(25 32 28)" opacity="0.8" />

      {/* Geo Pin Body */}
      <path
        d="M32 50 C32 50 46 36 46 25 C46 16.5 39.5 10 32 10 C24.5 10 18 16.5 18 25 C18 36 32 50 32 50 Z"
        fill="url(#pinGradient)"
        stroke="#7DD3FC"
        strokeWidth="1.5"
        filter="url(#glowEffect)"
        opacity="0.95"
      />

      {/* Globe Inside Pin */}
      <circle cx="32" cy="25" r="9" fill="#002A72" stroke="#38BDF8" strokeWidth="1" />
      
      {/* Globe Grid lines */}
      <line x1="23" y1="25" x2="41" y2="25" stroke="#7DD3FC" strokeWidth="0.8" opacity="0.8" />
      <line x1="32" y1="16" x2="32" y2="34" stroke="#7DD3FC" strokeWidth="0.8" opacity="0.8" />
      <ellipse cx="32" cy="25" rx="5" ry="8.8" stroke="#7DD3FC" strokeWidth="0.8" opacity="0.85" />
      <path d="M25 20 C28 22 36 22 39 20" stroke="#7DD3FC" strokeWidth="0.7" opacity="0.7" fill="none" />
      <path d="M25 30 C28 28 36 28 39 30" stroke="#7DD3FC" strokeWidth="0.7" opacity="0.7" fill="none" />

      {/* Pin point pulse ripple */}
      <ellipse cx="32" cy="51" rx="6" ry="2" fill="#38BDF8" opacity="0.6" />
      <circle cx="32" cy="50" r="1.5" fill="#FFFFFF" />

      {/* Golden accent spark */}
      <circle cx="42" cy="18" r="1.5" fill="#FCD34D" filter="url(#glowEffect)" />
      <circle cx="21" cy="32" r="1" fill="#38BDF8" />
    </svg>
  );
};

export default GeoCivicLogo;
