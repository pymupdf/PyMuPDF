.. include:: header.rst

.. _Appendix4:

================================================
Appendix 4: Performance Comparison Methodology
================================================

This article documents the approach to measure :title:`PyMuPDF's` performance and the tools and example files used to do comparisons.

The following three sections deal with different performance aspects:

* :ref:`Document Copying<app4_copying>` - This includes opening and parsing :title:`PDFs`, then writing them to an output file. Because the same basic activities are also used for joining (merging) :title:`PDFs`, the results also apply to these use cases.
* :ref:`Text Extraction<app4_text_extraction>` - This extracts plain text from :title:`PDFs` and writes it to an output text file.
* :ref:`Page Rendering<app4_page_rendering>` - This converts :title:`PDF` pages to image files looking identical to the pages. This ability is the basic prerequisite for using a tool in :title:`Python GUI` scripts to scroll through documents. We have chosen a medium-quality (resolution 150 DPI) version.

Please note that in all cases the actual speed in dealing with :title:`PDF` structures is not directly measured: instead, the timings also include the durations of writing files to the operating system's file system. This cannot be avoided because tools other than :title:`PyMuPDF` do not offer the option to e.g., separate the image **creation** step from the following step, which **writes** the image into a file.

So all timings documented include a common, OS-oriented base effort. Therefore, performance **differences per tool are actually larger** than the numbers suggest.


Files used
------------

Here is the list of example files. Each file name is accompanied by further information: **size** in bytes, number of **pages**, number of bookmarks (**Table of Contents** entries), number of **links**, **KB** size per page. The latter is an indicator for whether a file is text or graphics oriented.


.. list-table::
   :header-rows: 1

   * - **Name**
     - **Size (bytes)**
     - **Pages**
     - **TOC size**
     - **Links**
     - **KB/page**
     - **Remarks**
   * - Adobe.pdf
     - 32.472.771
     - 1.310
     - 794
     - 32.096
     - 24
     - linearized, many links / bookmarks
   * - Evolution.pdf
     - 13.497.490
     - 75
     - 15
     - 118
     - 176
     - graphics oriented
   * - PyMuPDF.pdf
     - 479.011
     - 47
     - 60
     - 491
     - 10
     - text oriented, many links
   * - sdw_2015_01.pdf
     - 14.668.972
     - 100
     - 36
     - 0
     - 143
     - graphics oriented
   * - sdw_2015_02.pdf
     - 13.295.864
     - 100
     - 38
     - 0
     - 130
     - graphics oriented
   * - sdw_2015_03.pdf
     - 21.224.417
     - 108
     - 35
     - 0
     - 192
     - graphics oriented
   * - sdw_2015_04.pdf
     - 15.242.911
     - 108
     - 37
     - 0
     - 138
     - graphics oriented
   * - sdw_2015_05.pdf
     - 16.495.887
     - 108
     - 43
     - 0
     - 149
     - graphics oriented
   * - sdw_2015_06.pdf
     - 23.447.046
     - 100
     - 38
     - 0
     - 229
     - graphics oriented
   * - sdw_2015_07.pdf
     - 14.106.982
     - 100
     - 38
     - 2
     - 138
     - graphics oriented
   * - sdw_2015_08.pdf
     - 12.321.995
     - 100
     - 37
     - 0
     - 120
     - graphics oriented
   * - sdw_2015_09.pdf
     - 23.409.625
     - 100
     - 37
     - 0
     - 229
     - graphics oriented
   * - sdw_2015_10.pdf
     - 18.706.394
     - 100
     - 24
     - 0
     - 183
     - graphics oriented
   * - sdw_2015_11.pdf
     - 25.624.266
     - 100
     - 20
     - 0
     - 250
     - graphics oriented
   * - sdw_2015_12.pdf
     - 19.111.666
     - 108
     - 36
     - 0
     - 173
     - graphics oriented





.. note::

     **Adobe.pdf** and **PyMuPDF.pdf** are clearly text oriented, all other files are graphics oriented.


Tools used
-------------

In each section, the same fixed set of PDF files is being processed by a set of tools. The set of tools used per performance aspect however varies, depending on the supported tool features.

All tools are either platform independent, or at least can run on both, :title:`Windows` and :title:`Unix` / :title:`Linux` (:title:`PDFtk`).


.. list-table::
   :header-rows: 1

   * - **Tool**
     - **Description**
   * - :title:`PyMuPDF`
     - tool of this manual
   * - PDFrw_
     - a pure Python tool, being used by rst2pdf, has interface to ReportLab
   * - PyPDF2_
     - a pure Python tool with a large function set
   * - PDFMiner_
     - a pure Python to extract text and other data from PDF
   * - PDFtk_
     - a command line utility with numerous functions
   * - XPDF_
     - a command line utility with multiple functions
   * - PikePDF_
     - a Python package similar to pdfrw, but based on C++ library QPDF
   * - PDF2JPG_
     - a Python package specialized on rendering PDF pages to JPG images



