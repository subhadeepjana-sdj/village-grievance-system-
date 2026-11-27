import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  Check,
  CheckCheck,
  Clock,
  AlertTriangle,
  ShieldAlert,
  Info,
  Search,
  Settings,
  RefreshCw,
  Trash2,
  ExternalLink,
  Layers,
  Bot,
  Database,
  Building2,
  FileText,
  MessageSquareWarning,
  Server,
  ShieldCheck,
  X,
  SlidersHorizontal,
  History,
  Sparkles,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import {
  adminService,
  DailyDigestSummary,
  NotificationItem,
  NotificationPreferences,
} from '../../services/adminService';

type FilterTab =
  | 'all'
  | 'unread'
  | 'critical'
  | 'pending_action'
  | 'complaints'
  | 'ai_alerts'
  | 'system_alerts'
  | 'history';

const FILTER_TABS: Array<{ id: FilterTab; label: string }> = [
  { id: 'all', label: 'All' },
  { id: 'unread', label: 'Unread' },
  { id: 'critical', label: 'Critical' },
  { id: 'pending_action', label: 'Pending Action' },
  { id: 'complaints', label: 'Complaints' },
  { id: 'ai_alerts', label: 'AI Alerts' },
  { id: 'system_alerts', label: 'System Alerts' },
  { id: 'history', label: 'History' },
];

const CATEGORY_OPTIONS: Array<{ value: string; label: string }> = [
  { value: '', label: 'All Categories' },
  { value: 'COMPLAINT', label: 'Complaints' },
  { value: 'DEADLINE_ESCALATION', label: 'Deadline & Escalation' },
  { value: 'DEPARTMENT', label: 'Department Actions' },
  { value: 'AI_INTELLIGENCE', label: 'AI Intelligence' },
  { value: 'KNOWLEDGE_BASE', label: 'Knowledge Base' },
  { value: 'AI_FEEDBACK', label: 'AI Feedback' },
  { value: 'SECURITY', label: 'Security' },
  { value: 'SYSTEM', label: 'System Health' },
];

const SEVERITY_OPTIONS = [
  { value: '', label: 'All Severities' },
  { value: 'CRITICAL', label: 'Critical' },
  { value: 'WARNING', label: 'Warning' },
  { value: 'INFO', label: 'Info' },
];

