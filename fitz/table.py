"""
Copyright (C) 2023 Artifex Software, Inc.

This file is part of PyMuPDF.

PyMuPDF is free software: you can redistribute it and/or modify it under the
terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option)
any later version.

PyMuPDF is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
details.

You should have received a copy of the GNU Affero General Public License
along with MuPDF. If not, see <https://www.gnu.org/licenses/agpl-3.0.en.html>

Alternative licensing terms are available from the licensor.
For commercial licensing, see <https://www.artifex.com/> or contact
Artifex Software, Inc., 39 Mesa Street, Suite 108A, San Francisco,
CA 94129, USA, for further information.

---------------------------------------------------------------------
Portions of this code have been ported from pdfplumber, see
https://pypi.org/project/pdfplumber/.

The ported code is under the following MIT license:

---------------------------------------------------------------------
The MIT License (MIT)

Copyright (c) 2015, Jeremy Singer-Vine

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
---------------------------------------------------------------------
Also see here: https://github.com/jsvine/pdfplumber/blob/stable/LICENSE.txt
---------------------------------------------------------------------

The porting mainly pertains to files "table.py" and relevant parts of
"utils/text.py" within pdfplumber's repository on Github.
With respect to "text.py", we have removed functions or features that are not
used by table processing. Examples are:

* the text search function
* simple text extraction
* text extraction by lines

Original pdfplumber code does neither detect, nor identify table headers.
This PyMuPDF port adds respective code to the 'Table' class as method '_get_header'.
This is implemented as new class TableHeader with the properties:
* bbox: A tuple for the header's bbox
* cells: A tuple for each bbox of a column header
* names: A list of strings with column header text
* external: A bool indicating whether the header is outside the table cells.

"""
import itertools
import string
from dataclasses import dataclass
from operator import itemgetter

# -------------------------------------------------------------------
# Start of PyMuPDF interface code
# -------------------------------------------------------------------
from . import (
    Rect,
    Matrix,
    TEXTFLAGS_TEXT,
    TOOLS,
    EMPTY_RECT,
    sRGB_to_pdf,
    Point,
)

EDGES = []  # vector graphics from PyMuPDF
CHARS = []  # text characters from PyMuPDF
TEXTPAGE = None  # TextPage of the page for optimized extraction
# -------------------------------------------------------------------
# End of PyMuPDF interface code
# -------------------------------------------------------------------


class UnsetFloat(float):
    pass


NON_NEGATIVE_SETTINGS = [
    "snap_tolerance",
    "snap_x_tolerance",
    "snap_y_tolerance",
    "join_tolerance",
    "join_x_tolerance",
    "join_y_tolerance",
    "edge_min_length",
    "min_words_vertical",
    "min_words_horizontal",
    "intersection_tolerance",
    "intersection_x_tolerance",
    "intersection_y_tolerance",
]


TABLE_STRATEGIES = ["lines", "lines_strict", "text", "explicit"]
UNSET = UnsetFloat(0)
DEFAULT_SNAP_TOLERANCE = 3
DEFAULT_JOIN_TOLERANCE = 3
DEFAULT_MIN_WORDS_VERTICAL = 3
DEFAULT_MIN_WORDS_HORIZONTAL = 1
DEFAULT_X_TOLERANCE = 3
DEFAULT_Y_TOLERANCE = 3
DEFAULT_X_DENSITY = 7.25
DEFAULT_Y_DENSITY = 13
bbox_getter = itemgetter("x0", "top", "x1", "bottom")


LIGATURES = {
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬆ": "st",
    "ﬅ": "st",
}


class TextMap:
    """
    A TextMap maps each unicode character in the text to an individual `char`
    object (or, in the case of layout-implied whitespace, `None`).
    """

    def __init__(self, tuples=None) -> None:
        self.tuples = tuples
        self.as_string = "".join(map(itemgetter(0), tuples))

    def match_to_dict(
        self,
        m,
        main_group: int = 0,
        return_groups: bool = True,
        return_chars: bool = True,
    ) -> dict:
        subset = self.tuples[m.start(main_group) : m.end(main_group)]
        chars = [c for (text, c) in subset if c is not None]
        x0, top, x1, bottom = objects_to_bbox(chars)

        result = {
            "text": m.group(main_group),
            "x0": x0,
            "top": top,
            "x1": x1,
            "bottom": bottom,
        }

        if return_groups:
            result["groups"] = m.groups()

        if return_chars:
            result["chars"] = chars

        return result


class WordMap:
    """
    A WordMap maps words->chars.
    """

    def __init__(self, tuples) -> None:
        self.tuples = tuples

    def to_textmap(
        self,
        layout: bool = False,
        layout_width=0,
        layout_height=0,
        layout_width_chars: int = 0,
        layout_height_chars: int = 0,
        x_density=DEFAULT_X_DENSITY,
        y_density=DEFAULT_Y_DENSITY,
        x_shift=0,
        y_shift=0,
        y_tolerance=DEFAULT_Y_TOLERANCE,
        use_text_flow: bool = False,
        presorted: bool = False,
        expand_ligatures: bool = True,
    ) -> TextMap:
        """
        Given a list of (word, chars) tuples (i.e., a WordMap), return a list of
        (char-text, char) tuples (i.e., a TextMap) that can be used to mimic the
        structural layout of the text on the page(s), using the following approach:

        - Sort the words by (doctop, x0) if not already sorted.

        - Calculate the initial doctop for the starting page.

        - Cluster the words by doctop (taking `y_tolerance` into account), and
          iterate through them.

        - For each cluster, calculate the distance between that doctop and the
          initial doctop, in points, minus `y_shift`. Divide that distance by
          `y_density` to calculate the minimum number of newlines that should come
          before this cluster. Append that number of newlines *minus* the number of
          newlines already appended, with a minimum of one.

        - Then for each cluster, iterate through each word in it. Divide each
          word's x0, minus `x_shift`, by `x_density` to calculate the minimum
          number of characters that should come before this cluster.  Append that
          number of spaces *minus* the number of characters and spaces already
          appended, with a minimum of one. Then append the word's text.

        - At the termination of each line, add more spaces if necessary to
          mimic `layout_width`.

        - Finally, add newlines to the end if necessary to mimic to
          `layout_height`.

        Note: This approach currently works best for horizontal, left-to-right
        text, but will display all words regardless of orientation. There is room
        for improvement in better supporting right-to-left text, as well as
        vertical text.
        """
        _textmap = []

        if not len(self.tuples):
            return TextMap(_textmap)

        expansions = LIGATURES if expand_ligatures else {}

        if layout:
            if layout_width_chars:
                if layout_width:
                    raise ValueError(
                        "`layout_width` and `layout_width_chars` cannot both be set."
                    )
            else:
                layout_width_chars = int(round(layout_width / x_density))

            if layout_height_chars:
                if layout_height:
                    raise ValueError(
                        "`layout_height` and `layout_height_chars` cannot both be set."
                    )
            else:
                layout_height_chars = int(round(layout_height / y_density))

            blank_line = [(" ", None)] * layout_width_chars
        else:
            blank_line = []

        num_newlines = 0

        words_sorted_doctop = (
            self.tuples
            if presorted or use_text_flow
            else sorted(self.tuples, key=lambda x: float(x[0]["doctop"]))
        )

        first_word = words_sorted_doctop[0][0]
        doctop_start = first_word["doctop"] - first_word["top"]

        for i, ws in enumerate(
            cluster_objects(
                words_sorted_doctop, lambda x: float(x[0]["doctop"]), y_tolerance
            )
        ):
            y_dist = (
                (ws[0][0]["doctop"] - (doctop_start + y_shift)) / y_density
                if layout
                else 0
            )
            num_newlines_prepend = max(
                # At least one newline, unless this iis the first line
                int(i > 0),
                # ... or as many as needed to get the imputed "distance" from the top
                round(y_dist) - num_newlines,
            )

            for i in range(num_newlines_prepend):
                if not len(_textmap) or _textmap[-1][0] == "\n":
                    _textmap += blank_line
                _textmap.append(("\n", None))

            num_newlines += num_newlines_prepend

            line_len = 0

            line_words_sorted_x0 = (
                ws
                if presorted or use_text_flow
                else sorted(ws, key=lambda x: float(x[0]["x0"]))
            )

            for word, chars in line_words_sorted_x0:
                x_dist = (word["x0"] - x_shift) / x_density if layout else 0
                num_spaces_prepend = max(min(1, line_len), round(x_dist) - line_len)
                _textmap += [(" ", None)] * num_spaces_prepend
                line_len += num_spaces_prepend

                for c in chars:
                    letters = expansions.get(c["text"], c["text"])
                    for letter in letters:
                        _textmap.append((letter, c))
                        line_len += 1

            # Append spaces at end of line
            if layout:
                _textmap += [(" ", None)] * (layout_width_chars - line_len)

        # Append blank lines at end of text
        if layout:
            num_newlines_append = layout_height_chars - (num_newlines + 1)
            for i in range(num_newlines_append):
                if i > 0:
                    _textmap += blank_line
                _textmap.append(("\n", None))

            # Remove terminal newline
            if _textmap[-1] == ("\n", None):
                _textmap = _textmap[:-1]

        return TextMap(_textmap)


