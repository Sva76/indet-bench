import unittest

from indetbench import PairScore, auroc, compare_to_reference, w_score


def row(pair, block, side, score):
    return PairScore(pair, block, side, score)


class MetricsTests(unittest.TestCase):
    def test_w_tie_half_and_equal_block_weights(self):
        data = [row('a', 'story-1', 'B', 0), row('a', 'story-1', 'C', 1),
                row('b', 'story-1', 'B', 2), row('b', 'story-1', 'C', 2),
                row('c', 'story-2', 'B', 4), row('c', 'story-2', 'C', 3)]
        result = w_score(data, n_bootstrap=0)
        self.assertAlmostEqual(result.value, 0.375)
        self.assertEqual((result.n_pairs, result.n_blocks), (3, 2))
        self.assertIsNone(result.ci_lower)

    def test_paired_comparison_restricts_to_common_pairs(self):
        method = [row('a', 'one', 'B', 0), row('a', 'one', 'C', 1),
                  row('b', 'two', 'B', 0), row('b', 'two', 'C', 1)]
        ref = [row('a', 'one', 'B', 0), row('a', 'one', 'C', 0),
               row('c', 'three', 'B', 0), row('c', 'three', 'C', 1)]
        result = compare_to_reference(method, ref, n_bootstrap=0)
        self.assertAlmostEqual(result.method.value, 1)
        self.assertAlmostEqual(result.reference.value, 0.5)
        self.assertAlmostEqual(result.delta_w.value, 0.5)
        self.assertEqual(result.delta_w.n_pairs, 1)

    def test_reject_duplicate_or_incomplete_pair(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            w_score([row('a', 'one', 'B', 0), row('a', 'one', 'B', 2)], n_bootstrap=0)
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            w_score([row('a', 'one', 'B', 0)], n_bootstrap=0)

    def test_reject_mismatched_blocks(self):
        method = [row('a', 'one', 'B', 0), row('a', 'one', 'C', 1)]
        reference = [row('a', 'other', 'B', 0), row('a', 'other', 'C', 1)]
        with self.assertRaisesRegex(ValueError, 'Mismatched blocks'):
            compare_to_reference(method, reference, n_bootstrap=0)

    def test_bootstrap_determinism(self):
        rows = [row(str(i), str(i), 'B', 0) for i in range(10)] + [
            row(str(i), str(i), 'C', i % 3 - 1) for i in range(10)
        ]
        self.assertEqual(w_score(rows, n_bootstrap=500), w_score(rows, n_bootstrap=500))

    def test_auroc_ties_and_perfect(self):
        self.assertEqual(auroc([0, 1], [0.2, 0.8]), 1.0)
        self.assertEqual(auroc([0, 1], [0.7, 0.7]), 0.5)
        self.assertEqual(auroc([0, 1], [0.8, 0.2]), 0.0)


if __name__ == '__main__':
    unittest.main()
