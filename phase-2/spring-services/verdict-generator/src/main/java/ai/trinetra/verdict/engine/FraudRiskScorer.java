package ai.trinetra.verdict.engine;

import org.springframework.stereotype.Component;

import java.util.*;

@Component
public class FraudRiskScorer {

    private static final Map<String, Double> SEVERITY_WEIGHTS = Map.of(
            "critical", 0.40,
            "high", 0.25,
            "medium", 0.12,
            "low", 0.05
    );

    public record ScoreResult(
            double compositeScore,
            String maxSeverity,
            Map<String, Object> factorBreakdown
    ) {}

    public ScoreResult computeScore(List<Map<String, Object>> signals) {
        if (signals == null || signals.isEmpty()) {
            return new ScoreResult(0.0, null, Collections.emptyMap());
        }

        double rawScore = 0.0;
        String maxSev = "low";
        Map<String, Object> breakdown = new HashMap<>();

        for (Map<String, Object> sig : signals) {
            String sev = ((String) sig.getOrDefault("severity", "low")).toLowerCase();
            double conf = Double.parseDouble(sig.getOrDefault("confidence_score", "0.5").toString());
            double weight = SEVERITY_WEIGHTS.getOrDefault(sev, 0.05);

            double contribution = weight * conf;
            rawScore += contribution;

            if ("critical".equals(sev)) maxSev = "critical";
            else if ("high".equals(sev) && !"critical".equals(maxSev)) maxSev = "high";
            else if ("medium".equals(sev) && "low".equals(maxSev)) maxSev = "medium";

            String type = (String) sig.get("signal_type");
            breakdown.put(type, Map.of("severity", sev, "confidence", conf, "contribution", Math.round(contribution * 1000.0) / 1000.0));
        }

        double finalScore = Math.min(1.0, Math.round(rawScore * 10000.0) / 10000.0);
        return new ScoreResult(finalScore, maxSev, breakdown);
    }
}
