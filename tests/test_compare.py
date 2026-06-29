import unittest
from argparse import Namespace

from rageval_lab.cli import _metric_comparison
from rageval_lab.stats import bootstrap_ci, holm_adjust, paired_differences, sign_flip_pvalue
from rageval_lab.validate import validate_rows


class CompareAndValidationTest(unittest.TestCase):
    def test_validation_and_statistics(self):
        gold = [{"query_id": "q1", "question": "x", "answerable": True, "gold_doc_ids": ["d1"]}]
        run = [{"query_id": "q1", "answer": "x", "retrieved": [{"doc_id": "d1"}, {"doc_id": "d1"}]}]
        errors = validate_rows(gold, run)
        self.assertTrue(any("duplicate retrieved" in error for error in errors))

        differences = paired_differences([0.1, 0.2], [0.2, 0.4])
        low, high = bootstrap_ci(differences, iterations=200)
        self.assertLessEqual(low, high)
        self.assertGreaterEqual(sign_flip_pvalue(differences), 0.0)
        self.assertEqual(len(holm_adjust([0.01, 0.04, 0.20])), 3)

    def test_metric_specific_pairs(self):
        left = {"q1": {"score": 0.2}, "q2": {"other": 1.0}}
        right = {"q1": {"score": 0.4}, "q2": {"score": 0.9}}
        result = _metric_comparison(
            left,
            right,
            ["q1", "q2"],
            "score",
            Namespace(iterations=100, seed=7),
        )
        self.assertEqual(result["n"], 1)
        self.assertEqual(result["excluded_shared_queries"], 1)


if __name__ == "__main__":
    unittest.main()
