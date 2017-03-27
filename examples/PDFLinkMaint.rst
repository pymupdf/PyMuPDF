PDFLinkMaint.py Help
=======================
A script based on wxPython and PyMuPDF to maintain links contained in a PDF document.

How it works
-------------
The script will at first present a file selection dialog to pick a PDF.

Then the document's first page will be displayed in another dialog. A number of controls at the dialog's top and left exist to do several things as follows. Availability of controls depends on the type of the link.

* You can browse forward and backward in the document using either the designated buttons or the mouse wheel.
* You can jump to a specific page.
* For each displayed page, its links will be shown by a surrounding blue rectangle, the link's "hot spot". Hovering the mouse on one of them will display basic destination information. Clicking on the rectangle will display link details on the left. The rectangle color will change from blue to red.
* Enabled link details can be directly changed.
* Clicking the "new" button on the left allows to paint a new rectangle on the page image - with standard link details. Afterwards this new link can be edited like any other link.
* In order to change a link's rectangle, move it around with a pressed down left mouse button, or change its shape by positioning the mouse over the bottom right corner and then move the mouse with a pressed down left button. For fine control you can also directly change value in the "hot spot" section.
* In order to fix any changes to a page's links, the button "update" must be pressed. Paging away without this, will discard changes made so far.
* In order to permanently save changes to disk, press the "save" button. This will display a FileSave dialog.