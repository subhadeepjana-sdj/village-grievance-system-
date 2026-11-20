import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { 
  FileText, 
  Clock, 
  RotateCw, 
  CheckCircle2, 
  PlusCircle, 
  Search, 
  Sparkles,
  MapPin,
  Calendar,
  Building2,
  ChevronRight,
  Send,
  MoreVertical
} from 'lucide-react';

const CitizenDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [quickQuestion, setQuickQuestion] = useState('');

  useEffect(() => {
    fetchComplaints();
  }, []);

  const fetchComplaints = async () => {
    try {
      const res = await api.get('/complaints');
      setComplaints(res.data);
    } catch (err) {
      console.error('Failed to load complaints:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAsk = (e) => {
    e.preventDefault();
    if (!quickQuestion.trim()) return;
    navigate(`/ai-assistant?q=${encodeURIComponent(quickQuestion)}`);
  };

  const total = complaints.length;
  const awaitingReview = complaints.filter(c => ['SUBMITTED', 'ACKNOWLEDGED', 'UNDER_REVIEW'].includes(c.status)).length;
  const inProgress = complaints.filter(c => ['ASSIGNED', 'IN_PROGRESS'].includes(c.status)).length;
  const resolved = complaints.filter(c => ['RESOLVED', 'CLOSED'].includes(c.status)).length;

  const greetingTime = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  return (
    <div className="space-y-6 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto animate-gis-fade">
      
      {/* 1. Header with Greeting & Quick Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-black tracking-widest text-[#0047BA] bg-[#E8F0FE] px-2.5 py-0.5 rounded-full border border-[#BFDBFE]">
              Citizen Portal
            </span>
            <span className="text-xs text-[#64748B]">Gram Panchayat Chandanpur</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-heading font-black text-[#1A202C]">
            {greetingTime()}, {user?.name?.split(' ')[0] || 'Citizen'}.
          </h1>
          <p className="text-xs text-[#64748B]">
            Here's the live resolution status for your filed community grievances.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link
            to="/submit"
            className="btn-gis-primary text-xs !py-2.5 !px-5"
          >
            <PlusCircle className="w-4 h-4 text-white" />
            <span>File Grievance</span>
          </Link>
          <Link
            to="/track"
            className="btn-gis-secondary text-xs !py-2.5 !px-4"
          >
            <Search className="w-4 h-4 text-[#64748B]" />
            <span>Track by ID</span>
          </Link>
        </div>
      </div>

      {/* 2. Top Metrics Card Row (GIS Style with indicator bars) */}
      <div className="gis-card p-6 grid grid-cols-2 lg:grid-cols-4 gap-6 divide-y sm:divide-y-0 sm:divide-x divide-[#EAEEF4]">
        
        {/* Total Filed */}
        <div className="flex flex-col justify-between pt-2 sm:pt-0 sm:pr-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#0047BA]">
              <FileText className="w-5 h-5 text-[#0047BA]" />
            </div>
            <div className="text-xs font-semibold text-[#1A202C]">Total Filed</div>
            <div className="text-[11px] text-[#64748B]">Active & historical</div>
          </div>
          <div className="text-3xl font-black text-[#1A202C] mt-4">{total}</div>
          <div className="h-1 bg-[#0047BA] rounded-full mt-3 w-full" />
        </div>

        {/* Pending Review */}
        <div className="flex flex-col justify-between pt-4 sm:pt-0 sm:px-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#FF8A00]">
              <Clock className="w-5 h-5 text-[#FF8A00]" />
            </div>
            <div className="text-xs font-semibold text-[#1A202C]">Pending Review</div>
            <div className="text-[11px] text-[#64748B]">Awaiting staff triage</div>
          </div>
          <div className="text-3xl font-black text-[#FF8A00] mt-4">{awaitingReview}</div>
          <div className="h-1 bg-[#FF8A00] rounded-full mt-3 w-full" />
        </div>

        {/* In Progress */}
        <div className="flex flex-col justify-between pt-4 sm:pt-0 sm:px-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#00A3E0]">
              <RotateCw className="w-5 h-5 text-[#00A3E0]" />
            </div>
            <div className="text-xs font-semibold text-[#1A202C]">In Progress</div>
            <div className="text-[11px] text-[#64748B]">Active department repairs</div>
          </div>
          <div className="text-3xl font-black text-[#00A3E0] mt-4">{inProgress}</div>
          <div className="h-1 bg-[#00A3E0] rounded-full mt-3 w-full" />
        </div>

        {/* Solved */}
        <div className="flex flex-col justify-between pt-4 sm:pt-0 sm:pl-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#00B050]">
              <CheckCircle2 className="w-5 h-5 text-[#00B050]" />
            </div>
            <div className="text-xs font-semibold text-[#1A202C]">Solved</div>
            <div className="text-[11px] text-[#64748B]">Redressed & closed</div>
          </div>
          <div className="text-3xl font-black text-[#00B050] mt-4">{resolved}</div>
          <div className="h-1 bg-[#00B050] rounded-full mt-3 w-full" />
        </div>

      </div>

      {/* 3. AI Assistant Inquiry Banner */}
      <div className="gis-card p-6 sm:p-7 bg-gradient-to-r from-[#0047BA] to-[#00368C] text-white space-y-3 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 text-white text-xs font-bold uppercase tracking-wider backdrop-blur-sm">
            <Sparkles className="w-3.5 h-3.5 text-[#00A3E0]" /> Evidence-Grounded AI Assistant
          </div>
          <span className="text-[11px] text-white/70 hidden sm:inline">100% Fact Checked</span>
        </div>

        <h3 className="text-lg sm:text-xl font-black text-white tracking-tight">
          Have questions about your complaint or village guidelines?
        </h3>
        <p className="text-xs text-white/80 max-w-2xl leading-relaxed">
          Ask the GIS assistant. Answers are strictly cross-referenced with official Gram Panchayat records and water charters before responding.
        </p>

        <form onSubmit={handleQuickAsk} className="flex items-center gap-2 pt-2">
          <input
            type="text"
            value={quickQuestion}
            onChange={(e) => setQuickQuestion(e.target.value)}
            placeholder="e.g. What is the status of my complaint? or When is drinking water supplied in Ward 4?"
            className="flex-1 px-4 py-2.5 rounded-xl bg-white text-[#1A202C] text-xs placeholder:text-[#94A3B8] focus:outline-none shadow-sm"
          />
          <button
            type="submit"
            className="btn-gis-cyan text-xs !py-2.5 !px-5 shrink-0"
          >
            <Send className="w-3.5 h-3.5" /> Ask AI
          </button>
        </form>
      </div>

      {/* 4. Recent Grievances List (GIS Table & Cards) */}
      <div className="gis-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-black text-[#1A202C]">
              Your Grievances
            </h2>
            <p className="text-xs text-[#64748B]">
              Click any record to inspect the official department inspection remarks and timeline.
            </p>
          </div>
          <Link
            to="/submit"
            className="text-xs font-bold text-[#0047BA] hover:underline flex items-center gap-1"
          >
            <span>+ File New</span>
          </Link>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-[#64748B] space-y-2">
            <div className="w-6 h-6 border-2 border-[#0047BA] border-t-transparent rounded-full animate-spin mx-auto" />
            <p>Loading your complaint records...</p>
          </div>
        ) : complaints.length === 0 ? (
          <div className="p-10 text-center space-y-4 border-dashed border-2 border-[#E2E8F0] rounded-2xl">
            <div className="w-12 h-12 rounded-full bg-[#E8F0FE] text-[#0047BA] flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-6 h-6 text-[#0047BA]" />
            </div>
            <div className="space-y-1 max-w-sm mx-auto">
              <h3 className="font-black text-sm text-[#1A202C]">
                No grievances on record
              </h3>
              <p className="text-xs text-[#64748B]">
                You currently have no active or historical complaints submitted for Gram Panchayat Chandanpur.
              </p>
            </div>
            <Link
              to="/submit"
              className="btn-gis-primary text-xs !py-2.5 !px-5 inline-flex"
            >
              <PlusCircle className="w-4 h-4 text-white" /> Submit Your First Grievance
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-[#F1F5F9]">
            {complaints.map((c) => (
              <div
                key={c.id}
                onClick={() => navigate(`/track?id=${c.complaint_number || c.id}`)}
                className="py-4 hover:bg-[#F8FAFC] transition cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 px-2 rounded-xl"
              >
                <div className="space-y-1.5 max-w-2xl">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-[#F0F4F9] text-[#0047BA] border border-[#E2E8F0]">
                      {c.complaint_number}
                    </span>
                    <span className="text-[11px] font-semibold text-[#64748B] bg-[#F1F5F9] px-2 py-0.5 rounded">
                      {c.category}
                    </span>
                  </div>

                  <h3 className="font-bold text-sm text-[#1A202C]">
                    {c.title}
                  </h3>

                  <p className="text-xs text-[#64748B] line-clamp-1">
                    {c.description}
                  </p>

                  <div className="flex flex-wrap items-center gap-4 text-[11px] text-[#94A3B8]">
                    {c.location && (
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-[#0047BA]" /> {c.location}
                      </span>
                    )}
                    <span className="flex items-center gap-1">
                      <Building2 className="w-3.5 h-3.5 text-[#0047BA]" /> {c.department_name || 'Village Water Department'}
                    </span>
                    {c.created_at && (
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" /> {new Date(c.created_at).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                  {c.status === 'RESOLVED' || c.status === 'CLOSED' ? (
                    <span className="gis-pill-closed">Closed</span>
                  ) : c.status === 'IN_PROGRESS' || c.status === 'ASSIGNED' ? (
                    <span className="gis-pill-progress">In Progress</span>
                  ) : (
                    <span className="gis-pill-open">Open</span>
                  )}
                  <ChevronRight className="w-4 h-4 text-[#94A3B8]" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
};

export default CitizenDashboard;