class WordExtractor:
    def __init__(
        self,
        x_tolerance=DEFAULT_X_TOLERANCE,
        y_tolerance=DEFAULT_Y_TOLERANCE,
        keep_blank_chars: bool = False,
        use_text_flow=False,
        horizontal_ltr=True,  # Should words be read left-to-right?
        vertical_ttb=True,  # Should vertical words be read top-to-bottom?
        extra_attrs=None,
        split_at_punctuation=False,
        expand_ligatures=True,
    ):
        self.x_tolerance = x_tolerance
        self.y_tolerance = y_tolerance
        self.keep_blank_chars = keep_blank_chars
        self.use_text_flow = use_text_flow
        self.horizontal_ltr = horizontal_ltr
        self.vertical_ttb = vertical_ttb
        self.extra_attrs = [] if extra_attrs is None else extra_attrs

        # Note: string.punctuation = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
        self.split_at_punctuation = (
            string.punctuation
            if split_at_punctuation is True
            else (split_at_punctuation or "")
        )

        self.expansions = LIGATURES if expand_ligatures else {}

    def merge_chars(self, ordered_chars: list):
        x0, top, x1, bottom = objects_to_bbox(ordered_chars)
        doctop_adj = ordered_chars[0]["doctop"] - ordered_chars[0]["top"]
        upright = ordered_chars[0]["upright"]

        direction = 1 if (self.horizontal_ltr if upright else self.vertical_ttb) else -1

        word = {
            "text": "".join(
                self.expansions.get(c["text"], c["text"]) for c in ordered_chars
            ),
            "x0": x0,
            "x1": x1,
            "top": top,
            "doctop": top + doctop_adj,
            "bottom": bottom,
            "upright": upright,
            "direction": direction,
        }

        for key in self.extra_attrs:
            word[key] = ordered_chars[0][key]

        return word

    def char_begins_new_word(
        self,
        prev_char,
        curr_char,
    ) -> bool:
        """This method takes several factors into account to determine if
        `curr_char` represents the beginning of a new word:

        - Whether the text is "upright" (i.e., non-rotated)
        - Whether the user has specified that horizontal text runs
          left-to-right (default) or right-to-left, as represented by
          self.horizontal_ltr
        - Whether the user has specified that vertical text the text runs
          top-to-bottom (default) or bottom-to-top, as represented by
          self.vertical_ttb
        - The x0, top, x1, and bottom attributes of prev_char and
          curr_char
        - The self.x_tolerance and self.y_tolerance settings. Note: In
          this case, x/y refer to those directions for non-rotated text.
          For vertical text, they are flipped. A more accurate terminology
          might be "*intra*line character distance tolerance" and
          "*inter*line character distance tolerance"

        An important note: The *intra*line distance is measured from the
        *end* of the previous character to the *beginning* of the current
        character, while the *inter*line distance is measured from the
        *top* of the previous character to the *top* of the next
        character. The reasons for this are partly repository-historical,
        and partly logical, as successive text lines' bounding boxes often
        overlap slightly (and we don't want that overlap to be interpreted
        as the two lines being the same line).

        The upright-ness of the character determines the attributes to
        compare, while horizontal_ltr/vertical_ttb determine the direction
        of the comparison.
        """

        # Note: Due to the grouping step earlier in the process,
        # curr_char["upright"] will always equal prev_char["upright"].
        if curr_char["upright"]:
            x = self.x_tolerance
            y = self.y_tolerance
            ay = prev_char["top"]
            cy = curr_char["top"]
            if self.horizontal_ltr:
                ax = prev_char["x0"]
                bx = prev_char["x1"]
                cx = curr_char["x0"]
            else:
                ax = -prev_char["x1"]
                bx = -prev_char["x0"]
                cx = -curr_char["x1"]

        else:
            x = self.y_tolerance
            y = self.x_tolerance
            ay = prev_char["x0"]
            cy = curr_char["x0"]
            if self.vertical_ttb:
                ax = prev_char["top"]
                bx = prev_char["bottom"]
                cx = curr_char["top"]
            else:
                ax = -prev_char["bottom"]
                bx = -prev_char["top"]
                cx = -curr_char["bottom"]

        return bool(
            # Intraline test
            (cx < ax)
            or (cx > bx + x)
            # Interline test
            or (cy > ay + y)
        )

    def iter_chars_to_words(self, ordered_chars):
        current_word: list = []

        def start_next_word(new_char=None):
            nonlocal current_word

            if current_word:
                yield current_word

            current_word = [] if new_char is None else [new_char]

        for char in ordered_chars:
            text = char["text"]

            if not self.keep_blank_chars and text.isspace():
                yield from start_next_word(None)

            elif text in self.split_at_punctuation:
                yield from start_next_word(char)
                yield from start_next_word(None)

            elif current_word and self.char_begins_new_word(current_word[-1], char):
                yield from start_next_word(char)

            else:
                current_word.append(char)

        # Finally, after all chars processed
        if current_word:
            yield current_word

    def iter_sort_chars(self, chars):
        def upright_key(x) -> int:
            return -int(x["upright"])

        for upright_cluster in cluster_objects(list(chars), upright_key, 0):
            upright = upright_cluster[0]["upright"]
            cluster_key = "doctop" if upright else "x0"

            # Cluster by line
            subclusters = cluster_objects(
                upright_cluster, itemgetter(cluster_key), self.y_tolerance
            )

            for sc in subclusters:
                # Sort within line
                sort_key = "x0" if upright else "doctop"
                to_yield = sorted(sc, key=itemgetter(sort_key))

                # Reverse order if necessary
                if not (self.horizontal_ltr if upright else self.vertical_ttb):
                    yield from reversed(to_yield)
                else:
                    yield from to_yield

    def iter_extract_tuples(self, chars):
        ordered_chars = chars if self.use_text_flow else self.iter_sort_chars(chars)

        grouping_key = itemgetter("upright", *self.extra_attrs)
        grouped_chars = itertools.groupby(ordered_chars, grouping_key)

        for keyvals, char_group in grouped_chars:
            for word_chars in self.iter_chars_to_words(char_group):
                yield (self.merge_chars(word_chars), word_chars)

    def extract_wordmap(self, chars) -> WordMap:
        return WordMap(list(self.iter_extract_tuples(chars)))

    def extract_words(self, chars: list) -> list:
        return list(word for word, word_chars in self.iter_extract_tuples(chars))


def extract_words(chars: list, **kwargs) -> list:
    return WordExtractor(**kwargs).extract_words(chars)


def line_to_edge(line):
    edge = dict(line)
    edge["orientation"] = "h" if (line["top"] == line["bottom"]) else "v"
    return edge


