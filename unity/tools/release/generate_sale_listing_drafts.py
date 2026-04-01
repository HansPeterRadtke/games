#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def section(text: str, heading: str) -> list[str]:
    pattern = re.compile(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(text)
    if not match:
        return []
    block = match.group(1).strip()
    return [line.rstrip() for line in block.splitlines() if line.strip()]


def bullet_lines(lines: list[str]) -> list[str]:
    result = []
    for line in lines:
        if line.lstrip().startswith("-"):
            result.append(line.strip()[1:].strip())
        elif re.match(r"^\d+\.\s+", line):
            result.append(re.sub(r"^\d+\.\s+", "", line).strip())
    return result


def first_paragraph(text: str) -> str:
    body = text.splitlines()
    paras = []
    cur = []
    for line in body[1:]:
        if line.startswith("## "):
            break
        if not line.strip():
            if cur:
                paras.append(" ".join(cur).strip())
                cur = []
            continue
        cur.append(line.strip())
    if cur:
        paras.append(" ".join(cur).strip())
    return paras[0] if paras else ""


def make_listing(package_dir: Path, artifact_dir: Path, screenshot_path: Path | None, info_path: Path) -> None:
    manifest = load_json(package_dir / "package.json")
    readme = (package_dir / "README.md").read_text(encoding="utf-8")
    overview = (package_dir / "Documentation~" / "Overview.md")
    overview_text = overview.read_text(encoding="utf-8") if overview.exists() else ""

    audience = bullet_lines(section(readme, "Audience"))
    included = bullet_lines(section(readme, "Included"))
    limitations = bullet_lines(section(readme, "Limitations"))
    quickstart = bullet_lines(section(readme, "Installation"))
    dependencies = manifest.get("dependencies", {})
    sample_entries = manifest.get("samples", [])

    lines = []
    lines.append(f"# {manifest['displayName']} Asset Store Listing Draft")
    lines.append("")
    lines.append("## Title")
    lines.append(manifest["displayName"])
    lines.append("")
    lines.append("## Short description")
    lines.append(manifest.get("description", "").strip())
    lines.append("")
    lines.append("## Long description")
    para = first_paragraph(readme) or manifest.get("description", "").strip()
    lines.append(para)
    lines.append("")
    if audience:
        lines.append("Use this package when you want:")
        lines.extend([f"- {item}" for item in audience])
        lines.append("")
    if included:
        lines.append("Included:")
        lines.extend([f"- {item}" for item in included])
        lines.append("")
    if quickstart:
        lines.append("Installation summary:")
        lines.extend([f"- {item}" for item in quickstart])
        lines.append("")
    if overview_text:
        lines.append("Documentation summary:")
        lines.append(first_paragraph(overview_text) or manifest.get("description", "").strip())
        lines.append("")
    if limitations:
        lines.append("Known product limits:")
        lines.extend([f"- {item}" for item in limitations])
        lines.append("")
    lines.append("## Technical details")
    lines.append(f"- Package name: `{manifest['name']}`")
    lines.append(f"- Version: `{manifest['version']}`")
    lines.append(f"- Unity version: `{manifest['unity']}`")
    dep_text = ", ".join(sorted(dependencies)) if dependencies else "none"
    lines.append(f"- Dependencies: {dep_text}")
    if sample_entries:
        lines.append(f"- Sample import path: `{sample_entries[0]['path']}`")
    if screenshot_path is not None:
        lines.append(f"- Screenshot: `{screenshot_path.relative_to(artifact_dir)}`")
    lines.append(f"- Artifact info: `{info_path.name}`")
    lines.append("")
    lines.append("## Human-only fields to fill before upload")
    lines.append("- Price")
    lines.append("- Category/subcategory")
    lines.append("- Support email or support URL")
    lines.append("- Marketing screenshots selection and ordering")
    lines.append("- Package icon / cover art if you want a bespoke visual instead of the captured demo screenshot")
    lines.append("")
    lines.append("## Suggested keywords")
    keywords = manifest.get("keywords", [])
    lines.extend([f"- {keyword}" for keyword in keywords])
    lines.append("")
    (artifact_dir / f"{manifest['name']}_listing_draft.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def make_index(repo_root: Path, config_path: Path, dist_root: Path) -> None:
    config = load_json(config_path)
    lines = ["# Asset Store Upload Matrix", ""]
    for entry in config["sellable_packages"]:
        name = entry["name"]
        package_dir = repo_root / "unity" / "packages" / name
        manifest = load_json(package_dir / "package.json")
        artifact_dir = dist_root / name
        lines.append(f"## {manifest['displayName']}")
        lines.append(f"- Package: `{name}`")
        lines.append(f"- Unitypackage: `{name}.unitypackage`")
        lines.append(f"- UPM zip: `{name}_upm.zip`")
        lines.append(f"- Listing draft: `{name}_listing_draft.md`")
        screenshots = sorted((artifact_dir / 'screenshots').glob('*.png')) if (artifact_dir / 'screenshots').exists() else []
        if screenshots:
            lines.append(f"- Screenshot: `screenshots/{screenshots[0].name}`")
        lines.append("")
    (dist_root / "UPLOAD_MATRIX.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: generate_sale_listing_drafts.py <repo-root> <release-packages.json> <dist-artifacts-root>", file=sys.stderr)
        return 1

    repo_root = Path(sys.argv[1])
    config_path = Path(sys.argv[2])
    dist_root = Path(sys.argv[3])
    config = load_json(config_path)

    for entry in config["sellable_packages"]:
        name = entry["name"]
        package_dir = repo_root / "unity" / "packages" / name
        artifact_dir = dist_root / name
        info_path = artifact_dir / f"{name}_info.txt"
        screenshot_dir = artifact_dir / "screenshots"
        screenshot_path = next(iter(sorted(screenshot_dir.glob("*.png"))), None) if screenshot_dir.exists() else None
        make_listing(package_dir, artifact_dir, screenshot_path, info_path)

    make_index(repo_root, config_path, dist_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
