"""Synthetic form-field reproducers for Julian's September 22 test wheels.

Run with an already installed PyMuPDF and pytest. No network or pypdf required.
Assertions describe the desired result, so affected builds should FAIL.
The supplied two-page PDF predates each test and has one shared text field.
"""

from pathlib import Path
import re

import pymupdf
import pytest


SHARED = Path(__file__).with_name("resources") / "shared-text-field.pdf"


@pytest.fixture(params=[0, 4], ids=["garbage-0", "garbage-4"])
def garbage(request):
    return request.param


def _add(page, name, value, kind=pymupdf.PDF_WIDGET_TYPE_TEXT, y=50):
    widget = pymupdf.Widget()
    widget.field_name = name
    widget.field_type = kind
    widget.field_value = value
    widget.rect = pymupdf.Rect(50, y, 270, y + 30)
    widget.text_fontsize = 12
    page.add_widget(widget)
    return page.parent.reload_page(page)


def _inherited_key(doc, xref, key):
    """Read a field key whether stored on the widget or its parent field."""
    seen = set()
    while xref not in seen:
        seen.add(xref)
        value = doc.xref_get_key(xref, key)
        if value[0] != "null":
            return value
        parent_type, parent = doc.xref_get_key(xref, "Parent")
        if parent_type != "xref":
            return value
        xref = int(parent.split()[0])
    raise AssertionError("Cycle in field parent chain")


def _field_values(doc):
    """Inspect reachable named AcroForm fields, even when /V is absent.

    These fixtures use indirect entries in Fields/Kids and simple field names.
    This is not intended to be a general PDF syntax parser.
    """
    result = {}
    visited = set()

    def walk(array, prefix=""):
        for ref in re.findall(r"(\d+)\s+\d+\s+R", array):
            xref = int(ref)
            assert xref not in visited, "Repeated or cyclic field-tree reference"
            visited.add(xref)
            kind, partial_name = doc.xref_get_key(xref, "T")
            name = prefix
            if kind == "string":
                name = prefix + "." + partial_name if prefix else partial_name
                # Deletion must remove the field, not just clear its value.
                result[name] = doc.xref_get_key(xref, "V")
            kids_kind, kids = doc.xref_get_key(xref, "Kids")
            if kids_kind == "array":
                walk(kids, name)

    kind, fields = doc.xref_get_key(doc.pdf_catalog(), "AcroForm/Fields")
    if kind != "null":
        assert kind == "array", (kind, fields)
        walk(fields)
    return result


@pytest.mark.parametrize("value", ["Alice", "café", "김민수 café"],
                         ids=["ascii-control", "latin", "korean-and-latin"])
def test_text_creation_preserves_value(tmp_path, garbage, value):
    """Non-ASCII initial values must survive save/close/reopen unchanged."""
    path = tmp_path / "text-created.pdf"
    with pymupdf.open() as doc:
        _add(doc.new_page(), "customer", value)
        doc.save(path, garbage=garbage)
    with pymupdf.open(path) as doc:
        page = doc[0]
        assert page.first_widget.field_value == value
        assert _field_values(doc)["customer"] == ("string", value)


def test_text_unicode_update_control(tmp_path, garbage):
    """Control: updating an ASCII field to Unicode works on the tested wheels."""
    path = tmp_path / "text-updated.pdf"
    with pymupdf.open() as doc:
        page = _add(doc.new_page(), "customer", "Alice")
        widget = page.first_widget
        widget.field_value = "café"
        widget.update()
        doc.reload_page(page)
        doc.save(path, garbage=garbage)
    with pymupdf.open(path) as doc:
        page = doc[0]
        assert page.first_widget.field_value == "café"
        assert _field_values(doc)["customer"] == ("string", "café")


@pytest.mark.parametrize("selected", [True, False], ids=["on", "off"])
def test_checkbox_creation_writes_pdf_name(tmp_path, garbage, selected):
    """PDF button /V is a name, not a text string (ISO 32000-1 12.7.4.2.3)."""
    path = tmp_path / "checkbox-created.pdf"
    with pymupdf.open() as doc:
        _add(doc.new_page(), "accepted", selected,
             pymupdf.PDF_WIDGET_TYPE_CHECKBOX)
        doc.save(path, garbage=garbage)
    with pymupdf.open(path) as doc:
        page = doc[0]
        widget = page.first_widget
        expected = "/" + str(widget.on_state()) if selected else "/Off"
        assert doc.xref_get_key(widget.xref, "AS") == ("name", expected)
        assert _inherited_key(doc, widget.xref, "V") == ("name", expected)
        assert _field_values(doc)["accepted"] == ("name", expected)


def test_checkbox_update_writes_pdf_name(tmp_path, garbage):
    """The documented on_state() update must also leave a name-valued /V."""
    path = tmp_path / "checkbox-updated.pdf"
    with pymupdf.open() as doc:
        page = _add(doc.new_page(), "accepted", False,
                    pymupdf.PDF_WIDGET_TYPE_CHECKBOX)
        widget = page.first_widget
        wanted = widget.on_state()
        widget.field_value = wanted
        widget.update()
        doc.reload_page(page)
        doc.save(path, garbage=garbage)
    with pymupdf.open(path) as doc:
        page = doc[0]
        widget = page.first_widget
        expected = ("name", "/" + str(wanted))
        assert doc.xref_get_key(widget.xref, "AS") == expected
        assert _inherited_key(doc, widget.xref, "V") == expected
        # Checking only the widget can miss a stale /V on its named parent.
        assert _field_values(doc)["accepted"] == expected


