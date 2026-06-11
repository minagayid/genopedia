"""
Genomics Data Pipeline (Genopedia)
==================================
Handles DNA/RNA sequence loading, preprocessing, variant detection,
and color-coded visualization.
"""

import os
import re
import json
import hashlib
import logging
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from collections import Counter
import numpy as np

# Bioinformatics
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from Bio.SeqUtils import GC

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NucleotideConfig:
    """Configuration for nucleotide color coding."""
    A_COLOR = "#FF0000"  # Red
    T_COLOR = "#FFFF00"  # Yellow
    G_COLOR = "#00FF00"  # Green
    C_COLOR = "#0000FF"  # Blue
    U_COLOR = "#8B4513"  # Brown (for RNA)
    N_COLOR = "#808080"  # Gray (unknown)
    
    COLOR_MAP = {
        'A': A_COLOR, 'a': A_COLOR,
        'T': T_COLOR, 't': T_COLOR,
        'G': G_COLOR, 'g': G_COLOR,
        'C': C_COLOR, 'c': C_COLOR,
        'U': U_COLOR, 'u': U_COLOR,
        'N': N_COLOR, 'n': N_COLOR,
    }


@dataclass
class Variant:
    """Represents a genetic variant."""
    chromosome: str
    position: int
    reference: str
    observed: str
    quality: float = 0.0
    variant_type: str = "SNP"  # SNP, Insertion, Deletion
    pathogenicity: str = "unknown"  # benign, likely_benign, uncertain, likely_pathogenic, pathogenic
    
    def to_dict(self):
        return {
            "chromosome": self.chromosome,
            "position": self.position,
            "reference": self.reference,
            "observed": self.observed,
            "quality": self.quality,
            "variant_type": self.variant_type,
            "pathogenicity": self.pathogenicity
        }


@dataclass
class FunctionalRegion:
    """Represents a functional region of a gene."""
    name: str
    start: int
    end: int
    region_type: str  # exon, intron, promoter, enhancer, utr
    

class GenomicsDataLoader:
    """Handles loading and preprocessing of genomic data."""
    
    def __init__(self, data_dir: str = "data/genomics"):
        self.data_dir = data_dir
        self.sequences = {}
        self.variants = []
        self.annotations = {}
        logger.info(f"GenomicsDataLoader initialized with data_dir: {data_dir}")
    
    def load_fasta(self, filepath: str, label: str = None) -> SeqRecord:
        """Load a FASTA file."""
        logger.info(f"Loading FASTA: {filepath}")
        records = list(SeqIO.parse(filepath, "fasta"))
        if label:
            self.sequences[label] = records
        logger.info(f"Loaded {len(records)} records from {filepath}")
        return records
    
    def load_fastq(self, filepath: str) -> List[SeqRecord]:
        """Load FASTQ sequencing reads."""
        logger.info(f"Loading FASTQ: {filepath}")
        records = list(SeqIO.parse(filepath, "fastq"))
        logger.info(f"Loaded {len(records)} reads from {filepath}")
        return records
    
    def load_vcf(self, filepath: str) -> List[Variant]:
        """Load VCF variant file."""
        logger.info(f"Loading VCF: {filepath}")
        variants = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('#') or line.startswith('##'):
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 5:
                    variant = Variant(
                        chromosome=parts[0],
                        position=int(parts[1]),
                        reference=parts[3],
                        observed=parts[4],
                        quality=float(parts[5]) if len(parts) > 5 else 0.0
                    )
                    variants.append(variant)
        logger.info(f"Loaded {len(variants)} variants from {filepath}")
        self.variants.extend(variants)
        return variants
    
    def generate_synthetic_dna(self, length: int = 1000, label: str = "synthetic") -> str:
        """Generate a synthetic DNA sequence for testing."""
        bases = ['A', 'T', 'G', 'C']
        sequence = ''.join(np.random.choice(bases, size=length))
        logger.info(f"Generated synthetic DNA sequence of length {length}")
        return sequence
    
    def generate_synthetic_rna(self, length: int = 1000, label: str = "synthetic_rna") -> str:
        """Generate a synthetic RNA sequence (with Uracil instead of Thymine)."""
        bases = ['A', 'U', 'G', 'C']
        sequence = ''.join(np.random.choice(bases, size=length))
        logger.info(f"Generated synthetic RNA sequence of length {length}")
        return sequence


