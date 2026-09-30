import unittest
from genopedia.evidence import EvidenceDocument, retrieve, retrieval_metrics


class EvidenceTests(unittest.TestCase):
    def test_ranking_preserves_source_and_content_hash(self):
        a = EvidenceDocument("a", "https://example.org/a", "fixture-v1", "protein annotation evidence", "synthetic")
        b = EvidenceDocument("b", "https://example.org/b", "fixture-v1", "neuroimaging atlas", "synthetic")
        result = retrieve("protein annotation", [b, a])
        self.assertEqual([r["source_id"] for r in result], ["a"])
        self.assertEqual(result[0]["content_sha256"], a.content_sha256)
        self.assertEqual(retrieval_metrics(["b", "a"], {"a"}), {"precision": .5, "recall": 1., "mrr": .5})
        self.assertEqual(retrieve("unknownword", [a, b]), [])

    def test_invalid_provenance_and_duplicate_sources_are_rejected(self):
        with self.assertRaises(ValueError):
            EvidenceDocument("a", "", "1", "text", "unknown")
        a = EvidenceDocument("a", "https://example.org", "1", "protein", "synthetic")
        with self.assertRaises(ValueError):
            retrieve("protein", [a, a])
