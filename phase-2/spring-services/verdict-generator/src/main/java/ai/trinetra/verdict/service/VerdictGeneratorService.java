package ai.trinetra.verdict.service;

import ai.trinetra.verdict.engine.EvidenceReconciliationEngine;
import ai.trinetra.verdict.engine.FraudRiskScorer;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.OffsetDateTime;
import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class VerdictGeneratorService {

    private final EvidenceReconciliationEngine reconciliationEngine;
    private final FraudRiskScorer fraudRiskScorer;
    private final JdbcTemplate jdbcTemplate;
    private final RabbitTemplate rabbitTemplate;
    private final StringRedisTemplate redisTemplate;

    @Transactional
    public void generateVerdict(UUID claimId) {
        log.info("Generating automated verdict for claim: {}", claimId);

        // 1. Fetch fraud signals
        List<Map<String, Object>> signals = jdbcTemplate.queryForList(
                "SELECT * FROM fraud_signals WHERE claim_id = ? ORDER BY confidence_score DESC",
                claimId
        );

        // 2. Fetch evidence metadata
        List<Map<String, Object>> evidenceRows = jdbcTemplate.queryForList(
                "SELECT evidence_type as source, metadata FROM evidence WHERE claim_id = ?",
                claimId
        );

        // 3. Reconcile evidence & compute fraud risk
        EvidenceReconciliationEngine.ReconciliationResult reconResult = reconciliationEngine.reconcile(evidenceRows);
        FraudRiskScorer.ScoreResult scoreResult = fraudRiskScorer.computeScore(signals);

        // 4. Decision matrix
        String verdict;
        double confidence;
        String newStatus;

        if ("critical".equalsIgnoreCase(scoreResult.maxSeverity()) || scoreResult.compositeScore() > 0.75) {
            verdict = "REJECT";
            confidence = Math.max(0.85, scoreResult.compositeScore());
            newStatus = "REJECTED";
        } else if (!reconResult.isConsistent() || (scoreResult.compositeScore() > 0.35 && !signals.isEmpty())) {
            verdict = "INVESTIGATE";
            confidence = Math.min(0.95, scoreResult.compositeScore() + (reconResult.isConsistent() ? 0.0 : 0.20));
            newStatus = "DECISION_PENDING_REVIEW";
        } else {
            verdict = "REFUND";
            confidence = Math.max(0.80, 1.0 - scoreResult.compositeScore());
            newStatus = "APPROVED";
        }

        // 5. Reasoning text
        StringBuilder sb = new StringBuilder();
        sb.append(String.format("Automated Verdict: %s (Risk Score: %.2f, Confidence: %.0f%%)\n", verdict, scoreResult.compositeScore(), confidence * 100));
        if (!signals.isEmpty()) {
            sb.append("\nDetected Signals:\n");
            for (Map<String, Object> sig : signals) {
                sb.append(String.format(" • [%s] %s: %s\n", ((String) sig.get("severity")).toUpperCase(), sig.get("signal_type"), sig.get("reasoning")));
            }
        }
        if (!reconResult.isConsistent()) {
            sb.append("\nStakeholder Discrepancies:\n");
            for (String conflict : reconResult.conflicts()) {
                sb.append(String.format(" • %s\n", conflict));
            }
        }

        // 6. Save to DB
        jdbcTemplate.update(
                "INSERT INTO verdict_reasoning (reasoning_id, claim_id, verdict, evidence_summary, fraud_signals_detected, factor_weights, final_confidence_score, reasoning_text, generated_at) " +
                "VALUES (?, ?, ?, ?::jsonb, ?::jsonb, ?::jsonb, ?, ?, CURRENT_TIMESTAMP)",
                UUID.randomUUID(), claimId, verdict, "{}", "[]", "{}", confidence, sb.toString()
        );

        jdbcTemplate.update(
                "UPDATE claims SET automated_verdict = ?, status = ?, confidence_score = ?, updated_at = CURRENT_TIMESTAMP WHERE claim_id = ?",
                verdict, newStatus, confidence, claimId
        );

        // 7. Cache in Redis
        try {
            redisTemplate.opsForValue().set("trinetra:verdict:" + claimId, verdict, Duration.ofHours(1));
        } catch (Exception ignored) {}

        // 8. Publish verdict.generated
        try {
            rabbitTemplate.convertAndSend("verdict.generated", Map.of(
                    "eventType", "verdict.generated",
                    "claimId", claimId.toString(),
                    "verdict", verdict,
                    "confidenceScore", confidence,
                    "timestamp", OffsetDateTime.now().toString()
            ));
            log.info("Final verdict for claim {}: {} (confidence: {})", claimId, verdict, confidence);
        } catch (Exception e) {
            log.warn("RabbitMQ publish notice: {}", e.getMessage());
        }
    }
}