const DATE_RANGE_OPTIONS = [
  { value: 'all', label: 'All Time' },
  { value: 'today', label: 'Today' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
];

const CATEGORY_LABEL: Record<string, string> = {
  COMPLAINT: 'Complaint',
  DEADLINE_ESCALATION: 'Escalation',
  DEPARTMENT: 'Department',
  AI_INTELLIGENCE: 'AI Intelligence',
  KNOWLEDGE_BASE: 'Knowledge Base',
  AI_FEEDBACK: 'AI Feedback',
  SECURITY: 'Security',
  SYSTEM: 'System',
};

function getCategoryIcon(category: string) {
  switch (category) {
    case 'COMPLAINT':
      return FileText;
    case 'DEADLINE_ESCALATION':
      return Clock;
    case 'DEPARTMENT':
      return Building2;
    case 'AI_INTELLIGENCE':
      return Bot;
    case 'KNOWLEDGE_BASE':
      return Database;
    case 'AI_FEEDBACK':
      return MessageSquareWarning;
    case 'SECURITY':
      return ShieldAlert;
    case 'SYSTEM':
      return Server;
    default:
      return Bell;
  }
}

function getSeverityStyles(severity: string) {
  const s = (severity || '').toUpperCase();
  if (s === 'CRITICAL') {
    return {
      badge: 'bg-red-50 text-red-700 border-red-200',
      bar: 'border-l-red-600',
      dot: 'bg-red-600',
      label: 'Critical',
    };
  }
  if (s === 'WARNING') {
    return {
      badge: 'bg-amber-50 text-amber-800 border-amber-200',
      bar: 'border-l-amber-500',
      dot: 'bg-amber-500',
      label: 'Warning',
    };
  }
  return {
    badge: 'bg-blue-50 text-blue-700 border-blue-200',
    bar: 'border-l-blue-600',
    dot: 'bg-blue-600',
    label: 'Info',
  };
}

function formatRelativeTime(isoString?: string): string {
  if (!isoString) return 'Just now';
  const dt = new Date(isoString);
  if (isNaN(dt.getTime())) return isoString;
  const diffSec = Math.max(0, Math.floor((Date.now() - dt.getTime()) / 1000));
  if (diffSec < 60) return 'Just now';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} min ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} hr ago`;
  return dt.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export const NotificationsPage: React.FC = () => {
  const navigate = useNavigate();

  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [selectedNotif, setSelectedNotif] = useState<NotificationItem | null>(null);
  const [digest, setDigest] = useState<DailyDigestSummary | null>(null);

  const [unreadCount, setUnreadCount] = useState(0);
  const [criticalCount, setCriticalCount] = useState(0);
  const [pendingActionCount, setPendingActionCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const [activeTab, setActiveTab] = useState<FilterTab>('all');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [dateRange, setDateRange] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [scanningSla, setScanningSla] = useState(false);
  const [statusBanner, setStatusBanner] = useState('');

  // Preferences Modal
  const [prefsOpen, setPrefsOpen] = useState(false);
  const [prefs, setPrefs] = useState<NotificationPreferences | null>(null);
  const [savingPrefs, setSavingPrefs] = useState(false);

  const computeDateFrom = (rangeKey: string): string | undefined => {
    const now = new Date();
    if (rangeKey === 'today') {
      const start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      return start.toISOString();
    }
    if (rangeKey === '7d') {
      return new Date(now.getTime() - 7 * 86400 * 1000).toISOString();
    }
    if (rangeKey === '30d') {
      return new Date(now.getTime() - 30 * 86400 * 1000).toISOString();
    }
    return undefined;
  };

  const fetchNotifications = useCallback(
    async (silent = false) => {
      if (!silent) setRefreshing(true);
      try {
        const isHistory = activeTab === 'history';
        const [listRes, digestRes] = await Promise.allSettled([
          adminService.listNotifications({
            filter: isHistory ? 'all' : activeTab,
            category: categoryFilter || undefined,
            severity: severityFilter || undefined,
            search: searchQuery.trim() || undefined,
            date_from: computeDateFrom(dateRange),
            include_dismissed: isHistory,
            page,
            page_size: 12,
          }),
          adminService.getNotificationDigest(),
        ]);

        if (listRes.status === 'fulfilled') {
          const data = listRes.value;
          setNotifications(data.items || []);
          setTotalCount(data.total || 0);
          setTotalPages(data.pages || 1);
          setUnreadCount(data.unread_count || 0);
          setCriticalCount(data.critical_count || 0);
          setPendingActionCount(data.pending_action_count || 0);
          setSelectedNotif((prev) => {
            if (!data.items?.length) return null;
            if (prev) {
              const updated = data.items.find((i) => i.id === prev.id);
              if (updated) return updated;
            }
            return data.items[0];
          });
        }
        if (digestRes.status === 'fulfilled') {
          setDigest(digestRes.value);
        }
      } catch (err) {
        console.error('Failed to fetch notifications:', err);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [activeTab, categoryFilter, severityFilter, dateRange, searchQuery, page]
  );

  useEffect(() => {
    fetchNotifications(false);
  }, [fetchNotifications]);

  // Real-time polling every 20 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      fetchNotifications(true);
    }, 20000);
    return () => clearInterval(timer);
  }, [fetchNotifications]);

  const handleToggleRead = async (notif: NotificationItem) => {
    try {
      await adminService.setNotificationRead(notif.id, !notif.is_read);
      await fetchNotifications(true);
    } catch {
      setStatusBanner('Unable to update read status.');
    }
  };

  const handleAcknowledge = async (notif: NotificationItem) => {
    try {
      await adminService.acknowledgeNotification(notif.id);
      setStatusBanner(`Acknowledged alert: ${notif.title}`);
      await fetchNotifications(true);
    } catch {
      setStatusBanner('Unable to acknowledge notification.');
    }
  };

  const handleDismiss = async (notif: NotificationItem) => {
    try {
      await adminService.dismissNotification(notif.id);
      setStatusBanner(`Moved "${notif.title}" to alert history.`);
      await fetchNotifications(true);
    } catch {
      setStatusBanner('Unable to dismiss notification.');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      const res = await adminService.markAllNotificationsRead();
      setStatusBanner(`Marked ${res.marked_read} notification(s) as read.`);
      await fetchNotifications(true);
    } catch {
      setStatusBanner('Unable to mark all notifications as read.');
    }
  };

  const handleScanSla = async () => {
    setScanningSla(true);
    try {
      const res = await adminService.scanNotificationSLA();
      setStatusBanner(`SLA & system health scan completed (${res.alerts_processed} check(s) processed).`);
      await fetchNotifications(true);
    } catch {
      setStatusBanner('SLA scan failed.');
    } finally {
      setScanningSla(false);
    }
  };

  const openPreferences = async () => {
    setPrefsOpen(true);
    try {
      const p = await adminService.getNotificationPreferences();
      setPrefs(p);
    } catch {
      setStatusBanner('Failed to load notification preferences.');
    }
  };

  const handleSavePrefs = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prefs) return;
    setSavingPrefs(true);
    try {
      const updated = await adminService.updateNotificationPreferences(prefs);
      setPrefs(updated);
      setPrefsOpen(false);
      setStatusBanner('Notification preferences & escalation rules saved.');
    } catch {
      setStatusBanner('Failed to save preferences.');
    } finally {
      setSavingPrefs(false);
    }
  };

  const toggleCategoryPref = (cat: string) => {
    if (!prefs) return;
    const exists = prefs.enabled_categories.includes(cat);
    const next = exists
      ? prefs.enabled_categories.filter((c) => c !== cat)
      : [...prefs.enabled_categories, cat];
    setPrefs({ ...prefs, enabled_categories: next });
  };

  const handleOpenAction = async (notif: NotificationItem) => {
    if (!notif.is_read) {
      await adminService.setNotificationRead(notif.id, true).catch(() => {});
    }
    navigate(notif.action_url || '/panchayat/dashboard');
  };

  return (
    <div className="space-y-6 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* ─── 1. TOP SUMMARY HEADER ─────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-[#EAEEF4] shadow-xs p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-5">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 text-[#0047BA] border border-blue-200 text-[11px] font-bold uppercase tracking-wider">
              <Bell className="w-3.5 h-3.5" /> Central Alert Management
            </span>
            <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
              Live Polling (20s)
            </span>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-[#1A202C] tracking-tight">
              Notifications &amp; Alerts
            </h1>
            <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-900">
              {unreadCount} Unread
            </span>
          </div>
          <p className="text-xs sm:text-sm text-[#64748B]">
            Monitor complaints, SLA deadline escalations, department updates, AI verification problems, knowledge base changes, and security events.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5 shrink-0">
          <button
            type="button"
            onClick={handleScanSla}
            disabled={scanningSla}
            className="px-3.5 py-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-xs font-semibold text-slate-700 flex items-center gap-1.5 transition cursor-pointer disabled:opacity-50"
          >
            <Clock className={`w-3.5 h-3.5 text-amber-600 ${scanningSla ? 'animate-spin' : ''}`} />
            <span>{scanningSla ? 'Scanning SLA...' : 'Run SLA Scan'}</span>
          </button>

          <button
            type="button"
            onClick={openPreferences}
            className="px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 flex items-center gap-1.5 transition cursor-pointer"
          >
            <Settings className="w-3.5 h-3.5 text-slate-600" />
            <span>Preferences</span>
          </button>

          <button
            type="button"
            onClick={() => fetchNotifications(false)}
            disabled={refreshing}
            className="px-3.5 py-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700 flex items-center gap-1.5 transition cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin text-[#0047BA]' : 'text-slate-500'}`} />
            <span>Refresh</span>
          </button>

          <button
            type="button"
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0}
            className="px-4 py-2 rounded-xl bg-[#0047BA] hover:bg-[#00368C] text-white text-xs font-bold flex items-center gap-1.5 transition shadow-xs cursor-pointer disabled:opacity-50"
          >
            <CheckCheck className="w-3.5 h-3.5" />
            <span>Mark all read</span>
          </button>
        </div>
      </div>

      {statusBanner && (
        <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 text-xs flex items-center justify-between gap-2">
          <span className="font-medium">{statusBanner}</span>
          <button type="button" onClick={() => setStatusBanner('')} className="text-blue-700 font-bold cursor-pointer">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <button
          type="button"
          onClick={() => { setActiveTab('unread'); setPage(1); }}
          className={`text-left bg-white rounded-2xl p-5 border shadow-xs transition cursor-pointer hover:shadow-md ${
            activeTab === 'unread' ? 'border-[#0047BA] ring-2 ring-blue-100' : 'border-[#EAEEF4]'
          }`}
        >
          <div className="flex items-center justify-between text-xs font-bold text-[#64748B]">
            <span>Unread</span>
            <Bell className="w-4 h-4 text-[#0047BA]" />
          </div>
          <div className="text-3xl font-black text-[#1A202C] mt-2">{unreadCount}</div>
          <div className="text-[11px] text-[#64748B] mt-1">Click to view unread notifications</div>
        </button>

        <button
          type="button"
          onClick={() => { setActiveTab('critical'); setPage(1); }}
          className={`text-left bg-white rounded-2xl p-5 border shadow-xs transition cursor-pointer hover:shadow-md ${
            activeTab === 'critical' ? 'border-red-600 ring-2 ring-red-100' : 'border-[#EAEEF4]'
          }`}
        >
          <div className="flex items-center justify-between text-xs font-bold text-red-700">
            <span>Critical</span>
            <ShieldAlert className="w-4 h-4 text-red-600" />
          </div>
          <div className="text-3xl font-black text-red-700 mt-2">{criticalCount}</div>
          <div className="text-[11px] text-[#64748B] mt-1">Immediate attention alerts</div>
        </button>

        <button
          type="button"
          onClick={() => { setActiveTab('pending_action'); setPage(1); }}
          className={`text-left bg-white rounded-2xl p-5 border shadow-xs transition cursor-pointer hover:shadow-md ${
            activeTab === 'pending_action' ? 'border-amber-600 ring-2 ring-amber-100' : 'border-[#EAEEF4]'
          }`}
        >
          <div className="flex items-center justify-between text-xs font-bold text-amber-700">
            <span>Pending Action</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-3xl font-black text-amber-700 mt-2">{pendingActionCount}</div>
          <div className="text-[11px] text-[#64748B] mt-1">Requires admin triage or acknowledgement</div>
        </button>
      </div>

      {/* ─── 2. FILTER BAR ─────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-[#EAEEF4] shadow-xs p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-1.5">
          {FILTER_TABS.map((tab) => {
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => { setActiveTab(tab.id); setPage(1); }}
                className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer ${
                  active
                    ? 'bg-[#0047BA] text-white shadow-xs'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200/70'
                }`}
              >
                {tab.id === 'history' && <History className="w-3.5 h-3.5" />}
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 pt-1">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
              placeholder="Search complaint ID or title..."
              className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#0047BA]"
            />
          </div>

          <select
            value={categoryFilter}
            onChange={(e) => { setCategoryFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#0047BA] cursor-pointer"
          >
            {CATEGORY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select
            value={severityFilter}
            onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#0047BA] cursor-pointer"
          >
            {SEVERITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>

          <select
            value={dateRange}
            onChange={(e) => { setDateRange(e.target.value); setPage(1); }}
            className="px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:bg-white focus:outline-none focus:ring-2 focus:ring-[#0047BA] cursor-pointer"
          >
            {DATE_RANGE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* ─── 3 & 4. FEED + QUICK ACTION / DIGEST PANEL ─────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Notification Feed */}
        <div className="lg:col-span-8 space-y-3">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-sm font-bold text-[#1A202C]">
              {activeTab === 'history' ? 'Notification & Acknowledgement History' : 'Recent notifications'}
            </h2>
            <span className="text-xs text-[#64748B] font-medium">
              {totalCount} record(s)
            </span>
          </div>

          {loading ? (
            <div className="bg-white rounded-2xl border border-[#EAEEF4] p-10 text-center text-xs text-[#64748B]">
              Loading live notifications...
            </div>
          ) : notifications.length === 0 ? (
            <div className="bg-white rounded-2xl border border-dashed border-slate-300 p-10 text-center space-y-2">
              <Bell className="w-8 h-8 text-slate-300 mx-auto" />
              <p className="text-sm font-bold text-[#1A202C]">No notifications in this view</p>
              <p className="text-xs text-[#64748B] max-w-md mx-auto">
                Real-time alerts are created automatically when citizens submit complaints, SLA deadlines escalate, AI NLI checks intercept issues, KB documents update, or security events occur.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {notifications.map((notif) => {
                const sev = getSeverityStyles(notif.severity);
                const CatIcon = getCategoryIcon(notif.category);
                const isSelected = selectedNotif?.id === notif.id;

                return (
                  <div
                    key={notif.id}
                    onClick={() => setSelectedNotif(notif)}
                    className={`bg-white rounded-2xl border border-l-4 p-4 sm:p-5 shadow-xs transition cursor-pointer ${sev.bar} ${
                      isSelected ? 'border-[#0047BA] ring-2 ring-blue-100' : 'border-[#EAEEF4] hover:border-slate-300'
                    } ${notif.is_read ? 'opacity-85' : ''}`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div className="space-y-1.5 min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${sev.badge}`}>
                            {sev.label}
                          </span>
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                            <CatIcon className="w-3 h-3" />
                            {CATEGORY_LABEL[notif.category] || notif.category}
                          </span>
                          {!notif.is_read && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#0047BA] text-white">
                              New
                            </span>
                          )}
                          {notif.occurrence_count > 1 && (
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                              ×{notif.occurrence_count} grouped
                            </span>
                          )}
                          {notif.acknowledged_at && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              <ShieldCheck className="w-3 h-3" /> Acknowledged
                            </span>
                          )}
                        </div>

                        <h3 className="text-sm font-bold text-[#1A202C] leading-snug">
                          {notif.title}
                        </h3>
                        <p className="text-xs text-[#475569] leading-relaxed">
                          {notif.message}
                        </p>

                        <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] text-[#64748B]">
                          <span>{formatRelativeTime(notif.updated_at || notif.created_at)}</span>
                          {notif.related_complaint_number && (
                            <span className="font-mono font-semibold text-[#0047BA]">
                              {notif.related_complaint_number}
                            </span>
                          )}
                          {notif.dismissed_at && (
                            <span className="text-slate-500">Dismissed</span>
                          )}
                        </div>
                      </div>

                      {/* Inline Action Controls */}
                      <div
                        className="flex flex-wrap sm:flex-col items-end gap-1.5 shrink-0"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          type="button"
                          onClick={() => handleOpenAction(notif)}
                          className="px-3 py-1.5 rounded-lg bg-[#0047BA] hover:bg-[#00368C] text-white text-[11px] font-bold flex items-center gap-1 transition cursor-pointer"
                        >
                          <span>{notif.action_label || 'Open details'}</span>
                          <ExternalLink className="w-3 h-3" />
                        </button>

                        <div className="flex items-center gap-1.5">
                          {notif.severity === 'CRITICAL' && !notif.acknowledged_at && (
                            <button
                              type="button"
                              onClick={() => handleAcknowledge(notif)}
                              className="px-2.5 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 text-[11px] font-semibold cursor-pointer"
                            >
                              Acknowledge
                            </button>
                          )}

                          <button
                            type="button"
                            onClick={() => handleToggleRead(notif)}
                            className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-semibold cursor-pointer"
                          >
                            {notif.is_read ? 'Mark unread' : 'Mark read'}
                          </button>

                          {!notif.dismissed_at && (
                            <button
                              type="button"
                              onClick={() => handleDismiss(notif)}
                              title="Dismiss to history"
                              className="px-2.5 py-1 rounded-lg bg-white hover:bg-red-50 text-slate-600 hover:text-red-700 border border-slate-200 text-[11px] font-semibold cursor-pointer"
                            >
                              Dismiss
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between bg-white rounded-xl border border-[#EAEEF4] px-4 py-2.5 text-xs">
                  <span className="text-[#64748B]">
                    Page <strong>{page}</strong> of <strong>{totalPages}</strong>
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      className="px-2.5 py-1 rounded-lg border border-slate-200 disabled:opacity-40 flex items-center gap-1 cursor-pointer"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" /> Prev
                    </button>
                    <button
                      type="button"
                      disabled={page >= totalPages}
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      className="px-2.5 py-1 rounded-lg border border-slate-200 disabled:opacity-40 flex items-center gap-1 cursor-pointer"
                    >
                      Next <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Quick Action Panel + Daily Digest */}
        <div className="lg:col-span-4 space-y-5">
          {/* Quick Action Panel */}
          <div className="bg-white rounded-2xl border border-[#EAEEF4] shadow-xs p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#1A202C] flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 text-[#0047BA]" />
                Quick Action Panel
              </h3>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Triage
              </span>
            </div>

            {selectedNotif ? (
              <div className="space-y-3 text-xs">
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900">{selectedNotif.title}</span>
                  </div>
                  <p className="text-slate-600 leading-relaxed">{selectedNotif.message}</p>
                  {selectedNotif.acknowledged_by && (
                    <div className="text-[11px] text-emerald-700 font-semibold pt-1">
                      Ack by: {selectedNotif.acknowledged_by}
                    </div>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => handleOpenAction(selectedNotif)}
                  className="w-full py-2 px-3 rounded-xl bg-[#0047BA] hover:bg-[#00368C] text-white font-bold text-xs flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <span>{selectedNotif.action_label || 'Open Target View'}</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            ) : (
              <p className="text-xs text-[#64748B]">
                Select any notification to inspect full details or jump directly to the relevant module.
              </p>
            )}

            <div className="border-t border-slate-100 pt-3 space-y-2">
              <div className="text-[11px] font-bold uppercase tracking-wider text-[#64748B]">
                Direct Jump Shortcuts
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => navigate('/panchayat/dashboard')}
                  className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-left font-semibold text-slate-700 cursor-pointer"
                >
                  Open Complaints
                </button>
                <button
                  type="button"
                  onClick={() => navigate('/department/dashboard')}
                  className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-left font-semibold text-slate-700 cursor-pointer"
                >
                  Assign Department
                </button>
                <button
                  type="button"
                  onClick={() => navigate('/admin/ai-monitoring')}
                  className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-left font-semibold text-slate-700 cursor-pointer"
                >
                  AI Verification
                </button>
                <button
                  type="button"
                  onClick={() => navigate('/knowledge-base')}
                  className="p-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-left font-semibold text-slate-700 cursor-pointer"
                >
                  Knowledge Base
                </button>
              </div>
            </div>
          </div>

          {/* Daily Digest Card */}
          <div className="bg-white rounded-2xl border border-[#EAEEF4] shadow-xs p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#1A202C] flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-500" />
                Daily Operational Digest
              </h3>
              <span className="text-[10px] font-semibold text-slate-500">Live</span>
            </div>

            <div className="grid grid-cols-2 gap-2.5 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
                <div className="text-[11px] text-[#64748B]">Pending Grievances</div>
                <div className="text-lg font-black text-[#1A202C]">{digest?.pending_complaints ?? 0}</div>
              </div>
              <div className="p-3 rounded-xl bg-red-50/70 border border-red-200">
                <div className="text-[11px] text-red-700">Overdue Cases</div>
                <div className="text-lg font-black text-red-700">{digest?.overdue_complaints ?? 0}</div>
              </div>
              <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200">
                <div className="text-[11px] text-amber-800">AI Interceptions</div>
                <div className="text-lg font-black text-amber-800">{digest?.ai_verification_issues ?? 0}</div>
              </div>
              <div className="p-3 rounded-xl bg-blue-50/70 border border-blue-200">
                <div className="text-[11px] text-[#0047BA]">Pending Feedback</div>
                <div className="text-lg font-black text-[#0047BA]">{digest?.pending_feedback_reviews ?? 0}</div>
              </div>
            </div>

            {digest?.highlights && digest.highlights.length > 0 ? (
              <ul className="space-y-1.5 text-xs text-slate-600 pt-1">
                {digest.highlights.map((h, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <Info className="w-3.5 h-3.5 text-[#0047BA] shrink-0 mt-0.5" />
                    <span>{h}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-[#64748B] pt-1">
                No overdue grievances or critical backlogs reported today.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* ─── 5. NOTIFICATION SETTINGS / PREFERENCES MODAL ──────────── */}
      {prefsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto bg-white rounded-2xl border border-slate-200 shadow-2xl">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#0047BA]">
                  Alert Configuration
                </span>
                <h3 className="text-base font-bold text-slate-900">
                  Notification Preferences &amp; Escalation Rules
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setPrefsOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-700 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {prefs ? (
              <form onSubmit={handleSavePrefs} className="p-6 space-y-5 text-xs">
                <div className="space-y-2">
                  <label className="font-bold text-slate-800 block">Enabled Alert Categories</label>
                  <div className="grid grid-cols-2 gap-2">
                    {CATEGORY_OPTIONS.filter((o) => o.value).map((opt) => {
                      const checked = prefs.enabled_categories.includes(opt.value);
                      return (
                        <label
                          key={opt.value}
                          className={`flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer ${
                            checked ? 'bg-blue-50/70 border-blue-200 text-slate-900' : 'bg-white border-slate-200 text-slate-500'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleCategoryPref(opt.value)}
                            className="rounded text-[#0047BA]"
                          />
                          <span className="font-semibold">{opt.label}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-bold text-slate-800 block">Minimum Severity</label>
                    <select
                      value={prefs.min_severity}
                      onChange={(e) => setPrefs({ ...prefs, min_severity: e.target.value })}
                      className="w-full px-3 py-2 rounded-xl border border-slate-300 bg-white"
                    >
                      <option value="INFO">Info &amp; Above</option>
                      <option value="WARNING">Warning &amp; Critical</option>
                      <option value="CRITICAL">Critical Only</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="font-bold text-slate-800 block">SLA Escalation (Hours)</label>
                    <input
                      type="number"
                      min={1}
                      max={720}
                      value={prefs.escalation_sla_hours}
                      onChange={(e) =>
                        setPrefs({ ...prefs, escalation_sla_hours: Number(e.target.value) || 48 })
                      }
                      className="w-full px-3 py-2 rounded-xl border border-slate-300 bg-white"
                    />
                  </div>
                </div>

                <div className="space-y-2 border-t border-slate-100 pt-3">
                  <label className="font-bold text-slate-800 block">Automation &amp; Delivery Channels</label>
                  <label className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                    <span className="font-medium text-slate-800">Smart Notification Grouping (deduplicate repeats)</span>
                    <input
                      type="checkbox"
                      checked={prefs.smart_grouping_enabled}
                      onChange={(e) => setPrefs({ ...prefs, smart_grouping_enabled: e.target.checked })}
                    />
                  </label>
                  <label className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                    <span className="font-medium text-slate-800">Automatic SLA Escalation Alerts</span>
                    <input
                      type="checkbox"
                      checked={prefs.auto_escalation_enabled}
                      onChange={(e) => setPrefs({ ...prefs, auto_escalation_enabled: e.target.checked })}
                    />
                  </label>
                  <label className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                    <span className="font-medium text-slate-800">Daily Digest Reporting Channel</span>
                    <input
                      type="checkbox"
                      checked={prefs.email_digest_enabled}
                      onChange={(e) => setPrefs({ ...prefs, email_digest_enabled: e.target.checked })}
                    />
                  </label>
                </div>

                <div className="flex items-center justify-end gap-2.5 pt-2">
                  <button
                    type="button"
                    onClick={() => setPrefsOpen(false)}
                    className="px-4 py-2 rounded-xl border border-slate-300 text-slate-700 font-semibold cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={savingPrefs}
                    className="px-5 py-2 rounded-xl bg-[#0047BA] hover:bg-[#00368C] text-white font-bold flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>{savingPrefs ? 'Saving...' : 'Save Preferences'}</span>
                  </button>
                </div>
              </form>
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">Loading preferences...</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationsPage;
