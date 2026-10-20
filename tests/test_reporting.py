from __future__ import annotations

import unittest

from genopedia import SequenceRecord, Variant
from genopedia.reporting import render_html_report, render_svg_sequence


class ReportingTests(unittest.TestCase):
    def test_html_report_contains_escaped_sequence_and_analysis_sections(self) -> None:
        html = render_html_report(
            [SequenceRecord(identifier="sample", sequence="ATGC")],
            [Variant(chromosome="chr1", position=2, reference="G", observed="A")],
        )

        self.assertIn("Genopedia report", html)
        self.assertIn("sample", html)
        self.assertIn("Adenine", html)
        self.assertIn("Observed variants", html)
        self.assertIn('class="base base-A"', html)
        self.assertIn('class="app-shell"', html)
        self.assertIn('id="theme-toggle"', html)
        self.assertIn('id="export-json"', html)
        self.assertIn('id="report-search"', html)
        self.assertIn('id="sequences"', html)
        self.assertIn('aria-label="Research use notice"', html)

    def test_svg_renderer_returns_empty_svg_for_empty_sequence(self) -> None:
        svg = render_svg_sequence("")

        self.assertIn("<svg", svg)
        self.assertIn("</svg>", svg)
        self.assertNotIn("NaN", svg)

    def test_html_report_escapes_embedded_data_and_supports_empty_reports(self) -> None:
        report = render_html_report(
            [SequenceRecord(identifier="</script><img src=x>", sequence="ATGC")],
            title='Report </title><script>alert("x")</script>',
        )

        self.assertIn(r"\u003c/script\u003e", report)
        self.assertIn("&lt;/title&gt;", report)
        self.assertIn("No sequences in this report", render_html_report([]))

