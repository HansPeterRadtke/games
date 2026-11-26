"""Standalone static HTML renderer for verified HPR Scene Identity Guard differences.

No JavaScript, external URLs, network access or filesystem reads. All user
paths, names and object IDs are HTML-escaped before interpolation. This module
ships alongside hpr_scene_identity.py; neither requires a Unity Editor runtime.
"""
from __future__ import annotations

from html import escape
from typing import Any

MAX_VISIBLE_ROWS = 500

STYLE = """
:root{color-scheme:light;font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
*{box-sizing:border-box}
body{margin:0;background:#e9eef5;color:#17263d;line-height:1.48}
.report{max-width:1100px;margin:0 auto;padding:36px 28px 70px}
a{color:#244ea3}
.banner{background:#13263f;color:#f2f7ff;border-radius:16px;padding:27px 32px;box-shadow:0 8px 24px rgba(18,38,64,.18)}
.brand{font-size:12px;letter-spacing:.13em;text-transform:uppercase;font-weight:750;color:#9dc8f7}
h1{font-size:clamp(25px,3.2vw,36px);line-height:1.2;margin:10px 0 14px}
.subtitle{font-size:15px;color:#dbe6f5;margin:0;max-width:790px}
.phase{display:inline-block;font-weight:750;font-size:13px;padding:8px 11px;border-radius:9px;letter-spacing:.03em}
.phase.warning{background:#ffe5c0;color:#623400}
.phase.success{background:#d7f8e8;color:#195a35}
.phase.notice{background:#cde4ff;color:#153f76}
.hero-meta{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:20px}
.hero-meta small{color:#dce9f8}
.stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:22px 0}
.stat{background:white;border:1px solid #d1dbe8;padding:16px;border-radius:13px}
.stat .count{font-size:29px;font-weight:800;line-height:1.15;display:block}
.stat .label{font-size:12px;color:#526780;line-height:1.35;margin-top:6px;display:block}
.stat.review .count{color:#a34224}
.stat.addition .count{color:#117258}
.note{border-left:4px solid #4779b2;border-radius:0 9px 9px 0;background:#f6f9fe;padding:14px 18px;margin:20px 0}
.note p{margin:0 0 8px}.note p:last-child{margin-bottom:0}
section{background:#fff;border:1px solid #d3ddea;border-radius:14px;margin:22px 0;overflow:hidden;box-shadow:0 2px 10px rgba(22,43,76,.04)}
.section-head{padding:18px 24px;border-bottom:1px solid #dce3ed;display:flex;justify-content:space-between;align-items:baseline;gap:8px}
h2{font-size:19px;margin:0;line-height:1.4}
.section-head span{font-size:12px;color:#526b82}
.entries{padding:4px 0}
.entry{padding:14px 24px;border-bottom:1px solid #e9eef5}
.entry:last-child{border-bottom:0}
.entry-top{display:flex;justify-content:space-between;gap:12px;align-items:start;flex-wrap:wrap}
.entry strong{font-size:15px;color:#172b46}
.entry .filename{font-size:13px;color:#344a62;word-break:break-word;margin:7px 0 5px}
.id{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;color:#30455c;font-size:11px;overflow-wrap:anywhere}
.badge{border-radius:5px;background:#eff3fa;color:#36536c;padding:4px 8px;font-size:11px;font-weight:700}
.badge.danger{background:#ffe9e2;color:#942f19}
.badge.ok{background:#d6f4e6;color:#136045}
.badge.info{background:#dfeafb;color:#234a85}
.mini{font-size:12px;color:#54687e}
.empty{padding:18px 24px;color:#476078;font-size:14px}
.truncation{background:#fff0d7;padding:14px 24px;color:#71481b;font-size:13px}
footer{font-size:12px;color:#556a82;margin-top:25px}
@media(max-width:760px){.report{padding:14px 11px 45px}.banner{padding:21px}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.stat{padding:12px}.stat .count{font-size:25px}section{margin:13px 0}.section-head,.entry,.empty{padding:12px 16px}}
@media print{body{background:white}.report{padding:0}.banner{box-shadow:none}.stat,section{box-shadow:none}footer{page-break-inside:avoid}.entry{page-break-inside:avoid}}
"""

def _t(value: Any) -> str:
    # No caller-provided HTML, CSS, attributes or script is ever trusted.
    return escape(str(value), quote=True)

def _short(value: Any, maximum: int = 800) -> str:
    text = str(value)
    if len(text) > maximum:
        text = text[:maximum] + "…"
    return _t(text)

def _object_entry(row: dict, *, badge: str, css: str) -> str:
    name = row.get("name", "")
    path = row.get("path", "")
    return (
        '<article class="entry"><div class="entry-top">'
        f'<strong>{_short(name or "Unnamed GameObject")}</strong>'
        f'<span class="badge {css}">{_t(badge)}</span></div>'
        f'<p class="filename">{_short(path)}</p>'
        f'<div class="id">Asset GUID: {_short(row.get("asset_guid", ""))}</div>'
        f'<div class="id">Local file ID: {_short(row.get("local_file_id", ""))}</div></article>'
    )

def _guid_entry(row: dict) -> str:
    return (
        '<article class="entry"><div class="entry-top">'
        '<strong>Asset identity changed at the same path</strong>'
        '<span class="badge danger">Review GUID</span></div>'
        f'<p class="filename">{_short(row.get("path", ""))}</p>'
        f'<div class="mini">Previous: <span class="id">{_short(row.get("was", ""))}</span></div>'
        f'<div class="mini">Current: <span class="id">{_short(row.get("now", ""))}</span></div></article>'
    )

