# TriNetra AI Phase 2: Start Services & UI Script
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  TriNetra AI — Phase 2 Architecture Launcher       " -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# 1. Start Infrastructure via Docker (if Docker Desktop running)
Write-Host "`n[1/3] Checking Docker infrastructure..." -ForegroundColor Yellow
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker compose -f docker-compose.yml up -d postgres redis rabbitmq minio
    Write-Host "Docker containers started." -ForegroundColor Green
} else {
    Write-Host "Docker command not found in current PATH. Ensure PostgreSQL/Redis/RabbitMQ/MinIO are running locally." -ForegroundColor DarkYellow
}

# 2. Information on Spring Boot services
Write-Host "`n[2/3] Spring Boot Microservices configured under spring-services/:" -ForegroundColor Yellow
Write-Host "  - claim-service (port 8080)" -ForegroundColor White
Write-Host "  - evidence-service (port 8081)" -ForegroundColor White
Write-Host "  - multimodal-processor (port 8082 - Python OpenCV/OCR worker)" -ForegroundColor White
Write-Host "  - fraud-detection-engine (port 8083)" -ForegroundColor White
Write-Host "  - verdict-generator (port 8084)" -ForegroundColor White
Write-Host "  - integration-service (port 8085)" -ForegroundColor White

# 3. Start Frontend Dashboard
Write-Host "`n[3/3] Starting React + TypeScript Frontend on port 3000..." -ForegroundColor Yellow
Set-Location "$PSScriptRoot\frontend-react"
& "C:\Program Files\nodejs\npm.cmd" run dev
