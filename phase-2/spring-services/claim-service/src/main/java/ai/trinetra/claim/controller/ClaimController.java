package ai.trinetra.claim.controller;

import ai.trinetra.claim.domain.dto.ClaimDto.*;
import ai.trinetra.claim.domain.entity.Claim;
import ai.trinetra.claim.service.ClaimService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v2/claims")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class ClaimController {

    private final ClaimService claimService;

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(Map.of("service", "claim-service", "status", "UP"));
    }

    @PostMapping
    public ResponseEntity<Map<String, Object>> createClaim(@Valid @RequestBody CreateClaimRequest request) {
        Claim claim = claimService.createClaim(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(Map.of(
                "claimId", claim.getClaimId().toString(),
                "status", claim.getStatus(),
                "createdAt", claim.getCreatedAt() != null ? claim.getCreatedAt().toString() : ""
        ));
    }

    @GetMapping("/search")
    public ResponseEntity<Map<String, Object>> searchClaims(
            @RequestParam(required = false) String status,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "50") int size
    ) {
        Page<ClaimSummaryResponse> result = claimService.searchClaims(status, page, size);
        return ResponseEntity.ok(Map.of(
                "claims", result.getContent(),
                "total", result.getTotalElements(),
                "totalPages", result.getTotalPages(),
                "page", page,
                "size", size
        ));
    }

    @GetMapping("/{claimId}")
    public ResponseEntity<ClaimDetailResponse> getClaimDetail(@PathVariable UUID claimId) {
        return ResponseEntity.ok(claimService.getClaimDetail(claimId));
    }

    @PostMapping("/{claimId}/assign")
    public ResponseEntity<Map<String, String>> assignClaim(
            @PathVariable UUID claimId,
            @RequestParam UUID investigatorId
    ) {
        claimService.assignClaim(claimId, investigatorId);
        return ResponseEntity.ok(Map.of("claimId", claimId.toString(), "assignedTo", investigatorId.toString()));
    }

    @PostMapping("/{claimId}/override")
    public ResponseEntity<Map<String, String>> overrideVerdict(
            @PathVariable UUID claimId,
            @Valid @RequestBody OverrideVerdictRequest request
    ) {
        claimService.overrideVerdict(claimId, request);
        return ResponseEntity.ok(Map.of(
                "claimId", claimId.toString(),
                "verdict", request.verdict(),
                "status", "UPDATED"
        ));
    }

    @PostMapping("/bulk-import")
    public ResponseEntity<BulkImportResponse> bulkImport(@RequestParam("file") MultipartFile file) throws Exception {
        return ResponseEntity.ok(claimService.bulkImportCsv(file));
    }
}
