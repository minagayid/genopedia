"""Self-contained HTML and SVG reporting for local/offline use."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Iterable

from .anomalies import SequenceAnomaly
from .core import QualityReport, SequenceRecord, Variant
from .correction import CorrectionSuggestion
from .references import ReferencePlan


BASE_COLORS = {
    "A": ("#d62828", "Adenine"),
    "T": ("#e9c46a", "Thymine"),
    "G": ("#2a9d8f", "Guanine"),
    "C": ("#457b9d", "Cytosine"),
    "U": ("#8d5524", "Uracil"),
    "N": ("#6c757d", "Ambiguous/unknown"),
}


def render_svg_sequence(sequence: str, width: int = 800, height: int = 80, max_bases: int = 240) -> str:
    sequence = "".join(sequence.split()).upper()
    visible = sequence[:max_bases]
    if not visible:
        return f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg"></svg>'
    base_width = width / len(visible)
    parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sequence visualization">'
    ]
    for index, base in enumerate(visible):
        color = BASE_COLORS.get(base, BASE_COLORS["N"])[0]
        x = round(index * base_width, 3)
        parts.append(
            f'<rect x="{x}" y="0" width="{round(base_width, 3)}" height="{height}" fill="{color}" stroke="#ffffff" stroke-width="0.5"><title>{index}: {html.escape(base)}</title></rect>'
        )
    if len(sequence) > max_bases:
        parts.append(f'<text x="8" y="{height - 8}" fill="#111111">… {len(sequence) - max_bases} more bases</text>')
    parts.append("</svg>")
    return "".join(parts)


def _render_sequence_spans(sequence: str, max_bases: int = 1000) -> str:
    sequence = "".join(sequence.split()).upper()
    spans: list[str] = []
    for index, base in enumerate(sequence[:max_bases]):
        safe_base = html.escape(base)
        spans.append(
            f'<span class="base base-{safe_base}" title="Position {index} · {BASE_COLORS.get(base, BASE_COLORS["N"])[1]}">{safe_base}</span>'
        )
    if len(sequence) > max_bases:
        spans.append(f'<span class="truncation">… {len(sequence) - max_bases} more bases</span>')
    return "".join(spans)


def _quality_section(reports: Iterable[QualityReport]) -> str:
    rows = []
    for report in reports:
        rows.append(
            "<tr>"
            f"<td>{html.escape(report.identifier)}</td>"
            f"<td>{report.length}</td>"
            f"<td>{report.gc_fraction:.3f}</td>"
            f"<td>{report.ambiguous_count}</td>"
            f"<td>{html.escape(report.status)}</td>"
            f"<td>{html.escape('; '.join(report.warnings) or 'None')}</td>"
            "</tr>"
        )
    if not rows:
        return "<p>No quality-control results.</p>"
    return (
        '<table><thead><tr><th>Sample</th><th>Length</th><th>GC fraction</th>'
        '<th>Ambiguous</th><th>Status</th><th>Warnings</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table>"
    )


def _variant_section(variants: Iterable[Variant]) -> str:
    rows = []
    for variant in variants:
        rows.append(
            "<tr>"
            f"<td>{html.escape(variant.chromosome)}</td>"
            f"<td>{variant.position}</td>"
            f"<td><code>{html.escape(variant.reference or '∅')}</code></td>"
            f"<td><code>{html.escape(variant.observed or '∅')}</code></td>"
            f"<td>{html.escape(variant.variant_type)}</td>"
            f"<td>{html.escape(variant.interpretation)}</td>"
            "</tr>"
        )
    if not rows:
        return "<p>No observed variants.</p>"
    return (
        '<table><thead><tr><th>Chromosome</th><th>Position</th><th>Reference</th>'
        '<th>Observed</th><th>Type</th><th>Interpretation</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table>"
    )


def _anomaly_section(anomalies: Iterable[SequenceAnomaly]) -> str:
    rows = []
    for anomaly in anomalies:
        rows.append(
            "<tr>"
            f"<td>{html.escape(anomaly.identifier)}</td>"
            f"<td>{html.escape(anomaly.category)}</td>"
            f"<td>{html.escape(anomaly.severity)}</td>"
            f"<td>{html.escape(anomaly.evidence)}</td>"
            f"<td>{html.escape(anomaly.suggested_action)}</td>"
            "</tr>"
        )
    if not rows:
        return "<p>No sequence-quality anomaly signals were detected.</p>"
    return (
        '<table><thead><tr><th>Sample</th><th>Signal</th><th>Severity</th><th>Evidence</th>'
        '<th>Suggested next action</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table>"
    )


def _correction_section(suggestions: Iterable[CorrectionSuggestion]) -> str:
    rows = []
    for suggestion in suggestions:
        rows.append(
            "<tr>"
            f"<td>{html.escape(suggestion.chromosome)}:{suggestion.position}</td>"
            f"<td>{html.escape(suggestion.observed)}</td>"
            f"<td>{html.escape(suggestion.candidate or 'none')}</td>"
            f"<td>{html.escape(suggestion.status)}</td>"
            f"<td>{html.escape('; '.join(suggestion.evidence))}</td>"
            f"<td>{html.escape(suggestion.next_action)}</td>"
            "</tr>"
        )
    if not rows:
        return "<p>No correction-planning candidates were supplied.</p>"
    return (
        '<table><thead><tr><th>Location</th><th>Observed</th><th>Candidate</th><th>Status</th>'
        '<th>Evidence</th><th>Next action</th></tr></thead><tbody>'
        + "".join(rows)
        + "</tbody></table>"
    )


def render_html_report(
    records: Iterable[SequenceRecord],
    variants: Iterable[Variant] = (),
    quality_reports: Iterable[QualityReport] = (),
    sequence_anomalies: Iterable[SequenceAnomaly] = (),
    correction_suggestions: Iterable[CorrectionSuggestion] = (),
    reference_plan: ReferencePlan | None = None,
    title: str = "Genopedia report",
) -> str:
    """Render an accessible, self-contained research report with a polished responsive UI.

    The generated page is entirely local: it has no runtime dependencies, network
    requests, accounts, analytics, or calls back into an analysis service.
    """
    from collections import Counter

    records = list(records)
    variants = list(variants)
    quality_reports = list(quality_reports)
    sequence_anomalies = list(sequence_anomalies)
    correction_suggestions = list(correction_suggestions)

    normalized_sequences = [
        "".join(str(record.sequence).split()).upper()
        for record in records
    ]
    total_bases = sum(len(sequence) for sequence in normalized_sequences)
    symbol_counts = Counter("".join(normalized_sequences))
    top_symbols = sorted(symbol_counts.items(), key=lambda item: (-item[1], item[0]))[:6]
    other_count = total_bases - sum(count for _, count in top_symbols)
    composition_items = list(top_symbols)
    if other_count:
        composition_items.append(("Other", other_count))

    def symbol_color(symbol: str) -> str:
        if symbol == "Other":
            return "#8b9c98"
        return BASE_COLORS.get(symbol, ("#8b9c98", "Other"))[0]

    composition_html_parts: list[str] = []
    for symbol, count in composition_items:
        percent = (count / total_bases * 100) if total_bases else 0
        label = "Other symbols" if symbol == "Other" else symbol
        color = symbol_color(symbol)
        composition_html_parts.append(
            '<div class="composition-row">'
            f'<div class="composition-label"><span class="symbol-chip" style="--symbol-color:{color}">{html.escape(label)}</span>'
            f'<span class="composition-percent">{percent:.1f}%</span></div>'
            f'<div class="composition-track" aria-label="{html.escape(label)}: {percent:.1f}%">'
            f'<span style="width:{percent:.3f}%;--symbol-color:{color}"></span></div>'
            f'<strong class="composition-count">{count:,}</strong></div>'
        )
    if not composition_html_parts:
        composition_html = (
            '<div class="empty-state compact"><span class="empty-icon">∅</span>'
            '<p>No sequence symbols are available for this report.</p></div>'
        )
    else:
        composition_html = "".join(composition_html_parts)

    legend = "".join(
        '<span class="legend-item">'
        f'<span class="swatch" style="--swatch-color:{color}" aria-hidden="true"></span>'
        f'<span class="legend-symbol">{html.escape(base)}</span>'
        f'<span class="legend-name">{html.escape(name)}</span></span>'
        for base, (color, name) in BASE_COLORS.items()
    )

    sequence_sections: list[str] = []
    for index, record in enumerate(records):
        sequence = normalized_sequences[index]
        sequence_length = len(sequence)
        description = html.escape(record.description or "No description supplied.")
        sequence_sections.append(
            f'<article class="sequence-card" data-search-card>'
            '<div class="sequence-card-top">'
            '<div class="sequence-title-wrap">'
            f'<span class="sequence-index">{index + 1:02d}</span>'
            f'<div><h3>{html.escape(record.identifier)}</h3>'
            f'<p class="sequence-description">{description}</p></div></div>'
            '<span class="tag tag-neutral">Local sequence</span></div>'
            '<div class="sequence-metrics">'
            f'<span><strong>{sequence_length:,}</strong> symbols</span>'
            f'<span><strong>{(sequence.count("G") + sequence.count("C")) / sequence_length * 100 if sequence_length else 0:.1f}%</strong> GC fraction</span>'
            '</div>'
            f'<div class="sequence" aria-label="Color-coded sequence for {html.escape(record.identifier)}">'
            f'{_render_sequence_spans(sequence)}</div>'
            f'<div class="svg-wrap">{render_svg_sequence(sequence)}</div>'
            '<div class="sequence-card-footer">'
            '<span class="sequence-footnote">Color key follows the nucleotide palette; unrecognized symbols stay neutral.</span>'
            f'<button class="text-button" type="button" data-copy-target="sequence-raw-{index}" aria-label="Copy sequence {html.escape(record.identifier)}">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="12" height="12" rx="2"></rect><path d="M16 8V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h3"></path></svg> Copy sequence</button>'
            f'<code class="sr-only" id="sequence-raw-{index}">{html.escape(sequence)}</code>'
            '</div></article>'
        )
    if not sequence_sections:
        sequence_sections.append(
            '<div class="empty-state"><span class="empty-icon">⌁</span>'
            '<h3>No sequences in this report</h3>'
            '<p>When sequence records are supplied, they will appear here with their symbol map and local quality metrics.</p></div>'
        )

    quality_html = _quality_section(quality_reports).replace("<table>", '<table class="filterable">')
    variant_html = _variant_section(variants).replace("<table>", '<table class="filterable">')
    anomaly_html = _anomaly_section(sequence_anomalies).replace("<table>", '<table class="filterable">')
    correction_html = _correction_section(correction_suggestions).replace("<table>", '<table class="filterable">')
    reference_section = "No reference plan supplied."
    if reference_plan:
        reference_section = json.dumps(reference_plan.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)
        reference_section = html.escape(reference_section)

    export_payload = {
        "title": title,
        "records": [
            {
                "identifier": record.identifier,
                "description": record.description,
                "sequence": normalized_sequences[index],
                "length": len(normalized_sequences[index]),
            }
            for index, record in enumerate(records)
        ],
        "quality_reports": [report.to_dict() for report in quality_reports],
        "variants": [variant.to_dict() for variant in variants],
        "sequence_anomalies": [item.to_dict() for item in sequence_anomalies],
        "correction_suggestions": [item.to_dict() for item in correction_suggestions],
        "reference_plan": reference_plan.to_dict() if reference_plan else None,
        "safety_notice": (
            "Research use only. This report is not a diagnosis, treatment recommendation, "
            "or instruction for laboratory action. No automatic sequence editing is performed."
        ),
    }
    report_json = json.dumps(
        export_payload, ensure_ascii=False, sort_keys=True, allow_nan=False
    )
    # A sequence identifier/description may contain text that would otherwise
    # terminate a script element when the JSON is embedded in this offline page.
    report_json = (
        report_json.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )

    template = """<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#142e2b">
