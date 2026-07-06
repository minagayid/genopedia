"""Genopedia demo: run the analysis pipeline over a synthetic sequence."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.genomics import GenomicsDataLoader  # noqa: E402
from src.pipeline import GenomicsPipeline  # noqa: E402

loader = GenomicsDataLoader("data/genomics")
reference = loader.generate_synthetic_dna(120)
# Introduce a couple of point mutations to demonstrate variant calling.
sample = list(reference)
sample[10] = "A" if sample[10] != "A" else "T"
sample[50] = "G" if sample[50] != "G" else "C"
sample = "".join(sample)

report = GenomicsPipeline().run(sample=sample, reference=reference, render_html=True)

print("[Genopedia] summary:", report.summary())
print("[Genopedia] reasoning:")
for step in report.reasoning:
    print("  -", step)
print("[Genopedia] html preview:")
print(report.html[:200], "...")
