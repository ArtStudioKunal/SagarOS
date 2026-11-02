# Local SagarOS Manager. No upstream Toolbox binary.
[CmdletBinding()]
param()
$root = Join-Path $env:ProgramData 'SagarOS\Recovery'
while ($true) {
    Clear-Host
    Write-Host '=== SagarOS Manager ===' -ForegroundColor Cyan
    Write-Host '1. Check firewall, network and computer name'
    Write-Host '2. Restore internet (administrator privileges required)'
    Write-Host '3. Open Windows Update'
    Write-Host '4. Exit'
    switch (Read-Host 'Select 1-4') {
        '1' {
            $path = Join-Path $root 'SagarOS-Verify.ps1'
            if (Test-Path $path) { & $path } else { Write-Warning "Verification script missing: $path" }
            Read-Host 'Press Enter' | Out-Null
        }
        '2' {
            $path = Join-Path $root 'SagarOS-Enable-Internet.ps1'
            if (Test-Path $path) {
                Start-Process powershell.exe -Verb RunAs -ArgumentList ('-NoProfile -File "' + $path + '"') -Wait
            } else { Write-Warning "Recovery script missing: $path" }
        }
        '3' { Start-Process 'ms-settings:windowsupdate' }
        '4' { return }
        default { Write-Warning 'Invalid selection.' }
    }
}
