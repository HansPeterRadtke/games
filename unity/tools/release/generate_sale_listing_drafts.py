#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def first_sample_path(package_dir: Path, manifest: dict) -> str:
    for sample in manifest.get("samples", []):
        path = sample.get("path")
        if path:
            return f"Assets/{manifest['name']}/{path}".replace("\\", "/")
    demo_root = package_dir / "Demo"
    if demo_root.exists():
        scene = next(iter(sorted(demo_root.rglob("*.unity"))), None)
        if scene is not None:
            rel = scene.relative_to(package_dir)
            return f"Assets/{manifest['name']}/{rel}".replace("\\", "/")
    return f"Assets/{manifest['name']}"


def format_price(value: float, status: str) -> str:
    if status == "bundle_only":
        return "bundle_only"
    return f"${value:.2f}"


def format_list(items: list[str], prefix: str = "- ") -> list[str]:
    return [f"{prefix}{item}" for item in items]


def validate_screenshots(dist_root: Path, package_names: list[str]) -> tuple[dict[str, list[Path]], dict[str, str]]:
    screenshot_map: dict[str, list[Path]] = {}
    hash_owner: dict[str, str] = {}
    all_hashes: dict[str, str] = {}
    for package_name in package_names:
        screenshot_dir = dist_root / package_name / "screenshots"
        shots = sorted(screenshot_dir.glob("*.png"))
        if len(shots) < 3:
            raise SystemExit(f"{package_name}: expected at least 3 screenshots, found {len(shots)}")
        local_hashes = set()
        for shot in shots:
            digest = sha256(shot)
            if digest in local_hashes:
                raise SystemExit(f"{package_name}: duplicate screenshot content detected inside package: {shot.name}")
            local_hashes.add(digest)
            if digest in hash_owner:
                raise SystemExit(
                    f"duplicate screenshot content detected across packages: {package_name}/{shot.name} == {hash_owner[digest]}"
                )
            hash_owner[digest] = f"{package_name}/{shot.name}"
            all_hashes[str(shot)] = digest
        screenshot_map[package_name] = shots
    return screenshot_map, all_hashes


