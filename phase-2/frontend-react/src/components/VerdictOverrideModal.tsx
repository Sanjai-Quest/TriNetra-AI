import React, { useState } from 'react';
import { X, Check, AlertTriangle } from 'lucide-react';
import { submitVerdictOverride } from '../services/api';

interface VerdictOverrideModalProps {
  claimId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const VerdictOverrideModal: React.FC<VerdictOverrideModalProps> = ({
  claimId,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [verdict, setVerdict] = useState('REFUND');
  const [reasoning, setReasoning] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (reasoning.trim().length < 10) {
      setError('Reasoning justification must be at least 10 characters.');
      return;
    }

    try {
      setSubmitting(true);
      setError('');
      await submitVerdictOverride(claimId, verdict, reasoning.trim());
      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to submit override decision.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div>
            <h3 className="text-base font-bold text-white">Investigator Verdict Override</h3>
            <p className="text-xs text-slate-400 font-mono mt-0.5">Claim: {claimId}</p>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5 uppercase">Override Decision</label>
            <select
              value={verdict}
              onChange={e => setVerdict(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 font-semibold"
            >
              <option value="REFUND">Approve Refund (REFUND)</option>
              <option value="REJECT">Reject Claim (REJECT)</option>
              <option value="INVESTIGATE">Flag for Further Investigation (INVESTIGATE)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-300 block mb-1.5 uppercase">
              Audit Justification (Min. 10 chars)
            </label>
            <textarea
              rows={4}
              value={reasoning}
              onChange={e => setReasoning(e.target.value)}
              placeholder="Detail reasons for overriding automated system verdict..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 resize-none"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="flex items-center space-x-1.5 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white text-xs font-semibold px-5 py-2 rounded-xl transition shadow-lg shadow-indigo-600/20 disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              <span>{submitting ? 'Submitting...' : 'Save Decision'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
