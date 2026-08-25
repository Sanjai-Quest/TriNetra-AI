package ai.trinetra.fraud.listener;

import ai.trinetra.fraud.service.FraudDetectionService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.UUID;

@Component
@RequiredArgsConstructor
@Slf4j
public class EvidenceProcessedListener {

    private final FraudDetectionService fraudDetectionService;

    @RabbitListener(queues = "evidence.processed")
    public void onEvidenceProcessed(Map<String, Object> message) {
        log.info("Received evidence.processed event: {}", message);
        Object claimIdObj = message.get("claimId");
        if (claimIdObj == null) {
            claimIdObj = message.get("claim_id");
        }

        if (claimIdObj != null) {
            try {
                UUID claimId = UUID.fromString(claimIdObj.toString());
                fraudDetectionService.analyzeClaim(claimId);
            } catch (Exception e) {
                log.error("Error running fraud analysis from event: {}", e.getMessage(), e);
            }
        }
    }
}
