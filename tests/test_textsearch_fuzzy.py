"""Edit-distance search and the original text/geometry returned to callers."""
import itertools
import os
import random

import pymupdf
import pytest

from pymupdf._textsearch import _candidates, _levenshtein, _normalize


@pytest.fixture
def page():
    with pymupdf.open() as doc:
        yield doc.new_page()


@pytest.fixture(params=[False, True])
def skip_quad_corrections(request):
    previous = pymupdf.TOOLS.unset_quad_corrections()
    pymupdf.TOOLS.unset_quad_corrections(request.param)
    try:
        yield
    finally:
        pymupdf.TOOLS.unset_quad_corrections(previous)


def _distance(left, right):
    # Deliberately use a full matrix, independently of the substring matcher.
    matrix = [[0] * (len(right) + 1) for _ in range(len(left) + 1)]
    for i in range(len(left) + 1):
        matrix[i][0] = i
    for j in range(len(right) + 1):
        matrix[0][j] = j
    for i, a in enumerate(left, 1):
        for j, b in enumerate(right, 1):
            matrix[i][j] = min(matrix[i - 1][j] + 1, matrix[i][j - 1] + 1,
                               matrix[i - 1][j - 1] + (a != b))
    return matrix[-1][-1]


def test_candidates_against_exhaustive_substrings():
    strings = ["".join(chars) for n in range(5)
               for chars in itertools.product("ab", repeat=n)]
    rng = random.Random(137)
    cases = list(itertools.product(strings, strings[1:15]))
    cases += [("".join(rng.choices("ab cß가", k=16)),
               "".join(rng.choices("ab cß가", k=6))) for _ in range(100)]
    for _ in range(10):
        needle = "".join(rng.choices("abcdefghijklmnopqrstuvwxyz", k=12))
        cases.append(("xx" + needle[:5] + "#" + needle[6:] + "yy", needle))
    for text, needle in cases:
        for limit in range(min(len(needle), 3)):
            expected = []
            for end in range(1, len(text) + 1):
                cost, start = min((_distance(text[start:end], needle), start)
                                  for start in range(end))
                if cost <= limit:
                    expected.append((cost, start, end))
            assert list(_candidates(text, needle, limit)) == expected


def test_candidate_windows_preserve_full_scan_results():
    rng = random.Random(148)
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    for case in range(200):
        needle = "".join(rng.choices(alphabet, k=24))
        changed = list(needle)
        limit = case % 4 + 1
        for _ in range(limit):
            index = rng.randrange(len(changed))
            edit = rng.randrange(3)
            if edit == 0:
                changed.insert(index, "#")
            elif edit == 1:
                del changed[index]
            else:
                changed[index] = "#"
        text = "".join(rng.choices(alphabet, k=40)) + "".join(changed)
        text += "".join(rng.choices(alphabet, k=40)) + needle
        # Some seed-window edges can fall inside expanded Unicode characters.
        boundaries = [True] + [rng.randrange(5) != 0 for _ in text[:-1]] + [True]
        assert list(_candidates(text, needle, limit, boundaries)) == list(
            _levenshtein(text, needle, limit, boundaries))


@pytest.mark.parametrize("text,normalized,offsets", [
    (" A \t B ", " a b ", [(0, 1), (1, 2), (2, 5), (5, 6), (6, 7)]),
    ("a-\nb", "ab", [(0, 1), (3, 4)]),
    ("a-\n\nb", "a- b", [(0, 1), (1, 2), (2, 4), (4, 5)]),
    ("ßﬂ İ", "ssfl i\u0307", [(0, 1)] * 2 + [(1, 2)] * 2 + [(2, 3)] + [(3, 4)] * 2),
    ("\u00a0A\u2002", " a ", [(0, 1), (1, 2), (2, 3)]),
])
def test_normalized_character_ranges(text, normalized, offsets):
    assert _normalize(text) == (normalized, offsets)


@pytest.mark.parametrize("needle,fragments", [("target", ["tar", "get"]),
                                              ("tar", ["tar"]), ("get", ["get"])])