@pytest.mark.parametrize("hierarchy", [False, True], ids=["plain", "dotted"])
def test_delete_last_widget_removes_field(tmp_path, garbage, hierarchy):
    """Deleting a field's only widget must not leave its value in AcroForm."""
    name = "Customer.Address.City" if hierarchy else "customer"
    path = tmp_path / "deleted.pdf"
    with pymupdf.open() as doc:
        page = _add(doc.new_page(), name, "Seoul")
        if hierarchy:
            page = _add(page, "Customer.Address.Country", "Korea", y=100)
        page.delete_widget(page.first_widget)
        doc.save(path, garbage=garbage)
    with pymupdf.open(path) as doc:
        page = doc[0]
        assert name not in [w.field_name for w in page.widgets()]
        fields = _field_values(doc)
        assert name not in fields, fields
        if hierarchy:
            assert fields["Customer.Address.Country"] == ("string", "Korea")


@pytest.mark.parametrize("delete_both", [False, True],
                         ids=["retain-one-control", "delete-both"])
def test_delete_shared_widgets(tmp_path, garbage, delete_both):
    """Independent fixture: retain a field while any widget remains.

    The delete-both case also fails on 1.28.2. Unlike the newly created plain
    field above, this shared-field cleanup problem is not a 2.0 regression.
    """
    path = tmp_path / "shared-deleted.pdf"
    with pymupdf.open(SHARED) as doc:
        page = doc[0]
        page.delete_widget(page.first_widget)
        if delete_both:
            page = doc[1]
            page.delete_widget(page.first_widget)
        doc.save(path, garbage=garbage)
    with pymupdf.open(path) as doc:
        count = sum(len(list(page.widgets())) for page in doc)
        assert count == (0 if delete_both else 1)
        fields = _field_values(doc)
        if delete_both:
            assert "customer" not in fields, fields
        else:
            assert fields["customer"] == ("string", "Alice")


@pytest.mark.parametrize("sync_flags", [False, True])
def test_shared_value_update_refreshes_other_widget(tmp_path, garbage, sync_flags):
    """Existing issue, also seen on 1.28.2. Do not call this a 2.0 regression.

    Compare page 2 with an explicit-update control using the same renderer.
    No hard-coded pixel hashes or appearance-stream text encoding assumptions.
    """
    path = tmp_path / "shared-updated.pdf"
    control = tmp_path / "shared-updated-both.pdf"
    with pymupdf.open(SHARED) as doc:
        before = doc[1].get_pixmap().digest
        page = doc[0]
        widget = page.first_widget
        widget.field_value = "Bob"
        widget.update(sync_flags=sync_flags)
        doc.reload_page(page)
        doc.save(path, garbage=garbage)
    with pymupdf.open(SHARED) as doc:
        for page in doc:
            widget = page.first_widget
            widget.field_value = "Bob"
            widget.update()
            doc.reload_page(page)
        doc.save(control, garbage=garbage)
    with pymupdf.open(control) as doc:
        expected = doc[1].get_pixmap().digest
        assert before != expected, "Control must visibly change Alice to Bob"
    with pymupdf.open(path) as doc:
        assert [page.first_widget.field_value for page in doc] == ["Bob", "Bob"]
        actual = doc[1].get_pixmap().digest
        assert actual == expected, "Page 2 still has a stale field appearance"


def test_shared_value_manual_update_control(tmp_path, garbage):
    path = tmp_path / "shared-updated-both.pdf"
    with pymupdf.open(SHARED) as doc:
        before = doc[1].get_pixmap().digest
        for page in doc:
            widget = page.first_widget
            widget.field_value = "Bob"
            widget.update()
            doc.reload_page(page)
        doc.save(path, garbage=garbage)
    with pymupdf.open(path) as doc:
        assert [page.first_widget.field_value for page in doc] == ["Bob", "Bob"]
        first, second = [page.get_pixmap().digest for page in doc]
        assert first == second
        assert second != before


def _create_radio_group(path, garbage):
    with pymupdf.open() as doc:
        page = _add(doc.new_page(), "shipping", "Standard",
                    pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON)
        _add(page, "shipping", "Express",
             pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON, y=100)
        doc.save(path, garbage=garbage)


def test_radio_creation_has_at_most_one_selected_widget(tmp_path, garbage):
    """Construction-path finding, not a test of Harald's forthcoming work.

    1.28.2 rejects this construction. Exclude radio tests for that comparison.
    """
    path = tmp_path / "radio-created.pdf"
    _create_radio_group(path, garbage)
    with pymupdf.open(path) as doc:
        page = doc[0]
        widgets = list(page.widgets())
        assert len(widgets) == 2
        assert {w.on_state() for w in widgets} == {"Standard", "Express"}
        flags = int(_inherited_key(doc, widgets[0].xref, "Ff")[1])
        assert flags & pymupdf.PDF_BTN_FIELD_IS_RADIO
        assert not flags & (1 << 25), "Fixture must not enable RadiosInUnison"
        states = [doc.xref_get_key(w.xref, "AS")[1] for w in widgets]
        assert len([s for s in states if s != "/Off"]) <= 1, states


def test_radio_selection_writes_pdf_name(tmp_path, garbage):
    initial = tmp_path / "radio-created.pdf"
    path = tmp_path / "radio-selected.pdf"
    _create_radio_group(initial, garbage)
    with pymupdf.open(initial) as doc:
        page = doc[0]
        widget = page.first_widget
        widget.field_value = widget.on_state()
        widget.update()
        doc.reload_page(page)
        doc.save(path, garbage=garbage)
    with pymupdf.open(path) as doc:
        page = doc[0]
        widgets = list(page.widgets())
        states = [doc.xref_get_key(w.xref, "AS")[1] for w in widgets]
        assert states == ["/Standard", "/Off"], states
        assert _inherited_key(doc, widgets[0].xref, "V") == ("name", "/Standard")
