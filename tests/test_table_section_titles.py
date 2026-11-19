"""Centered section titles preserve real slots, text ownership and body cells."""
import unittest
from types import SimpleNamespace

import pymupdf
from pymupdf import table
from pymupdf._table_headers import section_label_row_like
from pymupdf._table_refine import _refine_word_in_rect
from pymupdf._table_sections import (
    aligned_blocks, centered_extent, merge_title_row, section_repeat_plan,
    title_row_proof,
)
from pymupdf._table_spans import SpanCell


class SectionTitleTests(unittest.TestCase):
    words = [(42, 5, 68, 15, 'Section')]
    chars = [dict(x0=44, top=5, x1=46, bottom=15, text='S', bold=True)]

    def grid(self):
        row = [SpanCell((0, 0, 40, 20), '', 4, 1, 'th'),
               SpanCell((40, 0, 60, 20), 'Section', 2, 1, 'th'),
               SpanCell((60, 0, 110, 20), '', 5, 1, 'th')]
        row[1].source_marker = object()
        body = [SpanCell((i*10, 20, (i+1)*10, 40), str(i), 1, 1) for i in range(11)]
        return [row, body]

    def members(self, rect):
        return tuple(i for i, word in enumerate(self.words)
                     if _refine_word_in_rect(*word[:4], *tuple(rect)))

    def proof(self, grid, **changes):
        kwargs = dict(words=self.words, word_members=self.members,
                      chars=self.chars, char_members=lambda rect: (0,), paths=[],
                      width=11, section_like=section_label_row_like,
                      Rect=pymupdf.Rect, is_line_like=table._is_line_like, min_length=3)
        kwargs.update(changes)
        return title_row_proof(grid, 0, **kwargs)

    def test_real_colspan_geometry_source_and_body(self):
        grid = self.grid()
        proof, _ = self.proof(grid)
        self.assertIsNotNone(proof)
        merged, event = merge_title_row(grid, [proof], width=11, Rect=pymupdf.Rect,
                                       word_members=self.members)
        self.assertEqual(merged[0][0].colspan, 11)
        self.assertEqual(merged[0][0].bbox, (0, 0, 110, 20))
        self.assertIs(merged[0][0].source_marker, grid[0][1].source_marker)
        self.assertIs(merged[1], grid[1])
        self.assertEqual(grid[0][1].colspan, 2)
        self.assertEqual(event['word_indices'], (0,))

    def test_centered_extent_boundary(self):
        for title, expected in [((42, 68), True), ((45.5, 75.5), True),
                                ((45.6, 75.6), False), ((5, 25), False),
                                ((-1, 50), False), ((0, 110), False)]:
            with self.subTest(title=title):
                self.assertEqual(centered_extent(title, (0, 110)), expected)

    def test_competing_content_and_rowspan_keep_original(self):
        for change in ['other_text', 'rowspan', 'slots', 'unequal_band']:
            with self.subTest(change=change):
                grid = self.grid()
                if change == 'other_text':
                    grid[0][0].text = 'Other'
                elif change == 'rowspan':
                    grid[0][0].rowspan = 2
                elif change == 'slots':
                    grid[0][0].colspan = 3
                else:
                    grid[0][0].bbox = (0, 1, 40, 20)
                self.assertIsNone(self.proof(grid)[0])
        self.assertIsNone(self.proof(self.grid(), chars=[dict(self.chars[0], bold=False)])[0])
        self.assertIsNone(self.proof(self.grid(),
            word_members=lambda r: (0,) if tuple(r) == (40, 0, 60, 20) else (0, 1))[0])

    def test_native_partitions_are_scoped_to_title_band(self):
        def line(x, y0, y1):
            return dict(type='s', items=[('l', pymupdf.Point(x, y0), pymupdf.Point(x, y1))])
        cases = [([line(30, 0, 20)], False),
                 ([line(0, 0, 20), line(110, 0, 20)], True),
                 ([line(30, 20, 40)], True),
                 ([dict(type='f', items=[('re', pymupdf.Rect(29, 0, 31, 20), 1)])], False),
                 ([dict(type='f', items=[('re', pymupdf.Rect(0, 0, 110, 20), 1)])], True),
                 ([dict(type='s', items=[('re', pymupdf.Rect(30, 0, 80, 20), 1)])], False)]
        for paths, expected in cases:
            with self.subTest(paths=paths):
                self.assertEqual(self.proof(self.grid(), paths=paths)[0] is not None, expected)

    def test_changed_source_or_title_does_not_merge(self):
        grid = self.grid()
        proof, _ = self.proof(grid)
        self.assertIsNone(merge_title_row(grid, [proof], width=11, Rect=pymupdf.Rect,
                                         word_members=lambda rect: (1,))[1])
        grid[0][1].text = 'Changed'
        self.assertIsNone(merge_title_row(grid, [proof], width=11, Rect=pymupdf.Rect,
                                         word_members=self.members)[1])

    def test_all_blocks_proven_before_moving_cut(self):
        rows = [['First', ''], ['A', 'B'], ['x', '1'],
                ['Second', ''], ['A', 'B'], ['y', '2']]
        result = aligned_blocks(rows, 2, [[]]*6, repeat_labels=lambda r, d: (4,),
                                prove=lambda index: ({'row': index}, 'ok'))
        self.assertEqual(result[0], (3,))
        self.assertEqual(len(result[1]), 2)
        rejected = aligned_blocks(rows, 2, [[]]*6, repeat_labels=lambda r, d: (4,),
                                  prove=lambda index: (None, 'unproved'))
        self.assertEqual(rejected[0], (4,))
        self.assertFalse(rejected[1])

    def test_missing_cached_material_does_not_extract(self):
        page = SimpleNamespace()
        self.assertEqual(section_repeat_plan(page, self.grid(), [], 1, (4,), [],
            width=11, is_line_like=table._is_line_like, min_length=3), ((4,), ()))

    def test_repeated_labels_require_two_distinct_types(self):
        cut = table._refine_repeated_leading_header_cuts
        for labels, expected in [(['A', 'A', 'A'], ()),
                                 (['A', 'A', 'B'], (2,)),
                                 (['(omitted)', '(omitted)', ''], ()),
                                 (['(Actual)', '(Budget)', ''], (2,))]:
            with self.subTest(labels=labels):
                rows = [labels, ['x', '1', 'y'], labels, ['z', '2', 'w']]
                self.assertEqual(cut(rows, 1), expected)


if __name__ == '__main__':
    unittest.main()
