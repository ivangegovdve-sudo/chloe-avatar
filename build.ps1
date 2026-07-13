# Builds the deliverable HTML files from chloe-avatar.template.html + chloe-avatar-core.js.
#   chloe-avatar.html         — pure Three.js (no Theatre.js reference at all; built-in
#                               rAF timing + JS state flags). Open directly in a browser.
#   chloe-avatar-theatre.html — same core with @theatre/core driving ambient loops and
#                               transition easing (falls back to the built-in shim offline).
# Run after any core/template change: pwsh -File build.ps1
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$core = Get-Content (Join-Path $dir 'chloe-avatar-core.js') -Raw
$tpl = Get-Content (Join-Path $dir 'chloe-avatar.template.html') -Raw
$full = $tpl.Replace('/*__CORE__*/', $core)

$full | Set-Content (Join-Path $dir 'chloe-avatar-theatre.html') -NoNewline

# plain variant: strip the Theatre import-map entry and the dynamic import
$plain = $full -replace ',\s*"@theatre/core":\s*"[^"]*"', ''
$plain = $plain -replace '(?s)try \{\r?\n\s*theatre = await import\(''@theatre/core''\);\r?\n\} catch \(e\) \{\r?\n[^\}]*\r?\n\}', '// Theatre.js intentionally not loaded: core uses its built-in rAF timing shim.'
$plain | Set-Content (Join-Path $dir 'chloe-avatar.html') -NoNewline
# index.html — the fleet deliverable (same plain build; canonical embed URL)
$plain | Set-Content (Join-Path $dir 'index.html') -NoNewline

foreach ($f in 'index.html', 'chloe-avatar.html', 'chloe-avatar-theatre.html') {
  Write-Host "$f built ($([math]::Round((Get-Item (Join-Path $dir $f)).Length / 1KB, 1)) KB)"
}
