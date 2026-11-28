import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { 
  Cpu, 
  Sparkles, 
  BarChart3, 
  CheckCircle2, 
  AlertTriangle, 
  HelpCircle, 
  Play, 
  ShieldCheck, 
  FileText,
  Sliders,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Flame,
  Check,
  XCircle,
  Clock
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

const ResearchDashboard = () => {
  const [metrics, setMetrics] = useState([]);
  const [benchmarks, setBenchmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [msg, setMsg] = useState('');
  const [selectedCaseIdx, setSelectedCaseIdx] = useState(0);

  const fetchMetrics = async () => {
    try {
      const res = await api.get('/research/metrics');
      setMetrics(res.data);
    } catch (err) {
      console.error('Error fetching research metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const handleRunExperiment = async () => {
    setRunning(true);
    setMsg('');
    try {
      const res = await api.post('/research/run');
      setMetrics(res.data.results || []);
      setBenchmarks(res.data.benchmarks || []);
      if (res.data.status === 'NO_DATA') {
        setMsg('No live complaints or knowledge base documents available to evaluate yet. Submit a grievance or upload a document first.');
      } else {
        setMsg(`Comparative experiment '${res.data.run_id}' executed across live system records!`);
      }
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Experiment run failed.');
    } finally {
      setRunning(false);
    }
  };

  const mA = metrics.find(m => m.config_type === 'STANDALONE_LLM');
  const mB = metrics.find(m => m.config_type === 'RAG_LLM');
  const mC = metrics.find(m => m.config_type === 'RAG_VERIFICATION');

  const chartData = metrics.length > 0
    ? [
        {
          name: 'Config A: Standalone LLM',
          FactualAccuracy: mA?.factual_accuracy ?? 0,
          HallucinationRate: mA?.hallucination_rate ?? 0,
          Faithfulness: mA?.faithfulness ?? 0,
          AbstentionAccuracy: mA?.abstention_accuracy ?? 0,
        },
        {
          name: 'Config B: LLM + RAG',
          FactualAccuracy: mB?.factual_accuracy ?? 0,
          HallucinationRate: mB?.hallucination_rate ?? 0,
          Faithfulness: mB?.faithfulness ?? 0,
          AbstentionAccuracy: mB?.abstention_accuracy ?? 0,
        },
        {
          name: 'Config C: RAG + Verification',
          FactualAccuracy: mC?.factual_accuracy ?? 0,
          HallucinationRate: mC?.hallucination_rate ?? 0,
          Faithfulness: mC?.faithfulness ?? 0,
          AbstentionAccuracy: mC?.abstention_accuracy ?? 0,
        },
      ]
    : [];

  const testCases = Array.isArray(benchmarks) ? benchmarks : [];

  return (
    <div className="space-y-8 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E5E7DF]">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-extrabold tracking-wider text-[#153D32] bg-[#EFF5EF] px-2.5 py-0.5 rounded-full border border-[#DDE8DD]">
              Research & Evaluation Benchmarks
            </span>
            <span className="text-xs text-[#69736D]">Empirical NLP Grounding Study</span>
          </div>
          <h1 className="text-2xl font-heading font-extrabold text-[#17221F] flex items-center gap-2">
            <Cpu className="w-6 h-6 text-[#153D32]" />
            Hallucination Detection Performance Matrix
          </h1>
          <p className="text-xs text-[#69736D]">
            Comparative ablation study: Standalone LLM vs Hybrid RAG vs Evidence-Grounded Hallucination Verification.
          </p>
        </div>

        <button
          onClick={handleRunExperiment}
          disabled={running}
          className="btn-civic-primary text-xs !py-3 !px-5 font-bold shrink-0 disabled:opacity-50"
        >
          <Play className="w-4 h-4 text-[#D7F36A]" />
          <span>{running ? 'Running Benchmark Test Suite...' : 'Run Comparative Experiment'}</span>
        </button>
      </div>

      {msg && (
        <div className="p-3.5 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] text-[#065F46] text-xs flex items-center justify-between gap-2 animate-civic-fade">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{msg}</span>
          </div>
          <button onClick={() => setMsg('')} className="text-[#065F46] font-bold">×</button>
        </div>
      )}

      {/* Performance Matrix Table */}
      <div className="civic-card bg-[#FFFFFF] overflow-hidden">
        <div className="p-4 border-b border-[#E5E7DF] flex items-center justify-between">
          <div className="space-y-0.5">
            <h2 className="text-sm font-heading font-bold text-[#17221F] flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-[#153D32]" />
              System Configuration Evaluation Matrix
            </h2>
            <p className="text-[11px] text-[#69736D]">
              Measured across live comparative evaluation runs (Standalone LLM vs Hybrid RAG vs NLI Verification).
            </p>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#EFF5EF] text-[#153D32] font-semibold">
            Metric: Exact Match & NLI Entailment
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-[#F7F6F0] border-b border-[#E5E7DF] text-[11px] font-bold text-[#69736D] uppercase tracking-wider">
                <th className="p-3.5">Architecture Configuration</th>
                <th className="p-3.5">Factual Accuracy</th>
                <th className="p-3.5">Hallucination Rate</th>
                <th className="p-3.5">Faithfulness</th>
                <th className="p-3.5">Retrieval Recall</th>
                <th className="p-3.5">F1 Score</th>
                <th className="p-3.5">Abstention Acc</th>
                <th className="p-3.5">Avg Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E5E7DF] font-mono">
              {metrics.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center font-sans text-xs text-[#69736D]">
                    {loading ? 'Loading evaluation telemetry...' : 'No benchmark runs recorded yet. Click "Run Comparative Experiment" to generate live metrics.'}
                  </td>
                </tr>
              ) : (
                <>
                  <tr className="hover:bg-[#F7F6F0]/50 transition">
                    <td className="p-3.5 font-sans font-bold text-[#991B1B]">
                      Config A: Standalone LLM
                    </td>
                    <td className="p-3.5 text-[#991B1B] font-bold">{(mA?.factual_accuracy ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#991B1B] font-bold">{(mA?.hallucination_rate ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#69736D]">{(mA?.faithfulness ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#69736D]">{(mA?.retrieval_recall ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#69736D]">{(mA?.f1_score ?? 0).toFixed(2)}</td>
                    <td className="p-3.5 text-[#991B1B]">{(mA?.abstention_accuracy ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#17221F]">{(mA?.avg_latency ?? 0).toFixed(2)}s</td>
                  </tr>
                  <tr className="hover:bg-[#F7F6F0]/50 transition">
                    <td className="p-3.5 font-sans font-bold text-[#1D4ED8]">
                      Config B: LLM + RAG (No Verifier)
                    </td>
                    <td className="p-3.5 text-[#1D4ED8] font-bold">{(mB?.factual_accuracy ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#92400E] font-bold">{(mB?.hallucination_rate ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#17221F]">{(mB?.faithfulness ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#065F46] font-bold">{(mB?.retrieval_recall ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#17221F]">{(mB?.f1_score ?? 0).toFixed(2)}</td>
                    <td className="p-3.5 text-[#92400E]">{(mB?.abstention_accuracy ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#17221F]">{(mB?.avg_latency ?? 0).toFixed(2)}s</td>
                  </tr>
                  <tr className="bg-[#ECFDF5]/70 hover:bg-[#ECFDF5] transition font-bold">
                    <td className="p-3.5 font-sans text-[#065F46] flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-[#065F46]" />
                      <span>Config C: RAG + Verification (Ours)</span>
                    </td>
                    <td className="p-3.5 text-[#065F46] text-sm font-extrabold">{(mC?.factual_accuracy ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#065F46] font-extrabold">{(mC?.hallucination_rate ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#065F46]">{(mC?.faithfulness ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#065F46]">{(mC?.retrieval_recall ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#065F46]">{(mC?.f1_score ?? 0).toFixed(2)}</td>
                    <td className="p-3.5 text-[#065F46]">{(mC?.abstention_accuracy ?? 0).toFixed(1)}%</td>
                    <td className="p-3.5 text-[#17221F]">{(mC?.avg_latency ?? 0).toFixed(2)}s</td>
                  </tr>
                </>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Comparative Grouped Bar Chart */}
      <div className="civic-card p-6 bg-[#FFFFFF] space-y-4">
        <div className="space-y-0.5">
          <h3 className="text-sm font-heading font-bold text-[#17221F] flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-[#153D32]" />
            Factual Accuracy vs Hallucination Rate across Configurations
          </h3>
          <p className="text-xs text-[#69736D]">
            Measured live across Standalone LLM, Hybrid RAG, and NLI Verification runs.
          </p>
        </div>

        <div className="h-72">
          {chartData.length === 0 ? (
            <div className="h-full flex items-center justify-center rounded-xl border border-dashed border-[#E5E7DF] bg-[#F7F6F0]/50 text-xs text-[#69736D]">
              Chart will populate when a benchmark experiment is executed.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#69736D" fontSize={11} tickLine={false} />
                <YAxis stroke="#69736D" fontSize={11} unit="%" tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#FFFFFF', 
                    borderColor: '#E5E7DF', 
                    borderRadius: '12px', 
                    fontSize: '12px' 
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="FactualAccuracy" name="Factual Accuracy (%)" fill="#153D32" radius={[6, 6, 0, 0]} />
                <Bar dataKey="HallucinationRate" name="Hallucination Rate (%)" fill="#DC2626" radius={[6, 6, 0, 0]} />
                <Bar dataKey="Faithfulness" name="Faithfulness Entailment (%)" fill="#D7F36A" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Side-by-Side Question Ablation Samples */}
      {testCases.length > 0 && (
        <div className="civic-card p-6 bg-[#FFFFFF] space-y-5">
          <div className="space-y-1">
            <h3 className="text-sm font-heading font-bold text-[#17221F] flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#153D32]" />
              Side-by-Side Question Evaluation Inspector
            </h3>
            <p className="text-xs text-[#69736D]">
              Examine how each architecture processed live evaluation queries.
            </p>
          </div>

          <div className="flex gap-2 border-b border-[#E5E7DF] pb-2">
            {testCases.map((tc, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setSelectedCaseIdx(idx)}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition cursor-pointer ${
                  selectedCaseIdx === idx
                    ? 'bg-[#153D32] text-[#FFFFFF]'
                    : 'text-[#69736D] hover:bg-[#F7F6F0]'
                }`}
              >
                Test Case #{idx + 1}
              </button>
            ))}
          </div>

          {testCases[selectedCaseIdx] && (
            <div className="space-y-4">
              <div className="p-3.5 rounded-xl bg-[#F7F6F0] border border-[#E5E7DF] space-y-1">
                <span className="text-[10px] uppercase font-bold text-[#69736D]">Evaluation Query</span>
                <div className="font-heading font-bold text-sm text-[#17221F]">
                  "{testCases[selectedCaseIdx].question}"
                </div>
                {testCases[selectedCaseIdx].expected_answer && (
                  <div className="text-[11px] text-[#065F46] font-semibold pt-0.5">
                    Expected Ground Truth: {testCases[selectedCaseIdx].expected_answer}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-[#FEF2F2] border border-[#FECACA] space-y-1.5">
                  <div className="font-bold text-[#991B1B]">Config A: Standalone LLM</div>
                  <p className="text-[#7F1D1D] leading-relaxed">{testCases[selectedCaseIdx].config_a_answer}</p>
                  <div className="text-[11px] font-semibold text-[#991B1B]">{testCases[selectedCaseIdx].config_a_verdict}</div>
                </div>
                <div className="p-4 rounded-xl bg-[#EFF6FF] border border-[#BFDBFE] space-y-1.5">
                  <div className="font-bold text-[#1D4ED8]">Config B: LLM + RAG</div>
                  <p className="text-[#1E40AF] leading-relaxed">{testCases[selectedCaseIdx].config_b_answer}</p>
                  <div className="text-[11px] font-semibold text-[#1D4ED8]">{testCases[selectedCaseIdx].config_b_verdict}</div>
                </div>
                <div className="p-4 rounded-xl bg-[#ECFDF5] border border-[#A7F3D0] space-y-1.5">
                  <div className="font-bold text-[#065F46]">Config C: RAG + Verification</div>
                  <p className="text-[#064E3B] leading-relaxed font-medium">{testCases[selectedCaseIdx].config_c_answer}</p>
                  <div className="text-[11px] font-semibold text-[#065F46]">{testCases[selectedCaseIdx].config_c_verdict}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
};

export default ResearchDashboard;
