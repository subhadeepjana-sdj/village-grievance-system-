import React from 'react';
import { 
  FileCheck, 
  Clock, 
  UserCheck, 
  Search, 
  Wrench, 
  CheckCircle2, 
  XCircle, 
  Lock 
} from 'lucide-react';

const statusConfig = {
  SUBMITTED: { 
    bg: 'bg-[#F1EFE6] text-[#404B46] border-[#E5E7DF]', 
    icon: FileCheck, 
    label: 'Submitted' 
  },
  ACKNOWLEDGED: { 
    bg: 'bg-[#EFF5EF] text-[#153D32] border-[#DDE8DD]', 
    icon: Clock, 
    label: 'Acknowledged' 
  },
  ASSIGNED: { 
    bg: 'bg-[#EFF6FF] text-[#1E40AF] border-[#BFDBFE]', 
    icon: UserCheck, 
    label: 'Assigned' 
  },
  UNDER_REVIEW: { 
    bg: 'bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]', 
    icon: Search, 
    label: 'Under Review' 
  },
  IN_PROGRESS: { 
    bg: 'bg-[#EFF6FF] text-[#1D4ED8] border-[#93C5FD]', 
    icon: Wrench, 
    label: 'In Progress' 
  },
  RESOLVED: { 
    bg: 'bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]', 
    icon: CheckCircle2, 
    label: 'Resolved' 
  },
  REJECTED: { 
    bg: 'bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]', 
    icon: XCircle, 
    label: 'Rejected' 
  },
  CLOSED: { 
    bg: 'bg-[#F1F5F9] text-[#334155] border-[#CBD5E1]', 
    icon: Lock, 
    label: 'Closed' 
  }
};

const StatusBadge = ({ status }) => {
  const normalized = status ? status.toUpperCase() : 'SUBMITTED';
  const config = statusConfig[normalized] || statusConfig.SUBMITTED;
  const Icon = config.icon;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${config.bg}`}>
      <Icon className="w-3.5 h-3.5 shrink-0" />
      <span>{config.label}</span>
    </span>
  );
};

export default StatusBadge;
