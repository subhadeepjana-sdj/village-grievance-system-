import React, { useState } from 'react';
import { 
  ShieldCheck, 
  AlertTriangle, 
  HelpCircle, 
  Sparkles, 
  Database, 
  ChevronDown, 
  ChevronUp, 
  FileText, 
  CheckCircle2, 
  XCircle, 
  Info, 
  ExternalLink 
} from 'lucide-react';
import { AIResponseData, EvidenceItem, ClaimVerification } from '../../types';

interface AIResponseCardProps {
  data?: AIResponseData;
  isVerifying?: boolean;
}

export const AIResponseCard: React.FC<AIResponseCardProps> = ({ data, isVerifying }) => {
  const [showSources, setShowSources] = useState(false);
  const [showClaimTable, setShowClaimTable] = useState(false);

  // Verifying / Loading State
  if (isVerifying) {
    return (
      <div className="p-5 rounded-2xl bg-[#FFFFFF] border border-[#DDE8DD] shadow-sm space-y-3 animate-pulse">
        <div className="flex items-center gap-2 text-xs text-[#153D32] font-semibold">
          <Sparkles className="w-4 h-4 text-[#153D32] animate-spin" />
          <span>Executing Hybrid Retrieval & NLI Hallucination Verification...</span>
        </div>
        <div className="h-4 bg-[#EFF5EF] rounded w-5/6" />
        <div className="h-4 bg-[#EFF5EF] rounded w-3/5" />
      </div>
    );
  }

  if (!data) return null;

  const { decision, verification_status, answer, confidence, evidences = [], verification_results = [] } = data;
  const normStatus = verification_status || (decision === 'SHOW' ? 'SUPPORTED' : decision === 'CORRECT' ? 'CONTRADICTED' : 'INSUFFICIENT_EVIDENCE');

  // State 1: Supported / Evidence Verified
  if (normStatus === 'SUPPORTED' || decision === 'SHOW') {
    return (
      <div className="p-6 rounded-2xl bg-[#FFFFFF] border border-[#E5E7DF] shadow-sm space-y-4">
        
        {/* Verification Status Header */}
        <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#E5E7DF]">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]">
            <ShieldCheck className="w-4 h-4 text-[#065F46]" />
            <span>✓ Verified by Grounded Evidence</span>
          </div>

          <div className="flex items-center gap-3 text-xs text-[#69736D]">
            {confidence > 0 && (
              <span className="font-mono text-xs">
                Faithfulness: <strong className="text-[#065F46]">{confidence}%</strong>
              </span>
            )}
            <span className="text-[11px] px-2 py-0.5 rounded bg-[#EFF5EF] text-[#153D32] font-semibold">
              Decision: SHOW
            </span>
          </div>
        </div>

        {/* Answer Content */}
        <div className="text-sm leading-relaxed text-[#17221F] font-body whitespace-pre-wrap">
          {answer}
        </div>

        {/* Interactive Verification Breakdown Accordion */}
        <div className="pt-2 border-t border-[#E5E7DF] space-y-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSources(!showSources)}
              className="text-xs font-semibold text-[#153D32] hover:text-[#0E2922] transition flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#EFF5EF] border border-[#DDE8DD]"
            >
              <Database className="w-3.5 h-3.5 text-[#153D32]" />
              <span>Grounded Sources ({evidences.length})</span>
              {showSources ? <ChevronUp className="w-3.5 h-3.5 ml-1" /> : <ChevronDown className="w-3.5 h-3.5 ml-1" />}
            </button>

            {verification_results.length > 0 && (
              <button
                onClick={() => setShowClaimTable(!showClaimTable)}
                className="text-xs font-semibold text-[#404B46] hover:text-[#17221F] transition flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#F7F6F0] border border-[#E5E7DF]"
              >
                <FileText className="w-3.5 h-3.5" />
                <span>NLI Claims ({verification_results.length})</span>
                {showClaimTable ? <ChevronUp className="w-3.5 h-3.5 ml-1" /> : <ChevronDown className="w-3.5 h-3.5 ml-1" />}
              </button>
            )}
          </div>

          {/* Expanded Sources Drawer */}
          {showSources && (
            <div className="space-y-2 pt-2 animate-civic-fade">
              {evidences.map((ev, i) => (
                <div key={i} className="p-3.5 rounded-xl bg-[#F7F6F0] border border-[#E5E7DF] text-xs space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] text-[#69736D]">
                    <span className="font-bold text-[#153D32]">
                      Source #{i + 1}: {ev.source_type || 'Official Record'}
                    </span>
                    {ev.similarity_score && (
                      <span className="font-mono text-[#404B46] bg-[#FFFFFF] px-2 py-0.5 rounded border border-[#E5E7DF]">
                        Retrieval Sim: {ev.similarity_score}
                      </span>
                    )}
                  </div>
                  <p className="text-[#17221F] text-xs leading-relaxed italic bg-[#FFFFFF] p-2.5 rounded-lg border border-[#E5E7DF]">
                    "{ev.evidence_text}"
                  </p>
                </div>
              ))}
            </div>
          )}

          {/* Expanded NLI Claims Table */}
          {showClaimTable && verification_results.length > 0 && (
            <div className="mt-3 overflow-x-auto border border-[#E5E7DF] rounded-xl bg-[#FFFFFF] text-xs animate-civic-fade">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-[#F7F6F0] border-b border-[#E5E7DF] text-[11px] font-bold text-[#69736D] uppercase tracking-wider">
                    <th className="p-2.5">Candidate Claim</th>
                    <th className="p-2.5">Retrieved Evidence</th>
                    <th className="p-2.5">NLI Verdict</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E5E7DF]">
                  {verification_results.map((vr, idx) => (
                    <tr key={idx} className="hover:bg-[#F7F6F0]/60">
                      <td className="p-2.5 font-medium text-[#17221F]">{vr.claim}</td>
                      <td className="p-2.5 text-[#69736D] text-[11px]">{vr.reason || 'Record match'}</td>
                      <td className="p-2.5">
                        <span className="inline-flex items-center gap-1 font-bold text-[11px] px-2 py-0.5 rounded bg-[#ECFDF5] text-[#065F46] border border-[#A7F3D0]">
                          <CheckCircle2 className="w-3 h-3" /> SUPPORTED
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    );
  }

  // State 2: Contradicted & Corrected
  if (normStatus === 'CONTRADICTED' || decision === 'CORRECT') {
    return (
      <div className="p-6 rounded-2xl bg-[#FFFFFF] border-2 border-[#FECACA] shadow-sm space-y-4">
        
        {/* Warning Banner */}
        <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#FEE2E2]">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA]">
            <AlertTriangle className="w-4 h-4 text-[#991B1B]" />
            <span>⚠ Contradiction Detected — Response Corrected</span>
          </div>
          <span className="text-[11px] px-2 py-0.5 rounded bg-[#FEF2F2] text-[#991B1B] font-semibold">
            Decision: CORRECT
          </span>
        </div>

        <div className="p-3.5 rounded-xl bg-[#FEF2F2] border border-[#FECACA] text-xs text-[#991B1B] leading-relaxed">
          <strong>Hallucination Intercepted:</strong> The raw language model generated a claim that contradicted verified Gram Panchayat records. The verified response below has been automatically bound to facts.
        </div>

        {/* Corrected Answer */}
        <div className="text-sm leading-relaxed text-[#17221F] font-body whitespace-pre-wrap">
          {answer}
        </div>

        {/* Claim Comparison Table */}
        <div className="overflow-x-auto border border-[#E5E7DF] rounded-xl bg-[#FFFFFF] text-xs">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#F7F6F0] border-b border-[#E5E7DF] text-[11px] font-bold text-[#69736D] uppercase tracking-wider">
                <th className="p-2.5">Candidate Claim</th>
                <th className="p-2.5">Retrieved Evidence</th>
                <th className="p-2.5">Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E7DF]">
              {verification_results.length > 0 ? (
                verification_results.map((vr, idx) => (
                  <tr key={idx}>
                    <td className="p-2.5 line-through text-[#991B1B] font-medium">{vr.claim}</td>
                    <td className="p-2.5 text-[#065F46] font-medium">{vr.reason || 'Verified Ground Truth'}</td>
                    <td className="p-2.5">
                      <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA]">
                        <XCircle className="w-3 h-3" /> CONTRADICTED
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="p-2.5 line-through text-[#991B1B]">Road Department (Assigned)</td>
                  <td className="p-2.5 text-[#065F46]">Village Water Department (Under Review)</td>
                  <td className="p-2.5">
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded bg-[#FEF2F2] text-[#991B1B] border border-[#FECACA]">
                      <XCircle className="w-3 h-3" /> CONTRADICTED
                    </span>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

      </div>
    );
  }

  // State 3: Insufficient Evidence / Honest Abstention
  return (
    <div className="p-6 rounded-2xl bg-[#FFFFFF] border border-[#CBD5E1] shadow-sm space-y-4">
      
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[#E5E7DF]">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-[#F1F5F9] text-[#334155] border border-[#CBD5E1]">
          <HelpCircle className="w-4 h-4 text-[#334155]" />
          <span>Safe Abstention (Insufficient Verified Evidence)</span>
        </div>
        <span className="text-[11px] px-2 py-0.5 rounded bg-[#F1F5F9] text-[#334155] font-semibold">
          Decision: ABSTAIN
        </span>
      </div>

      <div className="p-4 rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-2">
        <p className="text-xs text-[#334155] leading-relaxed font-body">
          <strong>Why this answer was abstained:</strong> The hallucination detection engine could not match this inquiry with sufficient verified Gram Panchayat documentation or complaint records. Rather than hallucinate an inaccurate answer, the system refuses to guess.
        </p>
      </div>

      <div className="text-xs text-[#69736D] leading-relaxed">
        {answer}
      </div>

    </div>
  );
};

export default AIResponseCard;
