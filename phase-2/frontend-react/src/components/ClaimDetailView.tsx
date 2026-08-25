import React from 'react';
import { ClaimDetail } from '../services/api';
import { AlertOctagon, ShieldCheck, FileText, UserCheck, Calendar, DollarSign, Package } from 'lucide-react';

interface ClaimDetailViewProps {
  claim: ClaimDetail | null;
  onOpenOverride: () => void;
}

export const ClaimDetailView: React.FC<ClaimDetailViewProps> = ({ claim, onOpenOverride }) => {
  if (!claim) {
    return (
      <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-12 text-center text-slate-500 h-full flex flex-col items-center justify-center space-y-3">
        <Package className="w-12 h-12 text-slate-600 animate-bounce" />
        <h3 className="text-sm font-semibold text-slate-400">Select a Claim to Inspect</h3>
        <p className="text-xs text-slate-500 max-w-xs">
          Inspect multi-modal artifacts, detected fraud patterns, and submit investigator override decisions.
        </p>
      </div>
    );
  }

  const getSeverityStyle = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-rose-500/10 border-rose-500/30 text-rose-300';
      case 'high':
        return 'bg-orange-500/10 border-orange-500/30 text-orange-300';
      case 'medium':
        return 'bg-amber-500/10 border-amber-500/30 text-amber-300';
      default:
        return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300';
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-6 backdrop-blur flex flex-col h-full overflow-y-auto space-y-6 shadow-xl">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4 flex items-start justify-between">
        <div>
          <span className="text-[11px] font-mono text-indigo-400 font-bold uppercase tracking-wider block">
            Claim Inspection
          </span>
          <h2 className="text-lg font-bold text-white font-mono mt-0.5">{claim.claimId}</h2>
          <div className="flex items-center space-x-3 text-xs text-slate-400 mt-1">
            <span>Customer: {claim.customerId.substring(0, 8)}...</span>
            <span>•</span>
            <span>Created: {new Date(claim.createdAt).toLocaleDateString()}</span>
          </div>
        </div>

        <button
          onClick={onOpenOverride}
          className="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold px-4 py-2 rounded-xl transition shadow-lg shadow-indigo-500/20"
        >
          Verdict Override
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-500 block">Claim Amount</span>
          <span className="text-sm font-bold text-white mt-1 block">₹{claim.claimAmount || 0}</span>
        </div>
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-500 block">Product Value</span>
          <span className="text-sm font-bold text-slate-300 mt-1 block">₹{claim.productValue || 0}</span>
        </div>
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-500 block">Automated Verdict</span>
          <span className="text-sm font-bold text-indigo-400 mt-1 block">{claim.automatedVerdict || 'PENDING'}</span>
        </div>
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-500 block">Confidence</span>
          <span className="text-sm font-bold text-emerald-400 mt-1 block">
            {Math.round((claim.confidenceScore || 0) * 100)}%
          </span>
        </div>
      </div>

      {/* Fraud Signals Section */}
      <div className="space-y-3">
        <div className="flex items-center space-x-2">
          <AlertOctagon className="w-4 h-4 text-orange-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Detected Fraud Signals ({claim.fraudSignals?.length || 0})
          </h3>
        </div>

        <div className="space-y-2">
          {!claim.fraudSignals || claim.fraudSignals.length === 0 ? (
            <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20 text-xs text-emerald-400 flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4" />
              <span>No fraud signals detected. Clean claim submission.</span>
            </div>
          ) : (
            claim.fraudSignals.map((sig, idx) => (
              <div
                key={sig.signal_id || idx}
                className={`p-3.5 rounded-xl border text-xs space-y-1 ${getSeverityStyle(sig.severity)}`}
              >
                <div className="flex items-center justify-between font-semibold">
                  <span className="uppercase tracking-wide">{sig.signal_type}</span>
                  <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-black/20 font-mono">
                    {sig.severity} • {Math.round(sig.confidence_score * 100)}% conf
                  </span>
                </div>
                <p className="text-slate-300 text-[11px] leading-relaxed">{sig.reasoning}</p>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Automated Reasoning Text */}
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <FileText className="w-4 h-4 text-indigo-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Automated System Reasoning</h3>
        </div>

        <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-300 font-mono leading-relaxed whitespace-pre-wrap">
          {claim.verdictReasoning?.reasoning_text || 'No system reasoning generated yet.'}
        </pre>
      </div>

      {/* Audit Log */}
      {claim.investigatorActions && claim.investigatorActions.length > 0 && (
        <div className="space-y-2 border-t border-slate-800 pt-4">
          <div className="flex items-center space-x-2">
            <UserCheck className="w-4 h-4 text-violet-400" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Investigator Audit Trail</h3>
          </div>

          <div className="space-y-2">
            {claim.investigatorActions.map((action, i) => (
              <div key={i} className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 text-xs space-y-1">
                <div className="flex justify-between text-slate-400 text-[10px]">
                  <span className="font-bold text-violet-400">{action.action_type}</span>
                  <span>{new Date(action.created_at).toLocaleString()}</span>
                </div>
                {action.override_reasoning && (
                  <p className="text-slate-300 text-[11px]">{action.override_reasoning}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
