import csv
import json
import pathlib
import re
import time
from io import StringIO

import pymupdf
from pymupdf import NON_WIDGET_KEYS, PDF_NAME, mupdf

try:
    import pandas as PANDAS
except ImportError:
    PANDAS = None

PDF_NAME_Blur = mupdf.pdf_new_name("Bl")  # missing in mupdf.py
PDF_NAME_Focus = mupdf.pdf_new_name("Fo")  # codespell:ignore Fo


class FormFields:
    """
    This class creates a synopsis of the Form Fields in a PDF.
    The information is gathered in two ways that complement each other:
    * top-down via inspecting the /AcroForm/Fields array, and
    * bottom-up via parsing the /Annots arrays of the pages.
    """

    def __init__(self, doc, repair=False, verbose=False):
        """
        doc: PyMuPDF document or path to PDF file
        """
        if not isinstance(doc, pymupdf.Document):
            self.doc = pymupdf.open(doc)
        else:
            self.doc = doc
        if not self.doc.is_pdf:
            return
        self.pdfdoc = pymupdf._as_pdf_document(self.doc)
        self.repair = repair
        self.verbose = verbose
        self.refresh()  # create the initial form fields model
        t0 = None
        if verbose and (
            self.count_flat_fields or self.count_flat_rbgs or self.count_field_widgets
        ):
            pymupdf.message("Found PDF specification issues:")
            pymupdf.message(f"   flat RBGs: {self.count_flat_rbgs}\n"
            f"   flat fields: {self.count_flat_fields}\n"
            f"   field-widgets: {self.count_field_widgets}")
            if not self.repair:
                pymupdf.message("Repair is recommended.\n")
            else:
                pymupdf.message("Repair has been requested ...")
                t0 = time.time()

        if self.repair:  # execute repair routines
            # For each repair action, we start a fresh iteration as previous
            # repairs may have altered the structure of the fields.
            refresh_needed = False
            if self.count_field_widgets:
                for field_name in self.fields.keys():
                    self.repair_field_widget(field_name)
                    refresh_needed = True
            if self.count_flat_rbgs:
                for field_name in self.fields.keys():
                    self.repair_flat_rbg(field_name)
                    refresh_needed = True
            if self.count_flat_fields:
                for field_name in self.fields.keys():
                    self.repair_flat_field(field_name)
                    refresh_needed = True

            if refresh_needed:
                self.refresh()  # build the model again
                if self.verbose:
                    t1 = time.time() - t0
                    pymupdf.message(f"Repairs applied in {t1:.2f} seconds.")

    def refresh(self):
        """Refresh or build the form fields object."""
        self.count_flat_fields = 0
        self.count_flat_rbgs = 0
        self.count_field_widgets = 0
        self.page_xrefs = {}  # xref to page number if widgets present
        self.template_xrefs = []  # list of /Type/Template xrefs having widgets
        self.widgets = self._iter_page_widgets()  # walk through page PDF objects
        self._repair_widgets()  # indispensable repairs!
        # extract form fields starting from /AcroForm/Fields
        self.top = self._extract_form_fields_with_pages()
        if self.template_xrefs:
            self._iter_template_widgets()
        self.fields = {}  # contains all form fields
        self._build_model()  # bring everything together
        self._diagnose_all()  # store diagnosis results

    def _decode_pdf_name(self, name):
        """Decode PDF name objects that contain UTF-16BE escape sequences.

        Handles mixed content: octal escapes and literal ASCII characters.
        """
        if not name:
            return name

        # PDF names start with '/': strip it
        if name.startswith("/"):
            name = name[1:]
        if "\\" not in name:  # no escapes, return as-is
            return name
        result_bytes = bytearray()  # will store result here
        i = 0
        length = len(name)

        while i < length:
            ch = name[i]

            if ch == "\\":
                # Octal escape: up to 3 octal digits
                j = i + 1
                oct_digits = ""

                while j < length and len(oct_digits) < 3 and name[j] in "01234567":
                    oct_digits += name[j]
                    j += 1

                if oct_digits:
                    result_bytes.append(int(oct_digits, 8))
                    i = j
                    continue

                # Literal backslash
                result_bytes.append(ord("\\"))
                i += 1
                continue

            else:
                # Literal ASCII character
                result_bytes.append(ord(ch))
                i += 1

        # Try UTF-16BE decode
        try:
            return result_bytes.decode("UTF-16")
        except Exception:
            pymupdf.message(f"Failed to decode {result_bytes=}, {name=}")
            return name

    def _widget_object_from_widget(self, w, ppage):
        """Retrieve the PDF widget object from a widget wrapper."""
        widget = mupdf.pdf_first_widget(ppage)
        w_obj = widget.pdf_annot_obj()

        while w_obj.pdf_to_num() != w.xref and w_obj.pdf_is_dict():
            widget = widget.pdf_next_widget()
            w_obj = widget.pdf_annot_obj()

        if w_obj.pdf_to_num() != w.xref:
            raise ValueError(
                f"Internal error: Widget {w.xref} not found on page {w.page_number}."
            )
        return widget, w_obj

    def _is_js_rbg_script(self, js: str) -> bool:
        """Check if string is a typical JavaScript RBG script."""
        if not js:
            return False

        js_lower = js.lower()

        # typical JS-RBG patterns
        patterns = [
            "getfield(",  # Adobe AcroForm
            ".value =",  # direct value manipulation
            "rawvalue",  # XFA
            "resolveNode(",  # XFA
            "checkthisbox",  # checkbox manipulation
            "off",  # Off-State
        ]

        return any(p in js_lower for p in patterns)

    def _repair_widgets(self):
        """Repair basic widget problems:

        - missing /P (page reference) in widget annotation
        - missing mention in the /Kids array of /Parent
        """
        for w in self.widgets:
            w_obj = mupdf.pdf_new_indirect(self.pdfdoc, w.xref, 0)
            pno = w.page_number
            page_obj = mupdf.pdf_lookup_page_obj(self.pdfdoc, pno)
            try:
                # should always work:
                page_obj.pdf_ensure_indirect()
            except Exception:
                page_obj = mupdf.pdf_new_indirect(self.pdfdoc, page_obj.pdf_to_num(), 0)

            P = w_obj.pdf_dict_get(PDF_NAME("P"))
            if P.pdf_to_num() != page_obj.pdf_to_num():
                w_obj.pdf_dict_put(PDF_NAME("P"), page_obj)

            parent = w_obj.pdf_dict_get(PDF_NAME("Parent"))
            # Only if there indeed is a parent: ensure that it has a
            # /Kids array that references this widget
            if parent.pdf_is_dict():
                w.parent_xref = parent.pdf_to_num()
                # Ensure parent has a /Kids array that references this widget
                kids = parent.pdf_dict_get(PDF_NAME("Kids"))
                if not kids.pdf_is_array():  # /Kids array missing: make one
                    kids = parent.pdf_dict_put_array(PDF_NAME("Kids"), 1)
                # no mention in /Kids array: add this widget
                if not any(
                    kids.pdf_array_get(i).pdf_to_num() == w.xref
                    for i in range(kids.pdf_array_len())
                ):
                    kids.pdf_array_push(w_obj)
            else:
                w.parent_xref = 0

    def _make_widget_object(self, annots, widgets, owner_number, owner_type):
        """Create Widget objects from the annotation array.

        The owner of the array may be a /Page or a /Template. Depending on
        this, owner number is either the page number or the template xref.
        """
        has_widgets = False
        for i in range(annots.pdf_array_len()):
            annot = annots.pdf_array_get(i)
            subtype = annot.pdf_dict_get(PDF_NAME("Subtype"))
            if subtype.pdf_to_name() != "Widget":
                continue  # skip other annotation types
            has_widgets = True
            parent = annot.pdf_dict_get(PDF_NAME("Parent"))
            parent_xref = parent.pdf_to_num()
            # we use the standard Widget instance as a template for
            # storing basic widget information
            widget = pymupdf.Widget()
            widget.rect = pymupdf.Rect(annot.pdf_dict_get_rect(PDF_NAME("Rect")))
            widget.field_name = annot.pdf_load_field_name()
            widget.field_type = annot.pdf_field_type()
            widget.field_type_string = annot.pdf_field_type_string()
            widget.xref = annot.pdf_to_num()
            widget.field_value = annot.pdf_field_value()
            choices = []  # for ListBox or ComboBox options
            for j in range(annot.pdf_choice_field_option_count()):
                ch = annot.pdf_choice_field_option(1, j)
                choices.append(self._decode_pdf_name(ch))
            widget.choice_values = choices
            widget.page_number = owner_number if owner_type == "page" else None
            widget.template_xref = owner_number if owner_type == "template" else None
            widget.parent_xref = parent_xref
            widget.script = pymupdf.JM_get_script(annot.pdf_dict_get(PDF_NAME("A")))
            widget.script_stroke = pymupdf.JM_get_script(
                annot.pdf_dict_getl(PDF_NAME("AA"), PDF_NAME("K"))
            )
            widget.script_format = pymupdf.JM_get_script(
                annot.pdf_dict_getl(PDF_NAME("AA"), PDF_NAME("F"))
            )
            widget.script_change = pymupdf.JM_get_script(
                annot.pdf_dict_getl(PDF_NAME("AA"), PDF_NAME("V"))
            )
            widget.script_calc = pymupdf.JM_get_script(
                annot.pdf_dict_getl(PDF_NAME("AA"), PDF_NAME("C"))
            )
            widget.script_blur = pymupdf.JM_get_script(
                annot.pdf_dict_getl(PDF_NAME("AA"), PDF_NAME_Blur)
            )
            widget.script_focus = pymupdf.JM_get_script(
                annot.pdf_dict_getl(PDF_NAME("AA"), PDF_NAME_Focus)
            )

            if widget.field_type == pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON:
                if not self._is_js_rbg_script(widget.script):
                    # non-JS RadioButton: read Appearance State
                    onstate = annot.pdf_button_field_on_state()
                    widget.btn_on_state = self._decode_pdf_name(onstate.pdf_to_name())
                else:
                    # JS-RBG: no reliable On-State
                    widget.btn_on_state = None

            if widget.field_type == pymupdf.PDF_WIDGET_TYPE_CHECKBOX:
                widget.btn_on_state = self._decode_pdf_name(
                    annot.pdf_button_field_on_state().pdf_to_name()
                )

            widgets.append(widget)
        return has_widgets

    def _iter_template_widgets(self):
        """Return all widget annotations on /Template pages of the document.

        For every template object, only the /Annots array is inspected via
        low-level mupdf calls.
        Template objects do not occur in the PDF's page tree and are only
        detected by parsing /AcroForm/Fields. The list of template xrefs has
        been created previously in the code.
        """
        for xref in self.template_xrefs:
            page_obj = mupdf.pdf_load_object(self.pdfdoc, xref)
            annots = page_obj.pdf_dict_get(PDF_NAME("Annots"))
            if not annots.pdf_is_array():
                continue
            widgets = []
            has_annots = self._make_widget_object(annots, widgets, xref, "template")
            if has_annots:
                self.widgets.extend(widgets)

    def _iter_page_widgets(self):
        """Return all widget annotations on pages of the document.

        For every page PDF object, only the /Annots array is inspected via
        low-level mupdf calls. Fills self.page_xrefs with xref -> page number
        references for pages that contain at least one widget.
        """
        pdf = self.pdfdoc
        widgets = []
        for pno in range(self.doc.page_count):
            # we only look at page objects, and do not load the full page
            has_widgets = False
            page_obj = mupdf.pdf_lookup_page_obj(pdf, pno)  # page object
            annots = page_obj.pdf_dict_get(PDF_NAME("Annots"))
            has_widgets = self._make_widget_object(annots, widgets, pno, "page")
            if has_widgets:
                self.page_xrefs[page_obj.pdf_to_num()] = pno
        return widgets

    def _detect_js_radiogroups(self):
        """Build groups of RB widgets referencing each other via JavaScript."""

        groups = []
        visited = set()

        # collect all RadioButtons
        radios = [
            (name, entry)
            for name, entry in self.fields.items()
            if entry.get("type") == "radio" and entry.get("rbg_type") == "js"
        ]

        for name, entry in radios:
            if name in visited:
                continue

            widgets = entry["widgets"]
            if not widgets:
                continue

            w = widgets[0]
            script = w.script or ""
            # extract all field names referenced in the JS
            referenced = set(re.findall(r'getField\("([^"]+)"\)', script))

            # check if other RadioButtons are referenced
            group_members = [
                other_name for other_name, _ in radios if other_name in referenced
            ]

            if group_members:
                # group = this field + all referenced fields
                group = {name} | set(group_members)
                groups.append(group)
                visited |= group

        return groups

    def _extract_form_fields_with_pages(self):
        """
        Traverse /AcroForm/Fields hierarchy top-down and return a dict:
        fully qualified field name -> {"field_value": ..., "pages": [...]}
        We optionally include the xref of the field.

        As a side effect, we ensure that /DA and /DR exist in the AcroForm
        to avoid problems with missing default appearance and resources.
        """
        xrefs = True
        result = {}
        if not self.doc.is_form_pdf:
            return result
        default_DA = "(/Helv 0 Tf 0 g)"
        default_DR = (
            "<</Font <</Helv <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>>>>>"
        )

        # Access the AcroForm dictionary.
        cat = self.doc.pdf_catalog()
        pdfdoc = pymupdf._as_pdf_document(self.doc)
        acroform = mupdf.pdf_dict_getl(
            mupdf.pdf_trailer(pdfdoc),
            PDF_NAME("Root"),
            PDF_NAME("AcroForm"),
        )
        fields = acroform.pdf_dict_get(PDF_NAME("Fields"))

        # Ensure that /DA and /DR exist and are valid, otherwise set defaults.
        da = acroform.pdf_dict_get(PDF_NAME("DA"))
        dr = acroform.pdf_dict_get(PDF_NAME("DR"))
        if self.repair and not da.pdf_is_string():
            self.doc.xref_set_key(cat, "AcroForm/DA", default_DA)
        if self.repair and not dr.pdf_is_dict():
            self.doc.xref_set_key(cat, "AcroForm/DR", default_DR)

        def walk_field(field, prefix=""):
            # /T is the partial field name
            field_xref = field.pdf_to_num()
            name_x = field.pdf_dict_get(PDF_NAME("T"))
            name = name_x.pdf_to_text_string()
            if not name:
                return
            fq_name = f"{prefix}.{name}" if prefix else name

            # Pushbuttons carry no meaningful /V (pure action trigger) - skip
            # them. Nodes without their own/inherited /FT (hierarchy grouping
            # nodes) also report as PDF_WIDGET_TYPE_BUTTON with flags == 0, so
            # only skip when the pushbutton flag is actually set.
            if mupdf.pdf_field_type(field) == mupdf.PDF_WIDGET_TYPE_BUTTON and (
                mupdf.pdf_field_flags(field) & mupdf.PDF_BTN_FIELD_IS_PUSHBUTTON
            ):
                return

            # /V is the field value (may be None)
            value_x = field.pdf_dict_get(PDF_NAME("V"))
            if value_x.pdf_is_name():
                value = value_x.pdf_to_name()
            else:
                value = value_x.pdf_to_text_string() if value_x else ""

            # Collect page numbers from widget annotations
            pages = set()
            templates = set()  # /Template xrefs
            terminal = True
            kids = field.pdf_dict_get(PDF_NAME("Kids"))
            if kids.pdf_is_array():
                for i in range(kids.pdf_array_len()):
                    kid = kids.pdf_array_get(i)
                    kid_name_x = kid.pdf_dict_get(PDF_NAME("T"))
                    kid_name = kid_name_x.pdf_to_text_string()
                    if kid_name:
                        # Kid is a child field (has its own /T) - recurse only,
                        # its page(s) belong to it, not to this parent field.
                        terminal = False
                        walk_field(kid, fq_name)
                    else:
                        # Kid is a plain widget annotation of this field.
                        # Its container '/P' is either a /Page or a /Template.
                        owner = kid.pdf_dict_get(PDF_NAME("P"))
                        owner_xref = owner.pdf_to_num()  # xref of page
                        type_name = owner.pdf_dict_get(PDF_NAME("Type")).pdf_to_name()
                        if owner_xref in self.page_xrefs:  # implies /Type/Page
                            pages.add(self.page_xrefs.get(owner_xref))
                        elif type_name == "Template":  # exotic case: a "template" page
                            templates.add(owner_xref)

            # If no kids, check if this field itself has a page reference
            if not kids.pdf_array_len():
                owner = field.pdf_dict_get(PDF_NAME("P"))
                owner_xref = owner.pdf_to_num()
                type_name = owner.pdf_dict_get(PDF_NAME("Type")).pdf_to_name()
                if owner_xref in self.page_xrefs:
                    pages.add(self.page_xrefs.get(owner_xref))
                elif type_name == "Template":  # exotic case: a "template" page
                    templates.add(owner_xref)

            # Store result
            value_dict = {"field_value": value, "pages": sorted(pages)}
            if templates:
                value_dict["template_xrefs"] = sorted(templates)
                self.template_xrefs.extend(templates)
            if xrefs:
                value_dict["xref"] = field_xref
            value_dict["terminal"] = terminal

            existing = result.get(fq_name)
            if existing is None:
                result[fq_name] = value_dict
            else:
                # Same fully qualified name already seen: a "flat" radio-button
                # group (sibling field objects without a common /Kids parent).
                # Merge instead of overwriting so no field object is lost.
                if xrefs:
                    ex_xref = existing["xref"]
                    existing["xref"] = (
                        ex_xref if isinstance(ex_xref, list) else [ex_xref]
                    ) + [field_xref]
                existing["pages"] = sorted(set(existing["pages"]) | pages)
                existing["terminal"] = existing["terminal"] and terminal
                if existing["field_value"] in (None, "", "Off") and value not in (
                    None,
                    "",
                    "Off",
                ):
                    existing["field_value"] = value

        for i in range(fields.pdf_array_len()):
            field = fields.pdf_array_get(i)
            walk_field(field)

        return result

    def _diagnose_widget(self, w):
        """Sanity checks for a widget."""
        problems = []
        w_obj = mupdf.pdf_load_object(self.pdfdoc, w.xref)

        # Field name
        if not w.field_name:
            problems.append("Field has no field_name.")

        # Rect
        if not w.rect or w.rect.is_empty:
            problems.append("Widget /Rect is invalid or empty.")

        # Field type
        if not w.field_type:
            problems.append("Field has no valid type.")

        # Radio/Checkbox consistency
        if w.field_type in (
            pymupdf.PDF_WIDGET_TYPE_CHECKBOX,
            pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON,
        ):
            onstate = w_obj.pdf_button_field_on_state()
            if not onstate.pdf_is_name():
                problems.append("Button field has no valid on-state.")

        return {
            "widget": w,
            "ok": len(problems) == 0,
            "problems": problems,
        }

    def _diagnose_field(self, name):
        entry = self.fields[name]
        widgets = entry["widgets"]

        if not widgets:
            # Non-terminal (container) fields only group child fields via
            # /Kids and never have widget annotations of their own, so this
            # is expected rather than a problem.
            if not entry.get("terminal", True):
                return {"ok": True, "problems": [], "widget_reports": []}
            return {
                "ok": False,
                "problems": ["No widgets found for field."],
                "widget_reports": [],
            }
        parent_xrefs = {w.parent_xref for w in widgets}
        if (
            entry["type"] != "radio"
            and len(widgets) > 1
            and (len(parent_xrefs) > 1 or parent_xrefs == {0})
        ):
            # no parents at all or multiple parents: needs repair
            entry["invalid_parent_structure"] = True
            self.count_flat_fields += 1

        reports = [self._diagnose_widget(w) for w in widgets]
        entry["pages"] = sorted(
            set(entry.get("pages", []))
            | {w.page_number for w in widgets if w.page_number is not None}
        )
        entry["template_xrefs"] = sorted(
            set(entry.get("template_xrefs", []))
            | {w.template_xref for w in widgets if w.template_xref is not None}
        )
        for w in widgets:
            if not w.field_name:
                continue
            # JS-RBG widgets intentionally have different field names
            if w.field_name != name and entry.get("rbg_type") != "js":
                reports.append(
                    {
                        "widget": w,
                        "ok": False,
                        "problems": [
                            f"Widget field_name '{w.field_name}' does not match field '{name}'."
                        ],
                    }
                )
        problems = []
        for rep in reports:
            problems.extend(rep["problems"])

        # A checkbox field has one value (/V); widgets with different ON-states
        # cannot be addressed consistently, so the field is reported as faulty.
        if entry["type"] == "checkbox":
            cb_on_states = {w.btn_on_state for w in widgets}
            if len(cb_on_states) > 1:
                problems.append(
                    f"Multiple ON-states: {sorted(map(str, cb_on_states))}."
                )

        # ------------------------------------------------------------
        # RadioGroup value validation
        # ------------------------------------------------------------
        if entry["type"] == "radio":
            # Collect ON-State names of all widgets. For JS-RBGs the "on"
            # values are the widgets' field names.
            on_states = set()
            for w in widgets:
                if entry.get("rbg_type") == "js":
                    on_states.add(w.field_name)
                    continue
                w_obj = mupdf.pdf_load_object(self.pdfdoc, w.xref)
                onstate = w_obj.pdf_button_field_on_state()
                on = onstate.pdf_to_name()
                on_states.add(self._decode_pdf_name(on))

            # If a value exists but does not match any ON-State → warning
            val = entry["value"]
            if val and val not in on_states:
                problems.append(
                    f"RadioGroup value '{val}' does not match any widget ON-state {sorted(on_states)}"
                )

        """
        Indicate that the widget is its own field - contrary to:
        ------------------------------------------------------------------
        ISO 32000-1:2008, §12.7.3: Historically, a field and its widget
        annotation could be represented by the same dictionary object.
        This practice is discouraged in new PDF files.
        ------------------------------------------------------------------
        """
        entry["is_widget"] = len(widgets) == 1 and widgets[0].xref == entry["xref"]
        if entry["is_widget"]:
            self.count_field_widgets += 1
        rc = {
            "ok": len(problems) == 0,
            "problems": problems,
            "widget_reports": reports,
        }
        if rc["ok"]:  # no problems: remove unnecessary items
            del rc["problems"]
            del rc["widget_reports"]
        return rc

    def _build_model(self):
        """
        Build unified field model:
        - merge top-down field info with bottom-up widget info
        - group widgets by fully qualified field name
        """

        # --- classify RadioButton groups ---
        def classify_rbg(widgets):
            """Classify a set of radio button widgets into one of three types:
            - 'parent': Widgets having a /Parent entry, standard case
            - 'flat': Widgets forming a RBG implicitly via field name
            - 'js': Fallback for JavaScript-managed radio groups. The RBG logic
                    is established by JavaScript - not the PDF structure.
            """

            # 1. Parent RBG: some widget has a /Parent
            if any("Parent" in self.doc.xref_get_keys(w.xref) for w in widgets):
                return "parent"

            # 2. Flat RBG: all widgets have the same field name
            if len(widgets) > 1 and len({w.field_name for w in widgets}) == 1:
                self.count_flat_rbgs += 1
                return "flat"

            # 3. JS-RBG: fallback
            return "js"

        # 1. Top-down: initialize field entries
        for fq_name, info in self.top.items():
            self.fields[fq_name] = {
                "name": fq_name,
                "value": info.get("field_value"),
                "pages": info.get("pages", []),
                "xref": info.get("xref"),
                "terminal": info.get("terminal", True),
                "widgets": [],  # will be filled bottom-up
                "type": None,  # determined later
                "format": None,
                "choices": None,
                "diagnosis": None,
            }

        # 2. Bottom-up: attach widgets to fields
        for w in self.widgets:
            name = w.field_name
            if not name:
                continue

            if name not in self.fields:
                # Field exists only bottom-up (rare but possible)
                self.fields[name] = {
                    "name": name,
                    "value": w.field_value,
                    "pages": [w.page_number] if w.page_number is not None else [],
                    "template_xrefs": (
                        [w.template_xref] if w.template_xref is not None else []
                    ),
                    "xref": None,
                    "terminal": True,
                    "widgets": [],
                    "type": None,
                    "format": None,
                    "choices": None,
                    "diagnosis": None,
                }

            self.fields[name]["widgets"].append(w)

        # 3. Determine field types and formats
        for name, entry in self.fields.items():
            self._determine_field_type(entry)
            if entry["type"] == "radio":
                entry["rbg_type"] = classify_rbg(entry["widgets"])

        # 4. Join JS-RadioGroups
        js_groups = self._detect_js_radiogroups()

        for group in js_groups:
            # stabilize sequence order (natural sort: RadioButton2 < RadioButton10)
            group = sorted(
                group,
                key=lambda s: [
                    int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)
                ],
            )
            main = group[0]  # the main field that remains

            # Widgets of the main field
            main_entry = self.fields[main]

            # RBGs defined via JavaScript have a different field name for each
            # widget. These names represent the "choices". For other RBGs types,
            # the choices are the ON-state names of the widgets, which are
            # already collected in the main_entry["choices"] list.
            main_entry["choices"] = group
            main_entry["type"] = "radio"
            main_entry["format"] = "string"

            # Integrate all other fields into the group
            for other in group[1:]:
                other_entry = self.fields[other]

                # Append widgets
                main_entry["widgets"].extend(other_entry["widgets"])

                # Adopt value if set
                if other_entry["value"] not in (None, "", "Off"):
                    main_entry["value"] = other_entry["value"]

                # Delete field
                del self.fields[other]

        # 5. Normalize radio group values (fix illegal /V)
        for name, entry in self.fields.items():
            if entry["type"] != "radio":
                continue

            if entry["rbg_type"] == "js":
                # value of a JS-RBG is the field name of the widget that is ON
                entry["value"] = next(
                    (
                        w.field_name
                        for w in entry["widgets"]
                        if w.field_value not in (None, "", "Off")
                    ),
                    "",
                )
                continue

            # Collect ON-State names of the widgets
            on_states = set()
            for w in entry["widgets"]:
                w_obj = mupdf.pdf_load_object(self.pdfdoc, w.xref)
                onstate = w_obj.pdf_button_field_on_state()
                on = self._decode_pdf_name(onstate.pdf_to_name())
                on_states.add(on)
                if (
                    w.field_value != "Off"
                    and entry["value"] != w.field_value
                    and entry["rbg_type"] == "flat"
                ):
                    entry["value"] = on  # adopt first ON-state as value

            # If the current value does not match any ON-State → clear it
            val = entry["value"]
            if val and val not in on_states:
                entry["value"] = ""

        # 6. Build choices for radio fields (flat or JS)
        for name, entry in self.fields.items():
            if entry["type"] != "radio":
                continue

            # JS-RadioGroups already have choices
            if entry.get("choices"):
                continue

            # Flat RadioGroup: extract ON-state names from widgets
            on_states = []
            for w in entry["widgets"]:
                w_obj = mupdf.pdf_load_object(self.pdfdoc, w.xref)
                onstate = w_obj.pdf_button_field_on_state()
                on = onstate.pdf_to_name()
                on_states.append(self._decode_pdf_name(on))

            entry["choices"] = on_states

        # 7. Build list of widget xrefs in the choices order
        for name, entry in self.fields.items():
            if entry["type"] != "radio":
                continue
            rbg_type = entry.get("rbg_type")
            choices = entry.get("choices") or []
            widgets = entry.get("widgets") or []
            choice_xrefs = []
            for choice in choices:
                if rbg_type == "js":
                    choice_xref = [w.xref for w in widgets if w.field_name == choice][0]
                else:
                    choice_xref = [w.xref for w in widgets if w.btn_on_state == choice][
                        0
                    ]
                choice_xrefs.append(choice_xref)
            entry["choice_xrefs"] = choice_xrefs

    def _determine_field_type(self, entry):
        """Determine type / format of a field based on its first widget."""
        widgets = entry["widgets"]
        if not widgets:
            return

        w = widgets[0]
        ft = w.field_type_string.lower()

        # TEXT FIELD
        if "text" in ft:
            entry["type"] = "text"
            entry["format"] = "string"
            return
        if "radio" in ft:
            entry["type"] = "radio"
            entry["format"] = "string"
            return
        if "checkbox" in ft:
            entry["type"] = "checkbox"
            entry["format"] = "boolean"
            return
        if "signature" in ft:
            entry["type"] = "signature"
            entry["format"] = "binary"
            return
        if "button" in ft:
            entry["type"] = "button"
            entry["format"] = "string"
            return

        # CHOICE FIELDS
        if "choice" in ft or "list" in ft or "combo" in ft:
            entry["type"] = "choice"
            entry["format"] = "string"
            entry["choices"] = w.choice_values
            return

        # FALLBACK
        entry["type"] = "unknown"
        entry["format"] = "string"

    def _diagnose_all(self):
        for name in self.fields.keys():  # pylint: disable=consider-using-dict-items
            self.fields[name]["diagnosis"] = self._diagnose_field(name)

    def field_names(self):
        return sorted(self.fields.keys())

    def field_info(self, name):
        return self.fields.get(name)

    def list_valid_terminal_fields(self):
        """Return list of all valid terminal fields.

        We skip fields / field nodes that are invalid, non-terminal,
        or cannot have a value (signatures, pushbuttons).
        """
        result = []

        for name, entry in self.fields.items():
            # Container fields (grouping nodes without their own widgets)
            # are not editable themselves - only their leaf fields are.
            if not entry.get("terminal", True):
                continue
            if entry["type"] in ("signature", "button"):  # not "editable"
                continue
            current_value = entry["value"] or ""
            diag = entry["diagnosis"]
            if diag["ok"]:
                result.append(
                    {
                        "name": name,
                        "type": entry["type"],
                        "format": entry["format"],
                        "editable": bool(entry.get("pages")),
                        "choices": entry.get("choices"),
                        "value": current_value,
                        "widgets": len(entry["widgets"]),
                        "is_widget": entry.get("is_widget", False),
                    }
                )

        return result

    def repair_flat_rbg(self, field_name):
        """Cleans up a flat RBG.

        This converts a flat RBG into the standard parent-child structure.
        """

        doc = self.doc
        pdf = self.pdfdoc
        acro = mupdf.pdf_dict_getl(
            mupdf.pdf_trailer(pdf),
            PDF_NAME("Root"),
            PDF_NAME("AcroForm"),
        )
        fields = acro.pdf_dict_get(PDF_NAME("Fields"))

        entry = self.fields.get(field_name)
        if not entry:
            return False  # field not found
        widgets = entry["widgets"]  # the widgets associated with this field

        if not widgets or entry.get("rbg_type") != "flat":
            return False  # nothing to do

        old_xref = entry["xref"]  # xref in /AcroForm/Fields

        found_in_fields = False  # whether in /AcroForm/Fields
        for field_idx in range(fields.pdf_array_len()):
            item = fields.pdf_array_get(field_idx)
            if item.pdf_to_num() == old_xref:
                found_in_fields = True
                break
        if not found_in_fields:
            # The old field is not in the /AcroForm/Fields array.
            # Unexpected, but we cannot proceed here.
            return False

        # Create new field dictionary
        wxref = entry["choice_xrefs"][0]  # pick first widget xref as template
        kid = mupdf.pdf_load_object(pdf, wxref)
        parent_xref = doc.get_new_xref()  # allocate a new xref
        doc.update_object(parent_xref, "<<>>")  # make it a dictionary
        parent = mupdf.pdf_new_indirect(pdf, parent_xref, 0)
        # RadioButton Field
        for key in NON_WIDGET_KEYS:
            try:
                key_name = PDF_NAME(key)
            except Exception:
                key_name = mupdf.pdf_new_name(key)

            kid_item = kid.pdf_dict_get(key_name)
            if not kid_item.pdf_is_null():
                parent.pdf_dict_put(key_name, kid_item)
                kid.pdf_dict_del(key_name)

        # Create the /Kids Array
        kids = parent.pdf_dict_put_array(PDF_NAME("Kids"), len(widgets))

        # Clean up widgets and set /Parent
        for i, xref in enumerate(entry["choice_xrefs"]):
            kid = mupdf.pdf_new_indirect(pdf, xref, 0)
            kid.pdf_dict_put(PDF_NAME("Parent"), parent)
            kids.pdf_array_push(kid)
            if i == 0:
                continue
            # Remove field-only keys
            for key in NON_WIDGET_KEYS:
                try:
                    key_name = PDF_NAME(key)
                except Exception:
                    key_name = mupdf.pdf_new_name(key)
                kid.pdf_dict_del(key_name)

        # Set /V in the parent
        if entry["value"]:
            parent.pdf_dict_put_name(PDF_NAME("V"), entry["value"])
        else:
            parent.pdf_dict_put(PDF_NAME("V"), PDF_NAME("Off"))

        # replace entry in /Fields with the new parent dictionary
        fields.pdf_array_put(field_idx, parent)

        # update internal model
        entry["xref"] = parent_xref
        entry["rbg_type"] = "parent"
        entry["terminal"] = True
        return True

    def repair_flat_field(self, field_name):
        """Repairs a flat field by ensuring it has the correct structure.

        A set of widgets with the same field name (and field type) which
        either have no parent or different parents are called a "flat" field.
        Each member widget may or may not be present in /AcroForm/Fields.
        PDF viewers treat a flat field like a normal field which has multiple
        alias widgets.

        The repair process creates one field node whose /Kids array contains
        all the widget members. This field node is stored as a "root" in
        /AcroForm/Fields. Any other root fields with the same field name are
        removed from /AcroForm/Fields.
        """
        entry = self.fields.get(field_name)
        if not entry:
            return False  # field not found
        if not entry.get("invalid_parent_structure", False):
            return False  # not a flat field
        widgets = entry["widgets"]
        doc = self.doc
        pdf = self.pdfdoc
        parent_xref = doc.get_new_xref()
        doc.update_object(parent_xref, "<<>>")  # turn into a dictionary
        parent = mupdf.pdf_new_indirect(pdf, parent_xref, 0)
        kids = parent.pdf_dict_put_array(PDF_NAME("Kids"), len(widgets))
        for i, widget in enumerate(widgets):
            kid_xref = widget.xref
            kid = mupdf.pdf_new_indirect(pdf, kid_xref, 0)
            # move any non-widget keys from the kid to the parent
            for key in NON_WIDGET_KEYS:
                try:
                    key_name = PDF_NAME(key)
                except Exception:
                    key_name = mupdf.pdf_new_name(key)
                kid_obj = kid.pdf_dict_get(key_name)
                # if kid has this key, move it to the parent
                if not kid_obj.pdf_is_null():
                    if i == 0:
                        parent.pdf_dict_put(key_name, kid_obj)
                    kid.pdf_dict_del(key_name)
            kid.pdf_dict_put(PDF_NAME("Parent"), parent)
            kids.pdf_array_push(kid)
        # new parent is now built and its kids are cleaned up
        # remove any same-named root fields from /AcroForm/Fields
        fields = mupdf.pdf_dict_getl(
            mupdf.pdf_trailer(pdf),
            PDF_NAME("Root"),
            PDF_NAME("AcroForm"),
            PDF_NAME("Fields"),
        )
        for i in range(fields.pdf_array_len() - 1, -1, -1):
            f = fields.pdf_array_get(i)
            fname = f.pdf_dict_get(PDF_NAME("T"))
            if fname.pdf_to_text_string() == field_name:
                fields.pdf_array_del(i)
        # append our parent to fields
        fields.pdf_array_push(parent)
        return True

    def repair_field_widget(self, field_name):
        """Splits up a combined field-widget.

        The results are separate field and widget PDF dictionaries having the
        standard /Kids <-> /Parent relationship."""
        doc = self.doc
        pdf = self.pdfdoc
        entry = self.fields.get(field_name)
        if not entry:
            return False  # field not found
        if not entry.get("is_widget", False):
            return False  # nothing to do
        # the root fields array
        fields = mupdf.pdf_dict_getl(
            mupdf.pdf_trailer(pdf),
            PDF_NAME("Root"),
            PDF_NAME("AcroForm"),
            PDF_NAME("Fields"),
        )
        widget = entry["widgets"][0]
        wxref = widget.xref
        widget_obj = mupdf.pdf_new_indirect(pdf, wxref, 0)

        if "." in field_name:  # a name hierarchy: widget has a parent
            parent = widget_obj.pdf_dict_get(PDF_NAME("Parent"))
            if not parent.pdf_is_dict():
                return False  # irregular case: cannot handle this situation
            kids = parent.pdf_dict_get(PDF_NAME("Kids"))
            if not kids.pdf_is_array():
                return False  # irregular case: cannot handle this situation
        else:
            kids = fields

        found_in_kids = False
        for kid_idx in range(kids.pdf_array_len()):
            kid = kids.pdf_array_get(kid_idx)
            if kid.pdf_to_num() == wxref:
                found_in_kids = True
                break
        if not found_in_kids:
            return False  # irregular case: cannot handle this situation
        field_xref = doc.get_new_xref()  # make new xref
        doc.update_object(field_xref, "<<>>")  # turn into a dictionary
        field_obj = mupdf.pdf_new_indirect(pdf, field_xref, 0)

        # move non-widget keys over to the new field object
        for key in NON_WIDGET_KEYS:
            try:
                key_name = PDF_NAME(key)
            except Exception:
                key_name = mupdf.pdf_new_name(key)
            old = widget_obj.pdf_dict_get(key_name)
            if not old.pdf_is_null():
                field_obj.pdf_dict_put(key_name, old)
                widget_obj.pdf_dict_del(key_name)

        # give the widget a /Parent key pointing to the new field object
        widget_obj.pdf_dict_put(PDF_NAME("Parent"), field_obj)

        # give the new field object a /Kids array containing the widget
        field_kids = field_obj.pdf_dict_put_array(PDF_NAME("Kids"), 1)
        field_kids.pdf_array_push(widget_obj)

        # field replaces widget in parent kids array
        kids.pdf_array_put(kid_idx, field_obj)

        # Update internal model
        entry["is_widget"] = False
        entry["terminal"] = True
        self.fields[field_name] = entry
        return True

    def set_value(self, field_name, value):
        """Set the value of a field identified by field_name.

        Args:
            field_name (str): The name of the field to update.
            value: The value to set for the field.
        """

        def update_widget_lowlevel(w, value, choices=None, rbg_type=None):
            """Locate w as a MuPDF widget.

            Then update the widget using MuPDF functions."""
            pdf = self.pdfdoc
            if w.page_number is not None:
                ppage = mupdf.pdf_load_page(pdf, w.page_number)
            else:
                return False, None
            widget, w_obj = self._widget_object_from_widget(w, ppage)

            # determine widget's "On" for checkboxes and radio buttons
            if w.field_type in (
                pymupdf.PDF_WIDGET_TYPE_CHECKBOX,
                pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON,
            ):
                onstate = mupdf.pdf_button_field_on_state(w_obj)
                on = mupdf.pdf_to_name(onstate)
                on_decoded = f"{self._decode_pdf_name(on)}"

            # Checkbox
            if w.field_type == pymupdf.PDF_WIDGET_TYPE_CHECKBOX:
                parent = w_obj.pdf_dict_get(PDF_NAME("Parent"))
                if not parent.pdf_is_dict():  # if no parent, use the widget
                    parent = w_obj
                if value in (on, on_decoded):  # pylint: disable=possibly-used-before-assignment
                    w_obj.pdf_dict_put(PDF_NAME("AS"), onstate)
                    parent.pdf_dict_put(PDF_NAME("V"), onstate)
                else:
                    w_obj.pdf_dict_put(PDF_NAME("AS"), PDF_NAME("Off"))
                    parent.pdf_dict_put(PDF_NAME("V"), PDF_NAME("Off"))
                mupdf.pdf_update_widget(widget)
                return

            # RadioButton
            if w.field_type == pymupdf.PDF_WIDGET_TYPE_RADIOBUTTON:
                if rbg_type == "parent":  # this radio has a parent
                    parent = w_obj.pdf_dict_get(PDF_NAME("Parent"))

                    # The widget is ON only if its own on-state is the value
                    if value != "Off" and value == on_decoded:
                        parent.pdf_dict_put(PDF_NAME("V"), onstate)
                        w_obj.pdf_dict_put(PDF_NAME("AS"), onstate)
                    else:
                        w_obj.pdf_dict_put(PDF_NAME("AS"), PDF_NAME("Off"))
                        if value == "Off":
                            parent.pdf_dict_put(PDF_NAME("V"), PDF_NAME("Off"))
                elif rbg_type == "js":
                    # JS case: "ON" is the widget with the right field name
                    if w.field_name == value:
                        mupdf.pdf_set_annot_field_value(pdf, widget, f"{on}", 1)
                    else:
                        mupdf.pdf_set_annot_field_value(pdf, widget, "Off", 1)

                elif rbg_type == "flat":
                    # Flat case: "ON" is widget with the right on-state
                    if value == on_decoded:
                        self.doc.xref_set_key(w.xref, "V", f"/{on_decoded}")
                        self.doc.xref_set_key(w.xref, "AS", f"/{on_decoded}")
                    else:
                        mupdf.pdf_set_annot_field_value(pdf, widget, "Off", 1)

                mupdf.pdf_update_widget(widget)
                return

            # Text field
            if w.field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:
                mupdf.pdf_set_annot_field_value(pdf, widget, value, 1)
                mupdf.pdf_update_widget(widget)
                return

            # fallback
            mupdf.pdf_set_annot_field_value(pdf, widget, value, 1)
            mupdf.pdf_update_widget(widget)
            return

        if value is None:
            return False

        # --- field exists? ---
        if field_name not in self.fields:
            pymupdf.message(f"Unknown field: {field_name}")
            return False

        entry = self.fields[field_name]
        if not entry.get("terminal", True):
            pymupdf.message(f"Non-terminal '{field_name}' has no value.")
            return False

        diag = entry["diagnosis"]

        if not diag or not diag["ok"]:
            pymupdf.message(f"Cannot set value: '{field_name}' diagnosis failed.")
            for p in (diag or {}).get("problems", []):
                pymupdf.message(f"  - {p}")
            return False

        ftype = entry["type"]
        # Filter out widgets that do not have a valid page number.
        # We cannot currently edit fields which entirely reside on templates.
        widgets = [w for w in entry["widgets"] if w.page_number is not None]
        if not widgets:
            pymupdf.message(
                f"Cannot set value: Field '{field_name}' has no page-bound widgets."
            )
            return False
        rbg_type = entry.get("rbg_type")
        choices = entry.get("choices") or []
        if value in ("off", "Off", False, "False", "false", 0) and ftype in (
            "checkbox",
            "radio",
        ):
            value = "Off"

        # --- type normalization ---
        if ftype == "text":
            value = str(value)

        elif ftype == "checkbox":
            # choose proper "On" state for the checkbox
            if value != "Off":
                value = widgets[0].btn_on_state if widgets else "Yes"

        elif ftype == "radio":
            # if value isn't "Off", it must be one of the allowed choices
            if value != "Off" and value not in choices:
                pymupdf.message(f"Warning: '{value}' not in allowed choices {choices}")
                return False

            # RadioGroup: exactly one is ON
            for w in widgets:
                update_widget_lowlevel(w, value, choices=choices, rbg_type=rbg_type)

            entry["value"] = value
            return True

        elif ftype == "choice":
            if choices and str(value) not in choices:
                pymupdf.message(f"Warning: '{value}' not in allowed choices {choices}")
            value = str(value)

        # --- update field-level value ---
        entry["value"] = value
        rbg_type = entry.get("rbg_type")
        # --- update widgets ---
        for w in widgets:
            update_widget_lowlevel(w, value, choices=choices, rbg_type=rbg_type)

        return True

    def to_dicts(self):
        """Export editable fields as a Python list of dicts."""
        result = []

        for name, entry in self.fields.items():
            diag = entry["diagnosis"]
            if (
                not diag
                or not diag["ok"]
                or not entry.get("terminal", True)
                or entry["type"] in ("signature", "button")
            ):
                # Only export editable fields
                continue

            item = {
                "field": name,
                "type": entry["type"],
                "format": entry["format"],
                "editable": bool(entry.get("pages")),
                "choices": entry.get("choices") or [],
                "current_value": entry.get("value"),
                "new_value": None,
            }

            result.append(item)

        return result

    def to_json(self, file=None):
        """Export editable fields as a JSON string."""
        result = self.to_dicts()
        json_str = json.dumps(result)
        if file:
            with open(file, "w", encoding="utf-8") as f:
                f.write(json_str)
        else:
            return json_str

    def from_dicts(self, dicts):
        """Import form field value changes from a Python list of dictionaries."""
        for item in dicts:
            field_name = item.get("field")
            new_value = item.get("new_value")

            # Ignore empty new_value
            if new_value is None or new_value == "":
                continue

            if field_name not in self.fields:
                pymupdf.message(f"Warning: unknown field '{field_name}' in import")
                continue

            ok = self.set_value(field_name, new_value)
            if not ok:
                pymupdf.message(f"Failed to set '{field_name}' = '{new_value}'")
            else:
                pymupdf.message(f"Set '{field_name}' = '{new_value}'")

        pymupdf.message("Import from dicts completed.")

    def from_json(self, json_str):
        """Import form field value changes from a JSON string."""
        dicts = json.loads(json_str)
        return self.from_dicts(dicts)

    def to_csv(self, file=None):
        """
        Produce a CSV string listing all editable fields with metadata.
        """
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "field",
                "type",
                "format",
                "editable",
                "choices",
                "current_value",
                "new_value",
            ]
        )

        for name, entry in self.fields.items():
            # Container fields (grouping nodes without their own widgets)
            # are not editable themselves - only their leaf fields are.
            diag = entry["diagnosis"]
            if (
                not entry.get("terminal")
                or entry["type"] in ("signature", "button")
                or not diag
                or not diag["ok"]
            ):
                continue

            choices = entry.get("choices")
            choices_str = "|".join(choices) if choices else ""
            current_value = entry["value"] or ""
            writer.writerow(
                [
                    name,
                    entry["type"],
                    entry["format"],
                    "yes" if entry.get("pages", False) else "no",
                    choices_str,
                    current_value,
                    "",  # empty new_value for user to fill in
                ]
            )

        csv_content = output.getvalue()
        if file:
            with open(file, "w", newline="", encoding="utf-8") as f:
                f.write(csv_content)
            return
        return csv_content

    def _apply_csv_updates(self, csv_str):
        """
        Read a CSV with a 'field' and 'new_value' column and apply updates.
        """
        reader = csv.DictReader(StringIO(csv_str))

        for row in reader:
            name = row.get("field")
            new_value = row.get("new_value")
            if name and new_value not in (None, ""):
                self.set_value(name, new_value)

    def from_csv(self, filepath):
        csv_str = pathlib.Path(filepath).read_bytes().decode()
        self._apply_csv_updates(csv_str)
        pymupdf.message(f"from_csv({filepath}) completed.")

    def to_pandas(self):
        """
        Return a pandas DataFrame with all editable fields and metadata.
        """
        if PANDAS is None:
            raise ImportError("pandas is required but not installed.")
        buffer = StringIO(self.to_csv())
        df = PANDAS.read_csv(buffer)
        return df
