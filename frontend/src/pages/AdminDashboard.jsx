import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { 
  MoreVertical, 
  ChevronDown, 
  Search,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip 
} from 'recharts';

export const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [allComplaints, setAllComplaints] = useState([]);
  const [feedbackStats, setFeedbackStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dateRange] = useState('Live MongoDB & DB Telemetry');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, complaintsRes, fbRes] = await Promise.allSettled([
        api.get('/admin/statistics'),
        api.get('/complaints'),
        api.get('/admin/feedback/stats')
      ]);

      if (statsRes.status === 'fulfilled' && statsRes.value?.data) {
        setStats(statsRes.value.data);
      }

      if (complaintsRes.status === 'fulfilled' && Array.isArray(complaintsRes.value?.data)) {
        setAllComplaints(complaintsRes.value.data);
      }

      if (fbRes.status === 'fulfilled' && fbRes.value?.data) {
        setFeedbackStats(fbRes.value.data);
      }
    } catch (err) {
      console.error('Error loading dashboard telemetry:', err);
    } finally {
      setLoading(false);
    }
  };

  const { summary, ai_statistics } = stats || {};
  const pendingCount = summary?.pending_complaints ?? allComplaints.filter(c => ['SUBMITTED', 'ACKNOWLEDGED', 'ASSIGNED'].includes(c.status)).length;
  const inProgressCount = summary?.in_progress_complaints ?? allComplaints.filter(c => ['UNDER_REVIEW', 'IN_PROGRESS'].includes(c.status)).length;
  const resolvedCount = summary?.resolved_complaints ?? allComplaints.filter(c => c.status === 'RESOLVED').length;
  const totalComplaints = summary?.total_complaints ?? allComplaints.length;
  const serviceLevelPct = totalComplaints > 0 ? Math.round((resolvedCount / totalComplaints) * 1000) / 10 : 0;

  const recentComplaints = allComplaints.slice(0, 6).map(c => ({
    id: c.complaint_number || c.id,
    date: c.created_at
      ? new Date(c.created_at).toLocaleString('en-US', {
          day: '2-digit', month: 'short', year: 'numeric',
          hour: '2-digit', minute: '2-digit'
        })
      : 'Recent',
    name: c.citizen_name || 'Citizen',
    category: c.category || 'General',
    status: c.status === 'RESOLVED' || c.status === 'CLOSED'
      ? 'Closed'
      : c.status === 'IN_PROGRESS' || c.status === 'UNDER_REVIEW'
        ? 'In Progress'
        : 'Open'
  }));

  const trendData = (() => {
    if (!allComplaints.length) return [];
    const byDate = {};
    for (const c of allComplaints) {
      const label = c.created_at
        ? new Date(c.created_at).toLocaleDateString('en-US', { month: 'short', day: '2-digit' })
        : 'Today';
      if (!byDate[label]) byDate[label] = { date: label, pending: 0, inProgress: 0 };
      if (['SUBMITTED', 'ACKNOWLEDGED', 'ASSIGNED'].includes(c.status)) {
        byDate[label].pending += 1;
      } else {
        byDate[label].inProgress += 1;
      }
    }
    return Object.values(byDate).reverse();
  })();

  const categoryStats = (() => {
    if (!allComplaints.length) return [];
    const palette = ['#0047BA', '#FF8A00', '#00B050', '#00A3E0', '#7C3AED'];
    const counts = {};
    for (const c of allComplaints) {
      const cat = c.category || 'Other';
      counts[cat] = (counts[cat] || 0) + 1;
    }
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([name, count], idx) => ({
        name,
        count,
        percent: Math.round((count / allComplaints.length) * 100),
        color: palette[idx % palette.length],
      }));
  })();

  return (
    <div className="space-y-6 w-full max-w-[1340px] mx-auto animate-gis-fade">
      
      {/* ═══════════════════════════════════════════════
          ROW 1: THE 5 KPI CARDS
      ═══════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
        
        {/* 1. Pending Card */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAEEF4] shadow-xs flex flex-col justify-between relative">
          <div>
            <div className="flex items-center justify-between">
              {/* Yellow/Gold Clock on pedestal icon */}
              <div className="w-8 h-8 rounded-lg flex items-center justify-center">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="11" r="7"/>
                  <polyline points="12 8 12 11 14 12"/>
                  <line x1="7" y1="20" x2="17" y2="20" strokeWidth="2.5"/>
                </svg>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[10.5px] font-bold bg-[#FEF3C7] text-[#B45309] tracking-wide">
                Live
              </span>
            </div>
            <div className="mt-3">
              <div className="text-sm font-semibold text-[#1A202C]">Pending</div>
              <div className="text-[11px] text-[#64748B]">Awaiting review</div>
            </div>
          </div>
          
          <div className="mt-4">
            <div className="text-3xl font-black text-[#1A202C] tracking-tight">
              {pendingCount}
            </div>
            {/* Yellow bottom accent bar */}
            <div className="h-1 bg-[#F59E0B] rounded-full mt-3 w-full" />
          </div>
        </div>

        {/* 2. In Progress Card */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAEEF4] shadow-xs flex flex-col justify-between relative">
          <div>
            <div className="flex items-center justify-between">
              {/* Blue rotating arrows icon */}
              <div className="w-8 h-8 rounded-lg flex items-center justify-center">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0047BA" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 2v6h-6"/>
                  <path d="M21.1 15.5a9 9 0 1 1-.5-8.2L21 8"/>
                </svg>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[10.5px] font-bold bg-[#E0F2FE] text-[#0369A1] tracking-wide">
                Active
              </span>
            </div>
            <div className="mt-3">
              <div className="text-sm font-semibold text-[#1A202C]">In Progress</div>
              <div className="text-[11px] text-[#64748B]">Under review / field work</div>
            </div>
          </div>
          
          <div className="mt-4">
            <div className="text-3xl font-black text-[#1A202C] tracking-tight">
              {inProgressCount}
            </div>
            {/* Cyan bottom accent bar */}
            <div className="h-1 bg-[#00A3E0] rounded-full mt-3 w-full" />
          </div>
        </div>

        {/* 3. Solved Card */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAEEF4] shadow-xs flex flex-col justify-between relative">
          <div>
            <div className="flex items-center justify-between">
              {/* Green checkmark circle icon */}
              <div className="w-8 h-8 rounded-lg flex items-center justify-center">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00B050" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="9"/>
                  <polyline points="9 12 11 14 15 10"/>
                </svg>
              </div>
            </div>
            <div className="mt-3">
              <div className="text-sm font-semibold text-[#1A202C]">Solved</div>
              <div className="text-[11px] text-[#64748B]">Resolved total</div>
            </div>
          </div>
          
          <div className="mt-4">
            <div className="flex items-baseline gap-3">
              <span className="text-3xl font-black text-[#1A202C] tracking-tight">
                {resolvedCount}
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10.5px] font-bold bg-[#DCFCE7] text-[#15803D] tracking-wide">
                {totalComplaints} total
              </span>
            </div>
            {/* Green bottom accent bar */}
            <div className="h-1 bg-[#00B050] rounded-full mt-3 w-full" />
          </div>
        </div>

        {/* 4. Service Level Radial Ring */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAEEF4] shadow-xs flex flex-col items-center justify-center">
          <div className="relative w-28 h-28 flex items-center justify-center">
            {/* Background & Progress Circle SVG */}
            <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-[#E2E8F0]"
                strokeWidth="3.2"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                stroke="#0047BA"
                strokeDasharray={`${serviceLevelPct}, 100`}
                strokeWidth="3.2"
                strokeLinecap="round"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="absolute flex flex-col items-center text-center">
              <span className="text-[10px] text-[#64748B] font-medium">Resolution Rate</span>
              <span className="text-xl font-black text-[#1A202C] tracking-tight my-0.5">{serviceLevelPct}%</span>
              <span className="text-[9.5px] text-[#64748B]">{resolvedCount}/{totalComplaints} closed</span>
            </div>
          </div>
        </div>

        {/* 5. AI & Feedback Telemetry Card */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAEEF4] shadow-xs flex flex-col items-center justify-center text-center">
          <div className="w-9 h-9 rounded-full flex items-center justify-center text-[#0047BA] mb-1.5">
            <ShieldCheck className="w-7 h-7 text-[#0047BA]" />
          </div>
          <div className="text-xs font-semibold text-[#1A202C]">AI Queries Logged</div>
          <div className="text-[10px] text-[#64748B] mb-2">
            {feedbackStats?.total_feedback ?? 0} citizen reviews
          </div>
          <div className="text-3xl font-black text-[#1A202C] tracking-tight leading-none">
            {ai_statistics?.total_ai_questions ?? 0} <span className="text-xs font-normal text-[#64748B]">queries</span>
          </div>
        </div>

      </div>

      {/* ═══════════════════════════════════════════════
          ROW 2: TOTAL COMPLAINTS AREA CHART
      ═══════════════════════════════════════════════ */}
      <div className="bg-white rounded-2xl p-6 sm:p-7 border border-[#EAEEF4] shadow-xs relative">
        
        {/* Header & Date Range Dropdown */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-[#1A202C] tracking-tight">
              Total Complaints
            </h2>
            <p className="text-xs text-[#64748B] mt-0.5">
              Live complaint volume submitted across citizen and helpdesk portals
            </p>
          </div>

          <div className="relative">
            <span className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl border border-[#E2E8F0] text-xs font-semibold text-[#1A202C] bg-white shadow-2xs">
              <span>{dateRange}</span>
            </span>
          </div>
        </div>

        {/* Chart Container */}
        <div className="h-72 w-full relative">
          {loading ? (
            <div className="h-full flex items-center justify-center text-xs text-[#64748B]">
              Loading live database telemetry...
            </div>
          ) : trendData.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center border border-dashed border-[#E2E8F0] rounded-xl bg-[#F8FAFC] p-6">
              <p className="text-sm font-bold text-[#1A202C]">No Complaints Logged Yet</p>
              <p className="text-xs text-[#64748B] mt-1 max-w-md">
                Data entered by citizens in the User section will sync to MongoDB and appear here automatically in real time.
              </p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData} margin={{ top: 15, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="pendingGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0047BA" stopOpacity={0.35}/>
                    <stop offset="95%" stopColor="#0047BA" stopOpacity={0.02}/>
                  </linearGradient>
                  <linearGradient id="progressGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00A3E0" stopOpacity={0.35}/>
                    <stop offset="95%" stopColor="#00A3E0" stopOpacity={0.02}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fill: '#94A3B8', fontSize: 11 }} 
                  axisLine={{ stroke: '#E2E8F0' }}
                  tickLine={false}
                />
                <YAxis 
                  allowDecimals={false}
                  tick={{ fill: '#94A3B8', fontSize: 11 }} 
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#FFFFFF', 
                    borderColor: '#E2E8F0', 
                    borderRadius: '12px',
                    boxShadow: '0 4px 14px rgba(0,0,0,0.08)',
                    fontSize: '12px'
                  }} 
                />
                <Area 
                  type="monotone" 
                  dataKey="pending" 
                  name="Pending / New"
                  stroke="#0047BA" 
                  strokeWidth={2.4} 
                  fillOpacity={1} 
                  fill="url(#pendingGradient)"
                />
                <Area 
                  type="monotone" 
                  dataKey="inProgress" 
                  name="In Progress / Resolved"
                  stroke="#00A3E0" 
                  strokeWidth={2.4} 
                  fillOpacity={1} 
                  fill="url(#progressGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

      </div>

      {/* ═══════════════════════════════════════════════
          ROW 3: RECENT COMPLAINTS & COMPLAINTS IN CATEGORY
      ═══════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left: Recent Complaints Table */}
        <div className="lg:col-span-7 bg-white rounded-2xl p-6 border border-[#EAEEF4] shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-[#1A202C]">Recent Complaints</h3>
            <span className="text-xs font-semibold text-[#64748B]">{totalComplaints} total</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-[#64748B] font-semibold border-b border-[#EAEEF4]">
                  <th className="py-2.5 font-semibold text-[11px] tracking-wider uppercase">DATE</th>
                  <th className="py-2.5 font-semibold text-[11px] tracking-wider uppercase">CITIZEN NAME</th>
                  <th className="py-2.5 font-semibold text-[11px] tracking-wider uppercase">CATEGORY</th>
                  <th className="py-2.5 font-semibold text-[11px] tracking-wider uppercase text-right">STATUS</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#F8FAFC]">
                {recentComplaints.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-xs text-[#64748B]">
                      No grievances submitted yet. Entries from the Citizen / User portal will appear here automatically.
                    </td>
                  </tr>
                ) : recentComplaints.map((item, idx) => (
                  <tr key={item.id || idx} className="hover:bg-[#F8FAFC] transition">
                    <td className="py-3.5 text-[#64748B] font-normal">{item.date}</td>
                    <td className="py-3.5 text-[#1A202C] font-semibold">{item.name}</td>
                    <td className="py-3.5 text-[#64748B]">{item.category}</td>
                    <td className="py-3.5 text-right">
                      {item.status === 'Closed' && (
                        <span className="inline-flex items-center px-4 py-0.5 rounded-full text-xs font-semibold text-[#00B050] bg-[#DCFCE7]/70 border border-[#00B050]/40">
                          Closed
                        </span>
                      )}
                      {item.status === 'In Progress' && (
                        <span className="inline-flex items-center px-3.5 py-0.5 rounded-full text-xs font-semibold text-[#FF8A00] bg-[#FFF4E5] border border-[#FF8A00]/40">
                          In Progress
                        </span>
                      )}
                      {item.status === 'Open' && (
                        <span className="inline-flex items-center px-4 py-0.5 rounded-full text-xs font-semibold text-[#00A3E0] bg-[#E0F2FE]/50 border border-[#00A3E0]/40">
                          Open
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Complaints in Category */}
        <div className="lg:col-span-5 bg-white rounded-2xl p-6 border border-[#EAEEF4] shadow-xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-[#1A202C]">Complaints in Category</h3>
            <span className="text-xs font-semibold text-[#64748B]">Live Share</span>
          </div>

          {categoryStats.length === 0 ? (
            <div className="py-10 text-center text-xs text-[#64748B] border border-dashed border-[#E2E8F0] rounded-xl bg-[#F8FAFC]">
              Category distribution will populate once grievances are logged.
            </div>
          ) : (
            <div className="space-y-4 pt-1">
              {categoryStats.map((cat, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-bold text-[#1A202C]">
                    <span>{cat.name}</span>
                    <span className="text-[#64748B] font-semibold">{cat.count}</span>
                  </div>
                  {/* Horizontal progress track */}
                  <div className="h-3 w-full bg-[#EAEEF4] rounded-full overflow-hidden flex justify-end">
                    <div 
                      className="h-full rounded-full transition-all duration-500"
                      style={{ 
                        width: `${cat.percent}%`,
                        backgroundColor: cat.color 
                      }}
                    />
                  </div>
                  <div className="text-[11px] text-[#64748B] font-medium text-right">
                    {cat.percent}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

    </div>
  );
};

export default AdminDashboard;
