#Requires -RunAsAdministrator
# Migrates old SagarOS strict-offline builds to normal internet access.
[CmdletBinding()]
param([switch]$Silent)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $Silent) {
    Write-Host 'Restore normal internet access (Windows Firewall stays on).' -ForegroundColor Cyan
    if ((Read-Host 'Type ENABLE to continue') -cne 'ENABLE') { throw 'Cancelled.' }
}
if ((Get-Service -Name MpsSvc -ErrorAction Stop).Status -ne 'Running') {
    Start-Service -Name MpsSvc -ErrorAction Stop
}
foreach ($name in @('SagarOS-DenyAll-Inbound','SagarOS-DenyAll-Outbound')) {
    Get-NetFirewallRule -Name $name -ErrorAction SilentlyContinue |
        Remove-NetFirewallRule -ErrorAction Stop
}
Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled True -DefaultInboundAction Block -DefaultOutboundAction Allow -ErrorAction Stop
# Restore ONLY adapters previously enabled before an older SagarOS lockdown.
$csv = Join-Path $env:ProgramData 'SagarOS\Recovery\adapters-before-sagaros.csv'
if (Test-Path -LiteralPath $csv) {
    foreach ($entry in @(Import-Csv -LiteralPath $csv)) {
        if ($entry.Status -eq 'Disabled') { continue }
        $nic = Get-NetAdapter -Name $entry.Name -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $nic) {
            $nic = Get-NetAdapter -ErrorAction SilentlyContinue |
                Where-Object { $_.InterfaceDescription -eq $entry.InterfaceDescription } | Select-Object -First 1
        }
        if ($null -ne $nic -and $nic.Status -eq 'Disabled') {
            Enable-NetAdapter -InputObject $nic -Confirm:$false -ErrorAction Stop | Out-Null
        }
    }
}
$profiles = @(Get-NetFirewallProfile -PolicyStore ActiveStore -Profile Domain,Private,Public -ErrorAction Stop)
if ($profiles.Count -ne 3 -or @($profiles | Where-Object {
    -not $_.Enabled -or "$($_.DefaultInboundAction)" -ne 'Block' -or
    "$($_.DefaultOutboundAction)" -ne 'Allow'
}).Count -gt 0) { throw 'Effective firewall policy does not match expected defaults.' }
foreach ($name in @('SagarOS-DenyAll-Inbound','SagarOS-DenyAll-Outbound')) {
    if (Get-NetFirewallRule -PolicyStore ActiveStore -Name $name -ErrorAction SilentlyContinue) {
        throw "Legacy blanket block rule remains: $name"
    }
}
Write-Host 'SagarOS online firewall policy verified. Other restrictions may still affect network access.' -ForegroundColor Green
