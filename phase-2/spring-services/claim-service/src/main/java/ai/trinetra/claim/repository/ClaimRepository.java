package ai.trinetra.claim.repository;

import ai.trinetra.claim.domain.entity.Claim;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ClaimRepository extends JpaRepository<Claim, UUID> {

    List<Claim> findByCustomerId(UUID customerId);

    Optional<Claim> findByTrackingNumber(String trackingNumber);

    Optional<Claim> findByPaymentTxnId(String paymentTxnId);

    @Query("SELECT c FROM Claim c WHERE (:status IS NULL OR c.status = :status) " +
           "ORDER BY c.confidenceScore ASC NULLS FIRST, c.createdAt DESC")
    Page<Claim> searchClaimsForQueue(@Param("status") String status, Pageable pageable);

    @Query("SELECT COUNT(c) FROM Claim c WHERE c.customerId = :customerId AND c.createdAt >= :cutoffDate")
    long countRecentClaimsByCustomer(@Param("customerId") UUID customerId, @Param("cutoffDate") OffsetDateTime cutoffDate);
}
