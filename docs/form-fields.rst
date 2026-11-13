.. include:: header.rst

.. _FormFields:

================
FormFields
================

|pdf_only_class|

This class represents an integrated synopsis of all form fields and widgets in a Form PDF. It should be created by executing :meth:`Document.get_form_fields`.

============================================= ==============================================================================
**Method / Attribute**                        **Short Description**
============================================= ==============================================================================
:meth:`FormFields.field_info`                 Retrieve detailed information about a form field
:meth:`FormFields.field_names`                List of all of field node names in the PDF
:meth:`FormFields.list_valid_terminal_fields` List of all valid, terminal form fields in the PDF
:meth:`FormFields.set_value`                  Set the value of a form field
:meth:`FormFields.to_csv`                     Export form fields to CSV
:meth:`FormFields.from_csv`                   Import form field values from a CSV file
:meth:`FormFields.to_dicts`                   Export form fields to a list of Python dictionaries
:meth:`FormFields.from_dicts`                 Import form field values from a list of Python dictionaries
:meth:`FormFields.to_json`                    Export form fields to JSON
:meth:`FormFields.from_json`                  Import form field values from a JSON string
:meth:`FormFields.to_pandas`                  Export form fields to a Pandas DataFrame
:meth:`FormFields.repair_field_widget`        Convert a |field-widget| to parent-child format
:meth:`FormFields.repair_flat_rbg`            Convert a |flat RBG| to parent-child format
:meth:`FormFields.repair_flat_field`          Convert a flat form field to parent-child format
:meth:`FormFields.refresh`                    Update the ``FormFields`` object
:attr:`FormFields.doc`                        Reference to the owning document
:attr:`FormFields.fields`                     Dictionary of all form fields in the PDF
:attr:`FormFields.pdfdoc`                     Reference to the underlying (`mupdf`) PDF document
:attr:`FormFields.widgets`                    List of all widget annotations in the PDF
:attr:`FormFields.page_xrefs`                 Dictionary of page xrefs that contain widgets
:attr:`FormFields.template_xrefs`             List of page template xrefs in the PDF
:attr:`FormFields.count_field_widgets`        Number of field-widgets
:attr:`FormFields.count_flat_rbgs`            Number of flat RBGs
:attr:`FormFields.count_flat_fields`          Number of flat form fields
============================================= ==============================================================================


**Class API**

