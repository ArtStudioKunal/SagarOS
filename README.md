# SagarOS

**SagarOS** is an independent, experimental Windows 11 optimization playbook based on [AtlasOS](https://github.com/Atlas-OS/Atlas) (GPL-3.0).

> **Development status:** Source/bootstrap project. No Windows installation has been validated. Do **not** install on your primary PC until the Windows virtual-machine test plan passes.

## Intended behavior
- Display **SagarOS** throughout the playbook, post-install configuration and desktop branding.
- Rename the Windows computer to `SagarOS` after installation (requires a reboot).
- Keep **Windows Firewall enabled** on all profiles, with inbound connections blocked by default and outbound internet access allowed.
- **Do not** disable Wi-Fi or Ethernet adapters. Internet, browsers and downloads should work.
- Retain privacy-oriented Windows tweaks and **keep UAC secure desktop enabled**.
- Replace the optional upstream Atlas Toolbox download with a local SagarOS manager, not a relabeled upstream executable.
- Preserve upstream GPL-3.0 license notices and the identities of bundled Windows CAB component packages for compatibility.

## Source / building
This repo will hold the SagarOS build scripts, customizations, checks and CI workflow. A GitHub Actions runner can check out the **pinned AtlasOS 0.5.0-hotfix commit** `6cbd1a3401ae3bc73a1ad1b6eba324a7813fa48c`, apply the modifications, and attempt an **untested development** `.apbx` build.

This repository deliberately does not claim to contain a modified Windows ISO or a production-certified installer. Windows licensing, activation and hardware compatibility remain subject to Microsoft Windows requirements.

## Security
The firewall should remain enabled, but **normal internet access means that applications can communicate online**. This is not an air-gapped or complete-anonymity operating system. Validate the final firewall policy and network connectivity in a disposable Windows VM before deployment.

## Attribution and licensing
The upstream AtlasOS Playbook is [GPL-3.0](https://github.com/Atlas-OS/Atlas/blob/main/LICENSE), Copyright its respective contributors. The SagarOS modifications are derivative source material, **not an official AtlasOS release**. The Atlas name is retained here only for attribution and dependency links. The independent SagarOS playbook must retain the source code and GPL licensing notices of redistributed upstream materials.
