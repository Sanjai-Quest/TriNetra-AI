package ai.trinetra.integration.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/webhooks")
@RequiredArgsConstructor
@Slf4j
@CrossOrigin(origins = "*")
public class WebhookController {

    private final JdbcTemplate jdbcTemplate;
    private final RabbitTemplate rabbitTemplate;

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(Map.of("service", "integration-service", "status", "UP"));
    }

    @PostMapping("/shipping/delivered")
    public ResponseEntity<Map<String, Object>> handleShippingDelivery(@RequestBody Map<String, Object> payload) {
        String trackingNumber = (String) payload.get("trackingNumber");
        log.info("Received shipping delivery webhook for tracking: {}", trackingNumber);

        // Update claim delivery status if found
        if (trackingNumber != null) {
            jdbcTemplate.update(
                    "UPDATE claims SET delivery_proof = TRUE, delivery_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE tracking_number = ?",
                    trackingNumber
            );
        }

        // Store event
        jdbcTemplate.update(
                "INSERT INTO integration_events (event_id, provider, event_type, payload, status, created_at) " +
                "VALUES (?, 'shipping_carrier', 'delivery_confirmed', ?::jsonb, 'success', CURRENT_TIMESTAMP)",
                UUID.randomUUID(), "{}"
        );

        return ResponseEntity.accepted().body(Map.of("status", "received", "trackingNumber", trackingNumber != null ? trackingNumber : ""));
    }

    @PostMapping("/payment/refund-status")
    public ResponseEntity<Map<String, Object>> handlePaymentStatus(@RequestBody Map<String, Object> payload) {
        String txnId = (String) payload.get("transactionId");
        String refundStatus = (String) payload.getOrDefault("refundStatus", "completed");
        log.info("Received payment refund webhook for txn: {}, status: {}", txnId, refundStatus);

        if (txnId != null && "completed".equalsIgnoreCase(refundStatus)) {
            jdbcTemplate.update(
                    "UPDATE claims SET status = 'CLOSED', updated_at = CURRENT_TIMESTAMP WHERE payment_txn_id = ?",
                    txnId
            );
        }

        jdbcTemplate.update(
                "INSERT INTO integration_events (event_id, provider, event_type, payload, status, created_at) " +
                "VALUES (?, 'payment_processor', 'refund_processed', ?::jsonb, 'success', CURRENT_TIMESTAMP)",
                UUID.randomUUID(), "{}"
        );

        return ResponseEntity.accepted().body(Map.of("status", "received", "transactionId", txnId != null ? txnId : ""));
    }
}
