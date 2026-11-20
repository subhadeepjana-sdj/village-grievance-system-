import React from 'react';
import { ShieldCheck, AlertTriangle, HelpCircle } from 'lucide-react';

const EvidenceBadge = ({ status, confidence, onClick }) => {
  const norm = status ? status.toUpperCase() : 'SUPPORTED';

  if (norm === 'SUPPORTED' || norm === 'SHOW') {
    return (
      <button 
        type="button"
        onClick={onClick}
        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0] hover:bg-[#D1FAE5] transition cursor-pointer"
        title="Verified by Evidence"
      >
        <ShieldCheck className="w-3.5 h-3.5 text-[#065F46]" />
        <span>Evidence Grounded</span>
        {confidence ? <span className="bg-[#A7F3D0] px-1.5 py-0.2 rounded text-[10px] ml-1 font-mono">{confidence}%</span> : null}
      </button>
    );
  }

  if (norm === 'CONTRADICTED' || norm === 'CORRECT') {
    return (
      <button 
        type="button"
        onClick={onClick}
        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA] hover:bg-[#FEE2E2] transition cursor-pointer"
        title="Contradiction Caught and Corrected"
      >
        <AlertTriangle className="w-3.5 h-3.5 text-[#991B1B]" />
        <span>Contradiction Corrected</span>
      </button>
    );
  }

  return (
    <button 
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#F1F5F9] text-[#334155] border border-[#CBD5E1] hover:bg-[#E2E8F0] transition cursor-pointer"
      title="Insufficient Verified Evidence"
    >
      <HelpCircle className="w-3.5 h-3.5 text-[#334155]" />
      <span>Insufficient Evidence (Abstained)</span>
    </button>
  );
};

export default EvidenceBadge;
