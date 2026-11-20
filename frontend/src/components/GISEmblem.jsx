import React from 'react';

export const GISEmblem = ({ className = 'w-10 h-10', size = 40 }) => {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 100 100" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Tamil Nadu State Grievance Redressal Emblem"
    >
      {/* Outer circular medallion */}
      <circle cx="50" cy="50" r="48" fill="#F8FAFC" stroke="#FFD700" strokeWidth="3" />
      <circle cx="50" cy="50" r="43" fill="#0047BA" />
      
      {/* Decorative floral garland ring */}
      <circle cx="50" cy="50" r="40" stroke="#FFD700" strokeWidth="1.5" strokeDasharray="3 3" />
      
      {/* Historic Temple Gopuram (Tamil Nadu State Symbol) */}
      <path 
        d="M50 16 L53 23 L47 23 Z" 
        fill="#FFD700" 
      />
      <rect x="44" y="23" width="12" height="4" fill="#FFD700" rx="1" />
      
      {/* Gopuram Tiers */}
      <path 
        d="M42 27 L58 27 L56 34 L44 34 Z" 
        fill="#FFE885" 
      />
      <path 
        d="M39 34 L61 34 L59 42 L41 42 Z" 
        fill="#FFD700" 
      />
      <path 
        d="M36 42 L64 42 L62 51 L38 51 Z" 
        fill="#FFE885" 
      />
      <path 
        d="M33 51 L67 51 L65 61 L35 61 Z" 
        fill="#FFD700" 
      />
      
      {/* Gopuram arched entrance */}
      <path 
        d="M44 61 L44 54 Q50 51 56 54 L56 61 Z" 
        fill="#002D75" 
      />
      
      {/* Pillar details */}
      <line x1="48" y1="36" x2="48" y2="40" stroke="#00368C" strokeWidth="1.5" />
      <line x1="52" y1="36" x2="52" y2="40" stroke="#00368C" strokeWidth="1.5" />
      <line x1="46" y1="44" x2="46" y2="49" stroke="#00368C" strokeWidth="1.5" />
      <line x1="54" y1="44" x2="54" y2="49" stroke="#00368C" strokeWidth="1.5" />
      
      {/* Base Pedestal with State Laurel Leaves */}
      <path 
        d="M26 62 Q50 66 74 62 L71 67 Q50 71 29 67 Z" 
        fill="#FFD700" 
      />
      <path 
        d="M24 70 C34 76, 66 76, 76 70 C68 82, 32 82, 24 70 Z" 
        fill="#002661" 
      />
      
      {/* Three Golden Ashoka Lions Silhouette Representation */}
      <circle cx="50" cy="74" r="3" fill="#FFD700" />
      <circle cx="43" cy="74.5" r="2.5" fill="#FFD700" />
      <circle cx="57" cy="74.5" r="2.5" fill="#FFD700" />

      {/* Ribbon Banner at bottom */}
      <path 
        d="M32 82 Q50 86 68 82 L70 86 Q50 90 30 86 Z" 
        fill="#FFD700" 
      />
    </svg>
  );
};

export default GISEmblem;
