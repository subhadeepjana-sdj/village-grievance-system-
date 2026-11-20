import React from 'react';
import { Link } from 'react-router-dom';
import { Building2, ShieldCheck, Cpu, ExternalLink, FileCheck2, Scale, Heart } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="border-t border-[#E5E7DF] bg-[#FFFFFF] text-[#69736D] text-xs pt-12 pb-8 px-4 sm:px-6 lg:px-8 mt-auto">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Main Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          
          {/* Col 1: Brand & Academic Statement */}
          <div className="space-y-3 md:col-span-1">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[#153D32] text-[#D7F36A] flex items-center justify-center font-bold">
                <Building2 className="w-4 h-4 text-[#D7F36A]" />
              </div>
              <span className="font-heading font-extrabold text-sm text-[#17221F]">Civic Intelligence</span>
            </div>
            <p className="text-[#69736D] leading-relaxed text-xs">
              Evidence-grounded language model architecture designed for fact-verified grievance redressal and rural Gram Panchayat transparency.
            </p>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#EFF5EF] text-[#153D32] text-[11px] font-semibold">
              <ShieldCheck className="w-3.5 h-3.5" /> Academic Research Prototype
            </div>
          </div>

          {/* Col 2: Citizen Services */}
          <div className="space-y-2.5">
            <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-[#17221F]">
              Citizen Services
            </h4>
            <ul className="space-y-1.5">
              <li>
                <Link to="/submit" className="hover:text-[#153D32] transition">Submit Grievance</Link>
              </li>
              <li>
                <Link to="/track" className="hover:text-[#153D32] transition">Track Grievance Status</Link>
              </li>
              <li>
                <Link to="/ai-assistant" className="hover:text-[#153D32] transition">Ask AI Assistant</Link>
              </li>
              <li>
                <Link to="/knowledge-base" className="hover:text-[#153D32] transition">Citizen Service Charters</Link>
              </li>
            </ul>
          </div>

          {/* Col 3: Research & Verification */}
          <div className="space-y-2.5">
            <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-[#17221F]">
              Research & Governance
            </h4>
            <ul className="space-y-1.5">
              <li>
                <Link to="/research" className="hover:text-[#153D32] transition">Research Dashboard</Link>
              </li>
              <li>
                <a href="#verification-showcase" className="hover:text-[#153D32] transition">NLI Hallucination Verification</a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-[#153D32] transition">Hybrid RAG Pipeline</a>
              </li>
              <li>
                <Link to="/admin/dashboard" className="hover:text-[#153D32] transition">Admin Operations</Link>
              </li>
            </ul>
          </div>

          {/* Col 4: Trust & Transparency Disclaimer */}
          <div className="space-y-2.5">
            <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-[#17221F]">
              Trust & Transparency
            </h4>
            <p className="text-[11px] leading-relaxed text-[#69736D]">
              This application is an educational and academic research prototype for demonstrating hallucination-free retrieval in civic public services. It is not an official government seal nor does it claim official endorsement.
            </p>
            <div className="pt-1 flex items-center gap-3 text-[#153D32]">
              <span className="flex items-center gap-1 font-semibold text-[11px]">
                <FileCheck2 className="w-3.5 h-3.5" /> 100% Grounded
              </span>
              <span className="flex items-center gap-1 font-semibold text-[11px]">
                <Scale className="w-3.5 h-3.5" /> Open Civic Tech
              </span>
            </div>
          </div>

        </div>

        {/* Bottom Sub-strip */}
        <div className="border-t border-[#E5E7DF] pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-[#69736D]">
          <div>
            © 2026 Civic Intelligence Research Project. Dedicated to transparent village governance.
          </div>
          <div className="flex items-center gap-4">
            <span className="hover:text-[#17221F] cursor-pointer">Privacy Notice</span>
            <span>•</span>
            <span className="hover:text-[#17221F] cursor-pointer">Accessibility (WCAG 2.2 AA)</span>
            <span>•</span>
            <span className="hover:text-[#17221F] cursor-pointer">Model Cards</span>
          </div>
        </div>

      </div>
    </footer>
  );
};

export default Footer;
