package ai.trinetra.fraud.detector;

import ai.trinetra.fraud.domain.FraudSignal;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.*;

@Component
@RequiredArgsConstructor
public class WardrobingDetector {

    private final JdbcTemplate jdbcTemplate;

    public Optional<FraudSignal> detect(UUID claimId) {
        List<Map<String, Object>> artifacts = jdbcTemplate.queryForList(
                "SELECT ea.artifact_id, ea.evidence_id, ea.data, ea.confidence_score " +
                "FROM evidence_artifacts ea " +
                "JOIN evidence e ON ea.evidence_id = e.evidence_id " +
                "WHERE e.claim_id = ? AND ea.artifact_type = 'wear_analysis' " +
                "ORDER BY ea.created_at DESC LIMIT 1",
                claimId
        );

        if (artifacts.isEmpty()) {
            return Optional.empty();
        }

        Map<String, Object> artifact = artifacts.get(0);
        Object dataObj = artifact.get("data");
        String dataStr = dataObj != null ? dataObj.toString() : "";

        // Extract wear score heuristic from JSON string or check threshold
        double wearScore = 0.0;
        if (dataStr.contains("wear_score")) {
            try {
                int idx = dataStr.indexOf("\"wear_score\":");
                if (idx != -1) {
                    int end = dataStr.indexOf(",", idx);
                    if (end == -1) end = dataStr.indexOf("}", idx);
                    String val = dataStr.substring(idx + 13, end).trim();
                    wearScore = Double.parseDouble(val);
                }
            } catch (Exception ignored) {}
        }

        if (wearScore >= 0.70) {
            UUID sourceEvidenceId = (UUID) artifact.get("evidence_id");
            return Optional.of(FraudSignal.builder()
                    .signalId(UUID.randomUUID())
                    .claimId(claimId)
                    .signalType("wardrobing")
                    .severity("high")
                    .confidenceScore(wearScore)
                    .sourceEvidenceId(sourceEvidenceId)
                    .reasoning(String.format("Multi-modal image analysis indicates heavy garment wear (score=%.2f). Item condition shows usage before return.", wearScore))
                    .crossClaimIndicators(String.format("{\"wear_score\": %.2f, \"threshold\": 0.70}", wearScore))
                    .build());
        }

        return Optional.empty();
    }
}
