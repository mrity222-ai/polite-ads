import React from 'react';
import { CheckCircle2, AlertCircle, Info } from 'lucide-react';

export default function Toast({ show, message, type = 'info', onClose }) {
  if (!show) return null;

  const isSuccess = type === 'success';
  const isError = type === 'error';

  return (
    <div role="status" className="fixed bottom-6 left-4 right-4 sm:left-auto sm:right-6 z-50 bg-gray-950 text-white px-5 py-3.5 rounded-2xl shadow-2xl border border-emerald-500/30 flex items-center gap-3 transition-all animate-in fade-in slide-in-from-bottom-3 max-w-sm sm:max-w-md">
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold shrink-0 ${
        isSuccess ? 'bg-emerald-500 text-gray-950' : isError ? 'bg-red-500 text-white' : 'bg-blue-500 text-white'
      }`}>
        {isSuccess ? <CheckCircle2 className="w-5 h-5" /> : isError ? <AlertCircle className="w-5 h-5" /> : <Info className="w-5 h-5" />}
      </div>
      <div className="min-w-0 flex-1">
        <h5 className="text-xs font-bold whitespace-normal break-words">{message || 'Action Completed'}</h5>
      </div>
      {onClose && (
        <button aria-label="Dismiss notification" onClick={onClose} className="text-gray-400 hover:text-white text-xs font-bold ml-1">
          ✕
        </button>
      )}
    </div>
  );
}
