import unittest

from rageval_lab.metrics import answer_metrics, aggregate, retrieval_metrics


class MetricsTest(unittest.TestCase):
    def test_retrieval_metrics(self):
        result = retrieval_metrics(
            ["d1", "d3"], [{"doc_id": "d2"}, {"doc_id": "d1"}], [1, 2]
        )
        self.assertEqual(result["hit@1"], 0.0)
        self.assertEqual(result["hit@2"], 1.0)
        self.assertAlmostEqual(result["recall@2"], 0.5)
        self.assertAlmostEqual(result["mrr"], 0.5)

    def test_no_gold_documents_use_abstention_metrics(self):
        result = retrieval_metrics([], [{"doc_id": "d2"}], [1, 5])
        self.assertNotIn("recall@1", result)
        self.assertEqual(result["retrieval_overreach"], 1.0)

    def test_temporal_and_distractor_metrics(self):
        result = retrieval_metrics(
            ["d1"],
            [
                {
                    "doc_id": "d1",
                    "temporally_valid": True,
                    "outdated": False,
                    "distractor": False,
                },
                {
                    "doc_id": "d2",
                    "temporally_valid": False,
                    "outdated": True,
                    "distractor": True,
                },
            ],
            [2],
        )
        self.assertEqual(result["temporal_precision@2"], 0.5)
        self.assertEqual(result["outdated_rate@2"], 0.5)
        self.assertEqual(result["distractor_rate@2"], 0.5)

    def test_answer_and_citation_metrics(self):
        gold = {"required_claims": ["A"], "gold_doc_ids": ["d1"], "answerable": True}
        run = {
            "answer": "A",
            "predicted_claims": [{"text": "A", "supported": True, "relevant": True}],
            "citations": [{"claim": "A", "doc_ids": ["d1"], "supported": True}],
        }
        result = answer_metrics(gold, run)
        self.assertEqual(result["answer_claim_f1"], 1.0)
        self.assertEqual(result["citation_f1"], 1.0)
        self.assertEqual(result["faithfulness"], 1.0)

    def test_abstention(self):
        result = answer_metrics(
            {"answerable": False, "required_claims": [], "gold_doc_ids": []},
            {"answer": "", "abstained": True},
        )
        self.assertEqual(result["correct_abstention"], 1.0)
        self.assertEqual(result["unsafe_answer"], 0.0)

    def test_aggregate_latency_percentiles(self):
        result = aggregate([{"latency_ms": 10}, {"latency_ms": 30}])
        self.assertEqual(result["latency_p50_ms"], 20)
        self.assertEqual(result["query_count"], 2)


if __name__ == "__main__":
    unittest.main()
