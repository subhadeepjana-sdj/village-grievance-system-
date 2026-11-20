import React from 'react';
import { Sparkles } from 'lucide-react';

interface LoadingProps {
  message?: string;
}

export const Loading: React.FC<LoadingProps> = ({ message = 'Loading content...' }) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-3 text-slate-400">
      <Sparkles className="w-6 h-6 text-emerald-400 animate-spin" />
      <span className="text-xs font-semibold">{message}</span>
    </div>
  );
};

export default Loading;
