# Scientific evidence retrieval

`genopedia.evidence` adds a transparent local lexical baseline. Every document needs a source ID, URL, version, license label and content. Responses carry a SHA256 content hash. Query-token overlap determines ranking; deterministic source-ID ordering resolves ties. No-hit queries return no evidence. `retrieval_metrics` computes precision, recall and reciprocal rank from independent relevance labels.

Reproduce: `python -m pytest tests/test_evidence.py -q`. Current fixtures are synthetic contract checks, not a scientific retrieval quality study. RefSeq release 237 data acquisition, manifests, curated relevance judgments and comparison baselines need licensed/versioned source data. Do not infer scientific correctness from token overlap. No DNA/RNA generation or editing is added.
