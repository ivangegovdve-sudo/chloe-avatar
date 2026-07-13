# chloe-avatar-serve - idempotent starter for the avatar demo server.
# Registered as a Printing Press tool: pp run chloe-avatar-serve
# Bounded run, durable effect: the spawned server outlives this script
# and any Claude session. Safe to run repeatedly. ASCII only (PS 5.1).

$port = 8471
$dir = "D:\projects\chloe-avatar"
$tailPort = 8443

$listening = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($listening) {
    Write-Host "server: already listening on :$port (pid $($listening[0].OwningProcess))"
} else {
    $proc = Start-Process -FilePath "python" `
        -ArgumentList "-m", "http.server", "$port", "--directory", $dir `
        -WindowStyle Hidden -PassThru
    Start-Sleep -Seconds 2
    $check = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($check) { Write-Host "server: started (pid $($proc.Id)) on :$port" }
    else { Write-Host "server: FAILED to start"; exit 1 }
}

# tailscale serve is idempotent - re-applying the same mapping is a no-op
tailscale serve --bg --https=$tailPort "http://localhost:$port" 2>&1 | Out-Null
$status = tailscale serve status 2>&1 | Out-String
if ($status -match ":$tailPort") {
    Write-Host "tailscale: https :$tailPort maps to localhost:$port"
} else {
    Write-Host "tailscale: mapping missing - run: tailscale serve --bg --https=$tailPort http://localhost:$port"
    exit 1
}

# end-to-end probe
try {
    $r = Invoke-WebRequest -Uri "http://localhost:$port/demo.html" -UseBasicParsing -TimeoutSec 5
    Write-Host "probe: demo.html HTTP $($r.StatusCode), $($r.RawContentLength) bytes"
} catch {
    Write-Host "probe: FAILED ($($_.Exception.Message))"
    exit 1
}

Write-Host ""
Write-Host "URL: https://desktop-k3j3uqm.tail5837a3.ts.net:$tailPort/demo.html"
