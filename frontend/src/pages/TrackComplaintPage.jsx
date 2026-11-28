import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import StatusBadge from '../components/StatusBadge';
import Timeline from '../components/Timeline';
import { 
  Search, 
  Building2, 
  MapPin, 
  Calendar, 
  Clock, 
  AlertCircle, 
  Bot, 
  Sparkles, 
  ShieldCheck,
  CheckCircle2,
  User,
  Phone,
  ArrowRight
} from 'lucide-react';

const TrackComplaintPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialId = searchParams.get('id') || searchParams.get('q') || '';

  const [searchQuery, setSearchQuery] = useState(initialId);
  const [complaint, setComplaint] = useState(null);
  const [recentComplaints, setRecentComplaints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/complaints')
      .then((res) => {
        if (Array.isArray(res.data)) {
          setRecentComplaints(res.data);
          if (!initialId && res.data.length > 0) {
            setComplaint(res.data[0]);
            setSearchQuery(res.data[0].complaint_number);
          }
        }
      })
      .catch(() => {
        setRecentComplaints([]);
      });
  }, []);

  useEffect(() => {
    if (initialId) {
      handleSearch(initialId);
    }
  }, [initialId]);

  const handleSearch = async (idToSearch) => {
    const q = (idToSearch !== undefined ? idToSearch : searchQuery || '').trim();
    if (!q) return;

    setLoading(true);
    setError('');
    setComplaint(null);

    try {
      const res = await api.get(`/complaints/${encodeURIComponent(q)}`);
      setComplaint(res.data);
      setSearchParams({ id: res.data.complaint_number || q });
    } catch (err) {
      setError(err.response?.data?.detail || `Complaint record '${q}' not found in village grievance records.`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] py-8 sm:py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Title & Lookup Card */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-black tracking-widest text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200">
                  GIS Civic Transparency
                </span>
                <span className="text-xs text-slate-500 font-medium">{complaint?.village_name || 'Civic Grievance Portal'}</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-2 flex items-center gap-2.5">
                <Search className="w-6 h-6 text-blue-600" /> Track Grievance Status
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 mt-1">
                Search any complaint by identifier to inspect live field remarks, assigned officers, and milestone timelines.
              </p>
            </div>
            
            <Link
              to="/panchayat/dashboard"
              className="text-xs font-semibold text-blue-700 hover:text-blue-800 flex items-center gap-1 self-start sm:self-center shrink-0 hover:underline"
            >
              <span>Back to Panchayat Operations</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <form 
            onSubmit={(e) => { e.preventDefault(); handleSearch(); }}
            className="flex flex-col sm:flex-row gap-2.5 pt-2"
          >
            <div className="relative flex-1">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter complaint tracking ID"
                className="w-full pl-4 pr-4 py-3 rounded-xl border border-slate-200 font-mono text-xs sm:text-sm bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-600 transition shadow-2xs"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 rounded-xl bg-blue-700 hover:bg-blue-800 text-white font-bold text-xs sm:text-sm transition shadow-xs shrink-0 disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
            >
              {loading ? 'Retrieving Facts...' : 'Inspect Grievance'}
            </button>
          </form>

          {/* Recent Live Complaints */}
          {recentComplaints.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-slate-500">
              <span className="font-semibold text-slate-700">Recent Grievances:</span>
              {recentComplaints.slice(0, 5).map((item) => (
                <button
                  key={item.complaint_number}
                  type="button"
                  onClick={() => { setSearchQuery(item.complaint_number); handleSearch(item.complaint_number); }}
                  className={`px-2.5 py-1 rounded-lg border font-mono text-[11px] font-semibold transition cursor-pointer ${
                    complaint?.complaint_number === item.complaint_number
                      ? 'bg-blue-50 border-blue-300 text-blue-700 ring-1 ring-blue-300'
                      : 'bg-slate-50 hover:bg-blue-50/50 border-slate-200 text-slate-700'
                  }`}
                >
                  {item.complaint_number} <span className="font-sans font-normal text-slate-400">({item.category})</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {!complaint && !error && !loading && (
          <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-8 text-center text-xs text-slate-600">
            Enter a complaint tracking number above or submit a new grievance in the User portal to inspect its live verification timeline.
          </div>
        )}

        {error && (
          <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
            <span>{error}</span>
          </div>
        )}

        {/* Complaint Detail Card */}
        {complaint && (
          <div className="space-y-8">
            
            {/* Top Complaint Info Banner */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-xs space-y-6">
              
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="text-xl sm:text-2xl font-mono font-black text-slate-900">
                      {complaint.complaint_number}
                    </span>
                    <StatusBadge status={complaint.status} />
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                      {complaint.category}
                    </span>
                  </div>
                  <h2 className="text-lg sm:text-xl font-bold text-slate-900 leading-snug">
                    {complaint.title}
                  </h2>
                </div>

                <div className="flex sm:flex-col items-start sm:items-end justify-between sm:justify-start gap-1 text-xs">
                  <span className="text-slate-500">
                    Priority: <strong className="text-slate-800">{complaint.priority}</strong>
                  </span>
                  {complaint.sla_countdown && (
                    <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                      SLA: {complaint.sla_countdown}
                    </span>
                  )}
                </div>
              </div>

              {/* Metadata Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px] font-semibold">
                    <Building2 className="w-3.5 h-3.5 text-blue-600" /> Assigned Department
                  </div>
                  <div className="font-bold text-slate-900 text-xs">
                    {complaint.department_name || 'Unassigned'}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px] font-semibold">
                    <MapPin className="w-3.5 h-3.5 text-blue-600" /> Location / Ward
                  </div>
                  <div className="font-bold text-slate-900 text-xs truncate">
                    {complaint.location || 'Not specified'}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px] font-semibold">
                    <User className="w-3.5 h-3.5 text-blue-600" /> Complainant
                  </div>
                  <div className="font-bold text-slate-900 text-xs">
                    {complaint.citizen_name || 'Citizen'}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1">
                  <div className="flex items-center gap-1.5 text-slate-500 text-[11px] font-semibold">
                    <Calendar className="w-3.5 h-3.5 text-blue-600" /> Lodged Timestamp
                  </div>
                  <div className="font-bold text-slate-900 text-xs">
                    {new Date(complaint.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </div>
                </div>
              </div>

              {/* Grievance Description Statement */}
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5 text-xs">
                <span className="font-bold text-slate-500 text-[10px] uppercase tracking-wider block">
                  Citizen Problem Statement & Scope
                </span>
                <p className="text-slate-800 leading-relaxed font-normal">
                  {complaint.description}
                </p>
              </div>

            </div>

            {/* ─── Grievance History & Timeline (Exact Design Component) ─── */}
            <Timeline 
              currentStatus={complaint.status} 
              history={complaint.history} 
              complaint={complaint} 
            />

            {/* Ask AI About This Grievance Action Banner */}
            <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-sm font-bold text-blue-900">
                  <Sparkles className="w-4 h-4 text-blue-600" />
                  <span>Ask AI Assistant About This Grievance</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed max-w-xl">
                  Our evidence-grounded AI can quote verified officer remarks, repair timelines, and contractor SLA requirements for <strong>{complaint.complaint_number}</strong>.
                </p>
              </div>
              <Link
                to={`/ai-assistant?q=${encodeURIComponent(`What is the current progress and scheduled inspection update for complaint ${complaint.complaint_number}?`)}`}
                className="px-5 py-2.5 rounded-xl bg-blue-700 hover:bg-blue-800 text-white font-bold text-xs transition shadow-xs shrink-0 flex items-center justify-center gap-2 cursor-pointer"
              >
                <Bot className="w-4 h-4 text-amber-300" />
                <span>Query AI Assistant</span>
              </Link>
            </div>

          </div>
        )}

      </div>
    </div>
  );
};

export default TrackComplaintPage;
