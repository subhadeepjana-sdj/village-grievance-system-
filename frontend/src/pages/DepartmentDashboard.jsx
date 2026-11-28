import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/StatusBadge';
import { 
  Building2, 
  Wrench, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  MapPin, 
  Calendar,
  X,
  FileText,
  ChevronRight
} from 'lucide-react';

const DepartmentDashboard = () => {
  const { user } = useAuth();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  // Resolution Modal State
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [status, setStatus] = useState('IN_PROGRESS');
  const [remarks, setRemarks] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchDeptComplaints();
  }, []);

  const fetchDeptComplaints = async () => {
    try {
      const res = await api.get('/complaints');
      setComplaints(res.data);
    } catch (err) {
      console.error('Error loading department complaints:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenResolve = (c) => {
    setSelectedComplaint(c);
    setStatus(c.status);
    setRemarks('');
  };

  const handleSaveResolution = async (e) => {
    e.preventDefault();
    if (!selectedComplaint) return;
    setSaving(true);
    setMsg('');

    try {
      await api.patch(`/complaints/${selectedComplaint.complaint_number || selectedComplaint.id}`, {
        status: status,
        remarks: remarks || `Department official updated status to ${status}`
      });
      setMsg(`Updated complaint ${selectedComplaint.complaint_number} to ${status}`);
      setSelectedComplaint(null);
      fetchDeptComplaints();
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Update failed.');
    } finally {
      setSaving(false);
    }
  };

  const inReviewCount = complaints.filter(c => c.status === 'UNDER_REVIEW').length;
  const inProgressCount = complaints.filter(c => c.status === 'IN_PROGRESS').length;
  const resolvedCount = complaints.filter(c => c.status === 'RESOLVED').length;

  return (
    <div className="space-y-6 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-[#E5E7DF]">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs uppercase font-extrabold tracking-wider text-[#0047BA] bg-[#E8F0FE] px-2.5 py-0.5 rounded-full border border-[#BFDBFE]">
              Department Field Operations
            </span>
            <span className="text-xs text-[#64748B]">Authorized Scoped Access</span>
          </div>
          <h1 className="text-2xl font-heading font-extrabold text-[#1A202C]">
            Department Work Queue
          </h1>
          <p className="text-xs text-[#64748B]">
            Official: <strong className="text-[#1A202C]">{user?.name}</strong> ({user?.email})
            {complaints[0]?.village_name ? ` • ${complaints[0].village_name}` : ''}
          </p>
        </div>
      </div>

      {msg && (
        <div className="p-3.5 rounded-xl bg-[#E6F7ED] border border-[#A3E3BE] text-[#00B050] text-xs flex items-center justify-between gap-2 animate-gis-fade">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{msg}</span>
          </div>
          <button onClick={() => setMsg('')} className="text-[#00B050] font-bold">×</button>
        </div>
      )}

      {/* KPI Cards with GIS indicator lines */}
      <div className="gis-card p-6 grid grid-cols-1 sm:grid-cols-3 gap-6 divide-y sm:divide-y-0 sm:divide-x divide-[#EAEEF4]">
        <div className="flex flex-col justify-between pt-2 sm:pt-0 sm:pr-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#FF8A00]">
              <Clock className="w-5 h-5 text-[#FF8A00]" />
            </div>
            <div className="text-xs font-semibold text-[#1A202C]">Under Inspection / Review</div>
            <div className="text-[11px] text-[#64748B]">Awaiting field inspection</div>
          </div>
          <div className="text-3xl font-black text-[#FF8A00] mt-4">{inReviewCount}</div>
          <div className="h-1 bg-[#FF8A00] rounded-full mt-3 w-full" />
        </div>

        <div className="flex flex-col justify-between pt-4 sm:pt-0 sm:px-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#00A3E0]">
              <Wrench className="w-5 h-5 text-[#00A3E0]" />
            </div>
            <div className="text-xs font-semibold text-[#1A202C]">Field Work In Progress</div>
            <div className="text-[11px] text-[#64748B]">Active repairs on site</div>
          </div>
          <div className="text-3xl font-black text-[#00A3E0] mt-4">{inProgressCount}</div>
          <div className="h-1 bg-[#00A3E0] rounded-full mt-3 w-full" />
        </div>

        <div className="flex flex-col justify-between pt-4 sm:pt-0 sm:pl-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-[#00B050]">
              <CheckCircle2 className="w-5 h-5 text-[#00B050]" />
            </div>
            <div className="text-xs font-semibold text-[#1A202C]">Resolved Cases</div>
            <div className="text-[11px] text-[#64748B]">Closed with audit remarks</div>
          </div>
          <div className="text-3xl font-black text-[#00B050] mt-4">{resolvedCount}</div>
          <div className="h-1 bg-[#00B050] rounded-full mt-3 w-full" />
        </div>
      </div>

      {/* Assigned Cases Table */}
      <div className="civic-card bg-[#FFFFFF] overflow-hidden">
        <div className="p-4 border-b border-[#E5E7DF] flex items-center justify-between">
          <h2 className="text-sm font-heading font-bold text-[#17221F]">
            Assigned Grievance Cases ({complaints.length})
          </h2>
          <span className="text-xs text-[#69736D]">Inspect cases and log resolution notes</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-[#69736D]">
            <div className="w-6 h-6 border-2 border-[#153D32] border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            Loading assigned queue...
          </div>
        ) : complaints.length === 0 ? (
          <div className="p-8 text-center text-xs text-[#69736D]">
            No assigned complaints for your department.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-[#F0F4F9] border-b border-[#E2E8F0] text-[11px] font-bold text-[#64748B] uppercase tracking-wider">
                  <th className="p-3.5">ID</th>
                  <th className="p-3.5">Grievance Title</th>
                  <th className="p-3.5">Ward & Location</th>
                  <th className="p-3.5">Priority</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0]">
                {complaints.map((c) => (
                  <tr key={c.id} className="hover:bg-[#F8FAFC] transition">
                    <td className="p-3.5 font-mono font-bold text-[#0047BA]">
                      {c.complaint_number}
                    </td>
                    <td className="p-3.5 max-w-xs">
                      <div className="font-bold text-[#1A202C] truncate">{c.title}</div>
                      <div className="text-[11px] text-[#64748B] truncate">{c.description}</div>
                    </td>
                    <td className="p-3.5 text-[#1A202C]">
                      <div className="flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-[#0047BA]" />
                        <span>{c.location || 'Not specified'}</span>
                      </div>
                    </td>
                    <td className="p-3.5">
                      <span className="font-semibold text-xs text-[#1A202C]">{c.priority}</span>
                    </td>
                    <td className="p-3.5">
                      {c.status === 'RESOLVED' || c.status === 'CLOSED' ? (
                        <span className="gis-pill-closed">Closed</span>
                      ) : c.status === 'IN_PROGRESS' || c.status === 'ASSIGNED' ? (
                        <span className="gis-pill-progress">In Progress</span>
                      ) : (
                        <span className="gis-pill-open">Open</span>
                      )}
                    </td>
                    <td className="p-3.5 text-right">
                      <button
                        type="button"
                        onClick={() => handleOpenResolve(c)}
                        className="btn-gis-primary text-xs !py-1 !px-3 font-bold cursor-pointer"
                      >
                        Update Status
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Resolution & Status Update Modal */}
      {selectedComplaint && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#17221F]/70 backdrop-blur-sm animate-civic-fade">
          <div className="w-full max-w-lg bg-[#FFFFFF] rounded-2xl border border-[#E5E7DF] shadow-2xl p-6 text-[#17221F] space-y-4">
            
            <div className="flex items-center justify-between pb-3 border-b border-[#E5E7DF]">
              <div className="space-y-0.5">
                <span className="font-mono text-xs font-bold text-[#153D32]">{selectedComplaint.complaint_number}</span>
                <h3 className="font-heading font-bold text-sm text-[#17221F]">
                  Update Field Status & Resolution
                </h3>
              </div>
              <button 
                onClick={() => setSelectedComplaint(null)} 
                className="p-1 rounded text-[#69736D] hover:text-[#17221F]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveResolution} className="space-y-3.5 text-xs">
              <div className="space-y-1">
                <label className="font-bold text-[#17221F] block">Select New Milestone Status</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-[#E5E7DF] bg-[#FFFFFF] text-[#17221F] focus:outline-none focus:ring-2 focus:ring-[#153D32]"
                >
                  <option value="UNDER_REVIEW">Under Review / Inspection</option>
                  <option value="IN_PROGRESS">In Progress (Repair ongoing)</option>
                  <option value="RESOLVED">Resolved (Work completed)</option>
                  <option value="CLOSED">Closed</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="font-bold text-[#17221F] block">Field Remarks / Resolution Notes</label>
                <textarea
                  rows={4}
                  required
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  placeholder="Enter field inspection findings or resolution notes..."
                  className="w-full px-3 py-2 rounded-lg border border-[#E5E7DF] bg-[#FFFFFF] text-[#17221F] focus:outline-none focus:ring-2 focus:ring-[#153D32] leading-relaxed"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedComplaint(null)}
                  className="btn-civic-secondary text-xs !py-2 !px-4"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="btn-civic-primary text-xs !py-2 !px-5 font-bold"
                >
                  {saving ? 'Saving...' : 'Record Milestone'}
                </button>
              </div>
            </form>

          </div>
        </div>
      )}

    </div>
  );
};

export default DepartmentDashboard;
