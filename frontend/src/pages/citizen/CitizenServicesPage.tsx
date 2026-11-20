import React, { useState } from 'react';
import { Building2, FileText, CheckCircle2, ShieldCheck, ArrowRight, Search, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

const SERVICES = [
  {
    title: 'Gramin Housing Scheme (PMAY-G)',
    dept: 'Public Health & Schemes',
    description: 'Financial subsidy of Rs 1,20,000 for plain areas and Rs 1,30,000 for hilly areas for pucca house construction.',
    eligibility: 'Homeless households or living in zero/one/two room kucha houses per SECC data.',
    documents: 'Aadhaar Card, Job Card, Bank Account passbook, land ownership document.',
    source: 'Gram Panchayat Secretariat Notice Board',
    sampleQuestion: 'What are the eligibility criteria and subsidy amount for PMAY-G housing in our village?'
  },
  {
    title: 'Drinking Water Pipeline Supply & Leak Repairs',
    dept: 'Village Water Department',
    description: 'Drinking water supplied twice daily (6:00-9:00 AM & 5:00-7:00 PM). Pipeline leaks repaired within 24-48 hours.',
    eligibility: 'All resident households in Wards 1 through 4.',
    documents: 'Grievance ticket ID or oral submission at ward tap committee.',
    source: 'Water Supply Citizen Charter 2026',
    sampleQuestion: 'What are the daily drinking water supply timings for Ward 4?'
  },
  {
    title: 'Door-to-Door Garbage Collection & Composting',
    dept: 'Sanitation & Waste Management',
    description: 'Daily collection of wet organic waste (green bin) and dry recyclable waste (blue bin) between 7:00 AM and 10:00 AM.',
    eligibility: 'All Gram Panchayat Chandanpur households.',
    documents: 'Ward residence registration.',
    source: 'Gram Panchayat Sanitation Guidelines',
    sampleQuestion: 'What is the schedule and segregation rule for garbage collection?'
  },
  {
    title: 'Agricultural Power Connection & Transformer Service',
    dept: 'Electricity & Power Supply Board',
    description: 'Dedicated 8-hour uninterrupted agricultural power supply with free transformer fuse replacement under 12 hours.',
    eligibility: 'Farmers with verified land title deeds and agricultural pump meter.',
    documents: 'Khasra/Khatauni land record, electricity meter passbook.',
    source: 'Rural Electrification Charter',
    sampleQuestion: 'How many hours of agricultural electricity are provided to village farmers?'
  },
  {
    title: 'Village Road Maintenance & Drain Clearing',
    dept: 'Roads & Public Works Department',
    description: 'Annual monsoon pre-cleaning of storm drains and pothole patching of main paved village roads within 7 days of notice.',
    eligibility: 'All village residents and community elders.',
    documents: 'Photographic evidence with GPS or landmark detail.',
    source: 'Panchayat Works Directive 2026',
    sampleQuestion: 'Who is responsible for cleaning blocked storm drains in Ward 2?'
  }
];

export const CitizenServicesPage: React.FC = () => {
  const [search, setSearch] = useState('');

  const filtered = SERVICES.filter(s => 
    s.title.toLowerCase().includes(search.toLowerCase()) ||
    s.dept.toLowerCase().includes(search.toLowerCase()) ||
    s.description.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6 p-4 sm:p-8 max-w-7xl mx-auto">
      
      {/* Editorial Header */}
      <div className="civic-card p-6 sm:p-8 border-l-4 border-l-[#153D32] flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#DDE8DD] text-[#153D32] text-xs font-bold uppercase tracking-wider">
            <ShieldCheck className="w-3.5 h-3.5" /> Official Citizen Charters
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#17221F] tracking-tight">
            Gram Panchayat Verified Services & Schemes
          </h1>
          <p className="text-sm text-[#69736D] max-w-2xl leading-relaxed">
            Transparent service delivery timelines, eligibility criteria, and required documentation ground our AI reasoning models to prevent citizen misinformation.
          </p>
        </div>

        <Link
          to="/citizen/ai-assistant"
          className="btn-civic-primary self-start md:self-auto flex items-center gap-2"
        >
          <Sparkles className="w-4 h-4 text-[#D7F36A]" /> Query AI Assistant
        </Link>
      </div>

      {/* Search Input */}
      <div className="civic-card p-4 sm:p-5">
        <div className="relative max-w-md">
          <Search className="w-4 h-4 text-[#69736D] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search village schemes, charters, or services..."
            className="w-full pl-10 pr-4 py-2 text-sm bg-white border border-[#E5E7DF] rounded-xl text-[#17221F] placeholder-[#69736D] focus:outline-none focus:border-[#153D32]"
          />
        </div>
      </div>

      {/* Grid of Services */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((s, i) => (
          <div key={i} className="civic-card p-6 flex flex-col justify-between space-y-4 hover:shadow-md transition">
            <div className="space-y-3">
              <span className="text-[11px] uppercase font-bold px-2.5 py-1 rounded-md bg-[#DDE8DD] text-[#153D32]">
                {s.dept}
              </span>
              <h3 className="text-base font-bold text-[#17221F] leading-snug">{s.title}</h3>
              <p className="text-xs text-[#69736D] leading-relaxed">{s.description}</p>
              
              <div className="space-y-2 text-xs pt-3 border-t border-[#E5E7DF]">
                <div>
                  <span className="font-bold text-[#17221F]">Eligibility:</span>{' '}
                  <span className="text-[#69736D]">{s.eligibility}</span>
                </div>
                <div>
                  <span className="font-bold text-[#17221F]">Required Documents:</span>{' '}
                  <span className="text-[#69736D]">{s.documents}</span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-[#E5E7DF] flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 text-[#15803D] font-bold">
                <ShieldCheck className="w-4 h-4 text-[#15803D]" /> {s.source}
              </span>
              <Link 
                to={`/citizen/ai-assistant?q=${encodeURIComponent(s.sampleQuestion)}`} 
                className="font-bold text-[#153D32] hover:text-[#17221F] inline-flex items-center gap-1 transition"
              >
                Ask AI <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CitizenServicesPage;