def test_match_across_span_boundaries(page, needle, fragments, skip_quad_corrections):
    page.insert_text((30, 60), "prefix tar", fontsize=12)
    x = 30 + pymupdf.get_text_length("prefix tar", fontsize=12)
    page.insert_text((x, 60), "get suffix", fontname="hebo", fontsize=12)
    hits = page.search_for_fuzzy(needle, max_edits=0)
    assert len(hits) == 1
    assert hits[0]["text"] == needle
    assert len(hits[0]["quads"]) == len(fragments)
    for quad, fragment in zip(hits[0]["quads"], fragments):
        expected = page.search_for(fragment, quads=True)[0]
        assert max(abs(a - b) for a, b in zip(quad, expected)) < 0.001


@pytest.mark.parametrize("needle,text,distance", [
    ("revenue increasd today", "revenue increased today", 1),  # deletion in query; codespell:ignore increasd
    ("revenue increassed today", "revenue increased today", 1),  # insertion
    ("revenue increazed today", "revenue increased today", 1),  # substitution
    ("revenue incerased today", "revenue increased today", 2),  # transposition; codespell:ignore incerased
    ("the return was -5% today", "the return was 5% today", 1),
    ("the rate was 1.2 today", "the rate was 12 today", 1),
    ("the fund is not safe", "the fund is now safe", 1),
])
def test_edits(page, needle, text, distance):
    page.insert_text((30, 60), text)
    hits = page.search_for_fuzzy(needle, max_edits=distance)
    assert len(hits) == 1
    assert hits[0]["text"] == text
    assert hits[0]["distance"] == distance
    assert len(hits[0]["quads"]) == 1
    assert _distance(_normalize(text)[0], _normalize(needle)[0]) == distance


def test_repeated_and_exact_and_fuzzy(page):
    page.insert_text((30, 60), "cot | cat | cot | catcat")
    hits = page.search_for_fuzzy("cat", max_edits=1)
    assert [h["text"] for h in hits] == ["cot", "cat", "cot", "cat", "cat"]
    assert [h["distance"] for h in hits] == [1, 0, 1, 0, 0]
    assert page.search_for_fuzzy("unrelated", max_edits=2) == []


def test_overlapping_occurrences(page):
    page.insert_text((30, 60), "bananana")
    hits = page.search_for_fuzzy("ana", max_edits=0)
    assert [h["text"] for h in hits] == ["ana", "ana"]
    assert hits[0]["quads"][0].rect.x1 <= hits[1]["quads"][0].rect.x0


def test_equal_distance_prefers_closest_length(page):
    page.insert_text((30, 60), "revenue increased")
    hits = page.search_for_fuzzy("revenue increasd", max_edits=1)  # codespell:ignore increasd
    # Both the whole word and its prefix have distance one. This is a
    # substring API, so it does not add a word-completion heuristic.
    assert [(h["text"], h["distance"]) for h in hits] == [("revenue increase", 1)]


def test_casefold_glyph_boundaries(page):
    page.insert_text((30, 60), "ß")
    assert page.search_for_fuzzy("s", max_edits=0) == []
    hits = page.search_for_fuzzy("sa", max_edits=1)
    assert [(h["text"], h["distance"]) for h in hits] == [("ß", 1)]


def test_dehyphenated_textpage(page):
    page.insert_text((30, 60), "meth-\nod")
    tp = page.get_textpage(flags=pymupdf.TEXTFLAGS_SEARCH)
    hits = page.search_for_fuzzy("method", max_edits=0, textpage=tp)
    assert len(hits) == 1
    assert hits[0]["text"] == "meth-\nod"
    assert len(hits[0]["quads"]) == 2


@pytest.mark.parametrize("text,needle,expected", [
    ("Net   revenue\nincreased this year", "net revenue increased", "Net   revenue\nincreased"),
    ("A meth-\nod works", "method", "meth-\nod"),
    ("Straße", "STRASSE", "Straße"),
])
def test_normalization(page, text, needle, expected):
    page.insert_text((30, 60), text)
    hits = page.search_for_fuzzy(needle, max_edits=0)
    assert len(hits) == 1
    assert hits[0]["text"] == expected
    assert hits[0]["distance"] == 0
    assert len(hits[0]["quads"]) == (2 if "\n" in expected else 1)