def rect_to_edges(rect) -> list:
    top, bottom, left, right = [dict(rect) for x in range(4)]
    top.update(
        {
            "object_type": "rect_edge",
            "height": 0,
            "y0": rect["y1"],
            "bottom": rect["top"],
            "orientation": "h",
        }
    )
    bottom.update(
        {
            "object_type": "rect_edge",
            "height": 0,
            "y1": rect["y0"],
            "top": rect["top"] + rect["height"],
            "doctop": rect["doctop"] + rect["height"],
            "orientation": "h",
        }
    )
    left.update(
        {
            "object_type": "rect_edge",
            "width": 0,
            "x1": rect["x0"],
            "orientation": "v",
        }
    )
    right.update(
        {
            "object_type": "rect_edge",
            "width": 0,
            "x0": rect["x1"],
            "orientation": "v",
        }
    )
    return [top, bottom, left, right]


def curve_to_edges(curve) -> list:
    point_pairs = zip(curve["pts"], curve["pts"][1:])
    return [
        {
            "object_type": "curve_edge",
            "x0": min(p0[0], p1[0]),
            "x1": max(p0[0], p1[0]),
            "top": min(p0[1], p1[1]),
            "doctop": min(p0[1], p1[1]) + (curve["doctop"] - curve["top"]),
            "bottom": max(p0[1], p1[1]),
            "width": abs(p0[0] - p1[0]),
            "height": abs(p0[1] - p1[1]),
            "orientation": "v" if p0[0] == p1[0] else ("h" if p0[1] == p1[1] else None),
        }
        for p0, p1 in point_pairs
    ]


def obj_to_edges(obj) -> list:
    t = obj["object_type"]
    if "_edge" in t:
        return [obj]
    elif t == "line":
        return [line_to_edge(obj)]
    else:
        return {"rect": rect_to_edges, "curve": curve_to_edges}[t](obj)


def filter_edges(
    edges,
    orientation=None,
    edge_type=None,
    min_length=1,
) -> list:
    if orientation not in ("v", "h", None):
        raise ValueError("Orientation must be 'v' or 'h'")

    def test(e) -> bool:
        dim = "height" if e["orientation"] == "v" else "width"
        et_correct = e["object_type"] == edge_type if edge_type is not None else True
        orient_correct = orientation is None or e["orientation"] == orientation
        return bool(et_correct and orient_correct and (e[dim] >= min_length))

    return list(filter(test, edges))


def cluster_list(xs, tolerance=0) -> list:
    if tolerance == 0:
        return [[x] for x in sorted(xs)]
    if len(xs) < 2:
        return [[x] for x in sorted(xs)]
    groups = []
    xs = list(sorted(xs))
    current_group = [xs[0]]
    last = xs[0]
    for x in xs[1:]:
        if x <= (last + tolerance):
            current_group.append(x)
        else:
            groups.append(current_group)
            current_group = [x]
        last = x
    groups.append(current_group)
    return groups


def make_cluster_dict(values, tolerance) -> dict:
    clusters = cluster_list(list(set(values)), tolerance)

    nested_tuples = [
        [(val, i) for val in value_cluster] for i, value_cluster in enumerate(clusters)
    ]

    return dict(itertools.chain(*nested_tuples))


def cluster_objects(xs, key_fn, tolerance) -> list:
    if not callable(key_fn):
        key_fn = itemgetter(key_fn)

    values = map(key_fn, xs)
    cluster_dict = make_cluster_dict(values, tolerance)

    get_0, get_1 = itemgetter(0), itemgetter(1)

    cluster_tuples = sorted(((x, cluster_dict.get(key_fn(x))) for x in xs), key=get_1)

    grouped = itertools.groupby(cluster_tuples, key=get_1)

    return [list(map(get_0, v)) for k, v in grouped]


def move_object(obj, axis: str, value):
    assert axis in ("h", "v")
    if axis == "h":
        new_items = [
            ("x0", obj["x0"] + value),
            ("x1", obj["x1"] + value),
        ]
    if axis == "v":
        new_items = [
            ("top", obj["top"] + value),
            ("bottom", obj["bottom"] + value),
        ]
        if "doctop" in obj:
            new_items += [("doctop", obj["doctop"] + value)]
        if "y0" in obj:
            new_items += [
                ("y0", obj["y0"] - value),
                ("y1", obj["y1"] - value),
            ]
    return obj.__class__(tuple(obj.items()) + tuple(new_items))


def snap_objects(objs, attr: str, tolerance) -> list:
    axis = {"x0": "h", "x1": "h", "top": "v", "bottom": "v"}[attr]
    list_objs = list(objs)
    clusters = cluster_objects(list_objs, itemgetter(attr), tolerance)
    avgs = [sum(map(itemgetter(attr), cluster)) / len(cluster) for cluster in clusters]
    snapped_clusters = [
        [move_object(obj, axis, avg - obj[attr]) for obj in cluster]
        for cluster, avg in zip(clusters, avgs)
    ]
    return list(itertools.chain(*snapped_clusters))


def snap_edges(
    edges,
    x_tolerance=DEFAULT_SNAP_TOLERANCE,
    y_tolerance=DEFAULT_SNAP_TOLERANCE,
):
    """
    Given a list of edges, snap any within `tolerance` pixels of one another
    to their positional average.
    """
    by_orientation = {"v": [], "h": []}
    for e in edges:
        by_orientation[e["orientation"]].append(e)

    snapped_v = snap_objects(by_orientation["v"], "x0", x_tolerance)
    snapped_h = snap_objects(by_orientation["h"], "top", y_tolerance)
    return snapped_v + snapped_h


def resize_object(obj, key: str, value):
    assert key in ("x0", "x1", "top", "bottom")
    old_value = obj[key]
    diff = value - old_value
    new_items = [
        (key, value),
    ]
    if key == "x0":
        assert value <= obj["x1"]
        new_items.append(("width", obj["x1"] - value))
    elif key == "x1":
        assert value >= obj["x0"]
        new_items.append(("width", value - obj["x0"]))
    elif key == "top":
        assert value <= obj["bottom"]
        new_items.append(("doctop", obj["doctop"] + diff))
        new_items.append(("height", obj["height"] - diff))
        if "y1" in obj:
            new_items.append(("y1", obj["y1"] - diff))
    elif key == "bottom":
        assert value >= obj["top"]
        new_items.append(("height", obj["height"] + diff))
        if "y0" in obj:
            new_items.append(("y0", obj["y0"] - diff))
    return obj.__class__(tuple(obj.items()) + tuple(new_items))


def join_edge_group(edges, orientation: str, tolerance=DEFAULT_JOIN_TOLERANCE):
    """
    Given a list of edges along the same infinite line, join those that
    are within `tolerance` pixels of one another.
    """
    if orientation == "h":
        min_prop, max_prop = "x0", "x1"
    elif orientation == "v":
        min_prop, max_prop = "top", "bottom"
    else:
        raise ValueError("Orientation must be 'v' or 'h'")

    sorted_edges = list(sorted(edges, key=itemgetter(min_prop)))
    joined = [sorted_edges[0]]
    for e in sorted_edges[1:]:
        last = joined[-1]
        if e[min_prop] <= (last[max_prop] + tolerance):
            if e[max_prop] > last[max_prop]:
                # Extend current edge to new extremity
                joined[-1] = resize_object(last, max_prop, e[max_prop])
        else:
            # Edge is separate from previous edges
            joined.append(e)

    return joined


def merge_edges(
    edges,
    snap_x_tolerance,
    snap_y_tolerance,
    join_x_tolerance,
    join_y_tolerance,
):
    """
    Using the `snap_edges` and `join_edge_group` methods above,
    merge a list of edges into a more "seamless" list.
    """

    def get_group(edge):
        if edge["orientation"] == "h":
            return ("h", edge["top"])
        else:
            return ("v", edge["x0"])

    if snap_x_tolerance > 0 or snap_y_tolerance > 0:
        edges = snap_edges(edges, snap_x_tolerance, snap_y_tolerance)

    _sorted = sorted(edges, key=get_group)
    edge_groups = itertools.groupby(_sorted, key=get_group)
    edge_gen = (
        join_edge_group(
            items, k[0], (join_x_tolerance if k[0] == "h" else join_y_tolerance)
        )
        for k, items in edge_groups
    )
    edges = list(itertools.chain(*edge_gen))
    return edges


