import React from 'react';
import { Clock } from 'lucide-react';

// Helper to format date in "Month Day, Year at Hour:Minute AM/PM" format
const formatEventDate = (timestamp) => {
  if (!timestamp) return 'Recent update';
  try {
    const d = new Date(timestamp);
    if (isNaN(d.getTime())) return timestamp;
    const datePart = d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
    const timePart = d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    return `${datePart} at ${timePart}`;
  } catch (e) {
    return timestamp;
  }
};

const Timeline = ({ currentStatus, history = [], complaint = null }) => {
  let events = [];

  if (history && history.length > 0) {
    events = history.map((h, idx) => {
      const st = (h.new_status || '').toUpperCase();
      let title = 'Status Update';
      let dotColor = 'bg-[#2563EB]';
      let ringColor = 'ring-blue-100';

      if (st === 'SUBMITTED') {
        title = 'Grievance Filed';
        dotColor = 'bg-[#2563EB]';
        ringColor = 'ring-blue-100';
      } else if (st === 'ACKNOWLEDGED') {
        title = 'Received & Acknowledged';
        dotColor = 'bg-[#10B981]';
        ringColor = 'ring-emerald-100';
      } else if (st === 'ASSIGNED') {
        title = 'Assigned to Department';
        dotColor = 'bg-[#EAB308]';
        ringColor = 'ring-amber-100';
      } else if (st === 'UNDER_REVIEW') {
        title = 'Under Review / Inspection';
        dotColor = 'bg-[#F97316]';
        ringColor = 'ring-orange-100';
      } else if (st === 'IN_PROGRESS') {
        title = 'Resolution In Progress';
        dotColor = 'bg-[#A855F7]';
        ringColor = 'ring-purple-100';
      } else if (st === 'RESOLVED' || st === 'CLOSED') {
        title = 'Grievance Resolved & Closed';
        dotColor = 'bg-[#10B981]';
        ringColor = 'ring-emerald-100';
      }

      return {
        id: h.id || idx,
        title,
        description: h.remarks || `Status transitioned to ${st.replace('_', ' ')}.`,
        author: h.changed_by || 'System',
        date: formatEventDate(h.timestamp),
        dotColor,
        ringColor,
        status: st
      };
    });
  } else if (complaint) {
    events = [
      {
        id: '1',
        title: 'Grievance Filed',
        description: complaint.description || 'Complaint lodged on civic portal.',
        author: complaint.citizen_name || 'Citizen',
        date: formatEventDate(complaint.created_at),
        dotColor: 'bg-[#2563EB]',
        ringColor: 'ring-blue-100',
        status: currentStatus || 'SUBMITTED'
      }
    ];
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-6 sm:p-8 shadow-xs">
      <h2 className="text-2xl font-bold text-slate-900 tracking-tight mb-8">
        Grievance History & Timeline
      </h2>

      <div className="relative pl-1 sm:pl-2">
        {events.map((event, index) => {
          const isLast = index === events.length - 1;

          return (
            <div 
              key={event.id || index} 
              className="relative flex items-start gap-4 sm:gap-5 pb-8 last:pb-0 group"
            >
              {/* Continuous vertical connecting line */}
              {!isLast && (
                <div 
                  className="absolute left-[6px] top-[14px] bottom-0 w-[2px] bg-slate-200" 
                  aria-hidden="true"
                />
              )}

              {/* Colored status dot with white halo */}
              <div className="relative z-10 flex items-center justify-center shrink-0 mt-1">
                <div 
                  className={`w-3.5 h-3.5 rounded-full ${event.dotColor} ring-4 ring-white shadow-xs transition-transform duration-200 group-hover:scale-125`} 
                />
              </div>

              {/* Text content block */}
              <div className="flex-1 min-w-0 pt-0.5">
                <h3 className="text-base font-bold text-slate-900 leading-snug">
                  {event.title}
                </h3>
                <p className="text-sm text-slate-600 mt-1 leading-relaxed font-normal">
                  {event.description}
                </p>
                <div className="text-xs text-slate-400 mt-1.5 font-normal flex flex-wrap items-center gap-1.5">
                  <span>By {event.author}</span>
                  <span>•</span>
                  <span>{event.date}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Timeline;
