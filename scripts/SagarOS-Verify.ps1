# SagarOS post-install verification (run after reboot). Read-only checks.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$profiles = @(Get-NetFirewallProfile -PolicyStore ActiveStore -Profile Domain,Private,Public -ErrorAction Stop)
$firewallOK = ($profiles.Count -eq 3) -and (@($profiles | Where-Object {
    -not $_.Enabled -or "$($_.DefaultInboundAction)" -ne 'Block' -or
    "$($_.DefaultOutboundAction)" -ne 'Allow'
}).Count -eq 0)
$blocked = @('SagarOS-DenyAll-Inbound','SagarOS-DenyAll-Outbound') |
    Where-Object { Get-NetFirewallRule -PolicyStore ActiveStore -Name $_ -ErrorAction SilentlyContinue }
$nameOK = $env:COMPUTERNAME -ieq 'SagarOS'
$adapters = @(Get-NetAdapter -ErrorAction Stop)
$adapterOK = @($adapters | Where-Object { $_.Status -ne 'Disabled' }).Count -gt 0
$result = [pscustomobject]@{
    ComputerName=$env:COMPUTERNAME; Renamed=$nameOK
    FirewallProtecting=$firewallOK; OldBlanketBlockRemoved=(@($blocked).Count -eq 0)
    NetworkAdapterAvailable=$adapterOK
}
$result | Format-List
if (-not ($nameOK -and $firewallOK -and @($blocked).Count -eq 0 -and $adapterOK)) {
    throw 'SagarOS post-install checks failed.'
}
Write-Host 'Configuration passed. Verify internet: Test-NetConnection example.com -Port 443.'
