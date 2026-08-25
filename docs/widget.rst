.. include:: header.rst

.. _Widget:

================
Widget
================

|pdf_only_class|

This class represents a PDF Form field "widget". Widgets technically are a special case of PDF annotations, which allow users with limited permissions to enter information in a PDF. This is primarily used for filling out forms.

Like annotations, widgets live on PDF pages. Similar to annotations, the first widget on a page is accessible via :attr:`Page.first_widget` and subsequent widgets can be accessed via the :attr:`Widget.next` property.

Like annotations, widgets also lose connection to their page when the page becomes unavailable, please see `here <https://pymupdf.readthedocs.io/en/latest/app3.html#ensuring-consistency-of-important-objects-in-pymupdf>`_ for details. This is relevant especially when updating the widget: this will fail if the original page object is no longer available.




**Class API**

.. class:: Widget

    .. method:: button_states

      *New in version 1.18.15*

       Return the names of On / Off (i.e. selected / clicked or not) states a button field may have. While the 'Off' state usually is also named like so, the 'On' state is often given a name relating to the functional context, for example 'Yes', 'Female', etc.

       This method helps finding out the possible values of :attr:`field_value` in these cases.

       :returns: a dictionary with the names of 'On' and 'Off' for the *normal* and the *pressed-down* appearance of button widgets. The following example shows that the "selected" value is "Male":

         >>> print(field.field_name, field.button_states())
         Gender Second person {'down': ['Male', 'Off'], 'normal': ['Male', 'Off']}


    .. method:: on_state

      * New in version 1.22.2

       Return the value of the "ON" state of check boxes and radio buttons. For check boxes this is always the value "Yes". For radio buttons, this is the value to select / activate the button.

       :returns: the value that sets the button to "selected". For non-checkbox, non-radiobutton fields, always `None` is returned. For check boxes the return is `True`. For radio buttons this is the value "Male" in the following example:

         >>> print(field.field_name, field.button_states())
         Gender Second person {'down': ['Male', 'Off'], 'normal': ['Male', 'Off']}
         >>> print(field.on_state())
         Male

        So for check boxes and radio buttons, the recommended method to set them to "selected", or to check the state is the following:

         >>> field.field_value = field.on_state()
         >>> field.field_value == field.on_state()
         True


    .. method:: update(sync_flags=False)

       After any changes to a widget, this **method must be used** to reflect changes in the PDF [#f1]_.

       :arg bool sync_flags: if ``True``, the widget's :attr:`Widget.field_flags` are copied to the ``Parent`` object (if present) and all widgets named in its ``Kids`` array. This provides a convenient way to -- for example -- set all instances of the widget to read-only, no matter on which page they may occur [#f2]_.

    .. method:: reset

       Reset the field's value to its default -- if defined -- or remove it. Do not forget to issue :meth:`update` afterwards.

    .. attribute:: next

       Point to the next form field on the page. The last widget returns ``None``.

    .. attribute:: border_color

       A list of up to 4 floats defining the field's border color. Default value is ``None`` which causes border style and border width to be ignored.

    .. attribute:: border_style

       A string defining the line style of the field's border. See :attr:`Annot.border`. Default is "s" ("Solid") -- a continuous line. Only the first character (upper or lower case) will be regarded when creating a widget.

    .. attribute:: border_width

       A float defining the width of the border line. Default is 1.

    .. attribute:: border_dashes

       A list/tuple of integers defining the dash properties of the border line. This is only meaningful if *border_style == "D"* and :attr:`border_color` is provided.

    .. attribute:: choice_values

       Python sequence of strings defining the valid choices of list boxes and combo boxes. For these widget types, this property is mandatory and must contain at least two items. Ignored for other types.

    .. attribute:: field_name

       A mandatory string defining the field's name. If the name contains one or more colons "." the field is considered to be a child of a parent field. If the parent field does not exist, it will be created automatically. If the (full) name already exists anywhere in the PDF, the widget will become a new child of the existing field.

       All widgets with the same name -- whether or not a colon is part of it and independent of their position in the document -- will share the same field value and field flags.

       See also :ref:`the relationship between form fields and widgets <Widget>`.

    .. attribute:: field_label

       An optional string containing an "alternate" field name. Typically used for any notes, help on field usage, etc. Default is the field name.

    .. attribute:: field_value

       The value of the field.

    .. attribute:: field_flags

       An integer defining a large amount of properties of a field. Be careful when changing this attribute as this may change the field type.

    .. attribute:: field_type

       A mandatory integer defining the field type. This is a value in the range of 0 to 6. It cannot be changed when updating the widget.

    .. attribute:: field_type_string

       A string describing (and derived from) the field type.

    .. attribute:: fill_color

       A list of up to 4 floats defining the field's background color.

    .. attribute:: button_caption

       The caption string of a button-type field.

    .. attribute:: is_signed

       A bool indicating the signing status of a signature field, else ``None``.

    .. attribute:: rect

       The rectangle containing the field.

    .. attribute:: text_color

       A list of **1, 3 or 4 floats** defining the text color. Default value is black (`[0, 0, 0]`).

    .. attribute:: text_font

       A string defining the font to be used. Default and replacement for invalid values is *"Helv"*. For valid font reference names see the table below.

    .. attribute:: text_fontsize

       A float defining the text :data:`fontsize`. Default value is zero, which causes PDF viewer software to dynamically choose a size suitable for the annotation's rectangle and text amount.

    .. attribute:: text_maxlen

       An integer defining the maximum number of text characters. PDF viewers will (should) not accept a longer text.

    .. attribute:: text_type

       An integer defining acceptable text types (e.g. numeric, date, time, etc.). For reference only for the time being -- will be ignored when creating or updating widgets.

    .. attribute:: xref

       The PDF :data:`xref` of the widget.

    .. attribute:: script

       * New in version 1.16.12

       JavaScript text (unicode) for an action associated with the widget, or ``None``. This is the only script action supported for **button type** widgets.

    .. attribute:: script_stroke

       * New in version 1.16.12

       JavaScript text (unicode) to be performed when the user types a key-stroke into a text field or combo box or modifies the selection in a scrollable list box. This action can check the keystroke for validity and reject or modify it. ``None`` if not present.

    .. attribute:: script_format

       * New in version 1.16.12

       JavaScript text (unicode) to be performed before the field is formatted to display its current value. This action can modify the field's value before formatting. ``None`` if not present.

    .. attribute:: script_change

       * New in version 1.16.12

       JavaScript text (unicode) to be performed when the field's value is changed. This action can check the new value for validity. ``None`` if not present.

    .. attribute:: script_calc

       * New in version 1.16.12

       JavaScript text (unicode) to be performed to recalculate the value of this field when that of another field changes. ``None`` if not present.

    .. attribute:: script_blur

       * New in version 1.22.6

       JavaScript text (unicode) to be performed on losing the focus of this field. ``None`` if not present.

    .. attribute:: script_focus

       * New in version 1.22.6

       JavaScript text (unicode) to be performed on focusing this field. ``None`` if not present.

    .. note::

       1. For **adding** or **changing** one of the above scripts,
         just put the appropriate JavaScript source code in the widget attribute.
         To **remove** a script, set the respective attribute to ``None``.

       2. Button fields only support :attr:`script`.
         Other script entries will automatically be set to ``None``.

       3. It is worthwhile to look at
          `this <https://experienceleague.adobe.com/docs/experience-manager-learn/assets/FormsAPIReference.pdf?lang=en>`_
          manual with lots of information about Adobe's standard scripts for various field types.
          For example, if you want to add a text field representing a date,
          you may want to store the following scripts.
          They will ensure pattern-compatible date formats and display date pickers in supporting viewers::

              widget.script_format = 'AFDate_FormatEx("mm/dd/yyyy");'
              widget.script_stroke = 'AFDate_KeystrokeEx("mm/dd/yyyy");'


Standard Fonts for Widgets
----------------------------------
Widgets use their own resources object ``/DR``. A widget resources object must at least contain a ``/Font`` object. Widget fonts are independent from page fonts. We currently support the 14 PDF base fonts using the following fixed reference names, or any name of an already existing field font. When specifying a text font for new or changed widgets, **either** choose one in the first table column (upper and lower case supported), **or** one of the already existing form fonts. In the latter case, spelling must exactly match.

To find out already existing field fonts, inspect the list :attr:`Document.FormFonts`.

============= =======================
**Reference** **Base14 Fontname**
============= =======================
CoBI          Courier-BoldOblique
CoBo          Courier-Bold
CoIt          Courier-Oblique
Cour          Courier
HeBI          Helvetica-BoldOblique
HeBo          Helvetica-Bold
HeIt          Helvetica-Oblique
Helv          Helvetica **(default)**
Symb          Symbol
TiBI          Times-BoldItalic
TiBo          Times-Bold
TiIt          Times-Italic
TiRo          Times-Roman
ZaDb          ZapfDingbats
============= =======================

You are generally free to use any font for every widget. However, we recommend using ``ZaDb`` ("ZapfDingbats") and :data:`fontsize` 0 for check boxes: typical viewers will put a correctly sized tickmark in the field's rectangle, when it is clicked.

Supported Widget Types
-----------------------
PyMuPDF supports the creation and update of most widget types.

* text (`PDF_WIDGET_TYPE_TEXT`)
* push button (`PDF_WIDGET_TYPE_BUTTON`)
* check box (`PDF_WIDGET_TYPE_CHECKBOX`)
* combo box (`PDF_WIDGET_TYPE_COMBOBOX`)
* list box (`PDF_WIDGET_TYPE_LISTBOX`)
* radio button (`PDF_WIDGET_TYPE_RADIOBUTTON`): PyMuPDF now supports the creation and update of Radio Button Groups (RBGs). Adding a new radio button widget with the same (full) name as an existing one anywhere in the PDF will automatically create or extend an RBG.
* signature (`PDF_WIDGET_TYPE_SIGNATURE`) **read only** -- no update or creation of signatures and no signing support.

The Relationship between Form Fields and Widgets
--------------------------------------------------
A form field is a logical object in the document's form field tree. It may have one or more widgets, which are the visual appearances of that field on one or more pages. A widget is therefore the page-bound representation of a form field.

The connection between a widget and its form field is established through the widget's ``/Parent`` entry, which references the form field. Conversely, the form field's ``/Kids`` array contains references to all widgets that visually represent that field.

Form fields themselves are not tied to any page; they exist solely in the document's AcroForm hierarchy. Widgets, however, are page annotations and are always associated with a specific page.

A single form field may be represented by multiple widgets. For example, a field may have one widget on page 1 and another on page 2 (or even multiple widgets on the same page). In this case, both widgets share the same form field as their parent. Changing the value of one widget automatically updates the value shown by all other widgets of that field.

Form Field Hierarchy
--------------------------------------------------
Form fields support hierarchical naming. A form field may have child fields, forming a logical structure. The hierarchy is defined by the ``/Parent`` entry of a child field, which references its parent field. The parent field's ``/Kids`` array contains references to all its child fields.

This hierarchy is reflected in the field's name. For example, a field named "Parent.Child" has a parent field "Parent" and a child field "Child". The parent may have additional children such as "Parent.Child2" or "Parent.Child3".

Automatic Hierarchy Creation via Dotted Names
--------------------------------------------------
Using dots (".") in a widget's :attr:`field_name` automatically creates or updates the corresponding form field hierarchy. For example:

* Creating a widget named "Person.Name" creates or updates the form field "Person" and adds the widget as a child of "Person".

* Creating a widget named "Person.Address" adds another child field under "Person".

* Creating a widget named "Person.MaritalStatus" adds yet another child field.

In all cases, the widget becomes the visual representation of the terminal field in the hierarchy.

This mechanism allows complex information structures to be expressed naturally within a PDF form.


.. rubric:: Footnotes

.. [#f1] If you intend to re-access a new or updated field (e.g. for making a pixmap), make sure to reload the page first. Either close and re-open the document, or load another page first, or simply do `page = doc.reload_page(page)`.

.. [#f2] Among other purposes, ``Parent`` objects are also used to facilitate multiple occurrences of a field (on the same or on different pages). The ``Kids`` array in this ``Parent`` object contains the cross references of all widgets that are "copies" of the same field. Whenever the field value of any "kid" widget is changed, all the other kids are immediately updated too. This is a very efficient way to handle multiple copies of the same field, e.g. for filling out forms. This simultaneous update only happens for :attr:`Widget.field value`. The new parameter ``sync_flags`` extends this to :attr:`Widget.field_flags`. This cannot be automated in the same way as for the field value to allow for more flexibility.

.. include:: footer.rst
