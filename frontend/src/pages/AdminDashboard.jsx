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

// Trend line data matching the reference image curve exactly
const COMPLAINTS_TREND_DATA = [
  { date: 'Feb 01', pending: 220, inProgress: 140 },
  { date: 'Feb 02', pending: 270, inProgress: 210 },
  { date: 'Feb 03', pending: 250, inProgress: 190 },
  { date: 'Feb 04', pending: 290, inProgress: 200 },
  { date: 'Feb 05', pending: 380, inProgress: 320 },
  { date: 'Feb 06', pending: 350, inProgress: 290 },
  { date: 'Feb 07', pending: 380, inProgress: 310 },
  { date: 'Feb 08', pending: 330, inProgress: 270 },
  { date: 'Feb 09', pending: 340, inProgress: 280 },
  { date: 'Feb 10', pending: 231, inProgress: 180 }, // Highlighted anchor point from image
  { date: 'Feb 11', pending: 300, inProgress: 260 },
  { date: 'Feb 12', pending: 380, inProgress: 310 },
  { date: 'Feb 13', pending: 460, inProgress: 390 },
];

const DEFAULT_RECENT_COMPLAINTS = [
  {
    date: '01 Feb, 2023, 08:21 AM',
    name: 'B. Rajkumar',
    category: 'Amenities Petitions',
    status: 'Open'
  },
  {
    date: '02 Feb, 2023, 12:01 PM',
    name: 'Dev',
    category: 'Borewell & Watersupply',
    status: 'Closed'
  },
  {
    date: '04 Feb, 2023, 06:45 PM',
    name: 'Balu',
    category: 'Bus Stand Maintenance',
    status: 'In Progress'
  },
  {
    date: '05 Feb, 2023, 10:52 AM',
    name: 'Stepen',
    category: 'Canal Cleaning',
    status: 'Open'
  }
];

const CATEGORY_STATS = [
  { name: 'Amenities Petitions', percent: 82, color: '#0047BA' },
  { name: 'Borewell & Watersupply', percent: 32, color: '#FF8A00' },
  { name: 'Bus Stand Maintenance', percent: 32, color: '#00B050' },
  { name: 'Canal Cleaning', percent: 32, color: '#00A3E0' }
];

