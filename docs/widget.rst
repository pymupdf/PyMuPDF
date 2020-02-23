.. _Widget:

================
Widget
================

This class represents a PDF Form field, also called "widget". Fields are a special case of annotations, which allow users with limited permissions to enter information in a PDF. This is primarily used for filling out forms.

Like annotations, widgets live on PDF pages. Similar to annotations, the first widget on a page is accessible via :attr:`Page.firstWidget` and subsequent widgets can be accessed via the :attr:`Widget.next` property.

*(Changed in version 1.16.0)* Widgets are no longer mixed with annotations. :attr:`Page.firstAnnot` and :meth:`Annot.next` will deliver non-widget annotations exclusively, and be *None* if only form fields exist on a page. Vice versa, :attr:`Page.firstWidget` and :meth:`Widget.next` will only show widgets.


**Class API**

.. class:: Widget

    .. attribute:: next

       Point to the next form field on the page.

    .. method:: update

       After any changes to a widget, this method **must be used** to store them in the PDF.

    .. attribute:: border_color

       A list of up to 4 floats defining the field's border. Default value is *None* which causes border style and border width to be ignored.

    .. attribute:: border_style

       A string defining the line style of the field's border. See :attr:`Annot.border`. Default is "s" ("Solid") -- a continuous line. Only the first character (upper or lower case) will be regarded when creating a widget.

    .. attribute:: border_width

       A float defining the width of the border line. Default is 1.

    .. attribute:: border_dashes

       A list of integers defining the dash properties of the border line. This is only meaningful if *border_style == "D"* and :attr:`border_color` is provided.

    .. attribute:: choice_values

       Python sequence of strings defining the valid choices of list boxes and combo boxes. For these widget types the property is mandatory. Ignored for other types. The sequence must contain at least two items. When updating the widget, this sequence will always the complete new list of values must be specified.

    .. attribute:: field_name

       A mandatory string defining the field's name. No checking for duplicates takes place.

    .. attribute:: field_label

       An optional string containing an "alternate" field name. Typically used for any notes, help on field usage, etc. Default is the field name.

    .. attribute:: field_value

       The value of the field.

    .. attribute:: field_flags

       An integer defining a large amount of proprties of a field. Handle this attribute with care.

    .. attribute:: field_type

       A mandatory integer defining the field type. This is a value in the range of 0 to 6. It cannot be changed when updating the widget.

    .. attribute:: field_type_string

       A string describing (and derived from) the field type.

    .. attribute:: fill_color

       A list of up to 4 floats defining the field's background color.

    .. attribute:: button_caption

       The caption string of a button-type field.

    .. attribute:: is_signed

       A bool indicating the status of a signature field, else *None*.

    .. attribute:: rect

       The rectangle containing the field.

    .. attribute:: text_color

       A list of **1, 3 or 4 floats** defining the text color. Default value is black (`[0, 0, 0]`).

    .. attribute:: text_font

       A string defining the font to be used. Default and replacement for invalid values is *"Helv"*. For valid font reference names see the table below.

    .. attribute:: text_fontsize

       A float defining the text fontsize. Default value is zero, which causes PDF viewer software to dynamically choose a size suitable for the annotation's rectangle and text amount.

    .. attribute:: text_maxlen

       An integer defining the maximum number of text characters. PDF viewers will (should) not accept a longer text.

    .. attribute:: text_type

       An integer defining acceptable text types (e.g. numeric, date, time, etc.). For reference only for the time being -- will be ignored when creating or updating widgets.

    .. attribute:: xref

       An integer defining the PDF cross reference number of the widget.


Standard Fonts for Widgets
----------------------------------
Widgets use their own resources object */DR*. A widget resources object must at least contain a */Font* object. Widget fonts are independent from page fonts. We currently support the 14 PDF base fonts using the following fixed reference names, or any name of an already existing field font. When specifying a text font for new or changed widgets, **either** choose one in the first table column (upper and lower case supported), **or** one of the already existing form fonts. In the latter case, spelling must exactly match.

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

You are generally free to use any font for every widget. However, we recommend using *ZaDb* ("ZapfDingbats") and fontsize 0 for check boxes: typical viewers will put a correctly sized tickmark in the field's rectangle, when it is clicked.
