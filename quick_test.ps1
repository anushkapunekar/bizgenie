Write-Host "=== BizGenie Quick Test ===" -ForegroundColor Cyan
Write-Host ""

# Test 1: Backend Health
Write-Host "1. Testing Backend Health..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2
    if ($health.status -eq "healthy") {
        Write-Host "   [OK] Backend is healthy" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Backend returned unexpected status" -ForegroundColor Red
    }
} catch {
    Write-Host "   [FAIL] Backend is not running or not accessible" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Gray
    Write-Host "   Start backend with: .\start_backend.ps1" -ForegroundColor Yellow
    exit 1
}

# Test 2: Register a Test Business
Write-Host ""
Write-Host "2. Testing Business Registration..." -ForegroundColor Yellow
$testBusiness = @{
    name = "Test Business"
    description = "A test business for verification"
    services = @("Consulting", "Support")
    working_hours = @{
        monday = @{ open = "09:00"; close = "17:00" }
        tuesday = @{ open = "09:00"; close = "17:00" }
        wednesday = @{ open = "09:00"; close = "17:00" }
        thursday = @{ open = "09:00"; close = "17:00" }
        friday = @{ open = "09:00"; close = "17:00" }
    }
    contact_email = "test@example.com"
    contact_phone = "+1234567890"
}

try {
    $businessJson = $testBusiness | ConvertTo-Json -Depth 10
    $response = Invoke-RestMethod -Uri "http://localhost:8000/business/register" -Method Post -Body $businessJson -ContentType "application/json"
    $businessId = $response.id
    Write-Host "   [OK] Business registered successfully" -ForegroundColor Green
    Write-Host "   Business ID: $businessId" -ForegroundColor Gray
    Write-Host "   Business Name: $($response.name)" -ForegroundColor Gray
} catch {
    Write-Host "   [FAIL] Business registration failed" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Gray
    exit 1
}

# Test 3: Get Business Details
Write-Host ""
Write-Host "3. Testing Get Business..." -ForegroundColor Yellow
try {
    $business = Invoke-RestMethod -Uri "http://localhost:8000/business/$businessId" -Method Get
    Write-Host "   [OK] Business retrieved successfully" -ForegroundColor Green
    Write-Host "   Services: $($business.services -join ', ')" -ForegroundColor Gray
} catch {
    Write-Host "   [FAIL] Failed to retrieve business" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Gray
}

# Test 4: Test Chat
Write-Host ""
Write-Host "4. Testing Chat Endpoint..." -ForegroundColor Yellow
$chatRequest = @{
    business_id = $businessId
    user_name = "Test User"
    user_message = "What services do you offer?"
} | ConvertTo-Json

try {
    $chatResponse = Invoke-RestMethod -Uri "http://localhost:8000/chat/" -Method Post -Body $chatRequest -ContentType "application/json"
    Write-Host "   [OK] Chat endpoint working" -ForegroundColor Green
    Write-Host "   Intent: $($chatResponse.intent)" -ForegroundColor Gray
    Write-Host "   Response preview: $($chatResponse.reply.Substring(0, [Math]::Min(100, $chatResponse.reply.Length)))..." -ForegroundColor Gray
} catch {
    Write-Host "   [FAIL] Chat endpoint failed" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Gray
    Write-Host "   Note: This might fail if LLM is not configured" -ForegroundColor Yellow
}

# Test 5: Frontend Check
Write-Host ""
Write-Host "5. Testing Frontend..." -ForegroundColor Yellow
try {
    $frontend = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -UseBasicParsing
    if ($frontend.StatusCode -eq 200) {
        Write-Host "   [OK] Frontend is accessible" -ForegroundColor Green
    } else {
        Write-Host "   [FAIL] Frontend returned status: $($frontend.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "   [INFO] Frontend is not running" -ForegroundColor Yellow
    Write-Host "   Start frontend with: cd frontend && npm run dev" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  - Backend: Working" -ForegroundColor Green
Write-Host "  - Business Registration: Working" -ForegroundColor Green
Write-Host "  - Chat: Tested (check LLM config if failed)" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open frontend: http://localhost:3000" -ForegroundColor Gray
Write-Host "  2. Register a business via UI" -ForegroundColor Gray
Write-Host "  3. Upload a document" -ForegroundColor Gray
Write-Host "  4. Test the chat interface" -ForegroundColor Gray
Write-Host ""
Write-Host "Business Dashboard: http://localhost:3000/business/$businessId" -ForegroundColor Cyan
Write-Host "Chat Interface: http://localhost:3000/business/$businessId/chat" -ForegroundColor Cyan

