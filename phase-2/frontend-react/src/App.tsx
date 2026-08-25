import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { ClaimQueue } from './components/ClaimQueue';
import { ClaimDetailView } from './components/ClaimDetailView';
import { VerdictOverrideModal } from './components/VerdictOverrideModal';
import { ClaimDetail, ClaimSummary, fetchClaimDetail, fetchClaims } from './services/api';

export const App: React.FC = () => {
  const [claims, setClaims] = useState<ClaimSummary[]>([]);
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);
  const [selectedClaim, setSelectedClaim] = useState<ClaimDetail | null>(null);
  const [statusFilter, setStatusFilter] = useState('DECISION_PENDING_REVIEW');
  const [loading, setLoading] = useState(false);
  const [overrideModalOpen, setOverrideModalOpen] = useState(false);

  const loadClaims = async () => {
    setLoading(true);
    const data = await fetchClaims(statusFilter);
    setClaims(data.claims);
    if (data.claims.length > 0 && !selectedClaimId) {
      setSelectedClaimId(data.claims[0].claimId);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadClaims();
  }, [statusFilter]);

  useEffect(() => {
    if (selectedClaimId) {
      fetchClaimDetail(selectedClaimId).then(setSelectedClaim);
    } else {
      setSelectedClaim(null);
    }
  }, [selectedClaimId]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased">
      <Navbar onRefresh={loadClaims} loading={loading} />

      <main className="flex-1 p-6 grid grid-cols-12 gap-6 max-w-[1600px] w-full mx-auto">
        {/* Left Column: Queue */}
        <div className="col-span-12 lg:col-span-5 h-[calc(100vh-120px)]">
          <ClaimQueue
            claims={claims}
            selectedClaimId={selectedClaimId}
            onSelectClaim={setSelectedClaimId}
            statusFilter={statusFilter}
            onFilterChange={setStatusFilter}
            loading={loading}
          />
        </div>

        {/* Right Column: Claim Details & Inspector */}
        <div className="col-span-12 lg:col-span-7 h-[calc(100vh-120px)]">
          <ClaimDetailView
            claim={selectedClaim}
            onOpenOverride={() => setOverrideModalOpen(true)}
          />
        </div>
      </main>

      {/* Override Modal */}
      {selectedClaimId && (
        <VerdictOverrideModal
          claimId={selectedClaimId}
          isOpen={overrideModalOpen}
          onClose={() => setOverrideModalOpen(false)}
          onSuccess={() => {
            loadClaims();
            if (selectedClaimId) fetchClaimDetail(selectedClaimId).then(setSelectedClaim);
          }}
        />
      )}
    </div>
  );
};

export default App;
