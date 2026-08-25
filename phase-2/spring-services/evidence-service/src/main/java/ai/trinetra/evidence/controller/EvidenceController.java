package ai.trinetra.evidence.controller;

import ai.trinetra.evidence.domain.entity.Evidence;
import ai.trinetra.evidence.domain.entity.EvidenceArtifact;
import ai.trinetra.evidence.service.EvidenceService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v2/evidence")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class EvidenceController {

    private final EvidenceService evidenceService;

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(Map.of("service", "evidence-service", "status", "UP"));
    }

    @PostMapping("/upload")
    public ResponseEntity<Map<String, Object>> uploadEvidence(
            @RequestParam("claimId") UUID claimId,
            @RequestParam("evidenceType") String evidenceType,
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "metadata", required = false) String metadata
    ) throws Exception {
        Evidence evidence = evidenceService.uploadEvidence(claimId, evidenceType, file, metadata);
        return ResponseEntity.status(HttpStatus.ACCEPTED).body(Map.of(
                "evidenceId", evidence.getEvidenceId().toString(),
                "claimId", evidence.getClaimId().toString(),
                "evidenceType", evidence.getEvidenceType(),
                "status", evidence.getStatus(),
                "fileUrl", evidence.getFileUrl() != null ? evidence.getFileUrl() : ""
        ));
    }

    @GetMapping("/claim/{claimId}")
    public ResponseEntity<Map<String, Object>> getClaimEvidence(@PathVariable UUID claimId) {
        List<Evidence> list = evidenceService.getClaimEvidence(claimId);
        return ResponseEntity.ok(Map.of("claimId", claimId.toString(), "evidence", list));
    }

    @GetMapping("/{evidenceId}/artifacts")
    public ResponseEntity<Map<String, Object>> getArtifacts(@PathVariable UUID evidenceId) {
        List<EvidenceArtifact> artifacts = evidenceService.getEvidenceArtifacts(evidenceId);
        return ResponseEntity.ok(Map.of(
                "evidenceId", evidenceId.toString(),
                "artifactCount", artifacts.size(),
                "artifacts", artifacts
        ));
    }
}