def bbox_to_rect(bbox) -> dict:
    """
    Return the rectangle (i.e a dict with keys "x0", "top", "x1",
    "bottom") for an object.
    """
    return {"x0": bbox[0], "top": bbox[1], "x1": bbox[2], "bottom": bbox[3]}


def objects_to_rect(objects) -> dict:
    """
    Given an iterable of objects, return the smallest rectangle (i.e. a
    dict with "x0", "top", "x1", and "bottom" keys) that contains them
    all.
    """
    return bbox_to_rect(objects_to_bbox(objects))


def merge_bboxes(bboxes):
    """
    Given an iterable of bounding boxes, return the smallest bounding box
    that contains them all.
    """
    x0, top, x1, bottom = zip(*bboxes)
    return (min(x0), min(top), max(x1), max(bottom))


def objects_to_bbox(objects):
    """
    Given an iterable of objects, return the smallest bounding box that
    contains them all.
    """
    return merge_bboxes(map(bbox_getter, objects))


def words_to_edges_h(words, word_threshold: int = DEFAULT_MIN_WORDS_HORIZONTAL):
    """
    Find (imaginary) horizontal lines that connect the tops
    of at least `word_threshold` words.
    """
    by_top = cluster_objects(words, itemgetter("top"), 1)
    large_clusters = filter(lambda x: len(x) >= word_threshold, by_top)
    rects = list(map(objects_to_rect, large_clusters))
    if len(rects) == 0:
        return []
    min_x0 = min(map(itemgetter("x0"), rects))
    max_x1 = max(map(itemgetter("x1"), rects))

    edges = []
    for r in rects:
        edges += [
            # Top of text
            {
                "x0": min_x0,
                "x1": max_x1,
                "top": r["top"],
                "bottom": r["top"],
                "width": max_x1 - min_x0,
                "orientation": "h",
            },
            # For each detected row, we also add the 'bottom' line.  This will
            # generate extra edges, (some will be redundant with the next row
            # 'top' line), but this catches the last row of every table.
            {
                "x0": min_x0,
                "x1": max_x1,
                "top": r["bottom"],
                "bottom": r["bottom"],
                "width": max_x1 - min_x0,
                "orientation": "h",
            },
        ]

    return edges


def get_bbox_overlap(a, b):
    a_left, a_top, a_right, a_bottom = a
    b_left, b_top, b_right, b_bottom = b
    o_left = max(a_left, b_left)
    o_right = min(a_right, b_right)
    o_bottom = min(a_bottom, b_bottom)
    o_top = max(a_top, b_top)
    o_width = o_right - o_left
    o_height = o_bottom - o_top
    if o_height >= 0 and o_width >= 0 and o_height + o_width > 0:
        return (o_left, o_top, o_right, o_bottom)
    else:
        return None


def words_to_edges_v(words, word_threshold: int = DEFAULT_MIN_WORDS_VERTICAL):
    """
    Find (imaginary) vertical lines that connect the left, right, or
    center of at least `word_threshold` words.
    """
    # Find words that share the same left, right, or centerpoints
    by_x0 = cluster_objects(words, itemgetter("x0"), 1)
    by_x1 = cluster_objects(words, itemgetter("x1"), 1)

    def get_center(word):
        return float(word["x0"] + word["x1"]) / 2

    by_center = cluster_objects(words, get_center, 1)
    clusters = by_x0 + by_x1 + by_center

    # Find the points that align with the most words
    sorted_clusters = sorted(clusters, key=lambda x: -len(x))
    large_clusters = filter(lambda x: len(x) >= word_threshold, sorted_clusters)

    # For each of those points, find the bboxes fitting all matching words
    bboxes = list(map(objects_to_bbox, large_clusters))

    # Iterate through those bboxes, condensing overlapping bboxes
    condensed_bboxes = []
    for bbox in bboxes:
        overlap = any(get_bbox_overlap(bbox, c) for c in condensed_bboxes)
        if not overlap:
            condensed_bboxes.append(bbox)

    if len(condensed_bboxes) == 0:
        return []

    condensed_rects = map(bbox_to_rect, condensed_bboxes)
    sorted_rects = list(sorted(condensed_rects, key=itemgetter("x0")))

    max_x1 = max(map(itemgetter("x1"), sorted_rects))
    min_top = min(map(itemgetter("top"), sorted_rects))
    max_bottom = max(map(itemgetter("bottom"), sorted_rects))

    return [
        {
            "x0": b["x0"],
            "x1": b["x0"],
            "top": min_top,
            "bottom": max_bottom,
            "height": max_bottom - min_top,
            "orientation": "v",
        }
        for b in sorted_rects
    ] + [
        {
            "x0": max_x1,
            "x1": max_x1,
            "top": min_top,
            "bottom": max_bottom,
            "height": max_bottom - min_top,
            "orientation": "v",
        }
    ]


def edges_to_intersections(edges, x_tolerance=1, y_tolerance=1) -> dict:
    """
    Given a list of edges, return the points at which they intersect
    within `tolerance` pixels.
    """
    intersections = {}
    v_edges, h_edges = [
        list(filter(lambda x: x["orientation"] == o, edges)) for o in ("v", "h")
    ]
    for v in sorted(v_edges, key=itemgetter("x0", "top")):
        for h in sorted(h_edges, key=itemgetter("top", "x0")):
            if (
                (v["top"] <= (h["top"] + y_tolerance))
                and (v["bottom"] >= (h["top"] - y_tolerance))
                and (v["x0"] >= (h["x0"] - x_tolerance))
                and (v["x0"] <= (h["x1"] + x_tolerance))
            ):
                vertex = (v["x0"], h["top"])
                if vertex not in intersections:
                    intersections[vertex] = {"v": [], "h": []}
                intersections[vertex]["v"].append(v)
                intersections[vertex]["h"].append(h)
    return intersections


def obj_to_bbox(obj):
    """
    Return the bounding box for an object.
    """
    return bbox_getter(obj)


def intersections_to_cells(intersections):
    """
    Given a list of points (`intersections`), return all rectangular "cells"
    that those points describe.

    `intersections` should be a dictionary with (x0, top) tuples as keys,
    and a list of edge objects as values. The edge objects should correspond
    to the edges that touch the intersection.
    """

    def edge_connects(p1, p2) -> bool:
        def edges_to_set(edges):
            return set(map(obj_to_bbox, edges))

        if p1[0] == p2[0]:
            common = edges_to_set(intersections[p1]["v"]).intersection(
                edges_to_set(intersections[p2]["v"])
            )
            if len(common):
                return True

        if p1[1] == p2[1]:
            common = edges_to_set(intersections[p1]["h"]).intersection(
                edges_to_set(intersections[p2]["h"])
            )
            if len(common):
                return True
        return False

    points = list(sorted(intersections.keys()))
    n_points = len(points)

    def find_smallest_cell(points, i: int):
        if i == n_points - 1:
            return None
        pt = points[i]
        rest = points[i + 1 :]
        # Get all the points directly below and directly right
        below = [x for x in rest if x[0] == pt[0]]
        right = [x for x in rest if x[1] == pt[1]]
        for below_pt in below:
            if not edge_connects(pt, below_pt):
                continue

            for right_pt in right:
                if not edge_connects(pt, right_pt):
                    continue

                bottom_right = (right_pt[0], below_pt[1])

                if (
                    (bottom_right in intersections)
                    and edge_connects(bottom_right, right_pt)
                    and edge_connects(bottom_right, below_pt)
                ):
                    return (pt[0], pt[1], bottom_right[0], bottom_right[1])
        return None

    cell_gen = (find_smallest_cell(points, i) for i in range(len(points)))
    return list(filter(None, cell_gen))