.. _app4_copying:


Copying / Joining / Merging
----------------------------------

How fast is a :title:`PDF` file read and its content parsed for further processing? The sheer parsing performance cannot directly be compared, because batch utilities always execute a requested task completely, in one go, front to end. :title:`PDFrw` too, has a *lazy* strategy for parsing, meaning it only parses those parts of a document that are required in any moment.

To yet find an answer to the question, we therefore measure the time to copy a :title:`PDF` file to an output file with each tool, and do nothing else.

These are the commands for how each tool was used:

:title:`PyMuPDF`

.. code-block:: python

    import fitz
    doc = fitz.open("input.pdf")
    doc.save("output.pdf")

:title:`PDFrw`


.. code-block:: python

    doc = PdfReader("input.pdf")
    writer = PdfWriter()
    writer.trailer = doc
    writer.write("output.pdf")

:title:`PyPDF2`

.. code-block:: python

    pdfmerge = PyPDF2.PdfMerger()
    pdfmerge.append("input.pdf")
    pdfmerge.write("output.pdf")
    pdfmerge.close()

:title:`PikePDF`

.. code-block:: python

    from pikepdf import Pdf
    doc = Pdf.open("input.pdf")
    doc.save("output.pdf")


:title:`PDFtk`

.. code-block:: python

    pdftk input.pdf output output.pdf


**Observations**

These are our run time findings in **seconds**:



.. list-table::
   :header-rows: 1

   * - **Name**
     - **PyMuPDF**
     - **PDFrw**
     - **PikePDF**
     - **PDFtk**
     - **PyPDF2**
   * - Adobe.pdf
     - 1.76
     - 5.89
     - 22.76
     - 65.89
     - 400.64
   * - Evolution.pdf
     - 0.17
     - 0.08
     - 1.48
     - 0.56
     - 0.57
   * - PyMuPDF.pdf
     - 0.02
     - 0.05
     - 0.16
     - 0.45
     - 0.52
   * - sdw_2015_01.pdf
     - 0.09
     - 0.39
     - 1.37
     - 2.91
     - 3.07
   * - sdw_2015_02.pdf
     - 0.10
     - 0.44
     - 1.49
     - 3.69
     - 5.43
   * - sdw_2015_03.pdf
     - 0.17
     - 0.80
     - 3.34
     - 6.47
     - 7.27
   * - sdw_2015_04.pdf
     - 0.11
     - 0.43
     - 1.00
     - 4.18
     - 4.59
   * - sdw_2015_05.pdf
     - 0.22
     - 0.52
     - 1.74
     - 4.19
     - 4.61
   * - sdw_2015_06.pdf
     - 0.20
     - 0.92
     - 4.24
     - 7.75
     - 9.01
   * - sdw_2015_07.pdf
     - 0.14
     - 0.65
     - 2.08
     - 5.07
     - 5.88
   * - sdw_2015_08.pdf
     - 0.13
     - 0.54
     - 1.92
     - 4.64
     - 5.39
   * - sdw_2015_09.pdf
     - 0.16
     - 0.69
     - 3.66
     - 5.46
     - 6.38
   * - sdw_2015_10.pdf
     - 0.12
     - 0.53
     - 2.13
     - 1.57
     - 3.46
   * - sdw_2015_11.pdf
     - 0.60
     - 5.14
     - 7.62
     - 19.78
     - 30.40
   * - sdw_2015_12.pdf
     - 0.16
     - 0.70
     - 2.25
     - 5.01
     - 5.42
   * - **Total**
     - **4.15**
     - **17.77**
     - **57.24**
     - **137.62**
     - **492.64**





:title:`PyMuPDF` is by far the fastest: on average 4.3 times faster than the second best (pure :title:`Python` :title:`PDFrw`), and 118 times faster than the by far slowest (:title:`PyPDF2`).

In other words, where :title:`PyMuPDF` needs a minute, :title:`PyPDF2` would need **almost two hours**.


.. _app4_text_extraction:

Text Extraction
----------------------------------

The following table shows plain text extraction durations. All tools have been used with their most basic, fanciless functionality - no layout re-arrangements, etc.


