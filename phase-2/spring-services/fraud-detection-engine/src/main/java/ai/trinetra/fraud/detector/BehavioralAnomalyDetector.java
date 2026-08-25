package ai.trinetra.fraud.detector;

import ai.trinetra.fraud.domain.FraudSignal;
import lombok.RequiredArgsConstructor;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.Duration;
import java.time.OffsetDateTime;
import java.util.*;

@Component
@RequiredArgsConstructor
public class BehavioralAnomalyDetector {

    private final JdbcTemplate jdbcTemplate;

    public List<FraudSignal> detect(UUID claimId, Map<String, Object> claimData) {
        List<FraudSignal> signals = new ArrayList<>();

        // 1. Impossibly fast return (< 60 minutes)
        Object delDateObj = claimData.get("delivery_date");
        Object retDateObj = claimData.get("return_date");

        if (delDateObj != null && retDateObj != null) {
            try {
                OffsetDateTime deliveryDate = delDateObj instanceof OffsetDateTime odt ? odt : OffsetDateTime.parse(delDateObj.toString());
                OffsetDateTime returnDate = retDateObj instanceof OffsetDateTime odt ? odt : OffsetDateTime.parse(retDateObj.toString());

                long minutes = Duration.between(deliveryDate, returnDate).toMinutes();
                if (minutes >= 0 && minutes < 60) {
                    signals.add(FraudSignal.builder()
                            .signalId(UUID.randomUUID())
                            .claimId(claimId)
                            .signalType("impossibly_fast_return")
                            .severity("critical")
                            .confidenceScore(0.95)
                            .reasoning(String.format("Product returned within %d minutes of delivery. Insufficient time to assess item legitimately.", minutes))
                            .crossClaimIndicators(String.format("{\"possession_minutes\": %d}", minutes))
                            .build());
                }
            } catch (Exception ignored) {}
        }

        // 2. Inflated claim amount (> 150% of product value)
        Object prodValObj = claimData.get("product_value");
        Object claimAmtObj = claimData.get("claim_amount");

        if (prodValObj != null && claimAmtObj != null) {
            try {
                BigDecimal prodVal = new BigDecimal(prodValObj.toString());
                BigDecimal claimAmt = new BigDecimal(claimAmtObj.toString());

                if (prodVal.compareTo(BigDecimal.ZERO) > 0 && claimAmt.compareTo(prodVal.multiply(BigDecimal.valueOf(1.5))) > 0) {
                    signals.add(FraudSignal.builder()
                            .signalId(UUID.randomUUID())
                            .claimId(claimId)
                            .signalType("inflated_claim_amount")
                            .severity("medium")
                            .confidenceScore(0.75)
                            .reasoning(String.format("Claimed amount (₹%s) exceeds product value (₹%s) by >50%%.", claimAmt, prodVal))
                            .crossClaimIndicators(String.format("{\"claimed\": %s, \"product_value\": %s}", claimAmt, prodVal))
                            .build());
                }
            } catch (Exception ignored) {}
        }

        return signals;
    }
}
