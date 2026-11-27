import React, { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import GeoCivicLogo from "./GeoCivicLogo";

// ─── Crisp SVG Icons ──────────────────────────────────────────

const DashboardIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>
    <rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>
  </svg>
);

const LiveMonitorIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="3" width="20" height="14" rx="2.5"/>
    <path d="M8 21h8M12 17v4"/>
    <path d="M6 10l3 3 3-4 3 3 3-3" strokeWidth="1.6"/>
  </svg>
);

const AlertsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
    <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
    <circle cx="18" cy="4" r="3" fill="#F59E0B" stroke="#0047BA" strokeWidth="1.5"/>
  </svg>
);

const ComplaintsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <line x1="9" y1="13" x2="15" y2="13"/>
    <line x1="9" y1="17" x2="13" y2="17"/>
  </svg>
);

const TrackIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    <circle cx="11" cy="11" r="3" strokeWidth="1.2"/>
  </svg>
);

const DepartmentsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="17" rx="2"/>
    <line x1="9" y1="4" x2="9" y2="21"/>
    <line x1="15" y1="4" x2="15" y2="21"/>
    <line x1="3" y1="9" x2="21" y2="9"/>
    <line x1="3" y1="15" x2="21" y2="15"/>
  </svg>
);

const AnalyticsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
    <line x1="6" y1="20" x2="6" y2="14"/><line x1="3" y1="20" x2="21" y2="20"/>
    <polyline points="3 10 9 5 14 9 21 2" strokeWidth="1.8"/>
  </svg>
);

const AIVerifyIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    <path d="M9 12l2 2 4-4" strokeWidth="2"/>
  </svg>
);

const RagIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="4" width="16" height="16" rx="2"/>
    <rect x="9" y="9" width="6" height="6"/>
    <line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/>
    <line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/>
    <line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/>
    <line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>
  </svg>
);

const KnowledgeBaseIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="12" cy="5" rx="9" ry="3"/>
    <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>
    <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
  </svg>
);

const FeedbackIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="15" x2="12.01" y2="15" strokeWidth="2.5"/>
  </svg>
);

const ResearchIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10 2v7.31M14 2v7.31M8.5 2h7M14 9.3a6.5 6.5 0 1 1-4 0"/>
    <circle cx="12" cy="15" r="1.5" fill="currentColor"/>
  </svg>
);

const ExperimentsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/>
    <line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/>
    <line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/>
    <line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>
  </svg>
);

const DatasetIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 2 7 12 12 22 7 12 2"/>
    <polyline points="2 17 12 22 22 17"/>
    <polyline points="2 12 12 17 22 12"/>
  </svg>
);

const EvalReportsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
    <circle cx="12" cy="14" r="3"/>
    <path d="M10 16.5l-1 3.5 3-1.5 3 1.5-1-3.5"/>
  </svg>
);

const UsersIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
);

const SecurityIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
  </svg>
);

const SettingsIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
  </svg>
);

const LogoutIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
    <polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
);

// ─── Clean Data Arrays without hardcoded active states ─────────

const NAVIGATION_SECTIONS = [
  {
    category: "OVERVIEW",
    items: [
      { name: "Dashboard",              label: "Dashboard",              to: "/admin/dashboard",     Icon: DashboardIcon },
      { name: "Live Monitoring",        label: "Live Monitoring",        to: "/admin/ai-monitoring", Icon: LiveMonitorIcon },
      { name: "Notifications & Alerts", label: "Notifications & Alerts", to: "/panchayat/dashboard", Icon: AlertsIcon, badge: "12" },
    ]
  },
  {
    category: "GRIEVANCE OPERATIONS",
    items: [
      { name: "Complaints",                label: "Complaints",                to: "/panchayat/dashboard", Icon: ComplaintsIcon },
      { name: "Track Grievance",           label: "Track Grievance",           to: "/track",               Icon: TrackIcon },
      { name: "Departments & Escalations", label: "Departments & Escalations", to: "/department/dashboard",Icon: DepartmentsIcon },
      { name: "Reports & Analytics",       label: "Reports & Analytics",       to: "/research",            Icon: AnalyticsIcon },
    ]
  },
  {
    category: "AI INTELLIGENCE",
    items: [
      { name: "AI Verification Center",      label: "AI Verification Center",      to: "/admin/ai-monitoring", Icon: AIVerifyIcon },
      { name: "Model & RAG Management",      label: "Model & RAG Management",      to: "/admin/knowledge-base",Icon: RagIcon },
      { name: "Knowledge Base",              label: "Knowledge Base",              to: "/knowledge-base",      Icon: KnowledgeBaseIcon },
      { name: "AI Feedback & Error Review", label: "AI Feedback & Error Review", to: "/ai-assistant",        Icon: FeedbackIcon },
    ]
  },
  {
    category: "RESEARCH & EVALUATION",
    items: [
      { name: "Research Dashboard",             label: "Research Dashboard",             to: "/research",           Icon: ResearchIcon },
      { name: "Experiments & Model Comparison", label: "Experiments & Model Comparison", to: "/research/dashboard", Icon: ExperimentsIcon },
      { name: "Evaluation Dataset",             label: "Evaluation Dataset",             to: "/knowledge-base",     Icon: DatasetIcon },
      { name: "Evaluation Reports",             label: "Evaluation Reports",             to: "/research",           Icon: EvalReportsIcon },
    ]
  },
  {
    category: "ADMINISTRATION",
    items: [
      { name: "Users & Roles",          label: "Users & Roles",          to: "/admin/dashboard",     Icon: UsersIcon },
      { name: "Audit Logs & Security",  label: "Audit Logs & Security",  to: "/admin/ai-monitoring", Icon: SecurityIcon },
      { name: "Platform Settings",      label: "Platform Settings",      to: "/admin/ai-monitoring", Icon: SettingsIcon },
    ]
  }
];