.. list-table::
   :header-rows: 1

   * - **Name**
     - **PyMuPDF**
     - **XPDF**
     - **PyPDF2**
     - **PDFMiner**
   * - Adobe.pdf
     - 1.84
     - 6.26
     - 25.25
     - 48.43
   * - Evolution.pdf
     - 0.08
     - 0.26
     - 1.20
     - 2.65
   * - PyMuPDF.pdf
     - 0.03
     - 0.10
     - 0.40
     - 1.17
   * - sdw_2015_01.pdf
     - 0.33
     - 0.72
     - 3.99
     - 9.79
   * - sdw_2015_02.pdf
     - 0.40
     - 0.78
     - 4.28
     - 9.47
   * - sdw_2015_03.pdf
     - 0.80
     - 1.34
     - 14.75
     - 25.06
   * - sdw_2015_04.pdf
     - 0.45
     - 0.93
     - 7.59
     - 14.85
   * - sdw_2015_05.pdf
     - 0.37
     - 0.75
     - 4.34
     - 9.09
   * - sdw_2015_06.pdf
     - 0.74
     - 1.29
     - 13.65
     - 28.95
   * - sdw_2015_07.pdf
     - 0.37
     - 0.83
     - 5.03
     - 10.10
   * - sdw_2015_08.pdf
     - 0.40
     - 0.78
     - 4.24
     - 9.07
   * - sdw_2015_09.pdf
     - 0.79
     - 1.37
     - 16.12
     - 26.96
   * - sdw_2015_10.pdf
     - 0.42
     - 0.86
     - 7.15
     - 12.80
   * - sdw_2015_11.pdf
     - 1.00
     - 1.63
     - 12.93
     - 25.39
   * - sdw_2015_12.pdf
     - 0.40
     - 0.87
     - 6.15
     - 12.14
   * - **Total**
     - **8.42**
     - **18.77**
     - **127.07**
     - **245.92**



:title:`PyMuPDF` is the fastest around. Setting its total duration of 9 seconds to 1, the relationships are:


.. list-table::
   :header-rows: 1

   * - **Tool**
     - **to PyMuPDF**
   * - :title:`PyMuPDF`
     - 1
   * - :title:`XPDF`
     - 2.2
   * - :title:`PyPDF2`
     - 15.0
   * - :title:`PDFMiner`
     - 29.2



.. _app4_page_rendering:

Page Rendering
--------------------------

We have tested rendering speed of :title:`PyMuPDF` against :title:`XPDF`  and :title:`pdf2jpg`.


These are the commands for how each tool was used:


:title:`PyMuPDF`

.. code-block:: python

    def ProcessFile(datei):
    print "processing:", datei
    doc=fitz.open(datei)
    for p in fitz.Pages(doc):
        pix = p.get_pixmap(dpi=150)
        pix.save("t-%s.png" % p.number)
        pix = None
    doc.close()
    return


:title:`PDF2JPG`

.. code-block:: python

    def ProcessFile(datei):
        print("processing:", datei)
        pdf2jpg.convert_pdf2jpg(datei, "images", pages="ALL", dpi=150)
        return


:title:`XPDF`

.. code-block:: python

    pdftopng.exe -r 150 file.pdf ./


These are the resulting runtimes:


.. list-table::
   :header-rows: 1

   * - **Name**
     - **PyMuPDF**
     - **PDF2JPG**
     - **XPDF**
   * - Adobe.pdf
     - 51.97
     - 70.94
     - 89.29
   * - Evolution.pdf
     - 13.78
     - 19.28
     - 27.06
   * - PyMuPDF.pdf
     - 2.40
     - 4.13
     - 3.52
   * - sdw_2015_01.pdf
     - 11.22
     - 17.83
     - 19.20
   * - sdw_2015_02.pdf
     - 10.54
     - 18.84
     - 17.61
   * - sdw_2015_03.pdf
     - 11.60
     - 21.10
     - 20.20
   * - sdw_2015_04.pdf
     - 10.78
     - 16.62
     - 18.70
   * - sdw_2015_05.pdf
     - 10.99
     - 18.01
     - 19.15
   * - sdw_2015_06.pdf
     - 10.88
     - 20.50
     - 19.77
   * - sdw_2015_07.pdf
     - 11.21
     - 18.32
     - 19.38
   * - sdw_2015_08.pdf
     - 10.56
     - 18.05
     - 18.88
   * - sdw_2015_09.pdf
     - 12.92
     - 20.83
     - 20.76
   * - sdw_2015_10.pdf
     - 10.55
     - 15.89
     - 18.45
   * - sdw_2015_11.pdf
     - 11.63
     - 24.64
     - 19.84
   * - sdw_2015_12.pdf
     - 11.62
     - 22.80
     - 19.04
   * - **Total**
     - **202.65**
     - **327.78**
     - **350.85**


At a resolution of 150 DPI, :title:`PDF2JPG` and :title:`XPDF` are both about 1.62 and 1.73, respectively, times slower than :title:`PyMuPDF`.




.. include:: footer.rst


.. External links

.. _PDFrw : https://pypi.org/project/pdfrw/
.. _PyPDF2 : https://pypi.org/project/pypdf/
.. _PDFMiner : https://pypi.org/project/pdfminer.six/
.. _PDFtk : https://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/
.. _XPDF : https://www.xpdfreader.com/
.. _PikePDF : https://pypi.org/search/?q=pikepdf
.. _PDF2JPG : https://pypi.org/project/pdf2jpg/

