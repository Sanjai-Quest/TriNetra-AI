package ai.trinetra.fraud.domain;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "fraud_signals")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class FraudSignal {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "signal_id", updatable = false, nullable = false)
    private UUID signalId;

    @Column(name = "claim_id", nullable = false)
    private UUID claimId;

    @Column(name = "signal_type", length = 100, nullable = false)
    private String signalType;

    @Column(name = "severity", length = 20, nullable = false)
    private String severity; // low, medium, high, critical

    @Column(name = "confidence_score", nullable = false)
    private Double confidenceScore;

    @Column(name = "source_evidence_id")
    private UUID sourceEvidenceId;

    @Column(name = "reasoning", columnDefinition = "TEXT")
    private String reasoning;

    @Column(name = "cross_claim_indicators", columnDefinition = "JSONB")
    private String crossClaimIndicators;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;

    @Column(name = "processed_at")
    private OffsetDateTime processedAt;
}