def make_listing(
    package_name: str,
    manifest: dict,
    package_dir: Path,
    artifact_dir: Path,
    catalog_entry: dict,
    screenshots: list[Path],
    support_note: str,
) -> None:
    listing_path = artifact_dir / f"{package_name}_listing_draft.md"
    info_name = f"{package_name}_info.txt"
    sample_path = first_sample_path(package_dir, manifest)
    dependencies = sorted(manifest.get("dependencies", {}).keys())

    lines: list[str] = []
    lines.append(f"# {catalog_entry['title']} Listing Draft")
    lines.append("")
    lines.append("## Release recommendation")
    lines.append(f"- Status: `{catalog_entry['status']}`")
    lines.append(f"- Reason: {catalog_entry['reason']}")
    lines.append("")
    lines.append("## Title")
    lines.append(catalog_entry["title"])
    lines.append("")
    lines.append("## Short description")
    lines.append(catalog_entry["short_description"])
    lines.append("")
    lines.append("## Positioning")
    lines.append(catalog_entry["positioning"])
    lines.append("")
    lines.append("## Long description")
    lines.extend(catalog_entry["long_description"])
    lines.append("")
    lines.append("## Feature bullets")
    lines.extend(format_list(catalog_entry["feature_bullets"]))
    lines.append("")
    lines.append("## Use cases")
    lines.extend(format_list(catalog_entry["use_cases"]))
    lines.append("")
    lines.append("## Installation summary")
    lines.extend(format_list(catalog_entry["installation_summary"]))
    lines.append(f"- Demo/sample path after import: `{sample_path}`")
    lines.append("")
    lines.append("## Technical details")
    lines.append(f"- Package id: `{manifest['name']}`")
    lines.append(f"- Version: `{manifest['version']}`")
    lines.append(f"- Unity version: `{manifest['unity']}`")
    lines.append(f"- Category recommendation: `{catalog_entry['category']} / {catalog_entry['subcategory']}`")
    lines.append(f"- Price recommendation: `{format_price(float(catalog_entry['price_usd']), catalog_entry['status'])}`")
    dep_text = ", ".join(dependencies) if dependencies else "none"
    lines.append(f"- Explicit dependencies: `{dep_text}`")
    lines.extend(format_list(catalog_entry["technical_summary"]))
    lines.append(f"- Artifact info file: `{info_name}`")
    lines.append("")
    lines.append("## Known limits / non-goals")
    lines.extend(format_list(catalog_entry["known_limits"]))
    lines.append("")
    lines.append("## Screenshot order recommendation")
    for shot, caption in zip(screenshots, catalog_entry["screenshot_captions"], strict=True):
        lines.append(f"- `{shot.relative_to(artifact_dir)}` — {caption}")
    lines.append("")
    lines.append("## Cover art recommendation")
    lines.append(catalog_entry["cover_art_recommendation"])
    lines.append("")
    lines.append("## Keywords")
    lines.extend(format_list(catalog_entry["keywords"]))
    lines.append("")
    lines.append("## Cross-sell / bundle recommendation")
    lines.extend(format_list(catalog_entry["cross_sell"]))
    lines.append("")
    lines.append("## Naming recommendation")
    lines.append(catalog_entry["rename_recommendation"])
    lines.append("")
    lines.append("## Pricing strategy note")
    lines.append(catalog_entry["free_vs_paid_recommendation"])
    lines.append("")
    lines.append("## Support field")
    lines.append(support_note)
    lines.append("")
    listing_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_upload_matrix(
    repo_root: Path,
    dist_root: Path,
    config: dict,
    catalog: dict,
    screenshot_map: dict[str, list[Path]],
) -> None:
    lines = ["# Asset Store Upload Matrix", ""]
    lines.append("This matrix reflects the current tracked repo state and the latest regenerated sale artifacts.")
    lines.append("")
    for entry in config["sellable_packages"]:
        name = entry["name"]
        artifact_dir = dist_root / name
        info_path = artifact_dir / f"{name}_info.txt"
        unitypackage = artifact_dir / f"{name}.unitypackage"
        upm_zip = artifact_dir / f"{name}_upm.zip"
        shots = screenshot_map[name]
        catalog_entry = catalog["packages"][name]
        lines.append(f"## {catalog_entry['title']}")
        lines.append(f"- Package id: `{name}`")
        lines.append(f"- Release recommendation: `{catalog_entry['status']}`")
        lines.append(f"- Category recommendation: `{catalog_entry['category']} / {catalog_entry['subcategory']}`")
        lines.append(f"- Price recommendation: `{format_price(float(catalog_entry['price_usd']), catalog_entry['status'])}`")
        lines.append(f"- Unitypackage: `{unitypackage.relative_to(dist_root)}` ({unitypackage.stat().st_size} bytes)")
        lines.append(f"- UPM zip: `{upm_zip.relative_to(dist_root)}` ({upm_zip.stat().st_size} bytes)")
        lines.append(f"- Listing draft: `{name}/{name}_listing_draft.md`")
        lines.append(f"- Info file: `{info_path.relative_to(dist_root)}`")
        lines.append("- Screenshots:")
        for shot, caption in zip(shots, catalog_entry["screenshot_captions"], strict=True):
            lines.append(f"  - `{shot.relative_to(dist_root)}` — {caption}")
        lines.append(f"- Cover art recommendation: {catalog_entry['cover_art_recommendation']}")
        lines.append(f"- Launch reason: {catalog_entry['reason']}")
        lines.append("")
    (dist_root / "UPLOAD_MATRIX.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_finalization_doc(
    repo_root: Path,
    dist_root: Path,
    config: dict,
    catalog: dict,
    screenshot_map: dict[str, list[Path]],
    hash_map: dict[str, str],
) -> None:
    lines = ["# Package Sale Finalization", ""]
    lines.append("This report covers the frozen sellable package set from the current repo state.")
    lines.append("")
    lines.append("## Launch recommendation by package")
    for entry in config["sellable_packages"]:
        name = entry["name"]
        package = catalog["packages"][name]
        lines.append(f"- `{name}` — `{package['status']}` — {package['reason']}")
    lines.append("")
    lines.append("## Screenshot regeneration")
    lines.append("- Every package now carries three tracked screenshots in `dist/package_sale_artifacts/<package>/screenshots/`.")
    lines.append("- The screenshot generator is package-specific and reproducible from `unity/tools/release/HprPackageScreenshotRunner.cs`.")
    lines.append("- Exact duplicate screenshot hashes are rejected during draft generation.")
    lines.append("")
    lines.append("## Screenshot files")
    for entry in config["sellable_packages"]:
        name = entry["name"]
        lines.append(f"### `{name}`")
        for shot in screenshot_map[name]:
            lines.append(f"- `{shot.relative_to(repo_root)}` — sha256 `{hash_map[str(shot)]}`")
        lines.append("")
    lines.append("## Current tracked artifact root")
    lines.append(f"- `{dist_root.relative_to(repo_root)}`")
    lines.append("")
    lines.append("## Proof roots")
    lines.append("- `doc/logs/package_validation/`")
    lines.append("- `doc/logs/package_sale_prep/`")
    lines.append("- `doc/logs/asset_store_tools_validation/`")
    lines.append("- `doc/logs/` for release audit, dependency audit, build, and smoke logs")
    lines.append("")
    lines.append("## Human-only boundary")
    lines.append("See `doc/human-only-final-steps.md` for the remaining steps that cannot be completed by repository automation.")
    (repo_root / "doc" / "package-sale-finalization.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_launch_strategy_doc(repo_root: Path, catalog: dict) -> None:
    lines = ["# Package Launch Strategy", ""]
    lines.append("## First wave")
    for name in catalog["first_wave"]:
        package = catalog["packages"][name]
        lines.append(f"- `{name}` — {package['title']} — {format_price(float(package['price_usd']), package['status'])} — {package['reason']}")
    lines.append("")
    lines.append("## Second wave")
    for name in catalog["second_wave"]:
        package = catalog["packages"][name]
        lines.append(f"- `{name}` — {package['title']} — {format_price(float(package['price_usd']), package['status'])} — {package['reason']}")
    lines.append("")
    lines.append("## Bundle-only / support packages")
    for name in catalog["bundle_only"]:
        package = catalog["packages"][name]
        lines.append(f"- `{name}` — {package['title']} — {package['reason']}")
    lines.append("")
    lines.append("## Upsell and cross-sell recommendations")
    for name, package in catalog["packages"].items():
        lines.append(f"- `{name}` -> {', '.join(package['cross_sell'])}")
    lines.append("")
    lines.append("## Naming recommendations")
    for name, package in catalog["packages"].items():
        lines.append(f"- `{name}` — {package['rename_recommendation']}")
    lines.append("")
    lines.append("## Free vs paid recommendation")
    for name, package in catalog["packages"].items():
        lines.append(f"- `{name}` — {package['free_vs_paid_recommendation']}")
    (repo_root / "doc" / "package-launch-strategy.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_human_only_doc(repo_root: Path, catalog: dict) -> None:
    lines = ["# Human-Only Final Steps", ""]
    lines.append("- Choose and enter the single support email address or support URL you want to use across every listing.")
    lines.append("- Accept or override the proposed prices before entering them in the publisher portal.")
    lines.append("- Do a final visual sign-off on the generated screenshots and the chosen screenshot order per package.")
    lines.append("- Log into the Unity Asset Store publisher portal and upload the selected .unitypackage files.")
    lines.append("- Complete publisher-account, tax, payout, and legal agreement steps in the portal.")
    (repo_root / "doc" / "human-only-final-steps.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) not in {4, 5}:
        print(
            "usage: generate_sale_listing_drafts.py <repo-root> <release-packages.json> <dist-artifacts-root> [storefront-catalog.json]",
            file=sys.stderr,
        )
        return 1

    repo_root = Path(sys.argv[1]).resolve()
    config_path = Path(sys.argv[2]).resolve()
    dist_root = Path(sys.argv[3]).resolve()
    catalog_path = Path(sys.argv[4]).resolve() if len(sys.argv) == 5 else (Path(__file__).resolve().parent / "storefront_catalog.json")

    config = load_json(config_path)
    catalog = load_json(catalog_path)
    package_names = [entry["name"] for entry in config["sellable_packages"]]

    for name in package_names:
        if name not in catalog["packages"]:
            raise SystemExit(f"missing storefront catalog entry for {name}")

    screenshot_map, hash_map = validate_screenshots(dist_root, package_names)

    for name in package_names:
        package_dir = repo_root / "unity" / "packages" / name
        manifest = load_json(package_dir / "package.json")
        make_listing(
            name,
            manifest,
            package_dir,
            dist_root / name,
            catalog["packages"][name],
            screenshot_map[name],
            catalog["support_contact_note"],
        )

    write_upload_matrix(repo_root, dist_root, config, catalog, screenshot_map)
    write_finalization_doc(repo_root, dist_root, config, catalog, screenshot_map, hash_map)
    write_launch_strategy_doc(repo_root, catalog)
    write_human_only_doc(repo_root, catalog)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
