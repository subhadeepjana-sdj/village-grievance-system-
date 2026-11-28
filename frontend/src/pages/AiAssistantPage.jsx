import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api/client';
import EvidenceBadge from '../components/EvidenceBadge';
import EvidenceModal from '../components/EvidenceModal';
import {
  Bot,
  Send,
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  Cpu,
  Database,
  FileText,
  Clock,
  Plus,
  Search,
  ChevronRight,
  ExternalLink,
  Sliders,
  CheckCircle2,
  XCircle,
  FileCheck2,
  Layers,
  Info,
  Maximize2
} from 'lucide-react';

const SUGGESTED_QUESTIONS = [
  "Which department handles water supply issues?",
  "What are drinking water complaint resolution guidelines?",
  "What is the schedule and rule for garbage collection?",
  "How many hours of agricultural electricity are provided?",
  "Why was an answer marked as insufficient evidence?"
];

const AiAssistantPage = () => {
  const [searchParams] = useSearchParams();
  const queryParam = searchParams.get('q');

  const [messages, setMessages] = useState([
    {
      sender: 'ai',
      answer: "Welcome to the Evidence-Grounded AI Assistant. Ask questions about village services, your submitted complaints, responsible departments, or indexed records.",
      decision: 'SHOW',
      verification_status: 'SUPPORTED',
      confidence: null,
      processing_time: null,
      evidences: [],
      verification_results: []
    }
  ]);

  const [inputQuery, setInputQuery] = useState('');
  const [configuration, setConfiguration] = useState('rag_verification');
  const [loading, setLoading] = useState(false);
  const [activeEvidenceIndex, setActiveEvidenceIndex] = useState(0);
  const [showRightPanel, setShowRightPanel] = useState(true);

  // Inspector Modal
  const [selectedResponse, setSelectedResponse] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (queryParam) {
      handleSend(queryParam);
    }
  }, [queryParam]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (questionText) => {
    const q = questionText || inputQuery;
    if (!q || !q.trim()) return;

    const userMsg = { sender: 'user', text: q };
    setMessages(prev => [...prev, userMsg]);
    if (!questionText) setInputQuery('');
    setLoading(true);

    try {
      const res = await api.post('/ai/query', {
        question: q.trim(),
        configuration: configuration
      });

      const aiMsg = {
        sender: 'ai',
        answer: res.data.answer,
        decision: res.data.decision,
        verification_status: res.data.verification_status,
        confidence: res.data.confidence,
        processing_time: res.data.processing_time,
        configuration: res.data.configuration,
        evidences: res.data.evidences || [],
        verification_results: res.data.verification_results || []
      };

      setMessages(prev => {
        const next = [...prev, aiMsg];
        setActiveEvidenceIndex(next.length - 1);
        return next;
      });
    } catch (err) {
      console.error('AI Query Error:', err);
      const fallbackMsg = {
        sender: 'ai',
        answer: "I could not find sufficient verified information in village records to answer this question reliably.",
        decision: 'ABSTAIN',
        verification_status: 'INSUFFICIENT_EVIDENCE',
        confidence: 0,
        evidences: [],
        verification_results: []
      };
      setMessages(prev => [...prev, fallbackMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleInspect = (msg) => {
    setSelectedResponse(msg);
    setIsModalOpen(true);
  };

  // Find active message for right evidence panel
  const activeAIMessage = messages[activeEvidenceIndex]?.sender === 'ai'
    ? messages[activeEvidenceIndex]
    : [...messages].reverse().find(m => m.sender === 'ai');

  return (
    <div className="py-6 px-4 sm:px-6 lg:px-8 max-w-[1600px] mx-auto">

      {/* 3-Column Desktop Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-8rem)] min-h-[650px]">

        {/* ========================================================= */}
        {/* LEFT PANEL: Conversation Topics, Filters & Engine Config  */}
        {/* ========================================================= */}
        <div className="hidden lg:flex lg:col-span-3 flex-col justify-between civic-card p-4 bg-[#FFFFFF] border border-[#E5E7DF]">
          <div className="space-y-5 overflow-y-auto pr-1">

            {/* New Inquiry Button */}
            <button
              onClick={() => {
                setMessages([messages[0]]);
                setInputQuery('');
              }}
              className="w-full btn-civic-primary text-xs !py-2.5 flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4 text-white" />
              <span>New Conversation</span>
            </button>

            {/* Pipeline Configuration Selector */}
            <div className="p-3 rounded-xl bg-[#F0F4F9] border border-[#E2E8F0] space-y-2">
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#64748B] flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-[#0047BA]" /> Research Pipeline Config
              </span>
              <div className="space-y-1">
                {[
                  { id: 'rag_verification', label: 'Full RAG + Hallucination Verifier', desc: 'Active NLI check (Recommended)' },
                  { id: 'rag', label: 'RAG Only (No Verification)', desc: 'Direct vector retrieval' },
                  { id: 'baseline', label: 'Standalone LLM (Zero RAG)', desc: 'Raw parametric memory' }
                ].map((cfg) => (
                  <button
                    key={cfg.id}
                    type="button"
                    onClick={() => setConfiguration(cfg.id)}
                    className={`w-full text-left p-2 rounded-lg text-xs transition cursor-pointer ${configuration === cfg.id
                      ? 'bg-[#0047BA] text-white'
                      : 'bg-white text-[#1A202C] hover:bg-[#E8F0FE] border border-[#E2E8F0]'
                      }`}
                  >
                    <div className="font-bold text-[11px] leading-tight">{cfg.label}</div>
                    <div className={`text-[10px] mt-0.5 ${configuration === cfg.id ? 'text-white/80' : 'text-[#64748B]'}`}>
                      {cfg.desc}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Quick Topic Chips */}
            <div className="space-y-2">
              <span className="text-[10px] uppercase font-bold tracking-wider text-[#64748B] block">
                Suggested Questions
              </span>
              <div className="space-y-1.5">
                {SUGGESTED_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSend(q)}
                    className="w-full text-left p-2 rounded-lg bg-white hover:bg-[#E8F0FE] border border-[#E2E8F0] text-xs text-[#1A202C] hover:text-[#0047BA] transition line-clamp-2"
                  >
                    "{q}"
                  </button>
                ))}
              </div>
            </div>

          </div>

          {/* Bottom Grounding Specs */}
          <div className="pt-3 border-t border-[#E2E8F0] text-[11px] text-[#64748B] space-y-1">
            <div className="flex items-center justify-between font-mono">
              <span>Embedding:</span>
              <span className="font-bold text-[#1A202C]">all-MiniLM-L6-v2</span>
            </div>
            <div className="flex items-center justify-between font-mono">
              <span>Vector Store:</span>
              <span className="font-bold text-[#1A202C]">Qdrant (384-d)</span>
            </div>
          </div>
        </div>

        {/* ========================================================= */}
        {/* CENTER PANEL: Main Conversation Stream & Input Bar        */}
        {/* ========================================================= */}
        <div className="lg:col-span-6 flex flex-col justify-between gis-card p-4 sm:p-6 bg-white border border-[#E2E8F0]">

          {/* Conversation Header */}
          <div className="flex items-center justify-between pb-3 border-b border-[#E2E8F0]">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[#0047BA] text-white flex items-center justify-center font-bold">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div>
                <h2 className="text-sm font-heading font-extrabold text-[#1A202C]">
                  Civic Intelligence Assistant
                </h2>
                <span className="text-[10px] text-[#69736D] block">
                  Grounding Mode: <strong>{configuration.replace('_', ' ').toUpperCase()}</strong>
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setShowRightPanel(!showRightPanel)}
                className="lg:hidden text-xs font-semibold px-2.5 py-1 rounded-md bg-[#EFF5EF] text-[#153D32]"
              >
                {showRightPanel ? 'Hide Evidence' : 'Show Evidence'}
              </button>
            </div>
          </div>

          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} animate-civic-fade`}
              >
                {msg.sender === 'user' ? (
                  /* Citizen User Bubble */
                  <div className="max-w-[85%] rounded-2xl p-3.5 bg-[#153D32] text-[#FFFFFF] text-xs sm:text-sm font-medium shadow-sm">
                    {msg.text}
                  </div>
                ) : (
                  /* AI Verified Response Bubble */
                  <div
                    onClick={() => setActiveEvidenceIndex(i)}
                    className="max-w-[92%] rounded-2xl p-4 bg-[#F7F6F0] border border-[#E5E7DF] space-y-3 cursor-pointer hover:border-[#153D32] transition"
                  >
                    {/* Header Badge */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-[#E5E7DF]">
                      <EvidenceBadge
                        status={msg.verification_status || msg.decision}
                        confidence={msg.confidence}
                        onClick={() => handleInspect(msg)}
                      />
                      {msg.processing_time && (
                        <span className="text-[10px] font-mono text-[#69736D] flex items-center gap-1">
                          <Clock className="w-3 h-3" /> {msg.processing_time}s
                        </span>
                      )}
                    </div>

                    {/* Answer Text */}
                    <p className="text-xs sm:text-sm leading-relaxed text-[#17221F] font-body whitespace-pre-wrap">
                      {msg.answer}
                    </p>

                    {/* Citations Button */}
                    <div className="flex items-center justify-between pt-1 text-xs">
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); handleInspect(msg); }}
                        className="text-[11px] font-bold text-[#153D32] hover:underline flex items-center gap-1"
                      >
                        <FileCheck2 className="w-3.5 h-3.5" />
                        <span>Inspect Verification Trace ({msg.evidences?.length || 0} sources)</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 p-3.5 rounded-2xl bg-[#EFF5EF] text-[#153D32] text-xs font-semibold animate-pulse max-w-sm">
                <Sparkles className="w-4 h-4 text-[#15803D] animate-spin" />
                <span>Hybrid RAG query & NLI claim verification running...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="pt-3 border-t border-[#E5E7DF]">
            <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex items-center gap-2">
              <input
                type="text"
                value={inputQuery}
                onChange={(e) => setInputQuery(e.target.value)}
                placeholder="Ask about a complaint, department SLA, or village scheme..."
                disabled={loading}
                className="flex-1 px-4 py-3 rounded-xl border border-[#E5E7DF] text-xs sm:text-sm bg-[#FFFFFF] text-[#17221F] focus:outline-none focus:ring-2 focus:ring-[#153D32]"
              />
              <button
                type="submit"
                disabled={loading || !inputQuery.trim()}
                className="btn-civic-primary text-xs !py-3 !px-5 font-bold shrink-0 disabled:opacity-50"
              >
                <Send className="w-4 h-4 text-[#D7F36A]" />
              </button>
            </form>
          </div>

        </div>

        {/* ========================================================= */}
        {/* RIGHT PANEL: Live Grounded Evidence Inspector (Collapsible)*/}
        {/* ========================================================= */}
        {showRightPanel && (
          <div className="lg:col-span-3 flex flex-col justify-between civic-card p-4 bg-[#F7F6F0] border border-[#E5E7DF] overflow-y-auto">
            <div className="space-y-4">

              <div className="flex items-center justify-between pb-3 border-b border-[#E5E7DF]">
                <div className="flex items-center gap-1.5 text-xs font-heading font-extrabold text-[#17221F]">
                  <Database className="w-4 h-4 text-[#153D32]" />
                  <span>Grounding Evidence Panel</span>
                </div>
                {activeAIMessage && (
                  <button
                    onClick={() => handleInspect(activeAIMessage)}
                    className="p-1 text-[#69736D] hover:text-[#17221F]"
                    title="Expand full trace modal"
                  >
                    <Maximize2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {activeAIMessage?.evidences && activeAIMessage.evidences.length > 0 ? (
                <div className="space-y-3">
                  <span className="text-[10px] uppercase font-bold tracking-wider text-[#69736D] block">
                    Retrieved Sources ({activeAIMessage.evidences.length})
                  </span>

                  {activeAIMessage.evidences.map((ev, idx) => (
                    <div key={idx} className="p-3 rounded-xl bg-[#FFFFFF] border border-[#E5E7DF] text-xs space-y-1.5 shadow-sm">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-[#153D32] truncate max-w-[140px]">
                          [{ev.source_type || 'KNOWLEDGE_BASE'}]
                        </span>
                        {ev.similarity_score && (
                          <span className="font-mono text-[#69736D] text-[10px]">
                            Sim: {ev.similarity_score}
                          </span>
                        )}
                      </div>
                      <p className="text-[#404B46] text-[11px] leading-relaxed italic line-clamp-4">
                        "{ev.evidence_text}"
                      </p>
                    </div>
                  ))}

                  {/* NLI Verification Breakdown */}
                  {activeAIMessage.verification_results && activeAIMessage.verification_results.length > 0 && (
                    <div className="space-y-2 pt-2">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-[#69736D] block">
                        Claim NLI Verification
                      </span>
                      {activeAIMessage.verification_results.map((vr, vIdx) => (
                        <div key={vIdx} className="p-2.5 rounded-lg bg-[#FFFFFF] border border-[#E5E7DF] text-[11px] space-y-1">
                          <div className="flex items-center justify-between font-bold text-[#17221F]">
                            <span className="truncate max-w-[140px]">{vr.claim}</span>
                            <span className={`text-[9px] px-1.5 py-0.2 rounded ${vr.verification_result === 'SUPPORTED'
                              ? 'bg-[#ECFDF5] text-[#065F46]'
                              : 'bg-[#FEF2F2] text-[#991B1B]'
                              }`}>
                              {vr.verification_result}
                            </span>
                          </div>
                          {vr.reason && <p className="text-[10px] text-[#69736D]">{vr.reason}</p>}
                        </div>
                      ))}
                    </div>
                  )}

                </div>
              ) : (
                <div className="p-6 text-center space-y-2 text-xs text-[#69736D]">
                  <HelpCircle className="w-8 h-8 text-[#69736D] mx-auto opacity-40" />
                  <p>No active response selected or response did not require external corpora.</p>
                </div>
              )}

            </div>

            {activeAIMessage && (
              <div className="pt-3 border-t border-[#E5E7DF]">
                <button
                  type="button"
                  onClick={() => handleInspect(activeAIMessage)}
                  className="w-full btn-civic-secondary text-xs !py-2 flex items-center justify-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5" /> Full Audit Modal
                </button>
              </div>
            )}
          </div>
        )}

      </div>

      {/* Full Modal Trace Component */}
      {selectedResponse && (
        <EvidenceModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          evidences={selectedResponse.evidences}
          verificationResults={selectedResponse.verification_results}
          confidence={selectedResponse.confidence}
        />
      )}

    </div>
  );
};

export default AiAssistantPage;
