import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to load data',
  message = 'A connection error occurred while communicating with Gram Panchayat servers.',
  onRetry
}) => {
  return (
    <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 space-y-3 max-w-md mx-auto text-center">
      <AlertCircle className="w-8 h-8 text-rose-400 mx-auto" />
      <h3 className="font-bold text-sm text-rose-200">{title}</h3>
      <p className="text-xs text-rose-300/80">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs transition"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Try Again
        </button>
      )}
    </div>
  );
};

export default ErrorState;
