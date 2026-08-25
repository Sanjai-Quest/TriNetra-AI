package ai.trinetra.fraud.service;

import ai.trinetra.fraud.detector.BehavioralAnomalyDetector;
import ai.trinetra.fraud.detector.SerialFraudDetector;
import ai.trinetra.fraud.detector.WardrobingDetector;
import ai.trinetra.fraud.domain.FraudSignal;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class FraudDetectionService {

    private final SerialFraudDetector serialFraudDetector;
    private final BehavioralAnomalyDetector behavioralAnomalyDetector;
    private final WardrobingDetector wardrobingDetector;
    private final JdbcTemplate jdbcTemplate;
    private final RabbitTemplate rabbitTemplate;

    @Transactional
    public void analyzeClaim(UUID claimId) {
        log.info("Running fraud detection analysis for claim: {}", claimId);

        List<Map<String, Object>> claimRows = jdbcTemplate.queryForList(
                "SELECT * FROM claims WHERE claim_id = ?", claimId
        );
        if (claimRows.isEmpty()) {
            log.warn("Claim not found for fraud analysis: {}", claimId);
            return;
        }
        Map<String, Object> claimData = claimRows.get(0);
        UUID customerId = (UUID) claimData.get("customer_id");

        List<FraudSignal> detectedSignals = new ArrayList<>();

        // 1. Serial Fraudster
        serialFraudDetector.detect(claimId, customerId).ifPresent(detectedSignals::add);

        // 2. Behavioral Anomalies
        detectedSignals.addAll(behavioralAnomalyDetector.detect(claimId, claimData));

        // 3. Wardrobing
        wardrobingDetector.detect(claimId).ifPresent(detectedSignals::add);

        // Save detected signals to DB
        for (FraudSignal sig : detectedSignals) {
            jdbcTemplate.update(
                    "INSERT INTO fraud_signals (signal_id, claim_id, signal_type, severity, confidence_score, source_evidence_id, reasoning, cross_claim_indicators, created_at) " +
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?::jsonb, CURRENT_TIMESTAMP)",
                    sig.getSignalId(), sig.getClaimId(), sig.getSignalType(), sig.getSeverity(), sig.getConfidenceScore(),
                    sig.getSourceEvidenceId(), sig.getReasoning(), sig.getCrossClaimIndicators() != null ? sig.getCrossClaimIndicators() : "{}"
            );
        }

        // Update claim status
        jdbcTemplate.update(
                "UPDATE claims SET status = 'DECISION_PENDING_REVIEW', updated_at = CURRENT_TIMESTAMP WHERE claim_id = ?",
                claimId
        );

        // Publish fraud.analysis.complete
        try {
            rabbitTemplate.convertAndSend("fraud.analysis.complete", Map.of(
                    "eventType", "fraud.analysis.complete",
                    "claimId", claimId.toString(),
                    "signalCount", detectedSignals.size(),
                    "timestamp", OffsetDateTime.now().toString()
            ));
            log.info("Fraud analysis completed for claim {}: {} signals found", claimId, detectedSignals.size());
        } catch (Exception e) {
            log.warn("RabbitMQ publish notice: {}", e.getMessage());
        }
    }
}
