package ai.trinetra.claim.service;

import ai.trinetra.claim.domain.dto.ClaimDto.*;
import ai.trinetra.claim.domain.entity.Claim;
import ai.trinetra.claim.repository.ClaimRepository;
import com.opencsv.CSVReader;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStreamReader;
import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class ClaimService {

    private final ClaimRepository claimRepository;
    private final RabbitTemplate rabbitTemplate;
    private final JdbcTemplate jdbcTemplate;

    @Transactional
    public Claim createClaim(CreateClaimRequest request) {
        Claim claim = Claim.builder()
                .customerId(request.customerId())
                .orderId(request.orderId())
                .productId(request.productId())
                .productCategory(request.productCategory())
                .productValue(request.productValue())
                .claimAmount(request.claimAmount())
                .claimReason(request.claimReason())
                .deliveryDate(request.deliveryDate())
                .returnDate(request.returnDate())
                .trackingNumber(request.trackingNumber())
                .paymentTxnId(request.paymentTxnId())
                .status("CREATED")
                .build();

        Claim saved = claimRepository.save(claim);

        // Publish claim.created message to RabbitMQ
        Map<String, Object> event = Map.of(
                "eventType", "claim.created",
                "claimId", saved.getClaimId().toString(),
                "customerId", saved.getCustomerId().toString(),
                "productCategory", saved.getProductCategory() != null ? saved.getProductCategory() : "",
                "timestamp", OffsetDateTime.now().toString()
        );
        try {
            rabbitTemplate.convertAndSend("evidence.uploaded", event);
            log.info("Published claim.created event for claim: {}", saved.getClaimId());
        } catch (Exception e) {
            log.warn("RabbitMQ publish failed (continuing transaction): {}", e.getMessage());
        }

        return saved;
    }

    public Page<ClaimSummaryResponse> searchClaims(String status, int page, int size) {
        Page<Claim> claims = claimRepository.searchClaimsForQueue(
                (status != null && !status.isBlank()) ? status : null,
                PageRequest.of(page, size)
        );

        return claims.map(c -> ClaimSummaryResponse.builder()
                .claimId(c.getClaimId())
                .customerId(c.getCustomerId())
                .orderId(c.getOrderId())
                .productCategory(c.getProductCategory())
                .productValue(c.getProductValue())
                .claimAmount(c.getClaimAmount())
                .claimReason(c.getClaimReason())
                .status(c.getStatus())
                .automatedVerdict(c.getAutomatedVerdict())
                .confidenceScore(c.getConfidenceScore())
                .assignedTo(c.getAssignedTo())
                .createdAt(c.getCreatedAt())
                .build());
    }

    public ClaimDetailResponse getClaimDetail(UUID claimId) {
        Claim claim = claimRepository.findById(claimId)
                .orElseThrow(() -> new NoSuchElementException("Claim not found: " + claimId));

        // Safely fetch fraud signals
        List<Map<String, Object>> signals = new ArrayList<>();
        try {
            signals = jdbcTemplate.queryForList(
                    "SELECT * FROM fraud_signals WHERE claim_id = ? ORDER BY created_at DESC",
                    claimId
            );
        } catch (Exception e) {
            log.debug("Notice: fraud_signals query skipped ({})", e.getMessage());
        }

        // Safely fetch verdict reasoning
        Map<String, Object> reasoning = null;
        try {
            List<Map<String, Object>> reasoningList = jdbcTemplate.queryForList(
                    "SELECT * FROM verdict_reasoning WHERE claim_id = ? ORDER BY generated_at DESC LIMIT 1",
                    claimId
            );
            if (!reasoningList.isEmpty()) reasoning = reasoningList.get(0);
        } catch (Exception e) {
            log.debug("Notice: verdict_reasoning query skipped ({})", e.getMessage());
        }

        // Safely fetch investigator actions
        List<Map<String, Object>> actions = new ArrayList<>();
        try {
            actions = jdbcTemplate.queryForList(
                    "SELECT * FROM investigator_actions WHERE claim_id = ? ORDER BY created_at DESC",
                    claimId
            );
        } catch (Exception e) {
            log.debug("Notice: investigator_actions query skipped ({})", e.getMessage());
        }

        return ClaimDetailResponse.builder()
                .claimId(claim.getClaimId())
                .customerId(claim.getCustomerId())
                .orderId(claim.getOrderId())
                .productId(claim.getProductId())
                .productCategory(claim.getProductCategory())
                .productValue(claim.getProductValue())
                .claimAmount(claim.getClaimAmount())
                .claimReason(claim.getClaimReason())
                .deliveryDate(claim.getDeliveryDate())
                .returnDate(claim.getReturnDate())
                .trackingNumber(claim.getTrackingNumber())
                .paymentTxnId(claim.getPaymentTxnId())
                .deliveryProof(claim.getDeliveryProof())
                .status(claim.getStatus())
                .automatedVerdict(claim.getAutomatedVerdict())
                .confidenceScore(claim.getConfidenceScore())
                .assignedTo(claim.getAssignedTo())
                .createdAt(claim.getCreatedAt())
                .updatedAt(claim.getUpdatedAt())
                .fraudSignals(signals)
                .verdictReasoning(reasoning)
                .investigatorActions(actions)
                .build();
    }

    @Transactional
    public void assignClaim(UUID claimId, UUID investigatorId) {
        Claim claim = claimRepository.findById(claimId)
                .orElseThrow(() -> new NoSuchElementException("Claim not found: " + claimId));

        claim.setAssignedTo(investigatorId);
        claimRepository.save(claim);

        try {
            jdbcTemplate.update(
                    "INSERT INTO investigator_actions (action_id, claim_id, investigator_id, action_type, created_at) " +
                    "VALUES (?, ?, ?, 'ASSIGN', CURRENT_TIMESTAMP)",
                    UUID.randomUUID(), claimId, investigatorId
            );
        } catch (Exception e) {
            log.debug("Notice: investigator_actions insert skipped ({})", e.getMessage());
        }
    }

    @Transactional
    public void overrideVerdict(UUID claimId, OverrideVerdictRequest request) {
        Claim claim = claimRepository.findById(claimId)
                .orElseThrow(() -> new NoSuchElementException("Claim not found: " + claimId));

        String newStatus = switch (request.verdict().toUpperCase()) {
            case "REFUND" -> "APPROVED";
            case "REJECT" -> "REJECTED";
            default -> "INVESTIGATING";
        };

        claim.setStatus(newStatus);
        claim.setAutomatedVerdict(request.verdict().toUpperCase());
        claimRepository.save(claim);

        try {
            jdbcTemplate.update(
                    "INSERT INTO investigator_actions " +
                    "(action_id, claim_id, investigator_id, action_type, override_verdict, override_reasoning, created_at) " +
                    "VALUES (?, ?, ?, 'OVERRIDE', ?, ?, CURRENT_TIMESTAMP)",
                    UUID.randomUUID(), claimId, request.investigatorId(), request.verdict(), request.reasoning()
            );
        } catch (Exception e) {
            log.debug("Notice: investigator_actions override insert skipped ({})", e.getMessage());
        }

        // Publish event
        try {
            rabbitTemplate.convertAndSend("verdict.generated", Map.of(
                    "eventType", "verdict.finalized",
                    "claimId", claimId.toString(),
                    "verdict", request.verdict(),
                    "source", "INVESTIGATOR_OVERRIDE",
                    "investigatorId", request.investigatorId().toString(),
                    "timestamp", OffsetDateTime.now().toString()
            ));
        } catch (Exception e) {
            log.warn("RabbitMQ publish error: {}", e.getMessage());
        }
    }

    @Transactional
    public BulkImportResponse bulkImportCsv(MultipartFile file) throws Exception {
        List<String> createdIds = new ArrayList<>();
        List<Map<String, Object>> errors = new ArrayList<>();

        try (CSVReader reader = new CSVReader(new InputStreamReader(file.getInputStream()))) {
            String[] header = reader.readNext();
            String[] line;
            int rowNum = 2;

            while ((line = reader.readNext()) != null) {
                try {
                    UUID customerId = UUID.fromString(line[0].trim());
                    String orderId = line.length > 1 ? line[1].trim() : null;
                    String category = line.length > 2 ? line[2].trim() : null;
                    BigDecimal productVal = line.length > 3 && !line[3].isBlank() ? new BigDecimal(line[3].trim()) : BigDecimal.ZERO;
                    BigDecimal claimAmt = line.length > 4 && !line[4].isBlank() ? new BigDecimal(line[4].trim()) : BigDecimal.ZERO;
                    String reason = line.length > 5 ? line[5].trim() : null;

                    Claim c = Claim.builder()
                            .customerId(customerId)
                            .orderId(orderId)
                            .productCategory(category)
                            .productValue(productVal)
                            .claimAmount(claimAmt)
                            .claimReason(reason)
                            .status("CREATED")
                            .build();

                    Claim saved = claimRepository.save(c);
                    createdIds.add(saved.getClaimId().toString());
                } catch (Exception ex) {
                    errors.add(Map.of("row", rowNum, "error", ex.getMessage()));
                }
                rowNum++;
            }
        }

        return new BulkImportResponse(createdIds.size(), createdIds, errors);
    }
}
