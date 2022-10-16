.. _StoriesAPI:

==============
Stories API
==============


.. role:: htmlTag(emphasis)

This is a collection of methods and attributes that may be used to manipulate the HTML Document Object Model (DOM) nodes of a :ref:`Story`. More detailed explanations can be found in the :ref:`Xml` section.

================================== ===========================================================================================
**Method / Attribute**             **Description**
================================== ===========================================================================================
:meth:`Xml.add_bullet_list`        add a :htmlTag:`ul` tag - bulleted list, context manager.
:meth:`Xml.add_codeblock`          add a :htmlTag:`pre` tag, context manager.
:meth:`Xml.add_description_list`   add a :htmlTag:`dl` tag, context manager.
:meth:`Xml.add_division`           add a :htmlTag:`div` tag (renamed from “section”), context manager.
:meth:`Xml.add_header`             add a header tag (one of :htmlTag:`h1` to :htmlTag:`h6`), context manager.
:meth:`Xml.add_horizontal_line`    add a :htmlTag:`hr` tag.
:meth:`Xml.add_image`              add a :htmlTag:`img` tag.
:meth:`Xml.add_link`               add a :htmlTag:`a` tag.
:meth:`Xml.add_number_list`        add a :htmlTag:`ol` tag, context manager.
:meth:`Xml.add_paragraph`          add a :htmlTag:`p` tag.
:meth:`Xml.add_span`               add a :htmlTag:`span` tag, context manager.
:meth:`Xml.add_subscript`          add subscript text(:htmlTag:`sub` tag) - inline element, treated like text.
:meth:`Xml.add_superscript`        add subscript text (:htmlTag:`sup` tag) - inline element, treated like text.
:meth:`Xml.add_code`               add code text (:htmlTag:`code` tag) - inline element, treated like text.
:meth:`Xml.add_var`                add code text (:htmlTag:`code` tag) - inline element, treated like text.
:meth:`Xml.add_samp`               add code text (:htmlTag:`code` tag) - inline element, treated like text.
:meth:`Xml.add_kbd`                add code text (:htmlTag:`code` tag) - inline element, treated like text.
:meth:`Xml.add_text`               add a text string. Line breaks ``\n`` are honored as :htmlTag:`br` tags.
:meth:`Xml.set_align`              sets the alignment using a CSS style spec. Only works for block-level tags.
:meth:`Xml.set_attribute`          sets an arbitrary key to some value (which may be empty).
:meth:`Xml.set_bgcolor`            sets the background color. Only works for block-level tags.
:meth:`Xml.set_bold`               sets bold on or off or to some string value.
:meth:`Xml.set_color`              sets text color.
:meth:`Xml.set_columns`            sets the number of columns. Argument may be any valid number or string.
:meth:`Xml.set_font`               sets the font-family, e.g. “sans-serif”.
:meth:`Xml.set_fontsize`           sets the font size. Either a float or a valid HTML/CSS string.
:meth:`Xml.set_id`                 sets a :htmlTag:`id`. A check for uniqueness is performed.
:meth:`Xml.set_italic`             sets italic on or off or to some string value.
:meth:`Xml.set_leading`            set inter-block text distance (``-mupdf-leading``), only works on block-level nodes.
:meth:`Xml.set_lineheight`         set height of a line. Float like 1.5, which sets to `1.5 * fontsize`.
:meth:`Xml.set_margins`            sets the margin(s), float or string with up to 4 values.
:meth:`Xml.set_pagebreak_after`    insert a page break after this node.
:meth:`Xml.set_pagebreak_before`   insert a page break before this node.
:meth:`Xml.set_properties`         set any or all desired properties in one call.
:meth:`Xml.add_style`              set (add) some “style” attribute not supported by its own ``set_`` method.
:meth:`Xml.add_class`              set (add) some “class” attribute.
:meth:`Xml.set_text_indent`        set indentation for first textblock line. Only works for block-level nodes.
:attr:`Xml.tagname`                either the HTML tag name like :htmlTag:`p` or ``None`` if a text node.
:attr:`Xml.text`                   either the node's text or ``None`` if a tag node.
:attr:`Xml.is_text`                check if the node is a text.
:attr:`Xml.first_child`            contains the first node one level below this one (or ``None``).
:attr:`Xml.last_child`             contains the last node one level below this one (or ``None``).
:attr:`Xml.next`                   the next node at the same level (or ``None``).
:attr:`Xml.previous`               the previous node at the same level.
:attr:`Xml.root`                   the top node of the DOM, which hence has the tagname :htmlTag:`html`.
================================== ===========================================================================================


