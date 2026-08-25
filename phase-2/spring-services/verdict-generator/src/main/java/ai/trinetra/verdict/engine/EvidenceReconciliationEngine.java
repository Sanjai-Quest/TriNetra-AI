package ai.trinetra.verdict.engine;

import org.springframework.stereotype.Component;

import java.util.*;

@Component
public class EvidenceReconciliationEngine {

    public record ReconciliationResult(
            boolean isConsistent,
            List<String> conflicts,
            Map<String, Object> details
    ) {}

    public ReconciliationResult reconcile(List<Map<String, Object>> evidenceRecords) {
        List<String> conflicts = new ArrayList<>();
        Map<String, Object> details = new HashMap<>();

        if (evidenceRecords == null || evidenceRecords.size() < 2) {
            return new ReconciliationResult(true, conflicts, details);
        }

        // Compare multi-source attributes
        Double outboundWeight = null;
        Double returnWeight = null;

        for (Map<String, Object> record : evidenceRecords) {
            String source = (String) record.get("source");
            Object weightObj = record.get("weight_grams");
            if (weightObj != null) {
                double w = Double.parseDouble(weightObj.toString());
                if ("WAREHOUSE".equalsIgnoreCase(source) || "CARRIER_OUTBOUND".equalsIgnoreCase(source)) {
                    outboundWeight = w;
                } else if ("RETURN_CENTER".equalsIgnoreCase(source) || "CARRIER_RETURN".equalsIgnoreCase(source)) {
                    returnWeight = w;
                }
            }
        }

        // Weight drop conflict check (Phase 1 rule)
        if (outboundWeight != null && returnWeight != null) {
            double diffPct = Math.abs(outboundWeight - returnWeight) / outboundWeight * 100.0;
            if (diffPct > 10.0) {
                conflicts.add(String.format("Weight discrepancy detected: Outbound=%.1fg vs Return=%.1fg (%.1f%% difference)",
                        outboundWeight, returnWeight, diffPct));
                details.put("weight_diff_pct", diffPct);
            }
        }

        return new ReconciliationResult(conflicts.isEmpty(), conflicts, details);
    }
}
