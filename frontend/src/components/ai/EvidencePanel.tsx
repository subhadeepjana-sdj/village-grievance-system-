import React from 'react';
import { Database, ExternalLink, FileText } from 'lucide-react';
import { EvidenceItem } from '../../types';

interface EvidencePanelProps {
  evidences: EvidenceItem[];
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidences }) => {
  if (!evidences || evidences.length === 0) {
    return (
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 italic">
        No evidence retrieved from Qdrant vector database or PostgreSQL.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
        <Database className="w-4 h-4 text-emerald-400" /> Retrieved Evidence Chunks ({evidences.length})
      </h4>

      <div className="space-y-2">
        {evidences.map((item, idx) => (
          <div key={idx} className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs space-y-1.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-bold text-emerald-400 flex items-center gap-1">
                <FileText className="w-3.5 h-3.5" /> Source: {item.source_type || 'Knowledge Base'}
              </span>
              {item.similarity_score !== undefined && (
                <span className="bg-slate-800 px-2 py-0.5 rounded font-mono text-slate-300 text-[10px]">
                  Relevance Score: {item.similarity_score}
                </span>
              )}
            </div>

            <p className="text-slate-200 text-xs leading-relaxed font-sans bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
              {item.evidence_text}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EvidencePanel;
