package ai.trinetra.fraud.controller;

import ai.trinetra.fraud.service.FraudDetectionService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v2/fraud")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class FraudEngineController {

    private final FraudDetectionService fraudDetectionService;

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(Map.of("service", "fraud-detection-engine", "status", "UP"));
    }

    @PostMapping("/analyze/{claimId}")
    public ResponseEntity<Map<String, String>> triggerAnalysis(@PathVariable UUID claimId) {
        fraudDetectionService.analyzeClaim(claimId);
        return ResponseEntity.ok(Map.of("claimId", claimId.toString(), "status", "ANALYSIS_TRIGGERED"));
    }
}
