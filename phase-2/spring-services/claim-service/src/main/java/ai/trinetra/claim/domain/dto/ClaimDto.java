package ai.trinetra.claim.domain.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Builder;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public class ClaimDto {

    public record CreateClaimRequest(
            @NotNull(message = "customerId is mandatory")
            UUID customerId,
            String orderId,
            String productId,
            String productCategory,
            BigDecimal productValue,
            BigDecimal claimAmount,
            String claimReason,
            OffsetDateTime deliveryDate,
            OffsetDateTime returnDate,
            String trackingNumber,
            String paymentTxnId
    ) {}

    @Builder
    public record ClaimSummaryResponse(
            UUID claimId,
            UUID customerId,
            String orderId,
            String productCategory,
            BigDecimal productValue,
            BigDecimal claimAmount,
            String claimReason,
            String status,
            String automatedVerdict,
            Double confidenceScore,
            UUID assignedTo,
            OffsetDateTime createdAt
    ) {}

    @Builder
    public record ClaimDetailResponse(
            UUID claimId,
            UUID customerId,
            String orderId,
            String productId,
            String productCategory,
            BigDecimal productValue,
            BigDecimal claimAmount,
            String claimReason,
            OffsetDateTime deliveryDate,
            OffsetDateTime returnDate,
            String trackingNumber,
            String paymentTxnId,
            Boolean deliveryProof,
            String status,
            String automatedVerdict,
            Double confidenceScore,
            UUID assignedTo,
            OffsetDateTime createdAt,
            OffsetDateTime updatedAt,
            List<Map<String, Object>> fraudSignals,
            Map<String, Object> verdictReasoning,
            List<Map<String, Object>> investigatorActions
    ) {}

    public record OverrideVerdictRequest(
            @NotBlank(message = "verdict must be REFUND, REJECT, or INVESTIGATE")
            String verdict,
            @NotBlank(message = "reasoning justification is mandatory")
            @Size(min = 10, message = "reasoning must be at least 10 characters")
            String reasoning,
            @NotNull(message = "investigatorId is mandatory")
            UUID investigatorId
    ) {}

    public record BulkImportResponse(
            int claimsCreated,
            List<String> claimIds,
            List<Map<String, Object>> errors
    ) {}
}
