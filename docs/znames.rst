.. include:: header.rst

.. _Deprecated:

================
Deprecated Names
================

The original naming convention for methods and properties has been "camelCase". Since its creation around 2013, a tremendous increase of functionality has happened in PyMuPDF -- and with it a corresponding increase in classes, methods and properties. In too many cases, this has led to non-intuitive, illogical and ugly names, difficult to memorize or guess.

A few versions ago, I therefore decided to shift gears and switch to a "snake_cased" naming standard.
This was a major effort, which needed a step-wise approach. I think am done with it now (version 1.18.14).

The following list maps deprecated names to their new versions. For example, property `pageCount` became `page_count` in the :ref:`Document` class. There also are less obvious name changes, e.g. method `getPNGdata` was renamed to `tobytes` in the :ref:`Pixmap` class.

Names of classes (camel case) and package-wide constants (the majority is upper case) remain untouched.

Old names will remain available as deprecated aliases through MuPDF version 1.19.0 and **be removed** in the version that follows it - probably version 1.20.0, but this depends on upstream decisions (MuPDF).

Starting with version 1.19.0, we will issue deprecation warnings on `sys.stderr` like `Deprecation: 'newPage' removed from class 'Document' after v1.19.0 - use 'new_page'.` when aliased methods are being used. Using a deprecated property will not cause this type of warning.

Starting immediately, all deprecated objects (methods and properties) will show a copy of the original's docstring, **prefixed** with the deprecation message, for example::

    >>> print(pymupdf.Document.pageCount.__doc__)
    *** Deprecated and removed in version following 1.19.0 - use 'page_count'. ***
    Number of pages.
    >>> print(pymupdf.Document.newPage.__doc__)
    *** Deprecated and removed in version following 1.19.0 - use 'new_page'. ***
    Create and return a new page object.

        Args:
            pno: (int) insert before this page. Default: after last page.
            width: (float) page width in points. Default: 595 (ISO A4 width).
            height: (float) page height in points. Default 842 (ISO A4 height).
        Returns:
            A Page object.
        

There is a utility script `alias-changer.py <https://github.com/pymupdf/PyMuPDF-Utilities/tree/master/alias-changer.py>`_ which can be used to do mass-renames in your scripts. It accepts either a single file or a folder as argument. If a folder is supplied, all its Python files and those of its subfolders are changed. Optionally, backups of the scripts can be taken.


.. include:: footer.rst
