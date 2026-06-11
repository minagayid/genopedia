"""GenoProject - resume point."""
from GenoProject.src.genomics import GenomicsDataLoader, SequenceAnalyzer, GenomicsVisualizer
from GenoProject.src.models import DNAClassifier

loader = GenomicsDataLoader("data/genomics")
sequence = loader.generate_synthetic_dna(120)
analyzer = SequenceAnalyzer()
variants = analyzer.detect_variants("ATGCCGTAG", "ATGTCGTAG")
visualizer = GenomicsVisualizer()

print("[GenoProject] sequence:", sequence)
print("[GenoProject] variants:", [v.to_dict() for v in variants])
print("[GenoProject] html preview:")
print(visualizer.generate_color_html(sequence, 20))
