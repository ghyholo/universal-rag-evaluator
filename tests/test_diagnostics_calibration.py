import unittest

from rageval_lab.calibration import calibrate_binary
from rageval_lab.diagnostics import diagnose_conditions


class DiagnosticsCalibrationTest(unittest.TestCase):
    def test_diagnose_conditions(self):
        base = [{"query_id": "q1", "score": 0.2}, {"query_id": "q2", "score": 0.8}]
        oracle = [{"query_id": "q1", "score": 1.0}, {"query_id": "q2", "score": 0.5}]
        retrieved = [{"query_id": "q1", "score": 0.3}, {"query_id": "q2", "score": 0.4}]
        summary, rows = diagnose_conditions(base, oracle, retrieved, "score", 0.8)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["diagnosis"], "retrieval_or_context_failure")
        self.assertEqual(rows[1]["diagnosis"], "generator_or_task_failure")
        self.assertEqual(summary["n"], 2)

    def test_calibration(self):
        result = calibrate_binary([
            {"human_label": True, "judge_label": True},
            {"human_label": False, "judge_label": False},
            {"human_label": True, "judge_label": False},
        ])
        self.assertAlmostEqual(result["accuracy"], 2 / 3)
        self.assertGreaterEqual(result["cohen_kappa"], -1)
        self.assertLessEqual(result["cohen_kappa"], 1)


if __name__ == "__main__":
    unittest.main()
