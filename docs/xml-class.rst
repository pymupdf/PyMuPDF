.. include:: header.rst

.. _Xml:

================
Xml
================

.. role:: htmlTag(emphasis)

* New in v1.21.0

This represents an HTML or an XML node. It is a helper class intended to access the DOM (Document Object Model) content of a :ref:`Story` object.

There is no need to ever directly construct an :ref:`Xml` object: after creating a :ref:`Story`, simply take :attr:`Story.body` -- which is an Xml node -- and use it to navigate your way through the story's DOM.


================================ ===========================================================================================
**Method / Attribute**             **Description**
================================ ===========================================================================================
:meth:`~.add_bullet_list`        Add a :htmlTag:`ul` tag - bulleted list, context manager.
:meth:`~.add_codeblock`          Add a :htmlTag:`pre` tag, context manager.
:meth:`~.add_description_list`   Add a :htmlTag:`dl` tag, context manager.
:meth:`~.add_division`           add a :htmlTag:`div` tag (renamed from “section”), context manager.
:meth:`~.add_header`             Add a header tag (one of :htmlTag:`h1` to :htmlTag:`h6`), context manager.
:meth:`~.add_horizontal_line`    Add a :htmlTag:`hr` tag.
:meth:`~.add_image`              Add a :htmlTag:`img` tag.
:meth:`~.add_link`               Add a :htmlTag:`a` tag.
:meth:`~.add_number_list`        Add a :htmlTag:`ol` tag, context manager.
:meth:`~.add_paragraph`          Add a :htmlTag:`p` tag.
:meth:`~.add_span`               Add a :htmlTag:`span` tag, context manager.
:meth:`~.add_subscript`          Add subscript text(:htmlTag:`sub` tag) - inline element, treated like text.
:meth:`~.add_superscript`        Add subscript text (:htmlTag:`sup` tag) - inline element, treated like text.
:meth:`~.add_code`               Add code text (:htmlTag:`code` tag) - inline element, treated like text.
:meth:`~.add_var`                Add code text (:htmlTag:`code` tag) - inline element, treated like text.
:meth:`~.add_samp`               Add code text (:htmlTag:`code` tag) - inline element, treated like text.
:meth:`~.add_kbd`                Add code text (:htmlTag:`code` tag) - inline element, treated like text.
:meth:`~.add_text`               Add a text string. Line breaks ``\n`` are honored as :htmlTag:`br` tags.
:meth:`~.append_child`           Append a child node.
:meth:`~.clone`                  Make a copy if this node.
:meth:`~.create_element`         Make a new node with a given tag name.
:meth:`~.create_text_node`       Create direct text for the current node.
:meth:`~.find`                   Find a sub-node with given properties.
:meth:`~.find_next`              Repeat previous "find" with the same criteria.
:meth:`~.insert_after`           Insert an element after current node.
:meth:`~.insert_before`          Insert an element before current node.
:meth:`~.remove`                 Remove this node.
:meth:`~.set_align`              Set the alignment using a CSS style spec. Only works for block-level tags.
:meth:`~.set_attribute`          Set an arbitrary key to some value (which may be empty).
:meth:`~.set_bgcolor`            Set the background color. Only works for block-level tags.
:meth:`~.set_bold`               Set bold on or off or to some string value.
:meth:`~.set_color`              Set text color.
:meth:`~.set_columns`            Set the number of columns. Argument may be any valid number or string.
:meth:`~.set_font`               Set the font-family, e.g. “sans-serif”.
:meth:`~.set_fontsize`           Set the font size. Either a float or a valid HTML/CSS string.
:meth:`~.set_id`                 Set a :htmlTag:`id`. A check for uniqueness is performed.
:meth:`~.set_italic`             Set italic on or off or to some string value.
:meth:`~.set_leading`            Set inter-block text distance (`-mupdf-leading`), only works on block-level nodes.
:meth:`~.set_lineheight`         Set height of a line. Float like 1.5, which sets to `1.5 * fontsize`.
:meth:`~.set_margins`            Set the margin(s), float or string with up to 4 values.
:meth:`~.set_pagebreak_after`    Insert a page break after this node.
:meth:`~.set_pagebreak_before`   Insert a page break before this node.
:meth:`~.set_properties`         Set any or all desired properties in one call.
:meth:`~.add_style`              Set (add) a “style” that is not supported by its own `set_` method.
:meth:`~.add_class`              Set (add) a “class” attribute.
:meth:`~.set_text_indent`        Set indentation for first textblock line. Only works for block-level nodes.
:attr:`~.tagname`                Either the HTML tag name like :htmlTag:`p` or `None` if a text node.
:attr:`~.text`                   Either the node's text or `None` if a tag node.
:attr:`~.is_text`                Check if the node is a text.
:attr:`~.first_child`            Contains the first node one level below this one (or `None`).
:attr:`~.last_child`             Contains the last node one level below this one (or `None`).
:attr:`~.next`                   The next node at the same level (or `None`).
:attr:`~.previous`               The previous node at the same level.
:attr:`~.root`                   The top node of the DOM, which hence has the tagname :htmlTag:`html`.
================================ ===========================================================================================



