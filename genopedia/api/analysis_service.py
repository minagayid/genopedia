"""Run Genopedia core analysis on uploaded or pasted content for the API.

The heavy lifting stays in the offline-first ``genopedia`` core package; this
module only adapts in-memory request content to the file-based readers and
collects the outputs into JSON-safe structures plus an HTML report.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from ..anomalies import SequenceAnomalyDetector
from ..core import SequenceAnalyzer
from ..correction import CorrectionPlanner
from ..io import InputLimits, read_input
from ..reporting import render_html_report
from .config import ANALYSIS_STORE_MAX_BASES

_FORMAT_SUFFIXES={"fasta":".fasta","fastq":".fastq","vcf":".vcf","text":".txt","raw":".txt"}
_AUTO_SUFFIXES={".fasta":"fasta",".fa":"fasta",".fna":"fasta",".fastq":"fastq",".fq":"fastq",".vcf":"vcf",".txt":"text"}


class AnalysisInputError(ValueError):
    """Raised when submitted content cannot be analyzed."""


def detect_format(filename:str,requested:str)->str:
    requested=(requested or "auto").lower()
    if requested!="auto":
        if requested not in _FORMAT_SUFFIXES:raise AnalysisInputError(f"unsupported format: {requested}")
        return requested
    name=(filename or "").lower()
    if name.endswith(".vcf.gz"):return "vcf"
    for suffix,fmt in _AUTO_SUFFIXES.items():
        if name.endswith(suffix):return fmt
    return "text"


def run_analysis(content:bytes,*,filename:str="",requested_format:str="auto",molecule:str="DNA",limits:InputLimits|None=None)->dict:
    """Parse and analyze sequence content; returns summary/report structures."""

    if not content:raise AnalysisInputError("empty input")
    fmt=detect_format(filename,requested_format)
    text=content.decode("utf-8",errors="replace")
    if "�" in text:raise AnalysisInputError("input is not valid UTF-8 text")
    suffix=_FORMAT_SUFFIXES[fmt]
    try:
        with tempfile.NamedTemporaryFile("w",suffix=suffix,delete=False,encoding="utf-8") as handle:
            handle.write(text)
            temp_path=Path(handle.name)
        data=read_input(temp_path,format=fmt,limits=limits) if limits else read_input(temp_path,format=fmt)
    except AnalysisInputError:
        raise
    except Exception as exc:
        raise AnalysisInputError(f"could not parse input as {fmt}: {exc}") from exc
    finally:
        try:temp_path.unlink()
        except Exception:pass
    records=list(data.records);variants=list(data.variants)
    if not records and not variants:raise AnalysisInputError("no sequence records or variants found in input")
    if not variants and sum(len(record.sequence) for record in records)==0:raise AnalysisInputError("no sequence data found in input")
    analyzer=SequenceAnalyzer()
    reports=analyzer.summarize_records(records,molecule=molecule)
    sequence_anomalies=[item for record in records for item in SequenceAnomalyDetector().detect(record,molecule=molecule)]
    correction_plan=CorrectionPlanner().plan(variants)
    summary={
        "records":[report.to_dict() for report in reports],
        "variants":[variant.to_dict() for variant in variants],
        "sequence_anomalies":[item.to_dict() for item in sequence_anomalies],
        "correction_plan":[item.to_dict() for item in correction_plan],
        "safety":"Research use only; evidence requires human review and no automatic sequence edit is performed.",
    }
    report_html=render_html_report(records,variants=variants,quality_reports=reports,sequence_anomalies=sequence_anomalies,correction_suggestions=correction_plan)
    total_bases=sum(len(record.sequence) for record in records)
    stored_records=[]
    budget=ANALYSIS_STORE_MAX_BASES
    for record in records:
        if budget<=0:break
        sequence=record.sequence[:budget];budget-=len(sequence)
        stored_records.append({"identifier":record.identifier,"description":record.description,"source_format":record.source_format,"sequence":sequence,"truncated":len(sequence)<len(record.sequence)})
    return {
        "input_format":fmt,
        "record_count":len(records),
        "variant_count":len(variants),
        "total_bases":total_bases,
        "sequence_sha256":hashlib.sha256(content).hexdigest(),
        "summary_json":json.dumps(summary,sort_keys=True),
        "report_html":report_html,
        "records_json":json.dumps(stored_records),
    }


def compare_sequences(reference:str,sample:str,*,chromosome:str="chr1")->dict:
    analyzer=SequenceAnalyzer()
    variants=analyzer.detect_variants(reference,sample,chromosome=chromosome)
    return {
        "chromosome":chromosome,
        "reference_length":len(reference),
        "sample_length":len(sample),
        "variant_count":len(variants),
        "variants":[variant.to_dict() for variant in variants],
        "safety":"Research use only; positions are zero-based and evidence requires human review.",
    }
