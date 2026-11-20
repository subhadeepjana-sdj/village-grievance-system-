import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import GeoCivicLogo from './GeoCivicLogo';
import { 
  Menu, 
  X, 
  Search, 
  Bell, 
  Settings, 
  LogOut, 
  LogIn, 
  PlusCircle, 
  Sparkles, 
  FileText,
  ShieldCheck 
} from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleLogout = () => {
    logout();
    setMobileMenuOpen(false);
    navigate('/login');
  };

  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/' || path === '/dashboard' || path === '/admin/dashboard') return 'Overview';
    if (path.includes('/panchayat')) return 'Panchayat Operations';
    if (path.includes('/department')) return 'Department Queue';
    if (path.includes('/submit')) return 'File Grievance';
    if (path.includes('/track')) return 'Track Complaints';
    if (path.includes('/ai-assistant')) return 'AI Assistant & Evidence';
    if (path.includes('/research')) return 'Research Telemetry';
    if (path.includes('/knowledge-base')) return 'Knowledge Base';
    if (path.includes('/login')) return 'System Login';
    if (path.includes('/register')) return 'Citizen Registration';
    return 'Overview';
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    navigate(`/track?q=${encodeURIComponent(searchQuery.trim())}`);
  };

  // If user is authenticated (e.g. Divya Prasad / Admin), show executive dashboard top bar
  if (user) {
    return (
      <header className="sticky top-0 z-40 w-full min-h-[4rem] bg-[#F0F4F9] px-8 py-4 flex items-center justify-between border-b border-slate-200/70 gap-6">
        
        {/* Left: Hamburger + Page Title ("Panchayat Operations") + Search Input */}
        <div className="flex items-center gap-5 min-w-0 flex-1">
          <button 
            className="p-1.5 text-[#1A202C] hover:text-[#0047BA] transition shrink-0"
            aria-label="Toggle navigation"
          >
            <Menu className="w-5 h-5 stroke-[2.2]" />
          </button>

          <h1 className="text-lg sm:text-xl font-bold text-slate-900 tracking-tight shrink-0 whitespace-nowrap">
            {getPageTitle()}
          </h1>

          {/* Search Pill Input with responsive spacing */}
          <form onSubmit={handleSearchSubmit} className="hidden lg:block flex-1 max-w-xs">
            <div className="relative">
              <Search className="w-4 h-4 text-[#8291A5] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search complaints, ward, or citizen..."
                className="w-full pl-9 pr-4 py-2 text-xs bg-[#E5ECF6] border border-transparent rounded-full text-[#1A202C] placeholder-[#8291A5] focus:outline-none focus:border-[#0047BA] focus:bg-white transition"
              />
            </div>
          </form>
        </div>

        {/* Right: Notifications, Settings, Profile */}
        <div className="flex items-center gap-4 shrink-0">
          
          {/* Notification Bell with Gold/Yellow badge '12' */}
          <Link 
            to="/panchayat/dashboard" 
            className="relative p-2 rounded-full text-[#1A202C] hover:text-[#0047BA] hover:bg-white/80 transition"
            title="12 Active Grievance Alerts"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute -top-0.5 -right-0.5 min-w-[1.2rem] h-[1.2rem] px-1 bg-[#F59E0B] text-[#1A202C] font-black text-[10px] rounded-full flex items-center justify-center shadow-xs">
              12
            </span>
          </Link>

          {/* Settings Icon */}
          <Link 
            to="/admin/ai-monitoring" 
            className="p-2 rounded-full text-[#1A202C] hover:text-[#0047BA] hover:bg-white/80 transition"
            title="Settings"
          >
            <Settings className="w-5 h-5" />
          </Link>

          {/* User Profile matching Divya Prasad Admin */}
          <div className="flex items-center gap-3 pl-2 sm:pl-3">
            <div className="w-9 h-9 rounded-full overflow-hidden ring-2 ring-white shadow-xs bg-slate-200 shrink-0">
              <img 
                src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80" 
                alt={user.name || "Divya Prasad"} 
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            </div>
            <div className="hidden sm:block leading-tight text-left">
              <span className="font-bold text-xs text-[#1A202C] block">
                {user.name || "Divya Prasad"}
              </span>
              <span className="text-[11px] text-[#64748B] block">
                {user.role === 'ADMIN' ? 'Admin' : (user.role || 'Admin').toLowerCase().replace('_', ' ')}
              </span>
            </div>
          </div>

        </div>

      </header>
    );
  }

  // Public visitor header
  return (
    <header className="sticky top-0 z-40 w-full h-16 bg-white border-b border-[#E2E8F0] px-4 sm:px-6 lg:px-8 shadow-xs flex items-center">
      <div className="w-full max-w-7xl mx-auto flex items-center justify-between gap-4">
        
        {/* Left Section */}
        <div className="flex items-center gap-4 sm:gap-6 shrink-0">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-xl text-[#64748B] hover:text-[#0047BA] hover:bg-[#F0F4F9] transition lg:hidden"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-[#0047BA] to-[#00368C] p-1 flex items-center justify-center shadow-xs group-hover:scale-105 transition-transform">
              <GeoCivicLogo className="w-7 h-7" />
            </div>
            <div className="leading-tight">
              <span className="font-heading font-black text-lg text-[#0047BA] tracking-tight block">
                GEO CIVIC
              </span>
              <span className="text-[10px] font-semibold text-[#64748B] tracking-wider uppercase block">
                Civic Redressal
              </span>
            </div>
          </Link>

          <nav className="hidden lg:flex items-center gap-1 ml-2">
            <Link
              to="/admin/dashboard"
              className="px-3 py-1.5 text-xs font-semibold rounded-lg text-[#0047BA] bg-[#E8F0FE] hover:bg-[#D7E4FC] transition"
            >
              Dashboard
            </Link>
            <Link
              to="/knowledge-base"
              className="px-3 py-1.5 text-xs font-semibold rounded-lg text-[#475569] hover:text-[#0047BA] hover:bg-[#F8FAFC] transition"
            >
              Knowledge Base
            </Link>
            <Link
              to="/research"
              className="px-3 py-1.5 text-xs font-semibold rounded-lg text-[#475569] hover:text-[#0047BA] hover:bg-[#F8FAFC] transition"
            >
              Research
            </Link>
            <Link
              to="/ai-assistant"
              className="px-3 py-1.5 text-xs font-semibold rounded-lg text-[#475569] hover:text-[#0047BA] hover:bg-[#F8FAFC] transition flex items-center gap-1"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#00A3E0]" /> AI Assistant
            </Link>
          </nav>
        </div>

        {/* Center: Search Bar */}
        <form onSubmit={handleSearchSubmit} className="flex-1 max-w-sm sm:max-w-md mx-2">
          <div className="relative">
            <Search className="w-4 h-4 text-[#94A3B8] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search complaints, ward, or citizen..."
              className="w-full pl-9 pr-4 py-1.5 text-xs sm:text-sm bg-[#F1F5F9] border border-transparent rounded-full text-[#1A202C] placeholder-[#94A3B8] focus:outline-none focus:border-[#0047BA] focus:bg-white transition"
            />
          </div>
        </form>

        {/* Right Section */}
        <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
          <Link
            to="/admin/dashboard"
            className="inline-flex items-center gap-1 px-3.5 py-1.5 text-xs font-bold text-white bg-[#0047BA] hover:bg-[#00368C] rounded-full transition shadow-xs"
          >
            <span>Live Dashboard</span>
          </Link>
          <Link
            to="/login"
            className="inline-flex items-center gap-1 px-3.5 py-1.5 text-xs font-bold text-[#0047BA] bg-[#E8F0FE] hover:bg-[#D7E4FC] rounded-full transition"
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Login</span>
          </Link>
        </div>

      </div>
    </header>
  );
};

export default Navbar;
