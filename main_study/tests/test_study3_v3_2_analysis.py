from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))

from study3_v3_2_analysis import (  # noqa: E402
    holm_adjust,
    paired_differences,
    sign_flip_pvalue,
    target_condition_means,
)


class Study3V32AnalysisTests(unittest.TestCase):
    def test_target_is_independent_unit(self):
        rows = [
            {"target_id": "a", "condition": "H", "terminal_success": 1, "technical_failure": False},
            {"target_id": "a", "condition": "H", "terminal_success": 0, "technical_failure": False},
            {"target_id": "a", "condition": "R", "terminal_success": 0, "technical_failure": False},
            {"target_id": "a", "condition": "R", "terminal_success": 0, "technical_failure": False},
        ]
        means = target_condition_means(rows)
        targets, differences = paired_differences(means, "H", "R")
        self.assertEqual(targets, ["a"])
        self.assertEqual(differences.tolist(), [0.5])

    def test_technical_failure_is_missing_not_failure(self):
        rows = [
            {"target_id": "a", "condition": "H", "terminal_success": 0, "technical_failure": True},
            {"target_id": "a", "condition": "H", "terminal_success": 1, "technical_failure": False},
        ]
        self.assertEqual(target_condition_means(rows)["a"]["H"], 1.0)

    def test_zero_difference_sign_flip_is_one(self):
        self.assertEqual(sign_flip_pvalue([0.0, 0.0], resamples=100), 1.0)

    def test_holm_is_monotone_in_ordered_pvalues(self):
        adjusted = holm_adjust({"a": 0.01, "b": 0.03, "c": 0.5})
        self.assertLessEqual(adjusted["a"], adjusted["b"])
        self.assertLessEqual(adjusted["b"], adjusted["c"])


if __name__ == "__main__":
    unittest.main()
