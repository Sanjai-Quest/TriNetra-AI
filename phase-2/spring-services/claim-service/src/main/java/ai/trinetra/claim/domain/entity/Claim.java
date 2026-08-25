package ai.trinetra.claim.domain.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "claims")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Claim {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(name = "claim_id", updatable = false, nullable = false)
    private UUID claimId;

    @Column(name = "customer_id", nullable = false)
    private UUID customerId;

    @Column(name = "order_id")
    private String orderId;

    @Column(name = "product_id")
    private String productId;

    @Column(name = "product_category")
    private String productCategory;

    @Column(name = "product_value", precision = 12, scale = 2)
    private BigDecimal productValue;

    @Column(name = "claim_amount", precision = 12, scale = 2)
    private BigDecimal claimAmount;

    @Column(name = "claim_reason", columnDefinition = "TEXT")
    private String claimReason;

    @Column(name = "delivery_date")
    private OffsetDateTime deliveryDate;

    @Column(name = "return_date")
    private OffsetDateTime returnDate;

    @Column(name = "tracking_number")
    private String trackingNumber;

    @Column(name = "payment_txn_id")
    private String paymentTxnId;

    @Column(name = "delivery_proof")
    @Builder.Default
    private Boolean deliveryProof = false;

    @Column(name = "status", length = 50)
    @Builder.Default
    private String status = "CREATED";

    @Column(name = "automated_verdict", length = 50)
    private String automatedVerdict;

    @Column(name = "confidence_score")
    private Double confidenceScore;

    @Column(name = "assigned_to")
    private UUID assignedTo;

    @CreationTimestamp
    @Column(name = "created_at", updatable = false)
    private OffsetDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
}
