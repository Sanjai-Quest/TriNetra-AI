package ai.trinetra.evidence.domain.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "evidence")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Evidence {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "evidence_id", updatable = false, nullable = false)
    private UUID evidenceId;

    @Column(name = "claim_id", nullable = false)
    private UUID claimId;

    @Column(name = "evidence_type", length = 50, nullable = false)
    private String evidenceType; // product_image, receipt, shipping, behavioral

    @Column(name = "file_url", columnDefinition = "TEXT")
    private String fileUrl;

    @Column(name = "file_size_bytes")
    private Long fileSizeBytes;

    @Column(name = "mime_type", length = 100)
    private String mimeType;

    @Column(name = "metadata", columnDefinition = "JSONB")
    private String metadata;

    @Column(name = "status", length = 50)
    @Builder.Default
    private String status = "PENDING";

    @CreationTimestamp
    @Column(name = "uploaded_at", updatable = false)
    private OffsetDateTime uploadedAt;

    @Column(name = "processed_at")
    private OffsetDateTime processedAt;
}
