# SagarOS Windows 11 VM acceptance test plan

**Current status: NOT INSTALLATION-TESTED.** A successfully built APBX does not establish compatibility or safety on real hardware.

1. Create a disposable Windows 11 Pro or Enterprise VM with a snapshot, virtual NIC, and a working internet connection. Use a version explicitly listed in the playbook manifest (Windows 11 24H2 or 25H2 on this pinned source). Do not use a production PC.
2. Record baseline Windows version, firewall profiles, internet connectivity, device drivers, installed applications, System Restore/BitLocker state, and activation status.
3. Download the **SagarOS-APBX-DEV-UNTESTED** Actions artifact from the successful build run. Extract the artifact ZIP and run only the inner `.apbx` through a supported version of AME Wizard. Read its complete actions before accepting system changes.
4. Complete the installer and restart the VM. Confirm `hostname` returns `SagarOS`.
5. In an elevated PowerShell console, run the persisted `C:\ProgramData\SagarOS\Recovery\SagarOS-Verify.ps1`. Verify firewall is on for Public, Private and Domain with default inbound Block and outbound Allow.
6. Confirm ordinary internet access using a browser and `Test-NetConnection example.com -Port 443`. Also verify DNS resolution, Windows Update access, wireless/Ethernet behavior, and no blanket firewall deny rule.
7. Test `SagarOS-Manager.ps1` in the installed SagarDesktop tools. Check its verification and recovery actions. Test the standalone internet restoration helper and verify it leaves unrelated firewall rules unchanged.
8. Validate Windows Defender, UAC prompts, Windows Security, system recovery, Windows Update, Windows Hello, drivers, Xbox/Gaming Services where relevant, WSL/Docker if needed, and software installers.
9. Restore the VM snapshot and repeat installation to confirm it behaves consistently. Preserve logs, console output, and screenshots for issues. **Do not label a release production-ready if any check fails.**

**Limitations:** Network connectivity means SagarOS is not air-gapped and does not guarantee anonymity or complete privacy. Other firewall policies, third-party software and routers can still affect traffic. The user remains responsible for Microsoft Windows licensing.