def cells_to_tables(cells) -> list:
    """
    Given a list of bounding boxes (`cells`), return a list of tables that
    hold those cells most simply (and contiguously).
    """

    def bbox_to_corners(bbox) -> tuple:
        x0, top, x1, bottom = bbox
        return ((x0, top), (x0, bottom), (x1, top), (x1, bottom))

    remaining_cells = list(cells)

    # Iterate through the cells found above, and assign them
    # to contiguous tables

    current_corners = set()
    current_cells = []

    tables = []
    while len(remaining_cells):
        initial_cell_count = len(current_cells)
        for cell in list(remaining_cells):
            cell_corners = bbox_to_corners(cell)
            # If we're just starting a table ...
            if len(current_cells) == 0:
                # ... immediately assign it to the empty group
                current_corners |= set(cell_corners)
                current_cells.append(cell)
                remaining_cells.remove(cell)
            else:
                # How many corners does this table share with the current group?
                corner_count = sum(c in current_corners for c in cell_corners)

                # If touching on at least one corner...
                if corner_count > 0:
                    # ... assign it to the current group
                    current_corners |= set(cell_corners)
                    current_cells.append(cell)
                    remaining_cells.remove(cell)

        # If this iteration did not find any more cells to append...
        if len(current_cells) == initial_cell_count:
            # ... start a new cell group
            tables.append(list(current_cells))
            current_corners.clear()
            current_cells.clear()

    # Once we have exhausting the list of cells ...

    # ... and we have a cell group that has not been stored
    if len(current_cells):
        # ... store it.
        tables.append(list(current_cells))

    # Sort the tables top-to-bottom-left-to-right based on the value of the
    # topmost-and-then-leftmost coordinate of a table.
    _sorted = sorted(tables, key=lambda t: min((c[1], c[0]) for c in t))
    filtered = [t for t in _sorted if len(t) > 1]
    return filtered


class CellGroup(object):
    def __init__(self, cells):
        self.cells = cells
        self.bbox = (
            min(map(itemgetter(0), filter(None, cells))),
            min(map(itemgetter(1), filter(None, cells))),
            max(map(itemgetter(2), filter(None, cells))),
            max(map(itemgetter(3), filter(None, cells))),
        )


class TableRow(CellGroup):
    pass


class TableHeader(object):
    """PyMuPDF extension containing the identified table header."""

    def __init__(self, bbox, cells, names, above):
        self.bbox = bbox
        self.cells = cells
        self.names = names
        self.external = above


class Table(object):
    def __init__(self, page, cells):
        self.page = page
        self.cells = cells
        self.header = self._get_header()  # PyMuPDF extension

    @property
    def bbox(self):
        """Original replaced by PyMuPDF"""
        rect = EMPTY_RECT()
        for c in self.cells:
            rect |= c
        return tuple(rect)

    @property
    def rows(self) -> list:
        """Assign table cells to row cells observing page rotation"""
        rot = self.page.rotation
        if rot == 0:
            # sort by y, then by x
            i1, i2, f1, f2 = 1, 0, 1, 1
        elif rot == 90:
            # sort by x, then by y (desc)
            i1, i2, f1, f2 = 0, 1, -1, 1
        elif rot == 270:
            # sort by x (desc), then by y (asc)
            i1, i2, f1, f2 = 0, 1, 1, -1
        elif rot == 180:
            # sort by y (desc), then by x (desc)
            i1, i2, f1, f2 = 1, 0, -1, -1

        xs = sorted(list(set([c[i1] for c in self.cells])), key=lambda x: f2 * x)
        rows = []
        for x in xs:
            row = TableRow(
                sorted([c for c in self.cells if c[i1] == x], key=lambda c: f1 * c[i2])
            )
            rows.append(row)
        return rows

    @property
    def row_count(self) -> int:  # PyMuPDF extension
        return len(self.rows)

    @property
    def col_count(self) -> int:  # PyMuPDF extension
        return max([len(r.cells) for r in self.rows])

    def extract(self) -> list:
        """Extract the cell text for the comple table.

        Complete replacement by PyMuPDF text extraction.
        """
        global TEXTPAGE

        def get_text(cell):
            """Accept char bbox areas with a cell overlap of at least 50%."""
            cell = Rect(cell)  # we need a Rect object
            text = ""  # result text
            for block in TEXTPAGE.extractRAWDICT()["blocks"]:
                if Rect(block["bbox"]).intersect(cell).is_empty:
                    continue
                for line in block["lines"]:
                    if Rect(line["bbox"]).intersect(cell).is_empty:
                        continue
                    for span in line["spans"]:
                        chars = span["chars"]
                        if text and chars:
                            text += "\n"  # new span appended after linebreak
                        for char in chars:
                            bbox = Rect(char["bbox"])
                            if abs(bbox & cell) < 0.5 * abs(bbox):
                                continue
                            text += char["c"]

            # no final line break, no wrapping spaces
            return text.rstrip("\n").strip()

        table_arr = []  # final result

        for row in self.rows:
            arr = []  # text in this row
            for cell in row.cells:
                if cell is None:
                    cell_text = None
                else:
                    cell_text = get_text(cell)
                arr.append(cell_text)
            table_arr.append(arr)

        return table_arr

    def to_pandas(self):
        """Return a pandas DataFrame version of the table.

        This is original PyMuPDF code.
        """
        try:
            import pandas as pd
        except ModuleNotFoundError:
            print("Package 'pandas' is not installed")
            raise

        pd_dict = {}
        extract = self.extract()
        hdr = self.header
        names = self.header.names
        hdr_len = len(names)
        # ensure uniqueness of column names
        for i in range(hdr_len):
            name = names[i]
            if not name:
                names[i] = f"Col{i}"
        if hdr_len != len(set(names)):
            for i in range(hdr_len):
                name = names[i]
                if name != f"Col{i}":
                    names[i] = f"{i}-{name}"

        if not hdr.external:  # header is part of 'extract'
            extract = extract[1:]

        for i in range(hdr_len):
            key = names[i]
            value = []
            for j in range(len(extract)):
                value.append(extract[j][i])
            pd_dict[key] = value

        return pd.DataFrame(pd_dict)

    def _get_header(self, y_tolerance=3):
        """Identify the table header.

        *** PyMuPDF extension. ***

        Starting from the first line above the table upwards, check if it
        qualifies to be part of the table header.

        Criteria include:
        * A one-line table never has an extra header.
        * Column borders must not intersect any word. If this happens, all
          text of this line and above of it is ignored.
        * No excess inter-line distance: If a line further up has a distance
          of more than 1.5 times of its font size, it will be ignored and
          all lines above of it.
        * Must have same text properties.
        * Starting with the top table line, a bold text property cannot change
          back to non-bold.

        If not all criteria are met (or there is no text above the table),
        the first table row is assumed to be the header.
        """
        page = self.page
        y_delta = y_tolerance

        def top_row_is_bold(bbox):
            """Check if row 0 has bold text anywhere.

            If this is true, then any non-bold text in lines above disqualify
            these lines as header.

            bbox is the (potentially repaired) row 0 bbox.

            Returns True or False
            """
            for b in page.get_text("dict", flags=TEXTFLAGS_TEXT, clip=bbox)["blocks"]:
                for l in b["lines"]:
                    for s in l["spans"]:
                        if s["flags"] & 16:
                            return True
            return False

        def recover_top_row_cells(table):
            """Recreates top row cells if 'None' columns are present.

            We need all column x-coordinates even when the top table row
            contains None cells.
            """
            bbox = Rect(table.rows[0].bbox)  # top row bbox
            tbbox = Rect(table.bbox)  # table bbox
            y0, y1 = bbox.y0, bbox.y1  # top row upper / lower coordinates

            # make sure row0 bbox has the full table width
            bbox.x0 = tbbox.x0
            bbox.x1 = tbbox.x1

            l_r = set()  # (x0, x1) pairs for all table cells
            for cell in table.cells:
                if cell is None:  # skip non-existing cells
                    continue
                cellbb = Rect(cell)

                # only accept cells wider than a character
                if 10 < cellbb.width < tbbox.width:
                    l_r.add((cell[0], cell[2]))

            # sort (x0, x1) pairs by x0-values
            l_r = sorted(list(l_r), key=lambda c: c[0])

            # recovered row 0 cells
            cells = [(l_r[0][0], y0, l_r[0][1], y1)]

            for x0, x1 in l_r[1:]:
                if x0 >= cells[-1][2]:
                    cells.append((x0, y0, x1, y1))
            return cells, bbox

        # we depend on small glyph heights!
        old_small = TOOLS.set_small_glyph_heights()
        TOOLS.set_small_glyph_heights(True)
        try:
            row = self.rows[0]
            cells = row.cells
            bbox = Rect(row.bbox)
        except IndexError:  # this table has no rows
            return None

        if None in cells:  # if row 0 has empty cells, repair it
            cells, bbox = recover_top_row_cells(self)

        # return this if we determine that the top row is the header
        header_top_row = TableHeader(bbox, cells, self.extract()[0], False)

        # one-line tables have no extra header
        if len(self.rows) < 2:
            return header_top_row

        # x-ccordinates of columns between x0 and x1 of the table
        if len(cells) < 2:
            return header_top_row

        col_x = [c[2] for c in cells[:-1]]  # column (x) coordinates

        # Special check: is top row bold?
        # If first line above table is not bold, but top-left table cell is bold,
        # we take first table row as header
        top_row_bold = top_row_is_bold(bbox)

        # clip = area above table
        # We will inspect this area for text qualifying as column header.
        clip = +bbox  # take row 0 bbox
        clip.y0 = 0  # start at top of page
        clip.y1 = bbox.y0  # end at top of table

        spans = []  # the text spans inside clip
        for b in page.get_text("dict", clip=clip, flags=TEXTFLAGS_TEXT)["blocks"]:
            for l in b["lines"]:
                for s in l["spans"]:
                    if (
                        not s["flags"] & 1 and s["text"].strip()
                    ):  # ignore superscripts and empty text
                        spans.append(s)

        select = []  # y1 coordinates above, sorted descending
        line_heights = []  # line heights above, sorted descending
        line_bolds = []  # bold indicator per line above, same sorting

        # spans sorted descending
        spans.sort(key=lambda s: s["bbox"][3], reverse=True)
        # walk through the spans and fill above 3 lists
        for i in range(len(spans)):
            s = spans[i]
            y1 = s["bbox"][3]  # span bottom
            h = y1 - s["bbox"][1]  # span bbox height
            bold = s["flags"] & 16

            # use first item to start the lists
            if i == 0:
                select.append(y1)
                line_heights.append(h)
                line_bolds.append(bold)
                continue

            # get last items from the 3 lists
            y0 = select[-1]
            h0 = line_heights[-1]
            bold0 = line_bolds[-1]

            if bold0 and not bold:
                break  # stop if switching from bold to non-bold

            # if fitting in height of previous span, modify bbox
            if y0 - y1 <= y_delta or abs((y0 - h0) - s["bbox"][1]) <= y_delta:
                s["bbox"] = (s["bbox"][0], y0 - h0, s["bbox"][2], y0)
                spans[i] = s
                if bold:
                    line_bolds[-1] = bold
                continue
            elif y0 - y1 > 1.5 * h0:
                break  # stop if distance to previous line too large
            select.append(y1)
            line_heights.append(h)
            line_bolds.append(bold)

        if select == []:  # nothing above the table?
            return header_top_row

        select = select[:5]  # only accept up to 5 lines in any header

        # take top row as header if text above table is too far apart
        if bbox.y0 - select[0] >= line_heights[0]:
            return header_top_row

        # if top table row is bold, but line above is not:
        if top_row_bold and not line_bolds[0]:
            return header_top_row

        if spans == []:  # nothing left above the table, return top row
            return header_top_row

        # re-compute clip above table
        nclip = EMPTY_RECT()
        for s in [s for s in spans if s["bbox"][3] >= select[-1]]:
            nclip |= s["bbox"]
        if not nclip.is_empty:
            clip = nclip

        clip.y1 = bbox.y0  # make sure we still include every word above

        # Confirm that no word in clip is intersecting a column separator
        word_rects = [Rect(w[:4]) for w in page.get_text("words", clip=clip)]
        word_tops = sorted(list(set([r[1] for r in word_rects])), reverse=True)

        select = []

        # exclude lines with words that intersect a column border
        for top in word_tops:
            intersecting = [
                (x, r)
                for x in col_x
                for r in word_rects
                if r[1] == top and r[0] < x and r[2] > x
            ]
            if intersecting == []:
                select.append(top)
            else:  # detected a word crossing a column border
                break

        if select == []:  # nothing left over: return first row
            return header_top_row

        hdr_bbox = +clip  # compute the header cells
        hdr_bbox.y0 = select[-1]  # hdr_bbox top is smallest top coord of words
        hdr_cells = [(c[0], hdr_bbox.y0, c[2], hdr_bbox.y1) for c in cells]

        # adjust left/right of header bbox
        hdr_bbox.x0 = hdr_cells[0][0]
        hdr_bbox.x1 = hdr_cells[-1][2]

        # column names: no line breaks, no excess spaces
        hdr_names = [
            page.get_textbox(c).replace("\n", " ").replace("  ", " ").strip()
            for c in hdr_cells
        ]
        TOOLS.set_small_glyph_heights(old_small)
        return TableHeader(tuple(hdr_bbox), hdr_cells, hdr_names, True)