const CITIZEN_NAVIGATION_SECTIONS = [
  {
    category: "CITIZEN PORTAL",
    items: [
      { name: "Citizen Dashboard", label: "Dashboard",        to: "/citizen/dashboard",    Icon: DashboardIcon },
      { name: "File Grievance",    label: "File Grievance",   to: "/submit",               Icon: ComplaintsIcon },
      { name: "Track Grievance",   label: "Track Complaints", to: "/track",                Icon: TrackIcon },
    ]
  },
  {
    category: "SERVICES & AI HELP",
    items: [
      { name: "AI Assistant",      label: "AI Assistant",     to: "/ai-assistant",         Icon: FeedbackIcon },
      { name: "Knowledge Base",    label: "Knowledge Base",   to: "/knowledge-base",       Icon: KnowledgeBaseIcon },
      { name: "Village Services",  label: "Village Services", to: "/citizen/services",     Icon: DepartmentsIcon },
    ]
  }
];

const Sidebar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const isCitizen = user?.role === "CITIZEN";
  const sections = isCitizen ? CITIZEN_NAVIGATION_SECTIONS : NAVIGATION_SECTIONS;

  const resolveActiveTab = (path, citizenMode) => {
    if (citizenMode) {
      if (path.includes("/submit") || path.includes("/complaints/new")) return "File Grievance";
      if (path.includes("/track")) return "Track Grievance";
      if (path.includes("/ai-assistant")) return "AI Assistant";
      if (path.includes("/knowledge-base")) return "Knowledge Base";
      if (path.includes("/citizen/services")) return "Village Services";
      return "Citizen Dashboard";
    }
    if (path === "/admin/ai-monitoring") return "Live Monitoring";
    if (path === "/panchayat/dashboard") return "Complaints";
    if (path === "/track") return "Track Grievance";
    if (path === "/department/dashboard") return "Departments & Escalations";
    if (path === "/research") return "Reports & Analytics";
    if (path === "/research/dashboard") return "Experiments & Model Comparison";
    if (path === "/knowledge-base") return "Knowledge Base";
    if (path === "/ai-assistant") return "AI Feedback & Error Review";
    return "Dashboard";
  };

  // 1. Unified State: Single activeTab state variable tracking the active item globally
  const [activeTab, setActiveTab] = useState(() => resolveActiveTab(window.location.pathname, user?.role === "CITIZEN"));

  useEffect(() => {
    setActiveTab(resolveActiveTab(location.pathname, isCitizen));
  }, [location.pathname, isCitizen]);

  return (
    <aside style={{
      width: "250px", minWidth: "250px",
      background: "linear-gradient(180deg, #0047BA 0%, #00368C 100%)",
      display: "flex", flexDirection: "column",
      height: "100vh", maxHeight: "100vh",
      borderTopRightRadius: "30px", borderBottomRightRadius: "30px",
      boxShadow: "4px 0 24px rgba(0, 71, 186, 0.25)",
      position: "sticky", top: 0, zIndex: 30, overflow: "visible",
    }}>
      
      {/* ─── Top Brand: GEO CIVIC . Civic Intelligence ─── */}
      <div style={{ padding: "22px 18px 16px 18px", borderBottom: "1px solid rgba(255, 255, 255, 0.1)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{
            width: "44px", height: "44px",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0,
          }}>
            <GeoCivicLogo className="w-11 h-11" />
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <div style={{ 
              fontSize: "19px", fontWeight: 900, color: "#FFFFFF", 
              letterSpacing: "0.5px", lineHeight: 1.1, 
              fontFamily: "'Plus Jakarta Sans', sans-serif" 
            }}>
              GEO CIVIC
            </div>
            <div style={{ 
              fontSize: "11px", fontWeight: 600, color: "#38BDF8", 
              letterSpacing: "0.3px", marginTop: "2px", display: "flex", alignItems: "center", gap: "4px"
            }}>
              <span>•</span> Civic Intelligence
            </div>
          </div>
        </div>

        {/* Sub-label: ADMINISTRATION & AI RESEARCH */}
        <div style={{ marginTop: "12px" }}>
          <div style={{
            display: "inline-block",
            fontSize: "9px", fontWeight: 800, letterSpacing: "1.2px",
            textTransform: "uppercase",
            color: "#E0F2FE",
            background: "rgba(255, 255, 255, 0.12)",
            border: "1px solid rgba(56, 189, 248, 0.3)",
            padding: "3px 8px", borderRadius: "6px"
          }}>
            {isCitizen ? "CITIZEN PORTAL & SERVICES" : "ADMINISTRATION & AI RESEARCH"}
          </div>
        </div>
      </div>

      {/* ─── Categorized Navigation List (Scrollable) ─── */}
      <nav 
        style={{ 
          flex: 1, 
          padding: "6px 0 16px 0", 
          overflowY: "auto",
          overflowX: "hidden"
        }}
        className="gis-sidebar-scroll"
      >
        {sections.map((section, sIdx) => (
          <div key={section.category} style={{ marginTop: sIdx === 0 ? "4px" : "10px" }}>
            
            {/* Category Header */}
            <div style={{
              fontSize: "10px", fontWeight: 800, letterSpacing: "1.4px",
              textTransform: "uppercase",
              color: "rgba(186, 230, 253, 0.75)",
              padding: "8px 20px 4px 20px",
              fontFamily: "'Plus Jakarta Sans', sans-serif"
            }}>
              {section.category}
            </div>

            {/* Section Items */}
            {section.items.map((item) => {
              // 4. Strict Conditional Styling: strictly checks activeTab === item.name
              const isMatch = activeTab === item.name;

              return (
                <Link
                  key={item.name} 
                  to={item.to} 
                  // 3. Fix Click/Routing Logic: clicking an item cleanly sets it as the ONLY active tab
                  onClick={() => setActiveTab(item.name)}
                  style={{
                    display: "flex", alignItems: "center", gap: "11px",
                    padding: "9px 0 9px 18px",
                    margin: isMatch ? "2px 0 2px 10px" : "2px 0",
                    textDecoration: "none",
                    background: isMatch ? "#F0F4F9" : "transparent",
                    borderRadius: isMatch ? "20px 0 0 20px" : "0",
                    color: isMatch ? "#0047BA" : "rgba(255, 255, 255, 0.85)",
                    fontWeight: isMatch ? 700 : 500,
                    fontSize: "12.5px", fontFamily: "'Inter', sans-serif",
                    transition: "all 0.15s ease",
                    position: "relative",
                  }}
                  className={!isMatch ? "hover:bg-white/10 hover:text-white" : ""}
                >
                  {/* Curved Inverted Radius for Active Tab into #F0F4F9 */}
                  {isMatch && (
                    <>
                      <span style={{
                        position: "absolute", top: "-18px", right: 0,
                        width: "18px", height: "18px",
                        background: "transparent",
                        borderBottomRightRadius: "18px",
                        boxShadow: "7px 7px 0 7px #F0F4F9",
                        pointerEvents: "none",
                      }}/>
                      <span style={{
                        position: "absolute", bottom: "-18px", right: 0,
                        width: "18px", height: "18px",
                        background: "transparent",
                        borderTopRightRadius: "18px",
                        boxShadow: "7px -7px 0 7px #F0F4F9",
                        pointerEvents: "none",
                      }}/>
                    </>
                  )}
                  <span style={{ 
                    color: isMatch ? "#0047BA" : "rgba(255, 255, 255, 0.75)", 
                    display: "flex", alignItems: "center", flexShrink: 0 
                  }}>
                    <item.Icon />
                  </span>
                  <span style={{ flex: 1, paddingRight: "8px", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {item.label}
                  </span>
                  {item.badge && (
                    <span style={{
                      marginRight: "14px",
                      background: isMatch ? "#FF8A00" : "#F59E0B",
                      color: isMatch ? "#FFFFFF" : "#1A202C",
                      fontSize: "10px", fontWeight: 800,
                      padding: "1px 6px", borderRadius: "9999px"
                    }}>
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}

          </div>
        ))}
      </nav>

      {/* ─── Bottom Actions (Logout) ─── */}
      <div style={{ 
        padding: "10px 14px 14px 14px", 
        borderTop: "1px solid rgba(255, 255, 255, 0.12)" 
      }}>
        <button 
          onClick={() => { logout(); navigate("/login"); }}
          style={{
            display: "flex", alignItems: "center", gap: "10px",
            width: "100%", padding: "9px 14px",
            border: "none", background: "rgba(255, 255, 255, 0.08)",
            color: "rgba(255, 255, 255, 0.8)", fontSize: "12.5px",
            fontFamily: "'Inter', sans-serif", cursor: "pointer", textAlign: "left",
            borderRadius: "10px", transition: "all 0.15s ease",
          }}
          onMouseEnter={e => {
            e.currentTarget.style.color = "#FECACA";
            e.currentTarget.style.background = "rgba(239, 68, 68, 0.2)";
          }}
          onMouseLeave={e => {
            e.currentTarget.style.color = "rgba(255, 255, 255, 0.8)";
            e.currentTarget.style.background = "rgba(255, 255, 255, 0.08)";
          }}
        >
          <LogoutIcon />
          <span style={{ fontWeight: 600 }}>Sign Out</span>
        </button>
      </div>

    </aside>
  );
};

export default Sidebar;
