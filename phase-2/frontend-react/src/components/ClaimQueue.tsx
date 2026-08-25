import React, { useState } from 'react';
import { ClaimSummary } from '../services/api';
import { AlertTriangle, CheckCircle2, XCircle, Search, Filter, ArrowUpRight, Clock } from 'lucide-react';

interface ClaimQueueProps {
  claims: ClaimSummary[];
  selectedClaimId: string | null;
  onSelectClaim: (claimId: string) => void;
  statusFilter: string;
  onFilterChange: (status: string) => void;
  loading: boolean;
}

export const ClaimQueue: React.FC<ClaimQueueProps> = ({
  claims,
  selectedClaimId,
  onSelectClaim,
  statusFilter,
  onFilterChange,
  loading,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = claims.filter(c => {
    const term = searchTerm.toLowerCase();
    return (
      c.claimId.toLowerCase().includes(term) ||
      (c.orderId && c.orderId.toLowerCase().includes(term)) ||
      (c.productCategory && c.productCategory.toLowerCase().includes(term))
    );
  });

  const getVerdictBadge = (verdict?: string) => {
    if (!verdict) {
      return (
        <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
          <Clock className="w-3 h-3" />
          <span>PENDING</span>
        </span>
      );
    }
    switch (verdict.toUpperCase()) {
      case 'REFUND':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3" />
            <span>REFUND</span>
          </span>
        );
      case 'REJECT':
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3 h-3" />
            <span>REJECT</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3 h-3" />
            <span>INVESTIGATE</span>
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden backdrop-blur flex flex-col h-full shadow-xl">
      {/* Filters Header */}
      <div className="p-4 border-b border-slate-800/80 flex flex-col sm:flex-row gap-3 items-center justify-between bg-slate-950/40">
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Claim / Order / Category..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-500" />
          <select
            value={statusFilter}
            onChange={e => onFilterChange(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
          >
            <option value="DECISION_PENDING_REVIEW">Pending Review</option>
            <option value="APPROVED">Approved (Refund)</option>
            <option value="REJECTED">Rejected</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="ALL">All Statuses</option>
          </select>
        </div>
      </div>

      {/* Claims List Table */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60">
        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs">Loading queue...</div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">No claims found in this queue.</div>
        ) : (
          filtered.map(claim => {
            const isSelected = claim.claimId === selectedClaimId;
            const conf = Math.round((claim.confidenceScore || 0) * 100);

            return (
              <div
                key={claim.claimId}
                onClick={() => onSelectClaim(claim.claimId)}
                className={`p-4 cursor-pointer transition flex items-center justify-between ${
                  isSelected ? 'bg-indigo-600/10 border-l-4 border-indigo-500' : 'hover:bg-slate-800/40'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold text-indigo-400">
                      {claim.claimId.substring(0, 8)}...
                    </span>
                    <span className="text-xs text-slate-400">
                      {claim.orderId ? `Order: ${claim.orderId}` : 'No Order ID'}
                    </span>
                  </div>

                  <div className="flex items-center space-x-3 text-xs text-slate-300">
                    <span className="font-semibold text-white">₹{claim.claimAmount || 0}</span>
                    <span className="text-slate-500">•</span>
                    <span className="text-slate-400">{claim.productCategory || 'General'}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    {getVerdictBadge(claim.automatedVerdict)}
                    <div className="mt-1 text-[11px] text-slate-400 font-mono">
                      Conf: <span className="text-slate-200">{conf}%</span>
                    </div>
                  </div>

                  <button className="p-1.5 rounded-lg bg-slate-800 text-slate-400 hover:text-white transition">
                    <ArrowUpRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
