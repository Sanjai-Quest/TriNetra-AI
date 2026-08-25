package ai.trinetra.integration.dlq;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
@RequiredArgsConstructor
@Slf4j
public class DeadLetterQueueHandler {

    private final JdbcTemplate jdbcTemplate;
    private final RabbitTemplate rabbitTemplate;

    @RabbitListener(queues = "integration.events.dlq")
    public void onDeadLetterEvent(Map<String, Object> failedEvent) {
        log.warn("Processing event from Dead Letter Queue: {}", failedEvent);
        int retryCount = Integer.parseInt(failedEvent.getOrDefault("retryCount", "0").toString());

        if (retryCount < 3) {
            long delaySec = (long) Math.pow(2, retryCount);
            log.info("Scheduling retry #{} for failed event after {} seconds", retryCount + 1, delaySec);
            failedEvent.put("retryCount", retryCount + 1);
            // Re-publish after backoff
            try {
                Thread.sleep(delaySec * 1000);
                rabbitTemplate.convertAndSend("integration.events", failedEvent);
            } catch (Exception e) {
                log.error("Retry execution failed: {}", e.getMessage());
            }
        } else {
            log.error("Event exhausted maximum retries (3), marking as permanent failure.");
        }
    }
}
