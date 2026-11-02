#Requires -RunAsAdministrator
# Executed at the END of the SagarOS playbook. Does not disable network adapters.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$recovery = Join-Path $env:ProgramData 'SagarOS\Recovery'
$helper = Join-Path $PSScriptRoot 'SagarOS-Enable-Internet.ps1'
$verify = Join-Path $PSScriptRoot 'SagarOS-Verify.ps1'
foreach ($path in @($helper,$verify)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Required recovery file missing: $path" }
}
New-Item -ItemType Directory -Path $recovery -Force | Out-Null
Copy-Item -LiteralPath $helper -Destination $recovery -Force -ErrorAction Stop
Copy-Item -LiteralPath $verify -Destination $recovery -Force -ErrorAction Stop
& $helper -Silent
if ($env:COMPUTERNAME -ine 'SagarOS') {
    Rename-Computer -NewName 'SagarOS' -Force -ErrorAction Stop
    Write-Host 'Hostname change takes effect after restart.'
}
Write-Host "SagarOS configuration applied. Network recovery scripts: $recovery"