export const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [recentComplaints, setRecentComplaints] = useState(DEFAULT_RECENT_COMPLAINTS);
  const [dateRange, setDateRange] = useState('Feb 01 - Feb 14');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, complaintsRes] = await Promise.allSettled([
        api.get('/admin/statistics'),
        api.get('/complaints')
      ]);

      if (statsRes.status === 'fulfilled' && statsRes.value?.data) {
        setStats(statsRes.value.data);
      }

      if (complaintsRes.status === 'fulfilled' && Array.isArray(complaintsRes.value?.data) && complaintsRes.value.data.length > 0) {
        const mapped = complaintsRes.value.data.slice(0, 4).map(c => ({
          date: new Date(c.created_at).toLocaleString('en-US', {
            day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
          }),
          name: c.user_name || 'Citizen',
          category: c.category,
          status: c.status === 'RESOLVED' ? 'Closed' : c.status === 'IN_PROGRESS' ? 'In Progress' : 'Open'
        }));
        if (mapped.length >= 3) {
          setRecentComplaints(mapped);
        }
      }
    } catch (err) {
      console.log('Using default reference metrics');
    }
  };

  const { summary } = stats || {};

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
              <span className="px-2.5 py-0.5 rounded-full text-[10.5px] font-bold bg-[#F07167] text-white tracking-wide">
                +70%
              </span>
            </div>
            <div className="mt-3">
              <div className="text-sm font-semibold text-[#1A202C]">Pending</div>
              <div className="text-[11px] text-[#64748B]">Last 7 days</div>
            </div>
          </div>
          
          <div className="mt-4">
            <div className="text-3xl font-black text-[#1A202C] tracking-tight">
              {summary?.pending_complaints ?? 9}
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
              <span className="px-2.5 py-0.5 rounded-full text-[10.5px] font-bold bg-[#0284C7] text-white tracking-wide">
                +20%
              </span>
            </div>
            <div className="mt-3">
              <div className="text-sm font-semibold text-[#1A202C]">In Progress</div>
              <div className="text-[11px] text-[#64748B]">Last 7 days</div>
            </div>
          </div>
          
          <div className="mt-4">
            <div className="text-3xl font-black text-[#1A202C] tracking-tight">
              {summary?.in_progress_complaints ?? 2}
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
              <div className="text-[11px] text-[#64748B]">Last 7 days</div>
            </div>
          </div>
          
          <div className="mt-4">
            <div className="flex items-baseline gap-3">
              <span className="text-3xl font-black text-[#1A202C] tracking-tight">
                {summary?.resolved_complaints ?? 1}
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10.5px] font-bold bg-[#00B050] text-white tracking-wide">
                +1%
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
                strokeDasharray="76.5, 100"
                strokeWidth="3.2"
                strokeLinecap="round"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="absolute flex flex-col items-center text-center">
              <span className="text-[10px] text-[#64748B] font-medium">Service Level</span>
              <span className="text-xl font-black text-[#1A202C] tracking-tight my-0.5">76.5%</span>
              <span className="text-[9.5px] text-[#64748B]">Target 75%</span>
            </div>
          </div>
        </div>

        {/* 5. Feedback Rating Card */}
        <div className="bg-white rounded-2xl p-5 border border-[#EAEEF4] shadow-xs flex flex-col items-center justify-center text-center">
          <div className="w-9 h-9 rounded-full flex items-center justify-center text-[#0047BA] mb-1.5">
            <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#0047BA" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
              <line x1="9" y1="9" x2="9.01" y2="9" strokeWidth="2.5"/>
              <line x1="15" y1="9" x2="15.01" y2="9" strokeWidth="2.5"/>
            </svg>
          </div>
          <div className="text-xs font-semibold text-[#1A202C]">Feedback Rating</div>
          <div className="text-[10px] text-[#64748B] mb-2">All time</div>
          <div className="text-3xl font-black text-[#1A202C] tracking-tight leading-none">
            4.6 <span className="text-sm font-normal text-[#64748B]">of 5</span>
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
              Daily complaint volume across all panchayat wards
            </p>
          </div>

          <div className="relative">
            <button className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl border border-[#E2E8F0] text-xs font-semibold text-[#1A202C] bg-white hover:bg-[#F8FAFC] transition shadow-2xs">
              <span>{dateRange}</span>
              <ChevronDown className="w-3.5 h-3.5 text-[#64748B]" />
            </button>
          </div>
        </div>

        {/* Chart Container */}
        <div className="h-72 w-full relative">
          
          {/* Floating Legend / Stat Callout matching exact location at Feb 10 in image */}
          <div className="absolute right-20 sm:right-28 top-8 z-10 bg-white/95 backdrop-blur-xs rounded-xl border border-[#E2E8F0] px-4 py-2.5 shadow-sm space-y-1.5 pointer-events-none">
            <div className="flex items-center justify-between gap-6 text-xs">
              <span className="flex items-center gap-2 text-[#475569] font-medium">
                <span className="w-3 h-0.5 bg-[#0047BA] inline-block rounded-full" />
                Pending
              </span>
              <span className="text-[#1A202C] font-black">231</span>
            </div>
            <div className="flex items-center justify-between gap-6 text-xs">
              <span className="flex items-center gap-2 text-[#475569] font-medium">
                <span className="w-3 h-0.5 bg-[#00A3E0] inline-block rounded-full" />
                In Progress
              </span>
              <span className="text-[#1A202C] font-black">43</span>
            </div>
          </div>

          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={COMPLAINTS_TREND_DATA} margin={{ top: 15, right: 10, left: -10, bottom: 0 }}>
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
                domain={[0, 500]}
                ticks={[0, 100, 200, 300, 400, 500]}
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
                stroke="#0047BA" 
                strokeWidth={2.4} 
                fillOpacity={1} 
                fill="url(#pendingGradient)"
              />
              <Area 
                type="monotone" 
                dataKey="inProgress" 
                stroke="#00A3E0" 
                strokeWidth={2.4} 
                fillOpacity={1} 
                fill="url(#progressGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
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
            <button className="text-[#94A3B8] hover:text-[#1A202C] p-1">
              <MoreVertical className="w-4 h-4" />
            </button>
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
                {recentComplaints.map((item, idx) => (
                  <tr key={idx} className="hover:bg-[#F8FAFC] transition">
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
            <button className="text-[#94A3B8] hover:text-[#1A202C] p-1">
              <MoreVertical className="w-4 h-4" />
            </button>
          </div>

          <div className="space-y-4 pt-1">
            {CATEGORY_STATS.map((cat, idx) => (
              <div key={idx} className="space-y-1">
                <div className="text-xs font-bold text-[#1A202C]">
                  {cat.name}
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
        </div>

      </div>

    </div>
  );
};

export default AdminDashboard;
