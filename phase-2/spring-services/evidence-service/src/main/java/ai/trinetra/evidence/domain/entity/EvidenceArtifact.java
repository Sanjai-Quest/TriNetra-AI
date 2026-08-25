package ai.trinetra.evidence.domain.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "evidence_artifacts")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class EvidenceArtifact {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "artifact_id", updatable = false, nullable = false)
    private UUID artifactId;

    @Column(name = "evidence_id", nullable = false)
    private UUID evidenceId;

    @Column(name = "artifact_type", length = 50, nullable = false)
    private String artifactType;

    @Column(name = "content_type", length = 50)
    @Builder.Default
    private String contentType = "json";

    @Column(name = "data", columnDefinition = "JSONB", nullable = false)
    private String data;

    @Column(name = "confidence_score")
    private Double confidenceScore;

    @Column(name = "processor_service", length = 100)
    private String processorService;

    @Column(name = "processing_duration_ms")
    private Integer processingDurationMs;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;
}