@dataclass
class TableSettings:
    vertical_strategy: str = "lines"
    horizontal_strategy: str = "lines"
    explicit_vertical_lines: list = None
    explicit_horizontal_lines: list = None
    snap_tolerance: float = DEFAULT_SNAP_TOLERANCE
    snap_x_tolerance: float = UNSET
    snap_y_tolerance: float = UNSET
    join_tolerance: float = DEFAULT_JOIN_TOLERANCE
    join_x_tolerance: float = UNSET
    join_y_tolerance: float = UNSET
    edge_min_length: float = 3
    min_words_vertical: float = DEFAULT_MIN_WORDS_VERTICAL
    min_words_horizontal: float = DEFAULT_MIN_WORDS_HORIZONTAL
    intersection_tolerance: float = 3
    intersection_x_tolerance: float = UNSET
    intersection_y_tolerance: float = UNSET
    text_settings: dict = None

    def __post_init__(self) -> "TableSettings":
        """Clean up user-provided table settings.

        Validates that the table settings provided consists of acceptable values and
        returns a cleaned up version. The cleaned up version fills out the missing
        values with the default values in the provided settings.

        TODO: Can be further used to validate that the values are of the correct
            type. For example, raising a value error when a non-boolean input is
            provided for the key ``keep_blank_chars``.

        :param table_settings: User-provided table settings.
        :returns: A cleaned up version of the user-provided table settings.
        :raises ValueError: When an unrecognised key is provided.
        """

        for setting in NON_NEGATIVE_SETTINGS:
            if (getattr(self, setting) or 0) < 0:
                raise ValueError(f"Table setting '{setting}' cannot be negative")

        for orientation in ["horizontal", "vertical"]:
            strategy = getattr(self, orientation + "_strategy")
            if strategy not in TABLE_STRATEGIES:
                raise ValueError(
                    f"{orientation}_strategy must be one of"
                    f'{{{",".join(TABLE_STRATEGIES)}}}'
                )

        if self.text_settings is None:
            self.text_settings = {}

        # This next section is for backwards compatibility
        for attr in ["x_tolerance", "y_tolerance"]:
            if attr not in self.text_settings:
                self.text_settings[attr] = self.text_settings.get("tolerance", 3)

        if "tolerance" in self.text_settings:
            del self.text_settings["tolerance"]
        # End of that section

        for attr, fallback in [
            ("snap_x_tolerance", "snap_tolerance"),
            ("snap_y_tolerance", "snap_tolerance"),
            ("join_x_tolerance", "join_tolerance"),
            ("join_y_tolerance", "join_tolerance"),
            ("intersection_x_tolerance", "intersection_tolerance"),
            ("intersection_y_tolerance", "intersection_tolerance"),
        ]:
            if getattr(self, attr) is UNSET:
                setattr(self, attr, getattr(self, fallback))

        return self

    @classmethod
    def resolve(cls, settings=None):
        if settings is None:
            return cls()
        elif isinstance(settings, cls):
            return settings
        elif isinstance(settings, dict):
            core_settings = {}
            text_settings = {}
            for k, v in settings.items():
                if k[:5] == "text_":
                    text_settings[k[5:]] = v
                else:
                    core_settings[k] = v
            core_settings["text_settings"] = text_settings
            return cls(**core_settings)
        else:
            raise ValueError(f"Cannot resolve settings: {settings}")


