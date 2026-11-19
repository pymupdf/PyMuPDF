"""Nested rule grids are cell text only under a retained native container."""
import unittest

import pymupdf
from pymupdf import _table_union as union


def entry(box, rows=2, cols=2):
    x0, y0, x1, y1 = box
    grid = [[(x0+(x1-x0)*c/cols, y0+(y1-y0)*r/rows,
              x0+(x1-x0)*(c+1)/cols, y0+(y1-y0)*(r+1)/rows)
             for c in range(cols)] for r in range(rows)]
    return pymupdf.Rect(box), grid


class NestedCandidateTests(unittest.TestCase):
    def setUp(self):
        self.outer = entry((0, 0, 100, 100))
        self.left = entry((5, 5, 40, 40))
        self.right = entry((55, 55, 90, 90))
        self.args = dict(page=None, grid_ref=False, grid_ref_iou=.9,
                         span_mult_gate=False, span_mult_threshold=3)

    def test_single_actual_cell_and_order(self):
        nested = union._union_nested_candidate_indexes
        self.assertEqual(nested([self.outer, self.left, self.right]), {1, 2})
        self.assertEqual(nested([self.left, self.right, self.outer]), {0, 1})
        self.assertEqual(nested([self.outer, entry((0, 0, 50, 50))]), {1})
        self.assertEqual(nested([self.outer, self.left, entry((10, 10, 20, 20))]), {1, 2})

    def test_bbox_alone_is_not_cell_nesting(self):
        nested = union._union_nested_candidate_indexes
        for child in [entry((25, 25, 75, 75)), entry((75, 75, 125, 125)), self.outer]:
            with self.subTest(child=child[0]):
                self.assertFalse(nested([self.outer, child]))
        gap = (pymupdf.Rect(0, 0, 100, 100), [[None, (50, 0, 100, 100)]])
        self.assertFalse(nested([gap, self.left]))
        self.assertFalse(nested([self.left, self.right]))

    def test_only_approved_containers_may_shadow_children(self):
        nested = union._union_nested_candidate_indexes
        candidates = [self.outer, self.left]
        self.assertFalse(nested(candidates, set()))
        self.assertEqual(nested(candidates, {0}), {1})

    def test_retained_outer_is_not_rebuilt(self):
        result = union._union_replace_append([], [self.outer, self.left, self.right], **self.args)
        self.assertEqual(len(result), 1)
        self.assertIs(result[0], self.outer)
        self.assertEqual(len(result[0][1]), 2)

    def test_ambiguous_raw_container_does_not_remove_valid_child(self):
        primary = entry((0, 0, 100, 30))
        low = entry((10, 60, 25, 75))
        result = union._union_replace_append([primary], [self.outer, low], **self.args)
        self.assertEqual(len(result), 2)
        self.assertIs(result[1], low)

    def test_internal_children_do_not_replace_approved_grid_ref(self):
        result = union._union_replace_append([self.outer], [self.outer, self.left, self.right],
                                             **dict(self.args, grid_ref=True))
        self.assertEqual(len(result), 1)
        self.assertIs(result[0][1], self.outer[1])
        self.assertEqual(result[0][0], self.outer[0])

    def test_layout_overmerge_does_not_make_independent_panels_nested(self):
        result = union._union_replace_append([self.outer], [self.left, self.right], **self.args)
        self.assertEqual(result, [self.left, self.right])
        self.assertEqual(union._union_replace_append([], [self.left, self.right], **self.args),
                         [self.left, self.right])


if __name__ == '__main__':
    unittest.main()
