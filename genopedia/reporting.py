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
    records = list(records)
    variants = list(variants)
    quality_reports = list(quality_reports)
    sequence_anomalies = list(sequence_anomalies)
    correction_suggestions = list(correction_suggestions)
    reference_section = "No reference plan supplied."
    if reference_plan:
        reference_section = html.escape(json.dumps(reference_plan.to_dict(), indent=2, sort_keys=True))
    legend = "".join(
        f'<span class="legend-item"><span class="swatch" style="background:{color}"></span>{name} ({base})</span>'
        for base, (color, name) in BASE_COLORS.items()
    )
    sequence_sections = []
    for record in records:
        sequence_sections.append(
            f'<article><h3>{html.escape(record.identifier)}</h3>'
            f'<p>{html.escape(record.description)}</p>'
            f'<div class="sequence">{_render_sequence_spans(record.sequence)}</div>'
            f'<div class="svg-wrap">{render_svg_sequence(record.sequence)}</div></article>'
        )
    if not sequence_sections:
        sequence_sections.append("<p>No sequence records were supplied.</p>")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root {{ color-scheme: light; font-family: system-ui, sans-serif; color: #17202a; background: #f7f9fb; }}
body {{ margin: 0 auto; max-width: 1180px; padding: 2rem; }}
article, section {{ background: white; border: 1px solid #d9e2ec; border-radius: .75rem; padding: 1rem; margin: 1rem 0; }}
.sequence {{ font: 700 1rem/2 monospace; overflow-wrap: anywhere; word-break: break-all; }}
.base {{ display: inline-block; padding: 0 .18rem; border-radius: .2rem; margin: .08rem; color: white; }}
.base-A {{ background: #d62828; }} .base-T {{ background: #b88718; }} .base-G {{ background: #208476; }} .base-C {{ background: #35627f; }} .base-U {{ background: #6c3e1c; }} .base-N {{ background: #59636d; }}
.truncation {{ color: #59636d; }} .legend {{ display: flex; flex-wrap: wrap; gap: .7rem; }} .legend-item {{ display: inline-flex; align-items: center; gap: .3rem; }} .swatch {{ width: .8rem; height: .8rem; border-radius: 50%; display: inline-block; }}
.svg-wrap {{ overflow-x: auto; margin-top: 1rem; }} table {{ width: 100%; border-collapse: collapse; }} th, td {{ border-bottom: 1px solid #e5e7eb; padding: .55rem; text-align: left; vertical-align: top; }} th {{ background: #eef3f8; }} code {{ font-family: monospace; }}
</style></head><body>
<header><h1>{html.escape(title)}</h1><p>Offline, research-oriented sequence review. Interpretations require appropriate evidence and human review.</p></header>
<section><h2>Color legend</h2><div class="legend">{legend}</div></section>
<section><h2>Sequences</h2>{''.join(sequence_sections)}</section>
<section><h2>Quality control</h2>{_quality_section(quality_reports)}</section>
<section><h2>Sequence-quality anomaly signals</h2><p>These are research QC signals, not diagnoses.</p>{_anomaly_section(sequence_anomalies)}</section>
<section><h2>Reference selection plan</h2><p>Metadata-first source selection for research comparison; access terms remain provider-specific.</p><pre>{reference_section}</pre></section>
<section><h2>Observed variants</h2>{_variant_section(variants)}</section>
<section><h2>Correction planning</h2><p>Review-only planning; no automatic sequence edit is performed.</p>{_correction_section(correction_suggestions)}</section>
</body></html>"""


def write_html_report(path: str | Path, html_text: str) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_text, encoding="utf-8")
    return output

