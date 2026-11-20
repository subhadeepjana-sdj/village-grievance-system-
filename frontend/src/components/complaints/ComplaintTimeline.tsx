import React from 'react';
import { CheckCircle2, Circle, Clock } from 'lucide-react';
import { ComplaintStatusHistoryItem } from '../../types';

interface ComplaintTimelineProps {
  currentStatus: string;
  history?: ComplaintStatusHistoryItem[];
}

const STEPS = ['SUBMITTED', 'ACKNOWLEDGED', 'ASSIGNED', 'UNDER_REVIEW', 'IN_PROGRESS', 'RESOLVED'];

export const ComplaintTimeline: React.FC<ComplaintTimelineProps> = ({ currentStatus, history = [] }) => {
  const normCurrent = currentStatus ? currentStatus.toUpperCase() : 'SUBMITTED';
  const currentIndex = STEPS.indexOf(normCurrent);

  return (
    <div className="py-4 space-y-6">
      {/* Horizontal Stepper Progress */}
      <div className="hidden md:flex items-center justify-between relative">
        <div className="absolute left-0 right-0 top-1/2 h-1 bg-slate-800 -translate-y-1/2 z-0" />
        <div 
          className="absolute left-0 top-1/2 h-1 bg-emerald-500 -translate-y-1/2 z-0 transition-all duration-500" 
          style={{ width: `${Math.max(0, (currentIndex / (STEPS.length - 1)) * 100)}%` }}
        />

        {STEPS.map((step, idx) => {
          const isDone = idx <= currentIndex && normCurrent !== 'REJECTED';
          const isCurrent = idx === currentIndex;

          return (
            <div key={step} className="relative z-10 flex flex-col items-center">
              <div 
                className={`w-9 h-9 rounded-full flex items-center justify-center border-2 transition-all ${
                  isDone 
                    ? 'bg-emerald-500 border-emerald-400 text-slate-900 font-bold' 
                    : isCurrent 
                    ? 'bg-slate-800 border-amber-400 text-amber-400 animate-pulse' 
                    : 'bg-slate-800 border-slate-700 text-slate-500'
                }`}
              >
                {isDone ? <CheckCircle2 className="w-4 h-4" /> : <Circle className="w-3.5 h-3.5" />}
              </div>
              <span className={`text-[11px] font-semibold mt-2 ${isDone ? 'text-emerald-400' : 'text-slate-400'}`}>
                {step.replace('_', ' ')}
              </span>
            </div>
          );
        })}
      </div>

      {/* History Audit Log List */}
      <div className="space-y-2">
        <h4 className="text-xs font-bold text-slate-300 flex items-center gap-1.5 uppercase tracking-wider">
          <Clock className="w-3.5 h-3.5 text-emerald-400" /> Resolution Audit Log
        </h4>
        {history.length === 0 ? (
          <p className="text-xs text-slate-400 italic">No historical status updates recorded yet.</p>
        ) : (
          history.map((h, i) => (
            <div key={i} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2">
              <div className="flex items-center gap-2">
                <span className="font-bold text-emerald-400">{h.new_status}</span>
                <span className="text-slate-400">by {h.changed_by}</span>
              </div>
              <div className="text-slate-300 italic">{h.remarks || 'No remarks added'}</div>
              <div className="text-slate-500 text-[10px] font-mono">
                {new Date(h.timestamp).toLocaleString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ComplaintTimeline;