class TableFinder(object):
    """
    Given a PDF page, find plausible table structures.

    Largely borrowed from Anssi Nurminen's master's thesis:
    http://dspace.cc.tut.fi/dpub/bitstream/handle/123456789/21520/Nurminen.pdf?sequence=3

    ... and inspired by Tabula:
    https://github.com/tabulapdf/tabula-extractor/issues/16
    """

    def __init__(self, page, settings=None):
        self.page = page
        self.settings = TableSettings.resolve(settings)
        self.edges = self.get_edges()
        self.intersections = edges_to_intersections(
            self.edges,
            self.settings.intersection_x_tolerance,
            self.settings.intersection_y_tolerance,
        )
        self.cells = intersections_to_cells(self.intersections)
        self.tables = [
            Table(self.page, cell_group) for cell_group in cells_to_tables(self.cells)
        ]

    def get_edges(self) -> list:
        settings = self.settings

        for orientation in ["vertical", "horizontal"]:
            strategy = getattr(settings, orientation + "_strategy")
            if strategy == "explicit":
                lines = getattr(settings, "explicit_" + orientation + "_lines")
                if len(lines) < 2:
                    raise ValueError(
                        f"If {orientation}_strategy == 'explicit', "
                        f"explicit_{orientation}_lines "
                        f"must be specified as a list/tuple of two or more "
                        f"floats/ints."
                    )

        v_strat = settings.vertical_strategy
        h_strat = settings.horizontal_strategy

        if v_strat == "text" or h_strat == "text":
            words = extract_words(CHARS, **(settings.text_settings or {}))

        v_explicit = []
        for desc in settings.explicit_vertical_lines or []:
            if isinstance(desc, dict):
                for e in obj_to_edges(desc):
                    if e["orientation"] == "v":
                        v_explicit.append(e)
            else:
                v_explicit.append(
                    {
                        "x0": desc,
                        "x1": desc,
                        "top": self.page.rect[1],
                        "bottom": self.page.rect[3],
                        "height": self.page.rect[3] - self.page.rect[1],
                        "orientation": "v",
                    }
                )

        if v_strat == "lines":
            v_base = filter_edges(EDGES, "v")
        elif v_strat == "lines_strict":
            v_base = filter_edges(EDGES, "v", edge_type="line")
        elif v_strat == "text":
            v_base = words_to_edges_v(words, word_threshold=settings.min_words_vertical)
        elif v_strat == "explicit":
            v_base = []

        v = v_base + v_explicit

        h_explicit = []
        for desc in settings.explicit_horizontal_lines or []:
            if isinstance(desc, dict):
                for e in obj_to_edges(desc):
                    if e["orientation"] == "h":
                        h_explicit.append(e)
            else:
                h_explicit.append(
                    {
                        "x0": self.page.rect[0],
                        "x1": self.page.rect[2],
                        "width": self.page.rect[2] - self.page.rect[0],
                        "top": desc,
                        "bottom": desc,
                        "orientation": "h",
                    }
                )

        if h_strat == "lines":
            h_base = filter_edges(EDGES, "h")
        elif h_strat == "lines_strict":
            h_base = filter_edges(EDGES, "h", edge_type="line")
        elif h_strat == "text":
            h_base = words_to_edges_h(
                words, word_threshold=settings.min_words_horizontal
            )
        elif h_strat == "explicit":
            h_base = []

        h = h_base + h_explicit

        edges = list(v) + list(h)

        edges = merge_edges(
            edges,
            snap_x_tolerance=settings.snap_x_tolerance,
            snap_y_tolerance=settings.snap_y_tolerance,
            join_x_tolerance=settings.join_x_tolerance,
            join_y_tolerance=settings.join_y_tolerance,
        )

        return filter_edges(edges, min_length=settings.edge_min_length)

    def __getitem__(self, i):
        tcount = len(self.tables)
        if i >= tcount:
            raise IndexError("table not on page")
        while i < 0:
            i += tcount
        return self.tables[i]


"""
Start of PyMuPDF interface code.
The following functions are executed when "page.find_tables()" is called.

* make_chars: Fills the CHARS list with text character information extracted
              via "rawdict" text extraction. Items in CHARS are formatted
              as expected by the table code.
* make_edges: Fills the EDGES list with vector graphic information extracted
              via "get_drawings". Items in EDGES are formatted as expected
              by the table code.

The lists CHARS and EDGES are used to replace respective document access
of pdfplumber or, respectively pdfminer.
The table code has been modified to use these lists instead of accessing
page information themselves.
"""


# -----------------------------------------------------------------------------
# Extract all page characters to fill the CHARS list
# -----------------------------------------------------------------------------
def make_chars(page, clip=None):
    """Extract text as "rawdict" to fill CHARS."""
    global CHARS, TEXTPAGE
    old_small = TOOLS.set_small_glyph_heights()
    TOOLS.set_small_glyph_heights(True)
    page_number = page.number + 1
    page_height = page.rect.height
    ctm = page.transformation_matrix
    TEXTPAGE = page.get_textpage(clip, flags=TEXTFLAGS_TEXT)
    blocks = TEXTPAGE.extractRAWDICT()["blocks"]
    doctop_base = page_height * page.number
    for block in blocks:
        for line in block["lines"]:
            ldir = line["dir"]  # = (cosine, sine) of angle
            matrix = Matrix(ldir[0], -ldir[1], ldir[1], ldir[0], 0, 0)
            if ldir[1] == 0:
                upright = True
            else:
                upright = False
            for span in sorted(line["spans"], key=lambda s: s["bbox"][0]):
                fontname = span["font"]
                fontsize = span["size"]
                color = sRGB_to_pdf(span["color"])
                for char in sorted(span["chars"], key=lambda c: c["bbox"][0]):
                    bbox = Rect(char["bbox"])
                    bbox_ctm = bbox * ctm
                    origin = Point(char["origin"]) * ctm
                    matrix.e = origin.x
                    matrix.f = origin.y
                    text = char["c"]
                    char_dict = {
                        "adv": bbox.x1 - bbox.x0 if upright else bbox.y1 - bbox.y0,
                        "bottom": bbox.y1,
                        "doctop": bbox.y0 + doctop_base,
                        "fontname": fontname,
                        "height": bbox.y1 - bbox.y0,
                        "matrix": tuple(matrix),
                        "ncs": "DeviceRGB",
                        "non_stroking_color": color,
                        "non_stroking_pattern": None,
                        "object_type": "char",
                        "page_number": page_number,
                        "size": fontsize if upright else bbox.y1 - bbox.y0,
                        "stroking_color": color,
                        "stroking_pattern": None,
                        "text": text,
                        "top": bbox.y0,
                        "upright": upright,
                        "width": bbox.x1 - bbox.x0,
                        "x0": bbox.x0,
                        "x1": bbox.x1,
                        "y0": bbox_ctm.y0,
                        "y1": bbox_ctm.y1,
                    }
                    CHARS.append(char_dict)

    TOOLS.set_small_glyph_heights(old_small)


