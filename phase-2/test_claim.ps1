# TriNetra AI Phase 2: Ingest Sample Claim for Testing

$claimPayload = @{
    customerId      = "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
    orderId         = "ORD-9921-ELECTRONICS"
    productId       = "PRD-LAPTOP-PRO-16"
    productCategory = "Electronics"
    productValue    = 85000.00
    claimAmount     = 85000.00
    claimReason     = "Item arrived damaged in transit with broken display."
    deliveryDate    = "2026-08-25T08:00:00Z"
    returnDate      = "2026-08-25T08:25:00Z"  # 25 mins later -> flags 'impossibly_fast_return' (CRITICAL)
    trackingNumber  = "TRK-982347102"
    paymentTxnId    = "TXN-PAY-882310"
} | ConvertTo-Json

Write-Host "Creating sample claim in Claim Service (http://localhost:8080)..." -ForegroundColor Cyan
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8080/api/v2/claims" -Method Post -Body $claimPayload -ContentType "application/json"
    Write-Host "✅ Claim created successfully!" -ForegroundColor Green
    Write-Host "Claim ID: $($response.claimId)" -ForegroundColor Yellow
    Write-Host "Status:   $($response.status)" -ForegroundColor Yellow
    Write-Host "`nNow check your React Dashboard at http://localhost:3000 to see this claim in the Pending Review queue!" -ForegroundColor Green
} catch {
    Write-Host "❌ Error connecting to Claim Service: $_" -ForegroundColor Red
    Write-Host "Ensure the Spring Boot claim-service is running on port 8080." -ForegroundColor DarkYellow
}
