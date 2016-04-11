wxTableExtract.py Help
=======================
A script based on wxPython and PyMuPDF to browse a document and extract tables. It uses the method ``ParseTab`` contained in the same directory.

How it works
-------------
The script will at first present a file selection dialog to pick a document.

Then the document's first page will be displayed in another dialog. A number of controls at the dialog's top and left exist to do several things as follows. Controls' availabilities are dependent on the situation. E.g. you can only add a column after a rectangle has been painted, etc.

* You can browse forward and backward in the document using either the designated buttons or (since 2016-04-11) the mouse wheel.
* You can jump to a specific page.
* You can paint a rectangle on a displayed page using the ``New Rect`` button. You can fine tune your selection by using the spin controls. Now (2016-04-11), moving the rectangle around with the mouse is also supported.
* Pressing the ``New Rect`` button again will destroy any existing rectangle and columns. The same is true if you leave the page.
* After a rectangle has been painted, you can paint on or more columns into it via button ``New Col``. They are shown as vertical lines within the rectangle. You can correct your doing by selecting a column by the choice box and then changing its coordinate in the spin control. A column can be deleted by entering a "0" there, or by changing its value to something outside the rectangle's left / right borders.
* You can change a rectangle via the spin controls also after columns have been painted. Columns will not be affected in any way by this. However, if this causes a column to leave the rectangle area, it will be deleted. In contrast, if a rectangle is moved with the mouse (hold down left key), **columns will be moved together with it** and not be deleted.
* Any time after a rectangle has been painted, you can parse its text by pressing button ``Get Table``. The current script just prints the table to STDOUT if you do this - see the included example screens. You can also add / delete columns and repeatedly press this button to evaluate any differences.