# -----------------------------------------------------------------------------
# Extract all page vector graphics to fill the EDGES list.
# We are ignoring Bézier curves completely and are converting everything
# else to lines.
# -----------------------------------------------------------------------------
def make_edges(page, clip=None, tset=None):
    global EDGES
    paths = page.get_drawings()
    page_height = page.rect.height
    doctop_basis = page.number * page_height
    page_number = page.number + 1
    x_tolerance = tset.snap_x_tolerance
    y_tolerance = tset.snap_y_tolerance
    prect = page.rect
    if page.rotation in (90, 270):
        w, h = prect.br
        prect = Rect(0, 0, h, w)
    if clip is not None:
        clip = Rect(clip)
    else:
        clip = prect

    def is_parallel(p1, p2):
        """Check if line is roughly axis-parallel."""
        if abs(p1.x - p2.x) <= x_tolerance or abs(p1.y - p2.y) <= y_tolerance:
            return True
        return False

    def make_line(p, p1, p2, clip):
        """Given 2 points, make a line dictionary for table detection."""
        if not is_parallel(p1, p2):  # only accepting axis-parallel lines
            return {}
        # compute the extremal values
        x0 = min(p1.x, p2.x)
        x1 = max(p1.x, p2.x)
        y0 = min(p1.y, p2.y)
        y1 = max(p1.y, p2.y)

        # check for outside clip
        if x0 > clip.x1 or x1 < clip.x0 or y0 > clip.y1 or y1 < clip.y0:
            return {}

        if x0 < clip.x0:
            x0 = clip.x0  # adjust to clip boundary

        if x1 > clip.x1:
            x1 = clip.x1  # adjust to clip boundary

        if y0 < clip.y0:
            y0 = clip.y0  # adjust to clip boundary

        if y1 > clip.y1:
            y1 = clip.y1  # adjust to clip boundary

        width = x1 - x0  # from adjusted values
        height = y1 - y0  # from adjusted values
        if width == height == 0:
            return {}  # nothing left to deal with
        line_dict = {
            "x0": x0,
            "y0": page_height - y0,
            "x1": x1,
            "y1": page_height - y1,
            "width": width,
            "height": height,
            "pts": [(x0, y0), (x1, y1)],
            "linewidth": p["width"],
            "stroke": True,
            "fill": False,
            "evenodd": False,
            "stroking_color": p["color"] if p["color"] else p["fill"],
            "non_stroking_color": None,
            "object_type": "line",
            "page_number": page_number,
            "stroking_pattern": None,
            "non_stroking_pattern": None,
            "top": y0,
            "bottom": y1,
            "doctop": y0 + doctop_basis,
        }
        return line_dict

    for p in paths:
        items = p["items"]  # items in this path

        # if 'closePath', add a line from last to first point
        if p["closePath"] and items[0][0] == "l" and items[-1][0] == "l":
            items.append(("l", items[-1][2], items[0][1]))

        for i in items:
            if i[0] not in ("l", "re", "qu"):
                continue  # ignore anything else

            if i[0] == "l":  # a line
                p1, p2 = i[1:]
                line_dict = make_line(p, p1, p2, clip)
                if line_dict:
                    EDGES.append(line_to_edge(line_dict))

            elif i[0] == "re":  # a rectangle: decompose into 4 lines
                rect = i[1]  # rectangle itself
                # ignore minute rectangles
                if rect.height <= y_tolerance and rect.width <= x_tolerance:
                    continue

                if rect.width <= x_tolerance:  # simulates a vertical line
                    x = abs(rect.x1 + rect.x0) / 2  # take middle value for x
                    p1 = Point(x, rect.y0)
                    p2 = Point(x, rect.y1)
                    line_dict = make_line(p, p1, p2, clip)
                    if line_dict:
                        EDGES.append(line_to_edge(line_dict))
                    continue

                if rect.height <= y_tolerance:  # simulates a horizontal line
                    y = abs(rect.y1 + rect.y0) / 2  # take middle value for y
                    p1 = Point(rect.x0, y)
                    p2 = Point(rect.x1, y)
                    line_dict = make_line(p, p1, p2, clip)
                    if line_dict:
                        EDGES.append(line_to_edge(line_dict))
                    continue

                line_dict = make_line(p, rect.tl, rect.bl, clip)
                if line_dict:
                    EDGES.append(line_to_edge(line_dict))

                line_dict = make_line(p, rect.bl, rect.br, clip)
                if line_dict:
                    EDGES.append(line_to_edge(line_dict))

                line_dict = make_line(p, rect.br, rect.tr, clip)
                if line_dict:
                    EDGES.append(line_to_edge(line_dict))

                line_dict = make_line(p, rect.tr, rect.tl, clip)
                if line_dict:
                    EDGES.append(line_to_edge(line_dict))

            else:  # must be a quad
                # we convert it into (up to) 4 lines
                ul, ur, ll, lr = i[1]

                line_dict = make_line(p, ul, ll, clip)
                if line_dict:
                    EDGES.append(line_to_edge(line_dict))

                line_dict = make_line(p, ll, lr, clip)
                if line_dict:
                    EDGES.append(line_to_edge(line_dict))

                line_dict = make_line(p, lr, ur, clip)
                if line_dict:
                    EDGES.append(line_to_edge(line_dict))

                line_dict = make_line(p, ur, ul, clip)
                if line_dict:
                    EDGES.append(line_to_edge(line_dict))


def find_tables(
    page,
    clip=None,
    vertical_strategy: str = "lines",
    horizontal_strategy: str = "lines",
    vertical_lines: list = None,
    horizontal_lines: list = None,
    snap_tolerance: float = DEFAULT_SNAP_TOLERANCE,
    snap_x_tolerance: float = None,
    snap_y_tolerance: float = None,
    join_tolerance: float = DEFAULT_JOIN_TOLERANCE,
    join_x_tolerance: float = None,
    join_y_tolerance: float = None,
    edge_min_length: float = 3,
    min_words_vertical: float = DEFAULT_MIN_WORDS_VERTICAL,
    min_words_horizontal: float = DEFAULT_MIN_WORDS_HORIZONTAL,
    intersection_tolerance: float = 3,
    intersection_x_tolerance: float = None,
    intersection_y_tolerance: float = None,
    text_tolerance=3,
    text_x_tolerance=3,
    text_y_tolerance=3,
):
    global CHARS, EDGES
    CHARS = []
    EDGES = []
    if snap_x_tolerance is None:
        snap_x_tolerance = UNSET
    if snap_y_tolerance is None:
        snap_y_tolerance = UNSET
    if join_x_tolerance is None:
        join_x_tolerance = UNSET
    if join_y_tolerance is None:
        join_y_tolerance = UNSET
    if intersection_x_tolerance is None:
        intersection_x_tolerance = UNSET
    if intersection_y_tolerance is None:
        intersection_y_tolerance = UNSET
    settings = {
        "vertical_strategy": vertical_strategy,
        "horizontal_strategy": horizontal_strategy,
        "explicit_vertical_lines": vertical_lines,
        "explicit_horizontal_lines": horizontal_lines,
        "snap_tolerance": snap_tolerance,
        "snap_x_tolerance": snap_x_tolerance,
        "snap_y_tolerance": snap_y_tolerance,
        "join_tolerance": join_tolerance,
        "join_x_tolerance": join_x_tolerance,
        "join_y_tolerance": join_y_tolerance,
        "edge_min_length": edge_min_length,
        "min_words_vertical": min_words_vertical,
        "min_words_horizontal": min_words_horizontal,
        "intersection_tolerance": intersection_tolerance,
        "intersection_x_tolerance": intersection_x_tolerance,
        "intersection_y_tolerance": intersection_y_tolerance,
        "text_tolerance": text_tolerance,
        "text_x_tolerance": text_x_tolerance,
        "text_y_tolerance": text_y_tolerance,
    }
    tset = TableSettings.resolve(settings=settings)
    page.table_settings = tset
    make_chars(page, clip=clip)  # create character list of page
    make_edges(page, clip=clip, tset=tset)  # create lines and curves
    tables = TableFinder(page, settings=tset)
    return tables