class SequenceAnalyzer:
    """Analyzes DNA/RNA sequences."""
    
    def __init__(self):
        self.config = NucleotideConfig()
    
    def get_color_map(self, sequence: str) -> List[str]:
        """Get color mapping for a sequence."""
        return [self.config.COLOR_MAP.get(base, self.config.N_COLOR) for base in sequence]
    
    def calculate_gc_content(self, sequence: str) -> float:
        """Calculate GC content of a sequence."""
        return GC(Seq(sequence))
    
    def find_motifs(self, sequence: str, motif: str) -> List[int]:
        """Find all occurrences of a motif in a sequence."""
        positions = []
        for i in range(len(sequence) - len(motif) + 1):
            if sequence[i:i+len(motif)] == motif:
                positions.append(i)
        return positions
    
    def identify_functional_regions(self, sequence: str) -> List[FunctionalRegion]:
        """Identify potential functional regions in a sequence."""
        regions = []
        
        # Look for promoter regions (TATA box)
        tata_positions = self.find_motifs(sequence, "TATA")
        for pos in tata_positions:
            regions.append(FunctionalRegion(
                name=f"Promoter_{pos}",
                start=max(0, pos - 25),
                end=min(len(sequence), pos + 25),
                region_type="promoter"
            ))
        
        # Look for start codon (ATG)
        start_positions = self.find_motifs(sequence, "ATG")
        for pos in start_positions:
            regions.append(FunctionalRegion(
                name=f"Start_Codon_{pos}",
                start=pos,
                end=pos + 3,
                region_type="exon"
            ))
        
        return regions
    
    def detect_variants(self, reference: str, sample: str, chromosome: str = "chr1") -> List[Variant]:
        """Detect variants between reference and sample sequences."""
        variants = []
        min_len = min(len(reference), len(sample))
        
        for i in range(min_len):
            if reference[i] != sample[i]:
                variants.append(Variant(
                    chromosome=chromosome,
                    position=i,
                    reference=reference[i],
                    observed=sample[i],
                    variant_type="SNP"
                ))
        
        # Check for insertions/deletions at the end
        if len(sample) > len(reference):
            variants.append(Variant(
                chromosome=chromosome,
                position=min_len,
                reference="-",
                observed=sample[min_len:],
                variant_type="Insertion"
            ))
        elif len(reference) > len(sample):
            variants.append(Variant(
                chromosome=chromosome,
                position=min_len,
                reference=reference[min_len:],
                observed="-",
                variant_type="Deletion"
            ))
        
        return variants
    
    def classify_pathogenicity(self, variant: Variant) -> str:
        """Classify variant pathogenicity (simplified)."""
        # This is a simplified classification
        # In practice, this would use databases like ClinVar
        if variant.observed in ['A', 'G', 'C', 'T'] and variant.reference in ['A', 'G', 'C', 'T']:
            # Simple heuristic: transitions (A<->G, C<->T) are often less pathogenic
            transitions = {('A', 'G'), ('G', 'A'), ('C', 'T'), ('T', 'C')}
            if (variant.reference, variant.observed) in transitions:
                return "likely_benign"
            else:
                return "uncertain"
        return "unknown"


class GenomicsVisualizer:
    """Creates color-coded visualizations of genomic data."""
    
    def __init__(self):
        self.config = NucleotideConfig()
    
    def generate_color_html(self, sequence: str, max_length: int = 100) -> str:
        """Generate HTML representation of a sequence with color-coded nucleotides."""
        html = '<div style="font-family: monospace; line-height: 1.5; word-wrap: break-word;">'
        
        for i, base in enumerate(sequence[:max_length]):
            color = self.config.COLOR_MAP.get(base, self.config.N_COLOR)
            html += f'<span style="color: {color}; font-weight: bold;">{base}</span>'
            if (i + 1) % 10 == 0:
                html += ' '
            if (i + 1) % 60 == 0:
                html += '<br>'
        
        html += '</div>'
        return html
    
    def generate_svg_sequence(self, sequence: str, width: int = 800, height: int = 100) -> str:
        """Generate SVG visualization of a sequence."""
        svg = f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">\n'
        
        base_width = width / min(len(sequence), 100)
        
        for i, base in enumerate(sequence[:100]):
            color = self.config.COLOR_MAP.get(base, self.config.N_COLOR)
            x = i * base_width
            svg += f'  <rect x="{x}" y="0" width="{base_width}" height="{height}" '
            svg += f'fill="{color}" stroke="white" stroke-width="0.5"/>\n'
        
        svg += '</svg>'
        return svg