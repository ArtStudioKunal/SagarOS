#!/usr/bin/env python3
"""Transform pinned AtlasOS 0.5.0-hotfix source into an experimental SagarOS playbook.

Run on a disposable source checkout: python tools/prepare_playbook.py --source PATH
Never invokes changes on the build host's live Windows installation.
"""
from __future__ import annotations
import argparse
import pathlib
import re
import shutil
import uuid

UPSTREAM_SHA = "6cbd1a3401ae3bc73a1ad1b6eba324a7813fa48c"
URL = "https://github.com/ArtStudioKunal/SagarOS"
TEXT_EXT = {".ps1", ".psm1", ".psd1", ".cmd", ".bat", ".yml", ".yaml", ".xml",
            ".conf", ".theme", ".reg", ".md", ".txt", ".json", ".url", ".sh"}
RENAMES = (("AtlasModules", "SagarModules"), ("AtlasDesktop", "SagarDesktop"),
           ("AtlasOS", "SagarOS"), ("ATLAS", "SAGAR"), ("Atlas", "Sagar"), ("atlas", "sagar"))
URL_RE = re.compile(r'https?://[^\s"\'<>\]})]+', re.IGNORECASE)
PACKAGE_RE = re.compile(r'(?i)Z-Atlas(?:-NoDefender|-NoTelemetry|-Misc)[a-z0-9._*/\\-]*')


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def put(path: pathlib.Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8", newline="\n")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def replacement(text: str) -> str:
    saved: list[str] = []
    def protect(match: re.Match) -> str:
        saved.append(match.group(0))
        return "___PRESERVEDREF" + str(len(saved) - 1) + "___"
    text = URL_RE.sub(protect, text)
    text = PACKAGE_RE.sub(protect, text)
    for old, new in RENAMES:
        text = text.replace(old, new)
    for index, raw in enumerate(saved):
        text = text.replace("___PRESERVEDREF" + str(index) + "___", raw)
    return text


def remove_upstream_toolbox(source: pathlib.Path) -> None:
    pb = source / "src/playbook"
    conf = pb / "playbook.conf"
    data = read(conf)
    data, count = re.subn(
        r'\s*<CheckboxPage\s+IsRequired="true"\s+Description="Would you like to install AtlasOS Toolbox \(BETA\)\?">.*?</CheckboxPage>',
        "", data, count=1, flags=re.S)
    require(count == 1, "Cannot identify upstream Toolbox option; refusing unsafe patch")
    put(conf, data)

    start = pb / "Configuration/atlas/start.yml"
    data = read(start)
    data, count = re.subn(r'\n\s*#Toolbox\s*\n.*?(?=\n\s*# Browsers)', "\n", data, count=1, flags=re.S)
    require(count == 1, "Cannot identify upstream Toolbox task")
    put(start, data)

    software = pb / "Executables/SOFTWARE.ps1"
    data = read(software)
    data, count = re.subn(r'^\s*\[switch\]\$Toolbox,?\s*\n', "", data, count=1, flags=re.M)
    require(count == 1, "Cannot remove upstream Toolbox software argument")
    # Remove only the bounded Toolbox block; tolerate extra blank lines in upstream.
    marker = "\n# Toolbox\nif ($Toolbox) {"
    following = "\n# Brave\n"
    block_start = data.find(marker)
    block_end = data.find(following, block_start + len(marker))
    require(block_start >= 0 and block_end > block_start,
            "Cannot identify exact upstream Toolbox downloader boundaries")
    data = data[:block_start] + data[block_end:]
    # The removed Toolbox parameter was last in the param list; drop preceding comma.
    data = data.replace("[switch]$Firefox,\n)", "[switch]$Firefox\n)")
    put(software, data)
    for path in (pb / "Executables/AtlasModules/Toolbox",
                 pb / "Executables/AtlasModules/Scripts/installToolbox.ps1"):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()


def rebrand_text_and_paths(source: pathlib.Path) -> None:
    for path in sorted(source.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        rel = path.relative_to(source).as_posix()
        if rel in {"LICENSE", "UPSTREAM-CREDITS.md"} or rel.startswith("src/sxsc/") or "/Packages/" in rel:
            continue
        if path.suffix.lower() not in TEXT_EXT and path.name not in {".atlasPsModulesPath", ".gitignore", ".editorconfig", ".gitattributes"}:
            continue
        try:
            original = read(path)
        except (UnicodeError, OSError):
            continue
        changed = replacement(original)
        if changed != original:
            put(path, changed)

    paths = sorted(source.rglob("*"), key=lambda p: len(p.relative_to(source).parts), reverse=True)
    for path in paths:
        if not path.exists() or ".git" in path.parts:
            continue
        rel = path.relative_to(source).as_posix()
        if rel.startswith("src/sxsc/") or "/Packages/" in rel:
            continue
        name = ".sagarPsModulesPath" if path.name == ".atlasPsModulesPath" else replacement(path.name)
        if path.name != name:
            dest = path.with_name(name)
            require(not dest.exists(), "Rename collision: " + str(dest))
            path.rename(dest)


def patch_playbook(source: pathlib.Path, overlay: pathlib.Path) -> None:
    pb = source / "src/playbook"
    config = pb / "playbook.conf"
    manifest = read(config)
    require("<Name>SagarOS</Name>" in manifest, "Expected renamed playbook name")
    manifest = re.sub(r"<UniqueId>.*?</UniqueId>",
                      "<UniqueId>" + str(uuid.uuid5(uuid.NAMESPACE_URL, URL)) + "</UniqueId>", manifest)
    for tag, value in {
        "Git": URL, "Website": URL, "InstallGuide": URL + "/blob/main/README.md"
    }.items():
        manifest = re.sub(r"<" + tag + r">.*?</" + tag + r">",
                          "<" + tag + ">" + value + "</" + tag + ">", manifest)
    manifest = re.sub(r"\s*<DonateLink>.*?</DonateLink>", "", manifest)
    manifest = manifest.replace('DefaultOption="auto-updates-disable"',
                                'DefaultOption="auto-updates-default"')
    require("<SupportedBuilds>" in manifest and "<Requirement>" in manifest,
            "Windows version or installer preflight checks disappeared")
    put(config, manifest)

    custom = pb / "Configuration/custom.yml"
    body = read(custom)
    require("SagarOS-Finalize.ps1" not in body, "Source already patched")
    body += """
  # SagarOS: execute LAST, after ordinary Windows optimizations.
  - !writeStatus: {status: 'Applying SagarOS secure online defaults'}
  - !powerShell:
    command: '.\\SagarOS-Finalize.ps1'
    exeDir: true
    wait: true
    runas: currentUserElevated
    handleExitCodes: {"!0": halt}
"""
    put(custom, body)

    tweaks = pb / "Configuration/tweaks.yml"
    data = read(tweaks)
    key = "  - !task: {path: 'tweaks\\qol\\security\\disable-uac-secure-desktop.yml'}"
    require(key in data, "Cannot find upstream UAC secure desktop task")
    put(tweaks, data.replace(key, "  # SagarOS keeps UAC Secure Desktop enabled."))

    oem = pb / "Configuration/tweaks/misc/config-oem-information.yml"
    data = read(oem)
    data = data.replace("data: 'Sagar Team'", "data: 'SagarOS Project'")
    data = re.sub(r"(?m)(    value: 'SupportURL'\s*\n    data: ')[^']*(')",
                  r"\g<1>" + URL + r"\g<2>", data)
    data = re.sub(r"(?ms)^  - !registryValue:\n    path: 'HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\OEMInformation'\n    value: 'SupportPhone'\n    data: '[^']*'\n    type: REG_SZ\n?", "", data)
    put(oem, data)

    launcher = pb / "build-playbook.cmd"
    data = read(launcher)
    require("-Removals WinverRequirement, Verification" in data,
            "Upstream build launcher has changed; review necessary")
    data = data.replace("-AddLiveLog ", "").replace(
        "-Removals WinverRequirement, Verification", "-Removals Verification")
    put(launcher, data)

    builder = source / "src/dependencies/local-build.ps1"
    data = read(builder)
    old = ('Get-Content -Encoding "utf8" "playbook.conf" | Where-Object '
           "{ $_ -notmatch ($patterns -join '|') } | "
           'Set-Content -Encoding "utf8" $tempPbConfPath')
    new = ("$filteredManifestLines = @(Get-Content -Encoding 'utf8' 'playbook.conf' | "
           "Where-Object { $_ -notmatch ($patterns -join '|') })\n"
           "        [System.IO.File]::WriteAllLines($tempPbConfPath, "
           "[string[]]$filteredManifestLines, "
           "[System.Text.UTF8Encoding]::new($false))")
    require(old in data, "Upstream PowerShell 5.1 manifest packaging changed")
    put(builder, data.replace(old, new, 1))

    executable = pb / "Executables"
    for name in ("SagarOS-Finalize.ps1", "SagarOS-Enable-Internet.ps1", "SagarOS-Verify.ps1"):
        shutil.copy2(overlay / "scripts" / name, executable / name)
    manager = executable / "SagarDesktop/0. SagarOS Manager"
    manager.mkdir(parents=True, exist_ok=True)
    for name in ("SagarOS-Manager.ps1", "SagarOS-Manager.cmd"):
        shutil.copy2(overlay / "scripts" / name, manager / name)
    shutil.copy2(overlay / "README.md", source / "README.md")
    shutil.copy2(overlay / "UPSTREAM-CREDITS.md", source / "UPSTREAM-CREDITS.md")


def make_artwork(source: pathlib.Path) -> None:
    """Create original SagarOS image assets; no upstream artwork is redistributed."""
    from PIL import Image, ImageDraw, ImageFont
    pb = source / "src/playbook"
    base = pb / "Executables/SagarModules"
    wall = base / "Wallpapers"
    wall.mkdir(parents=True, exist_ok=True)

    def font(size: int):
        candidates = (
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        )
        for path in candidates:
            if pathlib.Path(path).is_file():
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()

    def paint(width: int, height: int, dark: bool, tagline: bool) -> Image.Image:
        bg = (10, 17, 40) if dark else (239, 244, 255)
        ink = (240, 247, 255) if dark else (18, 35, 70)
        accent = (65, 136, 250) if dark else (32, 95, 203)
        im = Image.new("RGB", (width, height), bg)
        d = ImageDraw.Draw(im)
        cx, cy = width // 2, height // 2
        scale = min(width, height)
        for multiplier, opacity in ((0.85, 0), (0.63, 1), (0.45, 2)):
            rad = int(scale * multiplier)
            color = tuple(min(255, c + (6 if dark else -6) * opacity) for c in bg)
            d.ellipse((cx-rad, cy-rad, cx+rad, cy+rad), outline=color, width=max(2, scale//400))
        thick = max(4, scale//65)
        rad = scale//8
        d.arc((cx-rad, cy-rad-scale//7, cx+rad, cy+rad-scale//7), 195, 520,
              fill=accent, width=thick)
        d.line(((cx-rad//2, cy-scale//7), (cx+rad//3, cy-scale//7)), fill=accent, width=thick)
        size = int(scale * 0.095)
        title = "SagarOS"
        d.text((cx, cy + scale//13), title, font=font(size), fill=ink, anchor="mm")
        if tagline:
            d.text((cx, cy + scale//7), "PRIVATE BY DESIGN  •  INTERNET READY",
                   font=font(max(13, size//4)), fill=accent, anchor="mm")
        return im

    themes = {
        "sagar-solid.png": True,
        "sagar-v0.4.x-dark.png": True,
        "sagar-v0.4.x-light.png": False,
        "sagar-v0.5.x-dark.png": True,
        "sagar-v0.5.x-light.png": False,
        "lockscreen_dark.png": True,
        "lockscreen_light.png": False,
    }
    for filename, is_dark in themes.items():
        paint(3840, 2160, is_dark, True).save(wall / filename, optimize=True)
    paint(512, 512, True, False).save(pb / "playbook.png", optimize=True)
    paint(512, 512, True, False).save(pb / "Executables/user.png", optimize=True)
    paint(256, 256, True, False).save(base / "Other/sagar-folder.ico", sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    for path in (pb / "Executables/Themes").glob("sagar-*.theme"):
        original = read(path)
        theme_id = str(uuid.uuid5(uuid.NAMESPACE_URL, URL + "/theme/" + path.name)).upper()
        updated = re.sub(r"(?im)^ThemeId=\{[0-9a-f-]+\}$",
                         "ThemeId={" + theme_id + "}", original)
        put(path, updated)
    # Delete any still-branded images, if upstream adds new filename variants.
    for path in wall.glob("atlas-*"):
        path.unlink()


def validate(source: pathlib.Path) -> None:
    pb = source / "src/playbook"
    conf = read(pb / "playbook.conf")
    custom = read(pb / "Configuration/custom.yml")
    require("<Name>SagarOS</Name>" in conf, "SagarOS manifest name missing")
    require("<SupportedBuilds>" in conf and "<Requirement>" in conf,
            "Version or preflight requirements missing")
    require("SagarOS-Finalize.ps1" in custom, "Post-install finalizer missing")
    require((pb / "Executables/SagarModules").is_dir(), "Module rename incomplete")
    require((pb / "Executables/SagarDesktop").is_dir(), "Desktop rename incomplete")
    require(not (pb / "Executables/AtlasModules").exists(), "Stale AtlasModules folder")
    require((pb / "Executables/SagarOS-Enable-Internet.ps1").is_file(),
            "Online recovery script missing")
    require((pb / "Executables/SagarModules/Wallpapers/sagar-v0.5.x-dark.png").is_file(),
            "SagarOS artwork missing")
    require("atlas-toolbox/releases/latest/download" not in read(pb / "Executables/SOFTWARE.ps1"),
            "Upstream Toolbox downloader present")
    print("SagarOS source transformation passed structural checks.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=pathlib.Path, required=True)
    parser.add_argument("--overlay", type=pathlib.Path, default=pathlib.Path("."))
    args = parser.parse_args()
    source = args.source.resolve()
    overlay = args.overlay.resolve()
    require((source / "src/playbook/playbook.conf").is_file(), "Atlas source checkout missing")
    require("<Name>AtlasOS</Name>" in read(source / "src/playbook/playbook.conf"),
            "Expected pristine pinned AtlasOS source")
    remove_upstream_toolbox(source)
    rebrand_text_and_paths(source)
    patch_playbook(source, overlay)
    make_artwork(source)
    validate(source)


if __name__ == "__main__":
    main()