def test_hyphens_at_block_boundaries(page):
    page.insert_text((30, 60), "meth-")
    page.insert_text((30, 200), "od")
    assert page.search_for_fuzzy("method", max_edits=0) == []
    assert _normalize("-5% 1.2 10-20 well-being")[0] == "-5% 1.2 10-20 well-being"


def test_cjk(page):
    page.insert_text((30, 60), "매출증가했습니다", fontname="korea")
    hits = page.search_for_fuzzy("매출증가했슴니다", max_edits=1)
    assert len(hits) == 1
    assert hits[0]["text"] == "매출증가했습니다"
    assert hits[0]["distance"] == 1


def test_ligatures():
    path = os.path.join(os.path.dirname(__file__), "resources", "text-find-ligatures.pdf")
    with pymupdf.open(path) as doc:
        hits = doc[0].search_for_fuzzy("flag", max_edits=0)
        assert len(hits) == 2
        assert all(_normalize(h["text"])[0] == "flag" for h in hits)


@pytest.mark.parametrize("needle", ["", " \n\t"])
def test_empty_needle(page, needle):
    assert page.search_for_fuzzy(needle, max_edits=2) == []


@pytest.mark.parametrize("limit,error", [(True, TypeError), (1.0, TypeError),
                                         ("1", TypeError), (-1, ValueError), (3, ValueError)])
def test_invalid_budget(page, limit, error):
    with pytest.raises(error):
        page.search_for_fuzzy("cat", max_edits=limit)


def test_empty_page_and_invalid_needle(page):
    assert page.search_for_fuzzy("cat", max_edits=1) == []
    with pytest.raises(TypeError):
        page.search_for_fuzzy(None, max_edits=1)
    with pytest.raises(TypeError):
        page.search_for_fuzzy("cat")


def test_clip_and_textpage(page, skip_quad_corrections):
    page.insert_text((30, 60), "prefix target suffix")
    page.insert_text((30, 160), "prefix target suffix")
    clip = pymupdf.Rect(0, 0, 300, 100)
    direct = page.search_for_fuzzy("target", max_edits=1, clip=clip)
    assert len(direct) == 1
    tp = page.get_textpage(clip=clip)
    reused = page.search_for_fuzzy("target", max_edits=1, textpage=tp,
                                   clip=pymupdf.Rect(0, 200, 10, 210))
    assert reused == direct
    assert page.get_textbox(direct[0]["quads"][0].rect) == "target"
    with pymupdf.open() as other:
        other_page = other.new_page()
        with pytest.raises(ValueError, match="not a textpage"):
            page.search_for_fuzzy("target", max_edits=1, textpage=other_page.get_textpage())


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
@pytest.mark.parametrize("text_rotation", [0, 90])
def test_geometry_and_annotation(tmp_path, rotation, text_rotation, skip_quad_corrections):
    with pymupdf.open() as doc:
        page = doc.new_page(width=500, height=500)
        page.insert_text((180, 280), "prefix target suffix", rotate=text_rotation)
        page.set_cropbox(pymupdf.Rect(30, 40, 470, 480))
        page.set_rotation(rotation)
        exact = page.search_for("target", quads=True)
        hits = page.search_for_fuzzy("targat", max_edits=1)
        assert len(hits) == 1
        assert hits[0]["text"] == "target"
        assert len(hits[0]["quads"]) == 1
        quad = hits[0]["quads"][0]
        for a, b in zip(quad, exact[0]):
            assert abs(a - b) < 0.001
        page.add_highlight_annot(hits[0]["quads"])
        path = tmp_path / "highlight.pdf"
        doc.save(path)
    with pymupdf.open(path) as reopened:
        page = reopened[0]
        assert len(list(page.annots())) == 1
        # Render both paths so a malformed quad/annotation cannot go unnoticed.
        assert page.get_pixmap(annots=True).samples != page.get_pixmap(annots=False).samples


def test_angled_text(skip_quad_corrections):
    path = os.path.join(os.path.dirname(__file__), "resources", "quad-calc-0.pdf")
    with pymupdf.open(path) as doc:
        page = doc[0]
        exact = page.search_for("angle 327", quads=True)
        hits = page.search_for_fuzzy("angle 327", max_edits=0)
        assert len(hits) == len(exact) == 1
        for a, b in zip(hits[0]["quads"][0], exact[0]):
            assert abs(a - b) < 0.01
