wxTableExtract.py Help
=======================
A script based on wxPython and PyMuPDF to browse a document and extract tables. It uses the method ``ParseTab`` contained inthe same directory.

How it works
-------------
The script will at first present a file selection dialog to pick the requested document.

Then the document's first page will displayed in a dialog. A number of controls at the dialog's top and left are available to do several things as follows. Controls' availability is dependent on the situation. E.g. you can only add a column with ``New Col`` after a rectangle has been painted, etc.

* You can browse forward and backward in the file.
* You can jump to a specific page.
* You can paint a rectangle on a page' displayed image using the ``Rect`` button. You can correct your selection by using the spin controls. Pressing the ``Rect`` button again, any previous rectangle and associated columns will be destroyed. The same is true if you leave the page, e.g. by browsing through the document.
* After a rectangle has been painted, you can paint columns on the picture by button ``New Col``. Columns are shown as vertical lines within the rectangle. You can correct your selection by the respective spin control. Several columns can be painted. They can be selected using the choice box. A columns can be deleted by entering a "0" in the spin control (after having selected it via the choice box) or by changing its value to something outside the rectangle's left / right border.
* You can change a rectangle via its 4 spin controls also after columns have been defined. Columns will not be affected in any way if you shrink / stretch / relocate the rectangle. However, if a column goes outside the rectangle area, it will be deleted.
* Anytime after a rectangle has been painted, you can parse its contained text by pressing button ``Get Table``. The current script just prints the table if you do this - see the included screen prints.
