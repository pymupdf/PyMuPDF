PDFLinkMaint.py Help
=======================
A script based on wxPython and PyMuPDF to maintain links contained in a PDF document.

How it works
-------------
The script will at first present a file selection dialog to pick a PDF.

Then the document's first page will be displayed in another dialog. A number of controls at the dialog's top and left exist to do several things as follows. Availability of controls depends on the type of the link.

* You can browse forward and backward in the document by using either the designated buttons or the mouse wheel.
* You can jump to a specific page by entering a value in the field and pressing enter.
* For each displayed page, its links will be shown by a surrounding blue rectangle, the link's "hot spot". Hovering the mouse over one of them will display basic destination information. Clicking on the rectangle will display link details on the left and the rectangle color will change from blue to red.
* Enabled link details can be directly changed.
* Clicking the `new` button on the left allows to paint a new rectangle on the page image - with standard link details. Afterwards this new link can be edited like any other link (i.e. by selecting it with a click).
* In order to change a link's hot spot, move it around with pressed down left mouse button, or change its shape by moving the bottom right corner with the mouse. For fine control you can also directly change values in the `hot spot` section.
* After painting a hot spot, click on it and start changing the link attributes. If link types `GoToR`, `Launch` or `URI` are selected, the text within the hot spot will be offered in the `File` or `URI` fields, respectively, and can then be changed as required.
* In order to delete a link, set its link type to `NONE`. It will remain available for further modification until you press the `update` button.
* In order to fix any changes made to links on a page, the button `update` must be pressed. Paging away without this, will discard changes made so far. This will not make changes to the underlying file.
* In order to permanently save changes to disk, press the `save` button. This will display a FileSave dialog.