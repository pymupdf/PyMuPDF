.. include:: header.rst

.. _RecipesJournalling:

=========================================
Journalling
=========================================


Starting with version 1.19.0, journalling is possible when updating PDF documents.

Journalling is a logging mechanism which permits either **reverting** or **re-applying** changes to a PDF. Similar to LUWs "Logical Units of Work" in modern database systems, one can group a set of updates into an "operation". In MuPDF journalling, an operation plays the role of a LUW.

.. note:: In contrast to LUW implementations found in database systems, MuPDF journalling happens on a **per document level**. There is no support for simultaneous updates across multiple PDFs: one would have to establish one's own logic here.

* Journalling must be *enabled* via a document method. Journalling is possible for existing or new documents. Journalling **can be disabled only** by closing the file.
* Once enabled, every change must happen inside an *operation* -- otherwise an exception is raised. An operation is started and stopped via document methods. Updates happening between these two calls form an LUW and can thus collectively be rolled back or re-applied, or, in MuPDF terminology "undone" resp. "redone".
* At any point, the journalling status can be queried: whether journalling is active, how many operations have been recorded, whether "undo" or "redo" is possible, the current position inside the journal, etc.
* The journal can be **saved to** or **loaded from** a file. These are document methods.
* When loading a journal file, compatibility with the document is checked and journalling is automatically enabled upon success.
* For an **existing** PDF being journalled, a special new save method is available: :meth:`Document.save_snapshot`. This performs a special incremental save that includes all journalled updates so far. If its journal is saved at the same time (immediately after the document snapshot), then document and journal are in sync and can later on be used together to undo or redo operations or to continue journalled updates -- just as if there had been no interruption.
* The snapshot PDF is a valid PDF in every aspect and fully usable. If the document is however changed in any way without using its journal file, then a desynchronization will take place and the journal is rendered unusable.
* Snapshot files are structured like incremental updates. Nevertheless, the internal journalling logic requires, that saving **must happen to a new file**. So the user should develop a file naming convention to support recognizable relationships between an original PDF, like `original.pdf` and its snapshot sets, like `original-snap1.pdf` / `original-snap1.log`, `original-snap2.pdf` / `original-snap2.log`, etc.

Example Session 1
~~~~~~~~~~~~~~~~~~
Description:

* Make a new PDF and enable journalling. Then add a page and some text lines -- each as a separate operation.
* Navigate within the journal, undoing and redoing these updates and displaying status and file results::

    >>> import pymupdf
    >>> doc=pymupdf.open()
    >>> doc.journal_enable()

    >>> # try update without an operation:
    >>> page = doc.new_page()
    mupdf: No journalling operation started
    ... omitted lines
    RuntimeError: No journalling operation started

    >>> doc.journal_start_op("op1")
    >>> page = doc.new_page()
    >>> doc.journal_stop_op()

    >>> doc.journal_start_op("op2")
    >>> page.insert_text((100,100), "Line 1")
    >>> doc.journal_stop_op()

    >>> doc.journal_start_op("op3")
    >>> page.insert_text((100,120), "Line 2")
    >>> doc.journal_stop_op()

    >>> doc.journal_start_op("op4")
    >>> page.insert_text((100,140), "Line 3")
    >>> doc.journal_stop_op()

    >>> # show position in journal
    >>> doc.journal_position()
    (4, 4)
    >>> # 4 operations recorded - positioned at bottom
    >>> # what can we do?
    >>> doc.journal_can_do()
    {'undo': True, 'redo': False}
    >>> # currently only undos are possible. Print page content:
    >>> print(page.get_text())
    Line 1
    Line 2
    Line 3

    >>> # undo last insert:
    >>> doc.journal_undo()
    >>> # show combined status again:
    >>> doc.journal_position();doc.journal_can_do()
    (3, 4)
    {'undo': True, 'redo': True}
    >>> print(page.get_text())
    Line 1
    Line 2

    >>> # our position is now second to last
    >>> # last text insertion was reverted
    >>> # but we can redo / move forward as well:
    >>> doc.journal_redo()
    >>> # our combined status:
    >>> doc.journal_position();doc.journal_can_do()
    (4, 4)
    {'undo': True, 'redo': False}
    >>> print(page.get_text())
    Line 1
    Line 2
    Line 3
    >>> # line 3 has appeared again!


Example Session 2
~~~~~~~~~~~~~~~~~~
Description:

* Similar to previous, but after undoing some operations, we now add a different update. This will cause:

    - permanent removal of the undone journal entries
    - the new update operation will become the new last entry.


    >>> doc=pymupdf.open()
    >>> doc.journal_enable()
    >>> doc.journal_start_op("Page insert")
    >>> page=doc.new_page()
    >>> doc.journal_stop_op()
    >>> for i in range(5):
            doc.journal_start_op("insert-%i" % i)
            page.insert_text((100, 100 + 20*i), "text line %i" %i)
            doc.journal_stop_op()

    >>> # combined status info:
    >>> doc.journal_position();doc.journal_can_do()
    (6, 6)
    {'undo': True, 'redo': False}

    >>> for i in range(3):  # revert last three operations
            doc.journal_undo()
    >>> doc.journal_position();doc.journal_can_do()
    (3, 6)
    {'undo': True, 'redo': True}

    >>> # now do a different update:
    >>> doc.journal_start_op("Draw some line")
    >>> page.draw_line((100,150), (300,150))
    Point(300.0, 150.0)
    >>> doc.journal_stop_op()
    >>> doc.journal_position();doc.journal_can_do()
    (4, 4)
    {'undo': True, 'redo': False}

    >>> # this has changed the journal:
    >>> # previous last 3 text line operations were removed, and
    >>> # we have only 4 operations: drawing the line is the new last one

.. include:: footer.rst
