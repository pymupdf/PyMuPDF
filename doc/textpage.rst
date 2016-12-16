.. raw:: pdf

    PageBreak

.. _TextPage:

================
TextPage
================

``TextPage`` represents the text of a page.

============================== ==============================================
**Method**                     **Short Description**
============================== ==============================================
:meth:`TextPage.extractText`   Extract the page's plain text
:meth:`TextPage.extractHTML`   Extract the page's text in HTML format
:meth:`TextPage.extractJSON`   Extract the page's text in JSON format
:meth:`TextPage.extractXML`    Extract the page's text in XML format
:meth:`TextPage.search`        Search for a string in the page
============================== ==============================================

**Class API**

.. class:: TextPage

   .. method:: extractText()

      Extract the text from a ``TextPage`` object. Returns a string of the page's complete text. No attempt is being made to adhere to a natural reading sequence: the text is returned UTF-8 encoded and in the same sequence as the PDF creator specified it. If this looks awkward for your PDF file, consider using program that re-arranges the text according to a more familiar layout, e.g. ``PDF2TextJS.py`` in the examples directory.

      :rtype: string

   .. method:: extractHTML()

      Extract the text from a ``TextPage`` object in HTML format. This version contains some more formatting information about how the text is being dislayed on the page. See the tutorial chapter for an example.

      :rtype: string

   .. method:: extractJSON()

      Extract the text from a ``TextPage`` object in JSON format. This version contains significantly more formatting information about how the text is being dislayed on the page. It is almost as complete as the ``extractXML`` version, except that positioning information is detailed down to the span level, not to a single character. See the tutorial chapter for an example. To process the returned JSON text use one of the json modules like ``json``, ``simplejson``, ``ujson``, ``cjson``, etc. See example program ``PDF2TextJS.py`` for how to do that.

      :rtype: string

   .. method:: extractXML()

      Extract the text from a ``TextPage`` object in XML format. This contains complete formatting information about every single text character on the page: font, size, line, paragraph, location, etc. This may easily reach several hundred kilobytes of uncompressed data for a text oriented page. See the tutorial chapter for an example.

      :rtype: string

   .. method:: search(string, hit_max = 16)

      Search for the string ``string``.

      :param `string`: The string to search for.
      :type `string`: string

      :param `hit_max`: Maximum number of expected hits (default 16).
      :type `hit_max`: int

      :rtype: list
      :returns: A python list. If not empty, each element of the list is a :ref:`Rect` (without transformation) surrounding a found ``string`` occurrence.

   .. note:: All of the above can be achieved by using the appropriate :meth:`Document.getPageText`, :meth:`Page.getText` and :meth:`Page.searchFor` methods.