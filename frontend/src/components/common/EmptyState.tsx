import React from 'react';
import { FileText, PlusCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  actionLink?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No records found',
  description = 'There are no active items to display.',
  actionText,
  actionLink
}) => {
  return (
    <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-3 max-w-md mx-auto">
      <FileText className="w-10 h-10 text-slate-500 mx-auto" />
      <h3 className="font-bold text-sm text-white">{title}</h3>
      <p className="text-xs text-slate-400">{description}</p>
      {actionText && actionLink && (
        <Link
          to={actionLink}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition shadow-md shadow-emerald-600/20"
        >
          <PlusCircle className="w-4 h-4" /> {actionText}
        </Link>
      )}
    </div>
  );
};

export default EmptyState;