def _rename_entry(row: dict) -> str:
    return (
        '<article class="entry"><div class="entry-top">'
        f'<strong>{_short(row.get("now_name", ""))}</strong>'
        '<span class="badge info">Identity retained</span></div>'
        f'<p class="filename">{_short(row.get("was_path", ""))}'
        ' &rarr; ' f'{_short(row.get("now_path", ""))}</p>'
        f'<div class="mini">Name before: {_short(row.get("was_name", ""))}</div>'
        f'<div class="id">Asset GUID: {_short(row.get("asset_guid", ""))}</div>'
        f'<div class="id">Local file ID: {_short(row.get("local_file_id", ""))}</div></article>'
    )

def render_report(comparison: dict) -> bytes:
    status = comparison.get("status")
    if status not in ("REVIEW_REQUIRED", "IDENTITY_STABLE", "ADDITIONS_ONLY"):
        raise ValueError("Unsupported comparison status")
    if comparison.get("scope") != "direct-serialized-gameobject-documents-only":
        raise ValueError("Report has no verified direct-GameObject scope")
    groups = (
        ("Lost direct GameObject identities", comparison.get("lost", []), "lost"),
        ("Asset GUID changed at an existing path", comparison.get("changed_asset_guids", []), "guid"),
        ("New directly serialized GameObjects", comparison.get("added", []), "added"),
        ("Renamed or moved without losing direct identity", comparison.get("renamed_or_moved_without_identity_loss", []), "rename"),
    )
    if any(not isinstance(items, list) for _, items, _ in groups):
        raise ValueError("Unrecognised comparison data")
    totals = [len(items) for _, items, _ in groups]
    danger = status == "REVIEW_REQUIRED"
    phase_label = "Review required" if danger else ("New objects only" if status == "ADDITIONS_ONLY" else "Direct identities stable")
    phase_css = "warning" if danger else ("notice" if status == "ADDITIONS_ONLY" else "success")
    groups_html = []
    remaining = MAX_VISIBLE_ROWS
    for title, items, kind in groups:
        available = min(remaining, len(items))
        display = items[:available]
        remaining -= available
        if kind == "lost":
            rendered = "".join(_object_entry(row, badge="No longer present", css="danger") for row in display)
        elif kind == "added":
            rendered = "".join(_object_entry(row, badge="New direct ID", css="ok") for row in display)
        elif kind == "guid":
            rendered = "".join(_guid_entry(row) for row in display)
        else:
            rendered = "".join(_rename_entry(row) for row in display)
        if not items:
            rendered = '<div class="empty">No findings in this category.</div>'
        if len(display) < len(items):
            rendered += (
                '<p class="truncation">Showing ' f'{available} of {len(items)}'
                ' findings in this category. The complete machine-readable JSON'
                ' contains all records; this preview is limited for readability.</p>'
            )
        groups_html.append(
            '<section aria-label="' + _t(title) + '">'
            f'<div class="section-head"><h2>{_t(title)}</h2>'
            f'<span>{len(items)} total</span></div>'
            f'<div class="entries">{rendered}</div></section>'
        )
    stat_labels = (
        ("Missing prior IDs", totals[0], "review" if totals[0] else ""),
        ("Changed asset GUIDs", totals[1], "review" if totals[1] else ""),
        ("Added IDs", totals[2], "addition"),
        ("Identity-preserving edits", totals[3], ""),
        ("Current direct objects", comparison.get("current_objects", 0), ""),
    )
    stat = "".join(
        '<div class="stat ' + css + '"><span class="count">' + _t(count) +
        '</span><span class="label">' + _t(label) + '</span></div>'
        for label, count, css in stat_labels
    )
    headline = (
        "At least one previously saved direct identity is missing or replaced."
        if danger else (
            "New direct objects were found without losing any baseline direct identities."
            if status == "ADDITIONS_ONLY"
            else "No baseline direct GameObject identities were lost."
        )
    )
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'none'; img-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>HPR Scene Identity Guard — Private project review</title>
<style>{STYLE}</style>
</head>
<body><main class="report">
<header class="banner">
<p class="brand">HPR / Multiverse &middot; Original project preflight</p>
<h1>Scene identity comparison</h1>
<p class="subtitle">{_t(headline)}</p>
<div class="hero-meta"><span class="phase {phase_css}">{_t(phase_label)}</span>
<small>Saved Unity YAML &middot; Direct GameObjects only &middot; Local read-only analysis</small></div>
</header>
<div class="stats" aria-label="Finding counts">{stat}</div>
<div class="note">
<p><strong>Scope:</strong> This report checks only directly serialized GameObject pairs of asset GUID and local file ID in saved Unity scene and prefab YAML. It does not prove that a game's save files still work.</p>
<p>Prefab-instance children, scripts, scene runtime state, components, generated objects, and unsaved Editor changes are outside this review. Always inspect the original approved baseline and the actual project migration workflow.</p>
<p><strong>Privacy:</strong> Names and paths may reveal project content. This file is static HTML with no scripts, external requests or telemetry. Do not publish without permission.</p>
</div>
{''.join(groups_html)}
<footer>HPR Scene Identity Guard &middot; Private technical evidence, not an Asset Store approval, Player build certificate or paid customer result.</footer>
</main></body></html>"""
    return doc.encode("utf-8")
