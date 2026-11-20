import React from 'react';
import { X, ShieldCheck, Database, FileText, CheckCircle2, AlertTriangle, HelpCircle } from 'lucide-react';

const EvidenceModal = ({ isOpen, onClose, evidences = [], verificationResults = [], confidence = 0 }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#17221F]/70 backdrop-blur-sm animate-civic-fade">
      <div className="relative w-full max-w-3xl max-h-[88vh] overflow-y-auto bg-[#FFFFFF] rounded-2xl border border-[#E5E7DF] shadow-2xl p-6 text-[#17221F]">
        
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-[#E5E7DF]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#EFF5EF] text-[#153D32] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-[#153D32]" />
            </div>
            <div>
              <h3 className="text-base font-heading font-extrabold text-[#17221F]">
                Evidence Verification & Grounding Trace
              </h3>
              <span className="text-xs text-[#69736D]">
                Natural Language Inference (NLI) & Multi-Source Audit
              </span>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#69736D] hover:text-[#17221F] hover:bg-[#F7F6F0] transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Confidence Metric Card */}
        <div className="my-4 p-4 rounded-xl bg-[#F7F6F0] border border-[#E5E7DF] flex items-center justify-between">
          <div>
            <span className="text-[11px] uppercase tracking-wider font-bold text-[#69736D] block">
              Faithfulness Entailment Score
            </span>
            <div className="text-2xl font-extrabold font-mono text-[#065F46] mt-0.5">
              {confidence}%
            </div>
          </div>
          <div className="text-xs text-[#69736D] max-w-xs text-right leading-relaxed">
            Cross-referenced against verified Gram Panchayat records and Qdrant vector corpora.
          </div>
        </div>

        {/* Claim Verification Table */}
        <div className="mb-6 space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-[#17221F] flex items-center gap-2">
            <FileText className="w-4 h-4 text-[#153D32]" />
            Deconstructed Claims & NLI Verdicts
          </h4>
          {verificationResults.length === 0 ? (
            <p className="text-xs text-[#69736D] italic p-3 bg-[#F7F6F0] rounded-xl border border-[#E5E7DF]">
              All generated response text was evaluated as directly grounded in structured complaint facts.
            </p>
          ) : (
            <div className="space-y-2">
              {verificationResults.map((vr, i) => {
                const isSupp = vr.verification_result === 'SUPPORTED';
                const isContra = vr.verification_result === 'CONTRADICTED';
                return (
                  <div key={i} className="p-3.5 rounded-xl bg-[#F7F6F0] border border-[#E5E7DF] text-xs">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-semibold text-[#17221F]">
                        Claim #{i+1}: {vr.claim}
                      </span>
                      <span className={`inline-flex items-center gap-1 font-bold px-2 py-0.5 rounded text-[11px] ${
                        isSupp 
                          ? 'bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]' 
                          : isContra 
                          ? 'bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA]' 
                          : 'bg-[#F1F5F9] text-[#334155] border border-[#CBD5E1]'
                      }`}>
                        {isSupp ? <CheckCircle2 className="w-3 h-3" /> : isContra ? <AlertTriangle className="w-3 h-3" /> : <HelpCircle className="w-3 h-3" />}
                        {vr.verification_result}
                      </span>
                    </div>
                    {vr.reason && (
                      <p className="text-[#69736D] text-[11px] mt-1 bg-[#FFFFFF] p-2 rounded border border-[#E5E7DF]">
                        {vr.reason}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Retrieved Evidence Chunks */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-[#17221F] flex items-center gap-2">
            <Database className="w-4 h-4 text-[#153D32]" />
            Retrieved Grounding Chunks
          </h4>
          {evidences.length === 0 ? (
            <p className="text-xs text-[#69736D] italic p-3 bg-[#F7F6F0] rounded-xl border border-[#E5E7DF]">
              No external document chunks required; answered via direct complaint database record.
            </p>
          ) : (
            <div className="space-y-2.5">
              {evidences.map((ev, i) => (
                <div key={i} className="p-3.5 rounded-xl bg-[#FFFFFF] border border-[#E5E7DF] text-xs space-y-1.5">
                  <div className="flex items-center justify-between text-[#69736D] text-[11px]">
                    <span className="font-bold text-[#153D32]">
                      [{ev.source_type || 'KNOWLEDGE_BASE'}] Chunk {ev.chunk_id || i+1}
                    </span>
                    {ev.similarity_score && (
                      <span className="bg-[#F7F6F0] border border-[#E5E7DF] px-2 py-0.5 rounded font-mono text-[#404B46]">
                        Similarity: {ev.similarity_score}
                      </span>
                    )}
                  </div>
                  <pre className="whitespace-pre-wrap font-body text-[#17221F] text-xs bg-[#F7F6F0] p-3 rounded-lg border border-[#E5E7DF] leading-relaxed">
                    {ev.evidence_text}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-6 pt-4 border-t border-[#E5E7DF] flex justify-end">
          <button 
            onClick={onClose}
            className="btn-civic-primary text-xs !py-2 !px-4"
          >
            Close Trace
          </button>
        </div>

      </div>
    </div>
  );
};

export default EvidenceModal;
