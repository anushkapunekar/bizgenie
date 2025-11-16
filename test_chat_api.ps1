Write-Host "Testing Chat API..." -ForegroundColor Cyan
Write-Host ""

$businessId = Read-Host "Enter Business ID (default: 1)"
if ([string]::IsNullOrWhiteSpace($businessId)) {
    $businessId = 1
}

$userMessage = Read-Host "Enter test message (default: 'What services do you offer?')"
if ([string]::IsNullOrWhiteSpace($userMessage)) {
    $userMessage = "What services do you offer?"
}

$body = @{
    business_id = [int]$businessId
    user_name = "Test User"
    user_message = $userMessage
} | ConvertTo-Json

Write-Host "Sending request..." -ForegroundColor Yellow
Write-Host "Business ID: $businessId" -ForegroundColor Gray
Write-Host "Message: $userMessage" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/chat/" -Method Post -Body $body -ContentType "application/json"
    
    Write-Host "[SUCCESS] Chat API responded!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Yellow
    Write-Host "  Reply: $($response.reply.Substring(0, [Math]::Min(200, $response.reply.Length)))..." -ForegroundColor White
    Write-Host "  Intent: $($response.intent)" -ForegroundColor Cyan
    Write-Host "  Conversation ID: $($response.conversation_id)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Full response:" -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 5
    
} catch {
    Write-Host "[ERROR] Chat API failed!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Status Code: $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Yellow
    }
}

