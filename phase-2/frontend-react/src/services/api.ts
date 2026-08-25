import axios from 'axios';

const CLAIM_API = 'http://localhost:8080/api/v2';
const EVIDENCE_API = 'http://localhost:8081/api/v2';

export interface ClaimSummary {
  claimId: string;
  customerId: string;
  orderId?: string;
  productCategory?: string;
  productValue?: number;
  claimAmount?: number;
  claimReason?: string;
  status: string;
  automatedVerdict?: string;
  confidenceScore?: number;
  assignedTo?: string;
  createdAt: string;
}

export interface FraudSignal {
  signal_id: string;
  claim_id: string;
  signal_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence_score: number;
  reasoning: string;
  cross_claim_indicators?: any;
}

export interface ClaimDetail extends ClaimSummary {
  productId?: string;
  deliveryDate?: string;
  returnDate?: string;
  trackingNumber?: string;
  paymentTxnId?: string;
  deliveryProof?: boolean;
  updatedAt?: string;
  fraudSignals?: FraudSignal[];
  verdictReasoning?: {
    verdict: string;
    final_confidence_score: number;
    reasoning_text: string;
    generated_at: string;
  };
  investigatorActions?: Array<{
    action_type: string;
    override_verdict?: string;
    override_reasoning?: string;
    created_at: string;
  }>;
}

export const fetchClaims = async (status?: string, page = 0, size = 50): Promise<{ claims: ClaimSummary[]; total: number }> => {
  try {
    const params: any = { page, size };
    if (status && status !== 'ALL') params.status = status;
    const res = await axios.get(`${CLAIM_API}/claims/search`, { params });
    return {
      claims: res.data.claims || [],
      total: res.data.total || 0,
    };
  } catch (error) {
    console.error('Failed to fetch claims:', error);
    return { claims: [], total: 0 };
  }
};

export const fetchClaimDetail = async (claimId: string): Promise<ClaimDetail | null> => {
  try {
    const res = await axios.get(`${CLAIM_API}/claims/${claimId}`);
    return res.data;
  } catch (error) {
    console.error(`Failed to fetch claim detail for ${claimId}:`, error);
    return null;
  }
};

export const submitVerdictOverride = async (
  claimId: string,
  verdict: string,
  reasoning: string,
  investigatorId = '00000000-0000-0000-0000-000000000001'
) => {
  return axios.post(`${CLAIM_API}/claims/${claimId}/override`, {
    verdict,
    reasoning,
    investigatorId,
  });
};