<meta name="description" content="A local, research-oriented Genopedia sequence analysis report.">
<title>__TITLE__ · Genopedia</title>
<style>
:root {
  color-scheme: light;
  --page: #f4f7f5;
  --surface: #ffffff;
  --surface-soft: #f7faf8;
  --surface-tint: #edf5f1;
  --text: #1b302d;
  --muted: #687b76;
  --muted-strong: #4a625c;
  --border: #dfe8e3;
  --accent: #176c5d;
  --accent-strong: #105448;
  --accent-soft: #e4f2ec;
  --accent-bright: #bde7d2;
  --sidebar: #142e2b;
  --sidebar-2: #1a3934;
  --sidebar-text: #f1f7f4;
  --sidebar-muted: #a8bdb7;
  --warning: #815b20;
  --warning-soft: #fff6df;
  --danger: #a34e48;
  --shadow: 0 3px 14px rgba(27, 55, 47, .035);
  --radius-lg: 18px;
  --radius-md: 12px;
  --radius-sm: 8px;
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #101b19;
  --surface: #172522;
  --surface-soft: #1c2c28;
  --surface-tint: #203a32;
  --text: #edf5f1;
  --muted: #a0b3ad;
  --muted-strong: #c3d1cb;
  --border: #30443d;
  --accent: #7bd0b4;
  --accent-strong: #9ce3c9;
  --accent-soft: #1b3b31;
  --accent-bright: #2c5244;
  --sidebar: #0c1715;
  --sidebar-2: #142823;
  --sidebar-text: #f1f7f4;
  --sidebar-muted: #9bb4ab;
  --warning: #efd194;
  --warning-soft: #3b3120;
  --danger: #f0a39b;
  --shadow: 0 3px 14px rgba(0, 0, 0, .12);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 100px; }
