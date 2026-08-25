package ai.trinetra.fraud.detector;

import ai.trinetra.fraud.domain.FraudSignal;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.time.OffsetDateTime;
import java.util.*;

@Component
@RequiredArgsConstructor
@Slf4j
public class SerialFraudDetector {

    private final JdbcTemplate jdbcTemplate;
    private final StringRedisTemplate redisTemplate;

    public Optional<FraudSignal> detect(UUID claimId, UUID customerId) {
        String cacheKey = "trinetra:fraud_pattern:" + customerId;
        String cachedCount = null;
        try {
            cachedCount = redisTemplate.opsForValue().get(cacheKey);
        } catch (Exception e) {
            log.debug("Redis read notice: {}", e.getMessage());
        }

        long returnCount;
        if (cachedCount != null) {
            returnCount = Long.parseLong(cachedCount);
        } else {
            OffsetDateTime cutoff = OffsetDateTime.now().minusDays(90);
            Long count = jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM claims WHERE customer_id = ? AND created_at >= ?",
                    Long.class, customerId, cutoff
            );
            returnCount = count != null ? count : 0;
            try {
                redisTemplate.opsForValue().set(cacheKey, String.valueOf(returnCount), Duration.ofHours(24));
            } catch (Exception e) {
                log.debug("Redis write notice: {}", e.getMessage());
            }
        }

        if (returnCount >= 7) {
            double conf = Math.min(0.95, 0.60 + (returnCount - 7) * 0.05);
            return Optional.of(FraudSignal.builder()
                    .signalId(UUID.randomUUID())
                    .claimId(claimId)
                    .signalType("serial_fraudster")
                    .severity("high")
                    .confidenceScore(conf)
                    .reasoning(String.format("Customer has filed %d claims in the past 90 days (threshold: 7). Pattern indicates serial return abuse.", returnCount))
                    .crossClaimIndicators(String.format("{\"total_returns_90d\": %d, \"threshold\": 7}", returnCount))
                    .build());
        }
        return Optional.empty();
    }
}
