package ai.trinetra.verdict.controller;

import ai.trinetra.verdict.service.VerdictGeneratorService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v2/verdict")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class VerdictController {

    private final VerdictGeneratorService verdictGeneratorService;

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(Map.of("service", "verdict-generator", "status", "UP"));
    }

    @PostMapping("/generate/{claimId}")
    public ResponseEntity<Map<String, String>> generateVerdict(@PathVariable UUID claimId) {
        verdictGeneratorService.generateVerdict(claimId);
        return ResponseEntity.ok(Map.of("claimId", claimId.toString(), "status", "VERDICT_GENERATED"));
    }
}