body { margin: 0; background: var(--page); color: var(--text); font: 15px/1.55 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; -webkit-font-smoothing: antialiased; }
button, input { font: inherit; }
button { cursor: pointer; }
button:focus-visible, a:focus-visible, input:focus-visible { outline: 3px solid #8ecfba; outline-offset: 3px; }
a { color: inherit; }
svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.skip-link { position: fixed; z-index: 100; top: 12px; left: 12px; padding: 10px 14px; border-radius: 8px; background: var(--surface); color: var(--text); transform: translateY(-160%); }
.skip-link:focus { transform: translateY(0); }
.app-shell { min-height: 100vh; }
.sidebar { position: fixed; inset: 0 auto 0 0; z-index: 40; display: flex; flex-direction: column; width: 248px; padding: 25px 16px 18px; background: var(--sidebar); color: var(--sidebar-text); }
.brand { display: flex; align-items: center; gap: 11px; padding: 0 10px 27px; color: var(--sidebar-text); text-decoration: none; }
.brand-mark { display: grid; place-items: center; width: 42px; height: 42px; border: 1px solid rgba(189,231,210,.35); border-radius: 13px; background: var(--sidebar-2); color: #c0ecd6; }
.brand-mark svg { width: 27px; height: 27px; }
.brand-name { display: block; font-size: 18px; line-height: 1.2; font-weight: 760; letter-spacing: -.55px; }
.brand-caption { display: block; margin-top: 5px; color: var(--sidebar-muted); font-size: 9px; font-weight: 750; letter-spacing: 1.55px; }
.nav-heading { padding: 10px 12px 9px; color: #88a49b; font-size: 10px; font-weight: 800; letter-spacing: 1.45px; }
.nav-list { display: grid; gap: 5px; }
.nav-link { display: flex; align-items: center; gap: 12px; min-height: 43px; padding: 10px 12px; border: 1px solid transparent; border-radius: 10px; color: var(--sidebar-muted); text-decoration: none; font-size: 13px; font-weight: 580; transition: background .16s ease, color .16s ease, border-color .16s ease; }
.nav-link svg { width: 17px; height: 17px; }
.nav-link:hover { background: rgba(255,255,255,.055); color: var(--sidebar-text); }
.nav-link.active { background: rgba(189,231,210,.12); border-color: rgba(189,231,210,.12); color: #e8f8ef; }
.nav-link.active::after { width: 5px; height: 5px; margin-left: auto; border-radius: 50%; background: #9bdfbf; content: ""; }
.sidebar-spacer { flex: 1; }
.sidebar-note { display: flex; align-items: flex-start; gap: 10px; margin: 18px 4px 15px; padding: 13px 11px; border: 1px solid rgba(190,221,208,.14); border-radius: 11px; background: rgba(255,255,255,.035); }
.sidebar-note .status-dot { flex: 0 0 auto; width: 7px; height: 7px; margin-top: 6px; border-radius: 50%; background: #7ad2aa; box-shadow: 0 0 0 4px rgba(122,210,170,.12); }
.sidebar-note strong { display: block; color: #edf6f1; font-size: 11px; font-weight: 700; }
.sidebar-note span { display: block; margin-top: 3px; color: var(--sidebar-muted); font-size: 10px; line-height: 1.5; }
.sidebar-foot { padding: 14px 10px 0; border-top: 1px solid rgba(255,255,255,.1); color: #89a39a; font-size: 10px; line-height: 1.7; }
.main-column { min-width: 0; margin-left: 248px; }
.topbar { position: sticky; top: 0; z-index: 30; display: flex; align-items: center; gap: 20px; min-height: 72px; padding: 12px clamp(20px, 3.1vw, 46px); border-bottom: 1px solid var(--border); background: color-mix(in srgb, var(--surface) 93%, transparent); backdrop-filter: blur(16px); }
.breadcrumbs { display: flex; align-items: center; gap: 9px; color: var(--muted); font-size: 11px; font-weight: 720; letter-spacing: .65px; white-space: nowrap; }
.breadcrumbs .crumb-current { color: var(--text); }
.breadcrumb-separator { color: #9fb0a9; font-size: 16px; font-weight: 400; }
.topbar-spacer { flex: 1; }
.search-wrap { position: relative; width: min(245px, 25vw); }
.search-wrap svg { position: absolute; top: 50%; left: 12px; width: 16px; height: 16px; color: var(--muted); transform: translateY(-50%); pointer-events: none; }
.search-input { width: 100%; height: 39px; padding: 0 12px 0 37px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface-soft); color: var(--text); font-size: 12px; }
.search-input::placeholder { color: var(--muted); }
.top-actions { display: flex; align-items: center; gap: 8px; }
.privacy-pill { display: inline-flex; align-items: center; gap: 7px; padding: 8px 10px; border: 1px solid var(--border); border-radius: 999px; color: var(--muted-strong); font-size: 10px; font-weight: 780; letter-spacing: .35px; white-space: nowrap; }
.privacy-pill .status-dot { width: 6px; height: 6px; border-radius: 50%; background: #24956f; }
.icon-button { display: inline-grid; place-items: center; width: 39px; height: 39px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); color: var(--muted-strong); }
.icon-button:hover { background: var(--surface-tint); color: var(--accent); }
.button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 39px; padding: 0 13px; border: 1px solid transparent; border-radius: 10px; font-size: 11px; font-weight: 760; white-space: nowrap; transition: transform .12s ease, background .12s ease; }
.button:active { transform: translateY(1px); }
.button svg { width: 15px; height: 15px; }
.button-secondary { border-color: var(--border); background: var(--surface); color: var(--text); }
.button-secondary:hover { background: var(--surface-soft); }
.button-primary { background: var(--accent); color: #fff; }
:root[data-theme="dark"] .button-primary { color: #10211b; }
.button-primary:hover { background: var(--accent-strong); }
.menu-toggle { display: none; flex: 0 0 auto; }
.content { width: min(100%, 1510px); margin: 0 auto; padding: 36px clamp(20px, 3.1vw, 46px) 46px; }
.page-intro { display: flex; align-items: flex-end; justify-content: space-between; gap: 30px; margin-bottom: 25px; }
.eyebrow { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; color: var(--accent); font-size: 10px; font-weight: 850; letter-spacing: 1.35px; text-transform: uppercase; }
.eyebrow-dot { width: 7px; height: 7px; border-radius: 2px; background: var(--accent); transform: rotate(45deg); }
h1, h2, h3, p { margin-top: 0; }
h1 { margin-bottom: 10px; color: var(--text); font-size: clamp(27px, 3vw, 38px); font-weight: 760; letter-spacing: -1.4px; line-height: 1.13; overflow-wrap: anywhere; }
.intro-copy { max-width: 690px; margin-bottom: 0; color: var(--muted); font-size: 13px; line-height: 1.8; }
.intro-tag { display: inline-flex; align-items: center; gap: 8px; padding: 9px 12px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); color: var(--muted-strong); font-size: 10px; font-weight: 700; white-space: nowrap; }
.intro-tag svg { width: 15px; height: 15px; color: var(--accent); }
.notice { display: flex; align-items: flex-start; gap: 12px; margin: 23px 0 25px; padding: 14px 16px; border: 1px solid #e9d8af; border-radius: 12px; background: var(--warning-soft); color: var(--warning); }
.notice-icon { display: grid; flex: 0 0 auto; place-items: center; width: 27px; height: 27px; border: 1px solid currentColor; border-radius: 8px; }
.notice-icon svg { width: 15px; height: 15px; }
.notice strong { display: block; margin: 1px 0 2px; font-size: 11px; font-weight: 800; letter-spacing: .2px; }
.notice p { margin: 0; font-size: 11px; line-height: 1.65; }
.kpi-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 22px; }
.kpi-card { position: relative; min-width: 0; padding: 17px 18px 16px; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--surface); box-shadow: var(--shadow); }
.kpi-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; color: var(--muted); font-size: 11px; font-weight: 670; }
.kpi-icon { display: grid; place-items: center; width: 33px; height: 33px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface-soft); color: var(--accent); }
.kpi-icon svg { width: 17px; height: 17px; }
.kpi-value { display: block; margin-bottom: 4px; color: var(--text); font-size: clamp(25px, 2.6vw, 33px); font-weight: 780; letter-spacing: -1.1px; line-height: 1.1; font-variant-numeric: tabular-nums; }
.kpi-caption { color: var(--muted); font-size: 10px; line-height: 1.5; }
.dashboard-grid { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(275px, .85fr); gap: 16px; align-items: stretch; margin-bottom: 18px; }
.panel { min-width: 0; margin: 0 0 18px; padding: 22px; border: 1px solid var(--border); border-radius: var(--radius-lg); background: var(--surface); box-shadow: var(--shadow); scroll-margin-top: 93px; }
.panel:last-child { margin-bottom: 0; }
.panel-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px; margin-bottom: 19px; }
.section-kicker { margin-bottom: 6px; color: var(--accent); font-size: 9px; font-weight: 850; letter-spacing: 1.35px; text-transform: uppercase; }
.panel h2 { margin-bottom: 5px; color: var(--text); font-size: 17px; font-weight: 760; letter-spacing: -.35px; line-height: 1.3; }
.panel-description { max-width: 720px; margin-bottom: 0; color: var(--muted); font-size: 11px; line-height: 1.7; }
.tag { display: inline-flex; align-items: center; gap: 6px; width: fit-content; padding: 5px 8px; border-radius: 6px; font-size: 9px; font-weight: 800; letter-spacing: .25px; white-space: nowrap; }
.tag-neutral { background: var(--surface-tint); color: var(--muted-strong); }
.tag-accent { background: var(--accent-soft); color: var(--accent); }
.composition-list { display: grid; gap: 14px; }
.composition-row { display: grid; grid-template-columns: 118px minmax(70px, 1fr) 54px; align-items: center; gap: 13px; }
.composition-label { display: flex; align-items: center; gap: 9px; min-width: 0; }
.symbol-chip { display: inline-grid; flex: 0 0 auto; place-items: center; min-width: 29px; height: 29px; padding: 0 6px; border: 1px solid color-mix(in srgb, var(--symbol-color) 28%, var(--border)); border-radius: 8px; background: color-mix(in srgb, var(--symbol-color) 11%, var(--surface)); color: var(--text); font: 760 11px/1 ui-monospace, SFMono-Regular, Menlo, monospace; }
.composition-percent { color: var(--muted); font-size: 10px; font-variant-numeric: tabular-nums; }
.composition-track { height: 7px; overflow: hidden; border-radius: 100px; background: var(--surface-tint); }
.composition-track span { display: block; height: 100%; min-width: 0; border-radius: inherit; background: var(--symbol-color); }
.composition-count { color: var(--text); text-align: right; font-size: 11px; font-variant-numeric: tabular-nums; }
.composition-foot { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-top: 22px; padding-top: 14px; border-top: 1px solid var(--border); color: var(--muted); font-size: 10px; }
.composition-foot strong { color: var(--text); font-weight: 760; }
.legend { display: flex; flex-wrap: wrap; gap: 8px 13px; margin-top: 16px; }
.legend-item { display: inline-flex; align-items: center; gap: 6px; color: var(--muted); font-size: 10px; }
.swatch { width: 9px; height: 9px; border-radius: 3px; background: var(--swatch-color); }
.legend-symbol { color: var(--text); font: 760 10px/1 ui-monospace, SFMono-Regular, Menlo, monospace; }
.snapshot-stack { display: grid; gap: 11px; }
.snapshot-item { display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid var(--border); border-radius: 11px; background: var(--surface-soft); }
.snapshot-icon { display: grid; flex: 0 0 auto; place-items: center; width: 34px; height: 34px; border-radius: 10px; background: var(--surface-tint); color: var(--accent); }
.snapshot-icon svg { width: 17px; height: 17px; }
.snapshot-copy { min-width: 0; flex: 1; }
.snapshot-copy strong { display: block; color: var(--text); font-size: 12px; font-weight: 760; }
.snapshot-copy span { display: block; margin-top: 2px; color: var(--muted); font-size: 10px; line-height: 1.45; }
.snapshot-number { color: var(--text); font-size: 18px; font-weight: 770; letter-spacing: -.55px; font-variant-numeric: tabular-nums; }
.section-panel { margin-bottom: 18px; }
.section-panel .panel-header { margin-bottom: 20px; }
.sequence-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 13px; }
.sequence-card { min-width: 0; overflow: hidden; padding: 16px; border: 1px solid var(--border); border-radius: 13px; background: var(--surface); transition: border-color .16s ease, transform .16s ease; }
.sequence-card:hover { border-color: color-mix(in srgb, var(--accent) 32%, var(--border)); transform: translateY(-1px); }
.sequence-card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; margin-bottom: 13px; }
.sequence-title-wrap { display: flex; align-items: center; gap: 10px; min-width: 0; }
.sequence-index { display: grid; flex: 0 0 auto; place-items: center; width: 33px; height: 33px; border: 1px solid var(--border); border-radius: 9px; background: var(--surface-soft); color: var(--muted-strong); font: 760 10px/1 ui-monospace, SFMono-Regular, Menlo, monospace; }
.sequence-card h3 { margin: 0; color: var(--text); font-size: 12px; font-weight: 760; overflow-wrap: anywhere; }
.sequence-description { margin: 3px 0 0; color: var(--muted); font-size: 10px; overflow-wrap: anywhere; }
.sequence-metrics { display: flex; flex-wrap: wrap; gap: 8px 16px; margin-bottom: 11px; padding-bottom: 12px; border-bottom: 1px solid var(--border); color: var(--muted); font-size: 10px; }
.sequence-metrics strong { color: var(--text); font-size: 11px; font-weight: 760; font-variant-numeric: tabular-nums; }
.sequence { max-height: 126px; overflow: auto; padding: 9px 10px; border: 1px solid var(--border); border-radius: 9px; background: var(--surface-soft); font: 700 11px/1.9 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow-wrap: anywhere; word-break: break-word; }
.base { display: inline-block; margin: 1px 0; padding: 0 1.5px; border-radius: 2px; }
.base-A { color: #d62828; background: rgba(214,40,40,.10); }
.base-T { color: #9a7514; background: rgba(233,196,106,.22); }
.base-G { color: #157a6e; background: rgba(42,157,143,.12); }
.base-C { color: #35627f; background: rgba(69,123,157,.12); }
.base-U { color: #8d5528; background: rgba(141,85,40,.12); }
.base-N { color: var(--muted); background: var(--surface-tint); }
.truncation { color: var(--muted); font-size: 10px; font-weight: 600; }
.svg-wrap { overflow-x: auto; margin-top: 10px; padding-bottom: 2px; }
.svg-wrap svg { display: block; width: 100%; min-width: 180px; height: auto; max-height: 48px; border-radius: 4px; }
.sequence-card-footer { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: 11px; }
.sequence-footnote { color: var(--muted); font-size: 9px; line-height: 1.5; }
.text-button { display: inline-flex; flex: 0 0 auto; align-items: center; gap: 6px; padding: 5px 0 5px 6px; border: 0; background: transparent; color: var(--accent); font-size: 10px; font-weight: 800; }
.text-button svg { width: 13px; height: 13px; }
.text-button:hover { color: var(--accent-strong); }
.table-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 10px; color: var(--muted); font-size: 10px; }
.table-toolbar strong { color: var(--text); font-weight: 750; }
.table-scroll { width: 100%; overflow-x: auto; border: 1px solid var(--border); border-radius: 11px; }
table { width: 100%; border-collapse: collapse; font-size: 11px; }
thead { background: var(--surface-soft); }
th, td { padding: 12px 13px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; line-height: 1.55; }
th { color: var(--muted-strong); font-size: 9px; font-weight: 850; letter-spacing: .45px; text-transform: uppercase; white-space: nowrap; }
td { color: var(--text); }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: var(--surface-soft); }
td code { padding: 2px 5px; border-radius: 5px; background: var(--surface-tint); color: var(--accent-strong); font: 650 10px/1.4 ui-monospace, SFMono-Regular, Menlo, monospace; }
td:first-child { font-weight: 650; }
.empty-state { display: grid; justify-items: center; padding: 36px 20px; border: 1px dashed var(--border); border-radius: 12px; background: var(--surface-soft); text-align: center; }
.empty-state.compact { padding: 20px 12px; }
.empty-icon { display: grid; place-items: center; width: 40px; height: 40px; margin-bottom: 12px; border: 1px solid var(--border); border-radius: 12px; background: var(--surface); color: var(--muted); font-size: 23px; }
.empty-state h3 { margin-bottom: 5px; font-size: 13px; }
.empty-state p { max-width: 400px; margin: 0; color: var(--muted); font-size: 11px; line-height: 1.7; }
.ref-plan { max-height: 330px; overflow: auto; margin: 0; padding: 16px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface-soft); color: var(--muted-strong); white-space: pre-wrap; overflow-wrap: anywhere; font: 11px/1.7 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
.panel-note { display: flex; gap: 9px; align-items: flex-start; margin-top: 13px; color: var(--muted); font-size: 10px; line-height: 1.6; }
.panel-note svg { flex: 0 0 auto; width: 14px; height: 14px; margin-top: 1px; color: var(--accent); }
.filter-status { min-height: 17px; margin-top: 10px; color: var(--muted); font-size: 10px; }
.report-footer { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: 25px; padding: 18px 2px 0; border-top: 1px solid var(--border); color: var(--muted); font-size: 10px; }
.footer-brand { display: flex; align-items: center; gap: 8px; color: var(--muted-strong); font-weight: 780; }
.footer-brand svg { width: 17px; height: 17px; color: var(--accent); }
.footer-disclaimer { max-width: 580px; text-align: right; line-height: 1.6; }
.toast { position: fixed; right: 24px; bottom: 24px; z-index: 70; max-width: min(360px, calc(100vw - 32px)); padding: 12px 16px; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); color: var(--text); box-shadow: 0 12px 34px rgba(0,0,0,.14); font-size: 12px; opacity: 0; pointer-events: none; transform: translateY(8px); transition: opacity .18s ease, transform .18s ease; }
.toast.visible { opacity: 1; transform: translateY(0); }
.sr-only { position: absolute !important; width: 1px !important; height: 1px !important; padding: 0 !important; margin: -1px !important; overflow: hidden !important; clip: rect(0,0,0,0) !important; white-space: nowrap !important; border: 0 !important; }
.sidebar-backdrop { display: none; }
@media (min-width: 1600px) { .content { padding-right: 52px; padding-left: 52px; } }
@media (max-width: 1250px) {
  .sidebar { width: 224px; }
  .main-column { margin-left: 224px; }
  .privacy-pill { display: none; }
  .kpi-grid { gap: 10px; }
  .kpi-card { padding: 15px; }
  .dashboard-grid { grid-template-columns: minmax(0, 1.25fr) minmax(250px, .9fr); }
  .sequence-grid { grid-template-columns: 1fr; }
}
@media (max-width: 940px) {
  .sidebar { width: 248px; transform: translateX(-102%); transition: transform .22s ease; box-shadow: none; }
  .sidebar.is-open { transform: translateX(0); box-shadow: 18px 0 50px rgba(0,0,0,.2); }
  .sidebar-backdrop.visible { position: fixed; inset: 0; z-index: 35; display: block; border: 0; background: rgba(7,20,17,.42); }
  .main-column { margin-left: 0; }
  .menu-toggle { display: inline-grid; }
  .dashboard-grid { grid-template-columns: 1fr; }
  .sequence-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 690px) {
  .topbar { gap: 10px; min-height: 63px; padding: 10px 15px; }
  .breadcrumbs { display: none; }
  .topbar-spacer { flex: 1; }
  .search-wrap { width: min(43vw, 205px); }
  .search-input { height: 37px; font-size: 11px; }
  .top-actions { gap: 6px; }
  .top-actions .button { width: 38px; min-width: 38px; padding: 0; font-size: 0; }
  .top-actions .button svg { width: 16px; height: 16px; }
  .icon-button { width: 37px; height: 37px; }
  .content { padding: 26px 14px 30px; }
  .page-intro { display: block; margin-bottom: 20px; }
  h1 { font-size: 29px; letter-spacing: -.8px; }
  .intro-copy { font-size: 12px; }
  .intro-tag { margin-top: 14px; }
  .notice { gap: 9px; margin: 18px 0; padding: 12px; }
  .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; margin-bottom: 14px; }
  .kpi-card { padding: 13px; border-radius: 11px; }
  .kpi-top { align-items: flex-start; gap: 5px; margin-bottom: 11px; font-size: 10px; }
  .kpi-icon { width: 28px; height: 28px; }
  .kpi-value { font-size: 27px; }
  .dashboard-grid { gap: 12px; margin-bottom: 12px; }
  .panel { padding: 16px; margin-bottom: 12px; border-radius: 13px; }
  .panel-header { gap: 10px; margin-bottom: 15px; }
  .panel h2 { font-size: 15px; }
  .panel-description { font-size: 10px; }
  .composition-row { grid-template-columns: 93px minmax(35px, 1fr) 38px; gap: 7px; }
  .composition-label { gap: 6px; }
  .symbol-chip { min-width: 26px; height: 26px; }
  .composition-count { font-size: 10px; }
  .composition-percent { font-size: 9px; }
  .sequence-grid { grid-template-columns: 1fr; }
  .table-scroll { border-radius: 9px; }
  th, td { padding: 10px; }
  .report-footer { display: block; }
  .footer-disclaimer { margin-top: 8px; text-align: left; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; animation-duration: .01ms !important; transition-duration: .01ms !important; }
}
@media print {
  :root, :root[data-theme="dark"] { color-scheme: light; --page:#fff; --surface:#fff; --surface-soft:#f7f8f7; --surface-tint:#eef3f0; --text:#172b27; --muted:#52645e; --muted-strong:#344941; --border:#d6dfda; --accent:#176c5d; }
  body { background: #fff; font-size: 10pt; }
  .sidebar, .topbar, .toast, .sidebar-backdrop, .search-wrap, .sequence-card-footer, .sidebar-backdrop, .intro-tag { display: none !important; }
  .main-column { margin: 0; }
  .content { width: 100%; padding: 0; }
  .panel, .kpi-card, .sequence-card { break-inside: avoid; box-shadow: none; }
  .panel { padding: 13px; margin-bottom: 12px; }
  .dashboard-grid { grid-template-columns: 1.3fr 1fr; }
  .sequence-grid { grid-template-columns: 1fr 1fr; }
  .svg-wrap svg { max-height: 38px; }
  .sequence { max-height: none; overflow: visible; }
  a { text-decoration: none; }
}
</style>
</head>
<body>
<a class="skip-link" href="#main-content">Skip to report</a>
<div class="app-shell">
<aside class="sidebar" id="sidebar" aria-label="Report navigation">
  <a class="brand" href="#overview" aria-label="Genopedia report overview">
    <span class="brand-mark"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3c7 3 3 15 10 18"></path><path d="M17 3C10 6 14 18 7 21"></path><path d="M8.5 6h7"></path><path d="M7.6 11h8.8"></path><path d="M7.7 16h8.6"></path></svg></span>
    <span><span class="brand-name">Genopedia</span><span class="brand-caption">SEQUENCE INTELLIGENCE</span></span>
  </a>
  <div class="nav-heading">REPORT WORKSPACE</div>
  <nav class="nav-list" aria-label="Report sections">
    <a class="nav-link active" href="#overview" data-nav-link><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1.5"></rect><rect x="14" y="3" width="7" height="4" rx="1.3"></rect><rect x="14" y="10" width="7" height="11" rx="1.5"></rect><rect x="3" y="13" width="7" height="8" rx="1.5"></rect></svg><span>Overview</span></a>
    <a class="nav-link" href="#sequences" data-nav-link><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3c7 3 3 15 10 18"></path><path d="M17 3C10 6 14 18 7 21"></path><path d="M8.5 6h7"></path><path d="M7.6 11h8.8"></path><path d="M7.7 16h8.6"></path></svg><span>Sequence explorer</span></a>
    <a class="nav-link" href="#quality" data-nav-link><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19V5"></path><path d="M4 19h17"></path><path d="m7 15 4-4 3 2 5-7"></path><path d="M15 6h4v4"></path></svg><span>Quality control</span></a>
    <a class="nav-link" href="#signals" data-nav-link><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 9 16H3L12 3Z"></path><path d="M12 9v4"></path><path d="M12 16h.01"></path></svg><span>QC signals</span></a>
    <a class="nav-link" href="#references" data-nav-link><svg viewBox="0 0 24 24" aria-hidden="true"><ellipse cx="12" cy="5" rx="8" ry="3"></ellipse><path d="M4 5v7c0 1.7 3.6 3 8 3"></path><path d="M20 5v5"></path><path d="M4 12v7c0 1.7 3.6 3 8 3"></path><circle cx="18" cy="17" r="3"></circle><path d="m20.2 19.2 1.8 1.8"></path></svg><span>Reference plan</span></a>
    <a class="nav-link" href="#variants" data-nav-link><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3v6a5 5 0 0 0 5 5 5 5 0 0 1 5 5v2"></path><path d="M17 3v4a4 4 0 0 1-4 4h-2"></path><path d="M4 3h6"></path><path d="M14 3h6"></path><path d="M14 21h6"></path></svg><span>Observed variants</span></a>
    <a class="nav-link" href="#corrections" data-nav-link><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 4 6v5c0 5 3.5 8 8 10 4.5-2 8-5 8-10V6l-8-3Z"></path><path d="m8.5 12 2.2 2.2 4.8-5"></path></svg><span>Correction planning</span></a>
  </nav>
  <div class="sidebar-spacer"></div>
  <div class="sidebar-note"><span class="status-dot" aria-hidden="true"></span><div><strong>Private by design</strong><span>This report runs locally. No data is uploaded by this page.</span></div></div>
  <div class="sidebar-foot">GENOPEDIA · RESEARCH EDITION<br>Offline report experience</div>
</aside>
<button class="sidebar-backdrop" id="sidebar-backdrop" type="button" aria-label="Close navigation" hidden></button>
<div class="main-column">
  <header class="topbar">
    <button class="icon-button menu-toggle" id="menu-toggle" type="button" aria-label="Open report navigation" aria-expanded="false" aria-controls="sidebar"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"></path></svg></button>
    <div class="breadcrumbs"><span>GENOPEDIA</span><span class="breadcrumb-separator">/</span><span class="crumb-current">ANALYSIS REPORT</span></div>
    <div class="topbar-spacer"></div>
    <label class="search-wrap"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="m16 16 4 4"></path></svg><input class="search-input" id="report-search" type="search" placeholder="Filter tables and sequences…" aria-label="Filter report tables and sequences"></label>
    <div class="top-actions">
      <span class="privacy-pill"><span class="status-dot" aria-hidden="true"></span> LOCAL REPORT</span>
      <button class="icon-button" id="theme-toggle" type="button" aria-label="Switch to dark theme" aria-pressed="false" title="Toggle theme"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 15.5A8.5 8.5 0 0 1 8.5 3.5 8.5 8.5 0 1 0 20.5 15.5Z"></path></svg></button>
      <button class="button button-secondary" id="export-json" type="button" title="Download the report data as JSON"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12"></path><path d="m7 10 5 5 5-5"></path><path d="M5 21h14"></path></svg> Export JSON</button>
      <button class="button button-primary" id="print-report" type="button" title="Print or save this report as PDF"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 8V3h10v5"></path><rect x="5" y="14" width="14" height="7" rx="1.5"></rect><path d="M5 17H3V10h18v7h-2"></path><path d="M17 11h1"></path></svg> Print report</button>
    </div>
  </header>
  <main class="content" id="main-content">
    <section class="page-intro" id="overview" aria-labelledby="report-title">
      <div>
        <div class="eyebrow"><span class="eyebrow-dot" aria-hidden="true"></span> SEQUENCE INTELLIGENCE · RESEARCH</div>
        <h1 id="report-title">__TITLE__</h1>
        <p class="intro-copy">A focused view of your sequence data, quality indicators, observed variants, and source-selection context. All report content is prepared for local inspection.</p>
      </div>
      <div class="intro-tag"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 4 6v5c0 5 3.5 8 8 10 4.5-2 8-5 8-10V6l-8-3Z"></path><path d="m8.5 12 2.2 2.2 4.8-5"></path></svg> Offline-first report</div>
    </section>
    <aside class="notice" aria-label="Research use notice">
      <span class="notice-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 9 16H3L12 3Z"></path><path d="M12 9v4"></path><path d="M12 16h.01"></path></svg></span>
      <div><strong>Research use only · Human review required</strong><p>Quality signals and candidate variants are informational. This report is not a diagnosis, treatment recommendation, or laboratory instruction. No automatic sequence editing is performed.</p></div>
    </aside>
    <section class="kpi-grid" aria-label="Report summary metrics">
      <article class="kpi-card"><div class="kpi-top"><span>Sequence records</span><span class="kpi-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3c7 3 3 15 10 18"></path><path d="M17 3C10 6 14 18 7 21"></path><path d="M8.5 6h7"></path><path d="M7.6 11h8.8"></path><path d="M7.7 16h8.6"></path></svg></span></div><strong class="kpi-value">__RECORD_COUNT__</strong><span class="kpi-caption">Inputs represented in this report</span></article>
      <article class="kpi-card"><div class="kpi-top"><span>Total symbols</span><span class="kpi-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"></path><circle cx="8" cy="7" r="1.5"></circle><circle cx="15" cy="12" r="1.5"></circle><circle cx="10" cy="17" r="1.5"></circle></svg></span></div><strong class="kpi-value">__TOTAL_BASES__</strong><span class="kpi-caption">Combined sequence length</span></article>
      <article class="kpi-card"><div class="kpi-top"><span>Observed variants</span><span class="kpi-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3v6a5 5 0 0 0 5 5 5 5 0 0 1 5 5v2"></path><path d="M17 3v4a4 4 0 0 1-4 4h-2"></path><path d="M4 3h6M14 3h6M14 21h6"></path></svg></span></div><strong class="kpi-value">__VARIANT_COUNT__</strong><span class="kpi-caption">Differences supplied or detected</span></article>
      <article class="kpi-card"><div class="kpi-top"><span>QC signal entries</span><span class="kpi-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 9 16H3L12 3Z"></path><path d="M12 9v4M12 16h.01"></path></svg></span></div><strong class="kpi-value">__SIGNAL_COUNT__</strong><span class="kpi-caption">Review signals, not diagnoses</span></article>
    </section>
    <div class="dashboard-grid">
      <section class="panel" aria-labelledby="composition-title">
        <div class="panel-header"><div><div class="section-kicker">AT A GLANCE</div><h2 id="composition-title">Sequence composition</h2><p class="panel-description">Symbol frequencies across all sequence records, summarized for quick visual scanning.</p></div><span class="tag tag-neutral">__TOTAL_BASES__ symbols</span></div>
        <div class="composition-list">__COMPOSITION__</div>
        <div class="composition-foot"><span>Symbols counted across all records</span><strong>__TOTAL_BASES__ total</strong></div>
      </section>
      <section class="panel" aria-labelledby="snapshot-title">
        <div class="panel-header"><div><div class="section-kicker">REPORT SNAPSHOT</div><h2 id="snapshot-title">Analysis inventory</h2><p class="panel-description">What this local report contains.</p></div></div>
        <div class="snapshot-stack">
          <div class="snapshot-item"><span class="snapshot-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19V5"></path><path d="M4 19h17"></path><path d="m7 15 4-4 3 2 5-7"></path></svg></span><span class="snapshot-copy"><strong>Quality control</strong><span>Per-record checks and warnings</span></span><strong class="snapshot-number">__QUALITY_COUNT__</strong></div>
          <div class="snapshot-item"><span class="snapshot-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m12 3 9 16H3L12 3Z"></path><path d="M12 9v4M12 16h.01"></path></svg></span><span class="snapshot-copy"><strong>QC signal entries</strong><span>Pattern-based review prompts</span></span><strong class="snapshot-number">__SIGNAL_COUNT__</strong></div>
          <div class="snapshot-item"><span class="snapshot-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 4 6v5c0 5 3.5 8 8 10 4.5-2 8-5 8-10V6l-8-3Z"></path></svg></span><span class="snapshot-copy"><strong>Correction planning</strong><span>Evidence-led suggestions for review</span></span><strong class="snapshot-number">__CORRECTION_COUNT__</strong></div>
          <div class="snapshot-item"><span class="snapshot-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><ellipse cx="12" cy="5" rx="8" ry="3"></ellipse><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"></path></svg></span><span class="snapshot-copy"><strong>Reference plan</strong><span>Optional metadata-first source guidance</span></span><strong class="snapshot-number">__REFERENCE_COUNT__</strong></div>
        </div>
      </section>
    </div>
    <section class="panel section-panel" id="sequences" aria-labelledby="sequences-title">
      <div class="panel-header"><div><div class="section-kicker">INPUTS</div><h2 id="sequences-title">Sequence explorer</h2><p class="panel-description">Inspect record metadata, scan color-coded symbols, and copy a normalized sequence for local work.</p></div><span class="tag tag-accent">__RECORD_COUNT__ records</span></div>
      <div class="sequence-grid">__SEQUENCE_CARDS__</div>
      <div class="legend" aria-label="Nucleotide color key">__LEGEND__</div>
    </section>
    <section class="panel section-panel" id="quality" aria-labelledby="quality-title">
      <div class="panel-header"><div><div class="section-kicker">QUALITY &amp; INTEGRITY</div><h2 id="quality-title">Quality control</h2><p class="panel-description">A record-level view of sequence length, GC fraction, ambiguous symbols, and parser or quality warnings.</p></div><span class="tag tag-neutral">__QUALITY_COUNT__ records</span></div>
      <div class="table-toolbar"><span><strong>Quality summary</strong> · use the top search field to filter rows</span><span>Local metrics</span></div>
      <div class="table-scroll">__QUALITY_TABLE__</div>
      <div class="filter-status" data-filter-status></div>
    </section>
    <section class="panel section-panel" id="signals" aria-labelledby="signals-title">
      <div class="panel-header"><div><div class="section-kicker">REVIEW PROMPTS</div><h2 id="signals-title">Sequence-quality signals</h2><p class="panel-description">Transparent pattern flags designed to focus human review. A signal is not proof of a biological defect.</p></div><span class="tag tag-neutral">__SIGNAL_COUNT__ entries</span></div>
      <div class="table-toolbar"><span><strong>Signals and suggested next steps</strong></span><span>Not diagnostic</span></div>
      <div class="table-scroll">__ANOMALY_TABLE__</div>
      <div class="filter-status" data-filter-status></div>
    </section>
    <section class="panel section-panel" id="references" aria-labelledby="references-title">
      <div class="panel-header"><div><div class="section-kicker">DATA PROVENANCE</div><h2 id="references-title">Reference selection plan</h2><p class="panel-description">A deterministic metadata-first plan for research comparison. Provider access, versions, and redistribution terms remain source-specific.</p></div><span class="tag tag-neutral">__REFERENCE_COUNT__ planned sources</span></div>
      <pre class="ref-plan">__REFERENCE_PLAN__</pre>
      <div class="panel-note"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><path d="M12 11v5M12 8h.01"></path></svg><span>Reference metadata does not establish scientific validity by itself. Verify source versions, access rights, and the relevance of every source before drawing conclusions.</span></div>
    </section>
    <section class="panel section-panel" id="variants" aria-labelledby="variants-title">
      <div class="panel-header"><div><div class="section-kicker">COMPARISON</div><h2 id="variants-title">Observed variants</h2><p class="panel-description">Differences represented in the analysis input. Interpretation remains unknown unless matching evidence has been supplied.</p></div><span class="tag tag-neutral">__VARIANT_COUNT__ entries</span></div>
      <div class="table-scroll">__VARIANT_TABLE__</div>
      <div class="filter-status" data-filter-status></div>
    </section>
    <section class="panel section-panel" id="corrections" aria-labelledby="corrections-title">
      <div class="panel-header"><div><div class="section-kicker">HUMAN REVIEW</div><h2 id="corrections-title">Correction planning</h2><p class="panel-description">Evidence-gated candidate suggestions to examine, not edits to apply. The observed sequence is never rewritten by this planner.</p></div><span class="tag tag-neutral">__CORRECTION_COUNT__ candidates</span></div>
      <div class="table-scroll">__CORRECTION_TABLE__</div>
      <div class="panel-note"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3 4 6v5c0 5 3.5 8 8 10 4.5-2 8-5 8-10V6l-8-3Z"></path><path d="m8.5 12 2.2 2.2 4.8-5"></path></svg><span>Every candidate requires independent evidence assessment and qualified human review. This report does not propose organism engineering or laboratory actions.</span></div>
    </section>
    <footer class="report-footer"><div class="footer-brand"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3c7 3 3 15 10 18"></path><path d="M17 3C10 6 14 18 7 21"></path><path d="M8.5 6h7M7.6 11h8.8M7.7 16h8.6"></path></svg> Genopedia <span class="tag tag-neutral">Research</span></div><div class="footer-disclaimer">Offline-first sequence review · not for clinical decision-making · report data stays in this page</div></footer>
  </main>
</div>
</div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>
(function () {
  "use strict";
  const reportData = __JSON_DATA__;
  const root = document.documentElement;
  const searchInput = document.getElementById("report-search");
  const filterStatuses = Array.from(document.querySelectorAll("[data-filter-status]"));
  const toast = document.getElementById("toast");
  const sidebar = document.getElementById("sidebar");
  const menuToggle = document.getElementById("menu-toggle");
  const backdrop = document.getElementById("sidebar-backdrop");
  let toastTimer;

  function announce(message) {
    toast.textContent = message;
    toast.classList.add("visible");
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(function () {
      toast.classList.remove("visible");
    }, 2600);
  }

  function closeMenu() {
    sidebar.classList.remove("is-open");
    backdrop.classList.remove("visible");
    backdrop.hidden = true;
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "Open report navigation");
  }

  menuToggle.addEventListener("click", function () {
    const isOpen = sidebar.classList.toggle("is-open");
    backdrop.hidden = !isOpen;
    backdrop.classList.toggle("visible", isOpen);
    menuToggle.setAttribute("aria-expanded", String(isOpen));
    menuToggle.setAttribute("aria-label", isOpen ? "Close report navigation" : "Open report navigation");
  });
  backdrop.addEventListener("click", closeMenu);
  document.querySelectorAll("[data-nav-link]").forEach(function (link) {
    link.addEventListener("click", function () {
      document.querySelectorAll("[data-nav-link]").forEach(function (item) {
        item.classList.toggle("active", item === link);
      });
      closeMenu();
    });
  });

  const themeToggle = document.getElementById("theme-toggle");
  themeToggle.addEventListener("click", function () {
    const isDark = root.dataset.theme !== "dark";
    root.dataset.theme = isDark ? "dark" : "light";
    themeToggle.setAttribute("aria-pressed", String(isDark));
    themeToggle.setAttribute("aria-label", isDark ? "Switch to light theme" : "Switch to dark theme");
    themeToggle.innerHTML = isDark
      ? '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2M12 20v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"></path></svg>'
      : '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.5 15.5A8.5 8.5 0 0 1 8.5 3.5 8.5 8.5 0 1 0 20.5 15.5Z"></path></svg>';
  });

  function applyFilter() {
    const query = (searchInput.value || "").trim().toLowerCase();
    let shownRows = 0;
    let shownSequences = 0;
    document.querySelectorAll(".filterable tbody tr").forEach(function (row) {
      const matched = !query || row.textContent.toLowerCase().includes(query);
      row.hidden = !matched;
      if (matched) shownRows += 1;
    });
    document.querySelectorAll("[data-search-card]").forEach(function (card) {
      const matched = !query || card.textContent.toLowerCase().includes(query);
      card.hidden = !matched;
      if (matched) shownSequences += 1;
    });
    filterStatuses.forEach(function (status) {
      if (!query) {
        status.textContent = "";
      } else {
        status.textContent = shownRows + " matching table row(s) · " + shownSequences + " matching sequence record(s).";
      }
    });
  }
  searchInput.addEventListener("input", applyFilter);

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    const field = document.createElement("textarea");
    field.value = text;
    field.setAttribute("readonly", "");
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();
    const copied = document.execCommand("copy");
    field.remove();
    if (!copied) throw new Error("Copy was blocked by this browser");
  }
  document.querySelectorAll("[data-copy-target]").forEach(function (button) {
    button.addEventListener("click", async function () {
      const source = document.getElementById(button.dataset.copyTarget);
      if (!source) return;
      try {
        await copyText(source.textContent);
        announce("Sequence copied to clipboard.");
      } catch (error) {
        announce("Clipboard access is unavailable. Select the sequence text to copy it manually.");
      }
    });
  });

  document.getElementById("print-report").addEventListener("click", function () {
    window.print();
  });
  document.getElementById("export-json").addEventListener("click", function () {
    const data = JSON.stringify(reportData, null, 2) + "\n";
    const blob = new Blob([data], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    const slug = (reportData.title || "genopedia-report")
      .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 64) || "genopedia-report";
    anchor.href = url;
    anchor.download = slug + ".json";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    announce("Report data export prepared.");
  });

  const navLinks = Array.from(document.querySelectorAll("[data-nav-link]"));
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver(function (entries) {
      const visible = entries.filter(function (entry) { return entry.isIntersecting; })
        .sort(function (a, b) { return b.intersectionRatio - a.intersectionRatio; });
      if (!visible.length) return;
      const id = visible[0].target.id;
      navLinks.forEach(function (link) {
        link.classList.toggle("active", link.getAttribute("href") === "#" + id);
      });
    }, { rootMargin: "-22% 0px -68% 0px", threshold: [0, 0.2, 0.5] });
    navLinks.forEach(function (link) {
      const target = document.querySelector(link.getAttribute("href"));
      if (target) observer.observe(target);
    });
  }

  window.addEventListener("resize", function () {
    if (window.innerWidth > 940) closeMenu();
  });
})();
</script>
</body>
</html>
"""
    replacements = {
        "__TITLE__": html.escape(title),
        "__RECORD_COUNT__": f"{len(records):,}",
        "__TOTAL_BASES__": f"{total_bases:,}",
        "__VARIANT_COUNT__": f"{len(variants):,}",
        "__SIGNAL_COUNT__": f"{len(sequence_anomalies):,}",
        "__QUALITY_COUNT__": f"{len(quality_reports):,}",
        "__CORRECTION_COUNT__": f"{len(correction_suggestions):,}",
        "__REFERENCE_COUNT__": f"{len(reference_plan.source_ids) if reference_plan else 0:,}",
        "__COMPOSITION__": composition_html,
        "__SEQUENCE_CARDS__": "".join(sequence_sections),
        "__LEGEND__": legend,
        "__QUALITY_TABLE__": quality_html,
        "__ANOMALY_TABLE__": anomaly_html,
        "__VARIANT_TABLE__": variant_html,
        "__CORRECTION_TABLE__": correction_html,
        "__REFERENCE_PLAN__": reference_section,
        "__JSON_DATA__": report_json,
    }
    for placeholder, value in replacements.items():
        template = template.replace(placeholder, value)
    return template


def write_html_report(path: str | Path, html_text: str) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_text, encoding="utf-8")
    return output

