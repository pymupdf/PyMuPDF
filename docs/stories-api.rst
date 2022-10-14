.. _StoriesAPI:

==============
Stories API
==============


.. role:: htmlTag(emphasis)


The Stories API supports text and image output via ``fitz.Story``.

The following methods are defined for any node, starting from ``story.body`` down to every other node.


- ``node.add_bullet_list`` - appends :htmlTag:`ul` tag - bulleted list (context manager support).
- ``node.add_codeblock`` - appends a :htmlTag:`pre` tag - (context manager support).
- ``node.add_description_list`` - add :htmlTag:`dl` tag - (context manager support).
- ``node.add_division`` - add :htmlTag:`div` tag (renamed from “section”) - (context manager support).
- ``node.add_header`` - appends one of the :htmlTag:`h1`, :htmlTag:`h2`, ... :htmlTag:`h6` header tags. Note: if node is also a header or the :htmlTag:`p` tag, appending happens to node.parent.
- ``node.add_horizontal_line`` - add :htmlTag:`hr` tag.
- ``node.add_image(name, width, height)`` - add :htmlTag:`img` tag. Width / height can either be absolute numbers (``int``) or percentage values. E.g. ``width="20%"`` and **height** unspecified (!) reproduces the image scaled such that the resulting width is 20% of the “where” rectangle. Using ``height="20%"`` (and **width** unspecified) reproduces the image with 20% of the “where” height. Aspect ratio is kept in both cases. Specifying both values (percentage or absolute values) will cause a reproduction that ignores the aspect ratio.
- ``node.add_link`` - appends a :htmlTag:`a` tag. Optional parameter: link text, inline element, treated like text.
- ``node.add_number_list`` - add :htmlTag:`ol` tag - (context manager support).
- ``node.add_paragraph`` - appends a :htmlTag:`p` tag. Note if node also is :htmlTag:`p`, appending happens to ``node.parent()``.
- ``node.add_span`` - appends a :htmlTag:`span` tag - (context manager support).
- ``node.add_subscript(text)`` - add subscript text(:htmlTag:`sub` tag) - inline element, treated like text.
- ``node.add_superscript(text)`` - add subscript text (:htmlTag:`sup` tag) - inline element, treated like text.
- ``node.add_code`` - add code text (:htmlTag:`code` tag) - inline element, treated like text. There are the following synonyms defined: ``add_var``, ``add_samp``, ``add_kbd``.
- ``node.add_text`` - appends a text string. Note: if "text" contains line breaks ``\n``, multiple lines will be appended, automatically using :htmlTag:`br` tags.
- ``node.set_align`` - sets the alignment using a CSS style spec. Only works for block-level tags. Hence if node is no block-level tag, the resp. style spec is set in ``node.parent()``.
- ``node.set_attribute(key,value)`` - sets an arbitrary key (**str** like “style”) to some value (**str**, may be empty).
- ``node.set_bgcolor`` - sets the background color. Same restrictions apply as for ``set_align``. Color may be specified as either RGB tuple or a HTML string.
- ``node.set_bold`` - sets bold on or off via ``True`` (default) or ``False`` or some valid CSS string.
- ``node.set_color`` - sets text color. Specify like in ``set_bgcolor``.
- ``node.set_columns`` - sets the number of columns. Argument may be any valid number or string.
- ``node.set_font`` - sets the font-family, e.g. “sans-serif”.
- ``node.set_fontsize`` - sets the font size. Either a float or a valid HTML/CSS string.
- ``node.set_id`` - sets a HTML :htmlTag:`id`. A check for uniqueness is performed.
- ``node.set_italic`` - sets italic on or off via ``True`` (default) or ``False`` or some valid CSS string.
- ``node.set_leading`` - set inter-block distance (``-mupdf-leading``), only works on block-level nodes.
- ``node.set_lineheight`` - set height of a line. Float like 1.5, which sets to `1.5 * fontsize`.
- ``node.set_margins`` - sets the margin(s), float or string with up to 4 values.
- ``node.set_pagebreak_after`` - insert a page break after this node.
- ``node.set_pagebreak_before`` - insert a page break before this node.
- ``node.set_properties`` - set all desired properties (above) in one call. Convenience method. **Must** be used for modifying nodes in existing HTML source. In contrast to separate ``set_*`` calls, this method assigns all properties to ``node`` itself, so any text underneath is affected.
- ``node.set_opacity`` - sets opacity. Apparently not supported by MuPDF yet?
- ``node.set_underline`` - sets underline. Apparently not supported by MuPDF yet?
- ``node.set_style`` - set some “style” attribute (i.e. not supported above).
- ``node.set_class`` - set some “class” attribute.
- ``node.set_text_indent`` - set indentation for first text line. Only works for block-level nodes.

Under the hood, above methods make use of new methods and properties defined for any node:

- ``node.tagname`` - either the HTML tag name like :htmlTag:`p` or ``None`` if a text node.
- ``node.text`` - either the node's text or ``None`` if a tag node.
- ``node.is_text`` - ``True`` or ``False``.
- ``node.first_child`` - contains first node under this one.
- ``node.last_child`` - contains last node under this one.
- ``node.next`` - next node, same level.
- ``node.previous`` - previous node, same level.
- ``node.root`` - always the top node with tagname :htmlTag:`html`.



