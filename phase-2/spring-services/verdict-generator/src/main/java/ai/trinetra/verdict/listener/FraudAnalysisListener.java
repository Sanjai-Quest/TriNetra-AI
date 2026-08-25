package ai.trinetra.verdict.listener;

import ai.trinetra.verdict.service.VerdictGeneratorService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.UUID;

@Component
@RequiredArgsConstructor
@Slf4j
public class FraudAnalysisListener {

    private final VerdictGeneratorService verdictGeneratorService;

    @RabbitListener(queues = "fraud.analysis.complete")
    public void onFraudAnalysisComplete(Map<String, Object> message) {
        log.info("Received fraud.analysis.complete event: {}", message);
        Object claimIdObj = message.get("claimId");
        if (claimIdObj == null) {
            claimIdObj = message.get("claim_id");
        }

        if (claimIdObj != null) {
            try {
                UUID claimId = UUID.fromString(claimIdObj.toString());
                verdictGeneratorService.generateVerdict(claimId);
            } catch (Exception e) {
                log.error("Error generating verdict from event: {}", e.getMessage(), e);
            }
        }
    }
}
