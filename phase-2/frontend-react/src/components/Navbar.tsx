import React from 'react';
import { ShieldAlert, RefreshCw, Cpu, Activity } from 'lucide-react';

interface NavbarProps {
  onRefresh: () => void;
  loading: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ onRefresh, loading }) => {
  return (
    <header className="bg-slate-950/80 backdrop-blur border-b border-slate-800 sticky top-0 z-30 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
          <ShieldAlert className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-xl font-bold tracking-tight text-white">TriNetra AI</h1>
            <span className="text-[11px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Phase 2
            </span>
          </div>
          <p className="text-xs text-slate-400">Multi-Modal Cross-Organizational Fraud Prevention Engine</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
          <Cpu className="w-4 h-4 text-emerald-400 animate-pulse" />
          <span>Spring Boot 3.2 + Redis + MinIO</span>
        </div>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-md shadow-indigo-600/20 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Queue</span>
        </button>
      </div>
    </header>
  );
};