**Class API**

.. class:: Xml

    .. method:: add_bullet_list

       Add an :htmlTag:`ul` tag - bulleted list, context manager. See `ul <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/ul>`_.

    .. method:: add_codeblock

       Add a :htmlTag:`pre` tag, context manager. See `pre <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/pre>`_.

    .. method:: add_description_list

       Add a :htmlTag:`dl` tag, context manager. See `dl <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/dl>`_.

    .. method:: add_division

       Add a :htmlTag:`div` tag, context manager. See `div <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/div>`_.

    .. method:: add_header(value)

       Add a header tag (one of :htmlTag:`h1` to :htmlTag:`h6`), context manager. See `headings <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/Heading_Elements>`_.

       :arg int value: a value 1 - 6.

    .. method:: add_horizontal_line

       Add a :htmlTag:`hr` tag. See `hr <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/hr>`_.

    .. method:: add_image(name, width=None, height=None)

       Add an :htmlTag:`img` tag. This causes the inclusion of the named image in the DOM.

       :arg str name: the filename of the image. This **must be the member name** of some entry of the :ref:`Archive` parameter of the :ref:`Story` constructor.
       :arg width: if provided, either an absolute (int) value, or a percentage string like "30%". A percentage value refers to the width of the specified `where` rectangle in :meth:`Story.place`. If this value is provided and `height` is omitted, the image will be included keeping its aspect ratio.
       :arg height: if provided, either an absolute (int) value, or a percentage string like "30%". A percentage value refers to the height of the specified `where` rectangle in :meth:`Story.place`. If this value is provided and `width` is omitted, the image's aspect ratio will be honored.

    .. method:: add_link(href, text=None)

       Add an :htmlTag:`a` tag - inline element, treated like text.

       :arg str href: the URL target.
       :arg str text: the text to display. If omitted, the `href` text is shown instead.

    .. method:: add_number_list

       Add an :htmlTag:`ol` tag, context manager.

    .. method:: add_paragraph

       Add a :htmlTag:`p` tag, context manager.

    .. method:: add_span

       Add a :htmlTag:`span` tag, context manager. See `span`_

    .. method:: add_subscript(text)

       Add "subscript" text(:htmlTag:`sub` tag) - inline element, treated like text.

    .. method:: add_superscript(text)

       Add "superscript" text (:htmlTag:`sup` tag) - inline element, treated like text.

    .. method:: add_code(text)

       Add "code" text (:htmlTag:`code` tag) - inline element, treated like text.

    .. method:: add_var(text)

       Add "variable" text (:htmlTag:`var` tag) - inline element, treated like text.

    .. method:: add_samp(text)

       Add "sample output" text (:htmlTag:`samp` tag) - inline element, treated like text.

    .. method:: add_kbd(text)

       Add "keyboard input" text (:htmlTag:`kbd` tag) - inline element, treated like text.

    .. method:: add_text(text)

       Add a text string. Line breaks ``\n`` are honored as :htmlTag:`br` tags.

    .. method:: set_align(value)

       Set the text alignment. Only works for block-level tags.

       :arg value: either one of the :ref:`TextAlign` or the `text-align <https://developer.mozilla.org/en-US/docs/Web/CSS/text-align>`_ values.

    .. method:: set_attribute(key, value=None)

       Set an arbitrary key to some value (which may be empty).

       :arg str key: the name of the attribute.
       :arg str value: the (optional) value of the attribute.

    .. method:: get_attributes()

       Retrieve all attributes of the current nodes as a dictionary.

       :returns: a dictionary with the attributes and their values of the node.

    .. method:: get_attribute_value(key)

       Get the attribute value of `key`.

       :arg str key: the name of the attribute.

       :returns: a string with the value of `key`.

    .. method:: remove_attribute(key)

       Remove the attribute `key` from the node.

       :arg str key: the name of the attribute.

    .. method:: set_bgcolor(value)

       Set the background color. Only works for block-level tags.

       :arg value: either an RGB value like (255, 0, 0) (for "red") or a valid `background-color <https://developer.mozilla.org/en-US/docs/Web/CSS/background-color>`_ value.

    .. method:: set_bold(value)

       Set bold on or off or to some string value.

       :arg value: `True`, `False` or a valid `font-weight <https://developer.mozilla.org/en-US/docs/Web/CSS/font-weight>`_ value.

    .. method:: set_color(value)

       Set the color of the text following.

       :arg value: either an RGB value like (255, 0, 0) (for "red") or a valid `color <https://developer.mozilla.org/en-US/docs/Web/CSS/color_value>`_ value.

    .. method:: set_columns(value)

       Set the number of columns.

       :arg value: a valid `columns <https://developer.mozilla.org/en-US/docs/Web/CSS/columns>`_ value.

       .. note:: Currently ignored - supported in a future MuPDF version.

    .. method:: set_font(value)

       Set the font-family.

       :arg str value: e.g. "sans-serif".

    .. method:: set_fontsize(value)

       Set the font size for text following.

       :arg value: a float or a valid `font-size <https://developer.mozilla.org/en-US/docs/Web/CSS/font-size>`_ value.

    .. method:: set_id(unqid)

       Set a :htmlTag:`id`. This serves as a unique identification of the node within the DOM. Use it to easily locate the node to inspect or modify it. A check for uniqueness is performed.

       :arg str unqid: id string of the node.

    .. method:: set_italic(value)

       Set italic on or off or to some string value for the text following it.

       :arg value: `True`, `False` or some valid `font-style <https://developer.mozilla.org/en-US/docs/Web/CSS/font-style>`_ value.

    .. method:: set_leading(value)

       Set inter-block text distance (`-mupdf-leading`), only works on block-level nodes.

       :arg float value: the distance in points to the previous block.

    .. method:: set_lineheight(value)

       Set height of a line.

       :arg value:  a float like 1.5 (which sets to `1.5 * fontsize`), or some valid `line-height <https://developer.mozilla.org/en-US/docs/Web/CSS/line-height>`_ value.

    .. method:: set_margins(value)

       Set the margin(s).

       :arg value: float or string with up to 4 values. See `CSS documentation <https://developer.mozilla.org/en-US/docs/Web/CSS/margin>`_.

    .. method:: set_pagebreak_after

       Insert a page break after this node.

    .. method:: set_pagebreak_before

       Insert a page break before this node.

    .. method:: set_properties(align=None, bgcolor=None, bold=None, color=None, columns=None, font=None, fontsize=None, indent=None, italic=None, leading=None, lineheight=None, margins=None, pagebreak_after=False, pagebreak_before=False, unqid=None, cls=None)

       Set any or all desired properties in one call. The meaning of argument values equal the values of the corresponding `set_` methods.

       .. note:: The properties set by this method are directly attached to the node, whereas every `set_` method generates a new :htmlTag:`span` below the current node that has the respective property. So to e.g. "globally" set some property for the :htmlTag:`body`, this method must be used.

    .. method:: add_style(value)

       Set (add) some style attribute not supported by its own `set_` method.

       :arg str value: any valid CSS style value.

    .. method:: add_class(value)

       Set (add) some "class" attribute.

       :arg str value: the name of the class. Must have been defined in either the HTML or the CSS source of the DOM.

    .. method:: set_text_indent(value)

       Set indentation for the first textblock line. Only works for block-level nodes.

       :arg value: a valid `text-indent <https://developer.mozilla.org/en-US/docs/Web/CSS/text-indent>`_ value. Please note that negative values do not work.


    .. method:: append_child(node)

       Append a child node. This is a low-level method used by other methods like :meth:`Xml.add_paragraph`.

       :arg node: the :ref:`Xml` node to append.

    .. method:: create_text_node(text)

       Create direct text for the current node.

       :arg str text: the text to append.

       :rtype: :ref:`Xml`
       :returns: the created element.

    .. method:: create_element(tag)

       Create a new node with a given tag. This a low-level method used by other methods like :meth:`Xml.add_paragraph`.

       :arg str tag: the element tag.

       :rtype: :ref:`Xml`
       :returns: the created element. To actually bind it to the DOM, use :meth:`Xml.append_child`.

    .. method:: insert_before(elem)

       Insert the given element `elem` before this node.

       :arg elem: some :ref:`Xml` element.

    .. method:: insert_after(elem)

       Insert the given element `elem` after this node.

       :arg elem: some :ref:`Xml` element.

    .. method:: clone()

       Make a copy of this node, which then may be appended (using :meth:`Xml.append_child`) or inserted (using one of :meth:`Xml.insert_before`, :meth:`Xml.insert_after`) in this DOM.

       :returns: the clone (:ref:`Xml`) of the current node.

    .. method:: remove()

       Remove this node from the DOM.


    .. method:: debug()

       For debugging purposes, print this node's structure in a simplified form.

    .. method:: find(tag, att, match)

       Under the current node, find the first node with the given `tag`, attribute `att` and value `match`.

       :arg str tag: restrict search to this tag. May be `None` for unrestricted searches.
       :arg str att: check this attribute. May be `None`.
       :arg str match: the desired attribute value to match. May be `None`.

       :rtype: :ref:`Xml`.
       :returns: `None` if nothing found, otherwise the first matching node.

    .. method:: find_next( tag, att, match)

       Continue a previous :meth:`Xml.find` (or :meth:`find_next`) with the same values.

       :rtype: :ref:`Xml`.
       :returns: `None` if none more found, otherwise the next matching node.


    .. attribute:: tagname

       Either the HTML tag name like :htmlTag:`p` or `None` if a text node.

    .. attribute:: text

       Either the node's text or `None` if a tag node.

    .. attribute:: is_text

       Check if a text node.

    .. attribute:: first_child

       Contains the first node one level below this one (or `None`).

    .. attribute:: last_child

       Contains the last node one level below this one (or `None`).

    .. attribute:: next

       The next node at the same level (or `None`).

    .. attribute:: previous

       The previous node at the same level.

    .. attribute:: root

       The top node of the DOM, which hence has the tagname :htmlTag:`html`.


Setting Text properties
------------------------

In HTML tags can be nested such that innermost text **inherits properties** from the tag enveloping its parent tag. For example `<p><b>some bold text<i>this is bold and italic</i></b>regular text</p>`.

To achieve the same effect, methods like :meth:`Xml.set_bold` and :meth:`Xml.set_italic` each open a temporary :htmlTag:`span` with the desired property underneath the current node.

In addition, these methods return there parent node, so they can be concatenated with each other.



Context Manager support
------------------------
The standard way to add nodes to a DOM is this::

   body = story.body
   para = body.add_paragraph()  # add a paragraph
   para.set_bold()  # text that follows will be bold
   para.add_text("some bold text")
   para.set_italic()  # text that follows will additionally be italic
   para.add_txt("this is bold and italic")
   para.set_italic(False).set_bold(False)  # all following text will be regular
   para.add_text("regular text")



Methods that are flagged as "context managers" can conveniently be used in this way::

   body = story.body
   with body.add_paragraph() as para:
      para.set_bold().add_text("some bold text")
      para.set_italic().add_text("this is bold and italic")
      para.set_italic(False).set_bold(False).add_text("regular text")
      para.add_text("more regular text")

.. include:: footer.rst

.. External links:

.. _span: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/span
