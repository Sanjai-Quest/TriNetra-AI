package ai.trinetra.evidence.service;

import ai.trinetra.evidence.domain.entity.Evidence;
import ai.trinetra.evidence.domain.entity.EvidenceArtifact;
import ai.trinetra.evidence.repository.EvidenceArtifactRepository;
import ai.trinetra.evidence.repository.EvidenceRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.time.OffsetDateTime;
import java.util.*;

@Service
@RequiredArgsConstructor
@Slf4j
public class EvidenceService {

    private final EvidenceRepository evidenceRepository;
    private final EvidenceArtifactRepository artifactRepository;
    private final MinioStorageService storageService;
    private final RabbitTemplate rabbitTemplate;
    private final JdbcTemplate jdbcTemplate;

    @Transactional
    public Evidence uploadEvidence(UUID claimId, String evidenceType, MultipartFile file, String metadata) throws Exception {
        UUID evidenceId = UUID.randomUUID();
        String fileUrl = storageService.uploadFile(claimId, evidenceId, file);

        Evidence evidence = Evidence.builder()
                .evidenceId(evidenceId)
                .claimId(claimId)
                .evidenceType(evidenceType)
                .fileUrl(fileUrl)
                .fileSizeBytes(file.getSize())
                .mimeType(file.getContentType())
                .metadata(metadata)
                .status("PENDING")
                .build();

        Evidence saved = evidenceRepository.save(evidence);

        // Update claim status to EVIDENCE_PENDING
        jdbcTemplate.update(
                "UPDATE claims SET status = 'EVIDENCE_PENDING', updated_at = CURRENT_TIMESTAMP WHERE claim_id = ?",
                claimId
        );

        // Publish evidence.uploaded to RabbitMQ
        Map<String, Object> event = Map.of(
                "eventType", "evidence.uploaded",
                "evidenceId", saved.getEvidenceId().toString(),
                "claimId", saved.getClaimId().toString(),
                "evidenceType", saved.getEvidenceType(),
                "fileUrl", fileUrl,
                "timestamp", OffsetDateTime.now().toString()
        );

        try {
            rabbitTemplate.convertAndSend("evidence.uploaded", event);
            log.info("Published evidence.uploaded for evidence: {}", saved.getEvidenceId());
        } catch (Exception e) {
            log.warn("RabbitMQ publish notice: {}", e.getMessage());
        }

        return saved;
    }

    public List<Evidence> getClaimEvidence(UUID claimId) {
        return evidenceRepository.findByClaimIdOrderByUploadedAtAsc(claimId);
    }

    public List<EvidenceArtifact> getEvidenceArtifacts(UUID evidenceId) {
        return artifactRepository.findByEvidenceIdOrderByCreatedAtAsc(evidenceId);
    }
}