.. class:: FormFields

   .. method:: __init__(repair=False)

      Create a ``FormFields`` object. The only way to obtain this object is by executing :meth:`Document.get_form_fields`.
      The method will scan all PDF page objects for locating widget annotations and also inspect the `/AcroForm` PDF dictionary for form field definitions. It then integrates this information to provide a comprehensive overview of all form fields and their associated widgets. Structure problems which frequently occur in PDF forms are detected and repaired automatically if the ``repair`` parameter is set to ``True``.

   .. attribute:: fields

      The dictionary of all form fields in the PDF. Key is the form field name, and value is a comprehensive description of the form field, including its associated widgets and properties.

   .. attribute:: widgets

      List of all widget annotations in the PDF -- independent of their presence on any page. Each widget annotation is represented as a stripped-down :doc:`widget` object.

   .. attribute:: page_xrefs

      Dictionary of page xrefs that contain widgets. Key is the page xref, and value is the number of the page.

   .. attribute:: template_xrefs

      List of page template xrefs in the PDF. A template is actually a reusable page structure that can be referenced multiple times within the document. Its PDF ``/Type`` is ``/Template``, otherwise its structure is fully compatible with the page dictionary definitions. It is used for providing a page template when a variable number of additional pages (with form fields) is needed. Form fields on template pages are treated similarly to those on regular pages, but usually do not contain any field values. We record such fields but do not support changing their field values.

   .. attribute:: count_flat_rbgs

      The number of flat |RBGs| [#f1]_ found in the PDF.

   .. attribute:: count_flat_fields

      The number of flat form fields [#f2]_ found in the PDF.

   .. attribute:: count_field_widgets

      The number of field-widgets [#f3]_ found in the PDF.

   .. method:: field_names()

      Retrieve a list of all form field names in the PDF.

      **Examples:**

      .. code-block:: python

         pprint(formfields.field_names())
         [
         'Person',
         'Person.Address',
         'Person.Address.City',
         'Person.Address.Street',
         'Person.MaritalStatus',
         'Person.Name',
         'Person.Name.First',
         'Person.Name.Last',
         'Person.WordOfMouth'
         ]

      This PDF contains a hierarchical structure of form fields, where some fields are parents of other fields.
      All names containing a dot like ``Person.Address`` indicate a hierarchical relationship, where ``Person`` is the parent field and ``Address`` is its child.
      Fields without a dot in their name are top-level fields, while fields with one or more dots are nested under their respective parent fields.
      Top-level fields are root fields. This PDF has only one of them.
      Only fields whose name is not equal to the first part of another field's name are considered **terminal** fields and will own a widget annotation as child elements.
      In our example, ``Person.Address.City`` is a terminal field because no other field starts with ``Person.Address.City``.


   .. method:: field_info(name)

      Retrieve detailed information about a form field by its name. Returns a dictionary containing the form field's properties and associated widgets.

      **Examples:**

      .. code-block:: python

         pprint(formfields.field_info("Person"))
         {'name': 'Person',
         'value': '',
         'pages': [],
         'xref': 11,
         'terminal': False,
         'widgets': [],
         'type': None,
         'format': None,
         'choices': None,
         'diagnosis': {'ok': True, 'problems': [], 'widget_reports': []}}

      This field does not occur on any page, it carries no type information and owns no widgets. The reason is, that it is a parent of yet other field nodes, as indicated by ``terminal=False``.
      Let us now examine a **terminal** field like ``Person.Address.City`` to see the difference.

      .. code-block:: python

         pprint(formfields.field_info("Person.Address.City"))
         {'name': 'Person.Address.City',
         'value': 'Lakeside',
         'pages': [0],
         'xref': 26,
         'terminal': True,
         'widgets': [Widget:(field_type=text script=None)],
         'type': 'text',
         'format': 'string',
         'choices': None,
         'diagnosis': {'ok': True},
         'is_widget': False}

      This terminal field is represented by a widget annotation on page 0, and has a value of ``"Lakeside"``. The ``terminal`` key is ``True``, indicating that it is a terminal field.
      The value ``is_widget`` is ``False``, indicating that its widget is a separate object (the recommended standard case).

   .. method:: list_valid_terminal_fields()

      Retrieve a list of all form fields in the PDF whose field values can be changed.

      **Examples:**

      .. code-block:: python

         pprint(formfields.list_valid_terminal_fields())
         [{'name': 'Person.Name.First',
         'type': 'text',
         'format': 'string',
         'choices': None,
         'value': 'John',
         'widgets': 1,
         'is_widget': False},
         ...
         {'name': 'Person.MaritalStatus',
         'type': 'radio',
         'format': 'string',
         'choices': ['married', 'single'],
         'value': 'married',
         'widgets': 2,
         'is_widget': False}]

      As expected, only terminal fields will occur in this list, since only they have editable values.
      The last field is of special interest because it is a radio button group, which typically -- as in this case -- has multiple widgets associated with it. We see that there are 2 widgets for this field, as indicated by the ``widgets`` key. Possible values are listed under the ``choices`` key. Of the two options, ``married`` is currently selected, as indicated by the ``value`` key.
      Further down we will explore how to interact with these editable fields programmatically, including reading their values and updating them as needed.

   .. method:: set_value(field_name, value)

      Set the value of an editable form field identified by its name.

      :arg field_name: The name of the editable form field whose value is to be set.
      :arg value: The new value to assign to the specified form field. This should be compatible with the field's type and format and be one of the "choices" if applicable.

      **Example:**

      .. code-block:: python

         formfields.set_value("Person.MaritalStatus", "single")

   .. method:: to_csv(file=None)
   .. method:: to_json(file=None)
   .. method:: to_dicts()
   .. method:: to_pandas()

      Export all editable form fields in CSV / JSON string format or to a file if a file path is provided. When using the `to_pandas` method, a DataFrame is returned instead of writing to a file. Pandas must be installed to use the `to_pandas` method. Method ``to_dicts()`` returns a list of dictionaries representing the editable form fields.

      :arg file: (optional) The path to the CSV / JSON file where the form fields will be exported. If omitted, the method returns a string.

      :returns: A string in CSV/JSON format if no file path is provided. If pandas output was chosen, a DataFrame is returned. A list of dictionaries is returned by ``to_dicts()``.

      **Example:**

      .. code-block:: python

         df = formfields.to_pandas()
         print(df.to_string(index=False))
                         field     type  format        choices    current_value  new_value
             Person.Name.First     text  string            NaN             John        NaN
              Person.Name.Last     text  string            NaN              Doe        NaN
         Person.Address.Street     text  string            NaN 123 Birch Street        NaN
           Person.Address.City     text  string            NaN         Lakeside        NaN
            Person.WordOfMouth checkbox boolean            NaN              Yes        NaN
          Person.MaritalStatus    radio  string married|single           single        NaN

   .. method:: from_csv(filepath)
   .. method:: from_json(json_string)
   .. method:: from_dicts(dicts)

      Update field values either from a CSV file, a JSON string, or a list of dictionaries.

      The format is expected to match the structure produced by the corresponding export methods.
      These methods are ideal for updating form field values in bulk.

   .. method:: refresh()

      Refresh the form fields object by reparsing the PDF document for any changes to the form fields.
      Execute this whenever the underlying PDF document has been modified.

      Modifications include, but are not limited to:

      * adding or deleting widgets
      * changing the structure of the PDF like deleting or inserting pages
      * executing methods :meth:`repair_flat_rbg` or :meth:`repair_field_widget`.

      It is of course always possible to simply create a new :class:`FormFields` object from the PDF document to get the latest state. Both ways, executing this method or creating a new object, are very fast and typically require less than 0.1 seconds -- even for PDFs with many fields.

   .. method:: repair_flat_rbg(field_name)

      Repair a **flat** |RBG| [#f1]_. This method modifies the internal structure of the PDF to ensure that the RBG is represented with a parent field and child widgets.

      If this ``FormFields`` object was created using `repair=True` any flat RBGs will already have been repaired.

      Execute :meth:`FormFields.refresh` after calling this method to ensure that the model is up-to-date.

      :returns: ``True`` if the repair was successful, ``False`` otherwise.

   .. method:: repair_flat_field(field_name)

      Repair a **flat** form field [#f2]_. This method modifies the internal structure of the PDF to ensure that a flat form field is represented with a parent field and child widgets, adhering to the standard PDF form field hierarchy.

      If this ``FormFields`` object was created using `repair=True` any flat fields will already have been repaired.

      Execute :meth:`FormFields.refresh` after calling this method to ensure that the model is up-to-date.

      :returns: ``True`` if the repair was successful, ``False`` otherwise.

   .. method:: repair_field_widget(field_name)

      Repair an object that is a combination of a widget annotation and a form field ("field-widget") [#f3]_. This method splits the object into a parent dictionary object containing field information and a widget (annotation) dictionary object representing its visual appearance on the page. This changes the internal structure of the PDF and the representation of the field within the form fields model.

      If the ``FormFields`` object was created using `repair=True` any field-widgets will already have been repaired.

      Execute :meth:`FormFields.refresh` after calling this method to ensure that the model is up-to-date.

      :returns: ``True`` if the repair was successful, ``False``  otherwise.

.. rubric:: footnotes

.. [#f1] A |flat RBG| is one that does not have the standard parent-child hierarchy in the PDF structure, but instead is a collection of Radio Button widgets having the same name -- and no ``/Parent`` entry. The field dictionary object itself does not exist and is implicitly created by PDF viewers when needed.
.. [#f2] A flat form field is one that does not have the standard parent-child hierarchy in the PDF structure. It consists of a collection of widget annotations sharing the same name, but without a parent field dictionary. The field dictionary object itself does not exist and is implicitly created by PDF viewers when needed.
.. [#f3] A |field-widget| is an object that combines both the form field and its visual widget annotation into a single dictionary object. It has no ``/Parent`` and is referenced by both, the PDF catalog's ``/AcroForm(Fields`` array and the page's ``/Annots`` array. While this is legal as per the PDF specifications, it is explicitly discouraged to use this structure by ISO 32000-2:2020, section 12.7.2.