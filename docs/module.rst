.. include:: header.rst

.. _Module:

============================
Command line interface
============================

* New in version 1.16.8

PyMuPDF can also be used from the command line to perform utility functions. This feature should obsolete writing some of the most basic scripts.

Admittedly, there is some functional overlap with the MuPDF CLI `mutool`. On the other hand, PDF embedded files are no longer supported by MuPDF, so PyMuPDF is offering something unique here.

Invocation
-----------

The command-line interface can be invoked in two ways.

* Use the installed `pymupdf` command::

    pymupdf <command and parameters>

* Or use Python's `-m` switch with PyMuPDF's `pymupdf` module::

    python -m pymupdf <command and parameters>


.. highlight:: python

General remarks:

* Request help via `"-h"`, resp. command-specific help via `"command -h"`.
* Parameters may be abbreviated where this does not introduce ambiguities.
* Several commands support parameters `-pages` and `-xrefs`. They are intended for down-selection. Please note that:

    - **page numbers** for this utility must be given **1-based**.
    - valid :data:`xref` numbers start at 1.
    - Specify a comma-separated list of either *single* integers or integer *ranges*. A **range** is a pair of integers separated by one hyphen "-". Integers must not exceed the maximum page, resp. xref number. To specify that maximum, the symbolic variable "N" may be used. Integers or ranges may occur several times, in any sequence and may overlap. If in a range the first number is greater than the second one, the respective items will be processed in reversed order.

* How to use the module inside your script::

    >>> import pymupdf.__main__
    >>> cmd = "clean input.pdf output.pdf -pages 1,N".split()  # prepare command line
    >>> saved_parms = sys.argv[1:]  # save original command line
    >>> sys.argv[1:] = cmd  # store new command line
    >>> pymupdf.__main__.()  # execute module
    >>> sys.argv[1:] = saved_parms  # restore original command line

* Use the following 2-liner and compile it with `Nuitka <https://pypi.org/project/Nuitka/>`_ in standalone mode. This will give you a CLI executable with all the module's features, that can be used on all compatible platforms without Python, PyMuPDF or MuPDF being installed.

::

    from pymupdf.__main__ import main
    main()


Cleaning and Copying
----------------------

.. highlight:: text

This command will optimize the PDF and store the result in a new file. You can use it also for encryption, decryption and creating sub documents. It is mostly similar to the MuPDF command line utility *"mutool clean"*::

    pymupdf clean -h
    usage: pymupdf clean [-h] [-password PASSWORD]
                    [-encryption {keep,none,rc4-40,rc4-128,aes-128,aes-256}]
                    [-owner OWNER] [-user USER] [-garbage {0,1,2,3,4}]
                    [-compress] [-ascii] [-linear] [-permission PERMISSION]
                    [-sanitize] [-pretty] [-pages PAGES]
                    input output

    -------------- optimize PDF or create sub-PDF if pages given --------------

    positional arguments:
    input                 PDF filename
    output                output PDF filename

    optional arguments:
    -h, --help            show this help message and exit
    -password PASSWORD    password
    -encryption {keep,none,rc4-40,rc4-128,aes-128,aes-256}
                          encryption method
    -owner OWNER          owner password
    -user USER            user password
    -garbage {0,1,2,3,4}  garbage collection level
    -compress             compress (deflate) output
    -ascii                ASCII encode binary data
    -linear               format for fast web display
    -permission PERMISSION
                          integer with permission levels
    -sanitize             sanitize / clean contents
    -pretty               prettify PDF structure
    -pages PAGES          output selected pages, format: 1,5-7,50-N

If you specify "-pages", be aware that only page-related objects are copied, **no document-level items** like e.g. embedded files.

Please consult :meth:`Document.save` for the parameter meanings.


Extracting Fonts and Images
----------------------------
Extract fonts or images from selected PDF pages to a desired directory::

    pymupdf extract -h
    usage: pymupdf extract [-h] [-images] [-fonts] [-output OUTPUT] [-password PASSWORD]
                        [-pages PAGES]
                        input

    --------------------- extract images and fonts to disk --------------------

    positional arguments:
    input                 PDF filename

    optional arguments:
    -h, --help            show this help message and exit
    -images               extract images
    -fonts                extract fonts
    -output OUTPUT        output directory, defaults to current
    -password PASSWORD    password
    -pages PAGES          only consider these pages, format: 1,5-7,50-N

**Image filenames** are built according to the naming scheme: **"img-xref.ext"**, where "ext" is the extension associated with the image and "xref" the :data:`xref` of the image PDF object.

**Font filenames** consist of the fontname and the associated extension. Any spaces in the fontname are replaced with hyphens "-".

The output directory must already exist.

.. note:: Except for output directory creation, this feature is **functionally equivalent** to and obsoletes `this script <https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/examples/extract-images/extract-from-pages.py>`_.


Joining PDF Documents
-----------------------
To join several PDF files specify::

    pymupdf join -h
    usage: pymupdf join [-h] -output OUTPUT [input [input ...]]

    ---------------------------- join PDF documents ---------------------------

    positional arguments:
    input           input filenames

    optional arguments:
    -h, --help      show this help message and exit
    -output OUTPUT  output filename

    specify each input as 'filename[,password[,pages]]'


.. note::

    1. Each input must be entered as **"filename,password,pages"**. Password and pages are optional.
    2. The password entry **is required** if the "pages" entry is used. If the PDF needs no password, specify two commas.
    3. The **"pages"** format is the same as explained at the top of this section.
    4. Each input file is immediately closed after use. Therefore you can use one of them as output filename, and thus overwrite it.


Example: To join the following files

1. **file1.pdf:** all pages, back to front, no password
2. **file2.pdf:** last page, first page, password: "secret"
3. **file3.pdf:** pages 5 to last, no password

and store the result as **output.pdf** enter this command:

*pymupdf join -o output.pdf file1.pdf,,N-1 file2.pdf,secret,N,1 file3.pdf,,5-N*


Low Level Information
----------------------

Display PDF internal information. Again, there are similarities to *"mutool show"*::

    pymupdf show -h
    usage: pymupdf show [-h] [-password PASSWORD] [-catalog] [-trailer] [-metadata]
                    [-xrefs XREFS] [-pages PAGES]
                    input

    ------------------------- display PDF information -------------------------

    positional arguments:
    input               PDF filename

    optional arguments:
    -h, --help          show this help message and exit
    -password PASSWORD  password
    -catalog            show PDF catalog
    -trailer            show PDF trailer
    -metadata           show PDF metadata
    -xrefs XREFS        show selected objects, format: 1,5-7,N
    -pages PAGES        show selected pages, format: 1,5-7,50-N

Examples::

    pymupdf show x.pdf
    PDF is password protected

    pymupdf show x.pdf -pass hugo
    authentication unsuccessful

    pymupdf show x.pdf -pass jorjmckie
    authenticated as owner
    file 'x.pdf', pages: 1, objects: 19, 58 MB, PDF 1.4, encryption: Standard V5 R6 256-bit AES
    Document contains 15 embedded files.

    pymupdf show FDA-1572_508_R6_FINAL.pdf -tr -m
    'FDA-1572_508_R6_FINAL.pdf', pages: 2, objects: 1645, 1.4 MB, PDF 1.6, encryption: Standard V4 R4 128-bit AES
    document contains 740 root form fields and is signed

    ------------------------------- PDF metadata ------------------------------
           format: PDF 1.6
            title: FORM FDA 1572
           author: PSC Publishing Services
          subject: Statement of Investigator
         keywords: None
          creator: PScript5.dll Version 5.2.2
         producer: Acrobat Distiller 9.0.0 (Windows)
     creationDate: D:20130522104413-04'00'
          modDate: D:20190718154905-07'00'
       encryption: Standard V4 R4 128-bit AES

    ------------------------------- PDF trailer -------------------------------
    <<
    /DecodeParms <<
        /Columns 5
        /Predictor 12
    >>
    /Encrypt 1389 0 R
    /Filter /FlateDecode
    /ID [ <9252E9E39183F2A0B0C51BE557B8A8FC> <85227BE9B84B724E8F678E1529BA8351> ]
    /Index [ 1388 258 ]
    /Info 1387 0 R
    /Length 253
    /Prev 1510559
    /Root 1390 0 R
    /Size 1646
    /Type /XRef
    /W [ 1 3 1 ]
    >>

Embedded Files Commands
------------------------

The following commands deal with embedded files -- which is a feature completely removed from MuPDF after v1.14, and hence from all its command line tools.

Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Show the embedded file names (long or short format)::

    pymupdf embed-info -h
    usage: pymupdf embed-info [-h] [-name NAME] [-detail] [-password PASSWORD] input

    --------------------------- list embedded files ---------------------------

    positional arguments:
    input               PDF filename

    optional arguments:
    -h, --help          show this help message and exit
    -name NAME          if given, report only this one
    -detail             show detail information
    -password PASSWORD  password

Example::

    pymupdf embed-info some.pdf
    'some.pdf' contains the following 15 embedded files.

    20110813_180956_0002.jpg
    20110813_181009_0003.jpg
    20110813_181012_0004.jpg
    20110813_181131_0005.jpg
    20110813_181144_0006.jpg
    20110813_181306_0007.jpg
    20110813_181307_0008.jpg
    20110813_181314_0009.jpg
    20110813_181315_0010.jpg
    20110813_181324_0011.jpg
    20110813_181339_0012.jpg
    20110813_181913_0013.jpg
    insta-20110813_180944_0001.jpg
    markiert-20110813_180944_0001.jpg
    neue.datei

Detailed output would look like this per entry::

        name: neue.datei
    filename: text-tester.pdf
   ufilename: text-tester.pdf
        desc: nur zum Testen!
        size: 4639
      length: 1566

Extraction
~~~~~~~~~~~~~~~~~~~~~~~~~

Extract an embedded file like this::

    pymupdf embed-extract -h
    usage: pymupdf embed-extract [-h] -name NAME [-password PASSWORD] [-output OUTPUT]
                            input

    ---------------------- extract embedded file to disk ----------------------

    positional arguments:
    input                 PDF filename

    optional arguments:
    -h, --help            show this help message and exit
    -name NAME            name of entry
    -password PASSWORD    password
    -output OUTPUT        output filename, default is stored name

For details consult :meth:`Document.embfile_get`. Example (refer to previous section)::

    pymupdf embed-extract some.pdf -name neue.datei
    Saved entry 'neue.datei' as 'text-tester.pdf'

Deletion
~~~~~~~~~~~~~~~~~~~~~~~~
Delete an embedded file like this::

    pymupdf embed-del -h
    usage: pymupdf embed-del [-h] [-password PASSWORD] [-output OUTPUT] -name NAME input

    --------------------------- delete embedded file --------------------------

    positional arguments:
    input                 PDF filename

    optional arguments:
    -h, --help            show this help message and exit
    -password PASSWORD    password
    -output OUTPUT        output PDF filename, incremental save if none
    -name NAME            name of entry to delete

For details consult :meth:`Document.embfile_del`.

Insertion
~~~~~~~~~~~~~~~~~~~~~~~~
Add a new embedded file using this command::

    pymupdf embed-add -h
    usage: pymupdf embed-add [-h] [-password PASSWORD] [-output OUTPUT] -name NAME -path
                        PATH [-desc DESC]
                        input

    ---------------------------- add embedded file ----------------------------

    positional arguments:
    input                 PDF filename

    optional arguments:
    -h, --help            show this help message and exit
    -password PASSWORD    password
    -output OUTPUT        output PDF filename, incremental save if none
    -name NAME            name of new entry
    -path PATH            path to data for new entry
    -desc DESC            description of new entry

*"NAME"* **must not** already exist in the PDF. For details consult :meth:`Document.embfile_add`.

Updates
~~~~~~~~~~~~~~~~~~~~~~~
Update an existing embedded file using this command::

    pymupdf embed-upd -h
    usage: pymupdf embed-upd [-h] -name NAME [-password PASSWORD] [-output OUTPUT]
                        [-path PATH] [-filename FILENAME] [-ufilename UFILENAME]
                        [-desc DESC]
                        input

    --------------------------- update embedded file --------------------------

    positional arguments:
    input                 PDF filename

    optional arguments:
    -h, --help            show this help message and exit
    -name NAME            name of entry
    -password PASSWORD    password
    -output OUTPUT        Output PDF filename, incremental save if none
    -path PATH            path to new data for entry
    -filename FILENAME    new filename to store in entry
    -ufilename UFILENAME  new unicode filename to store in entry
    -desc DESC            new description to store in entry

    except '-name' all parameters are optional

Use this method to change meta-information of the file -- just omit the *"PATH"*. For details consult :meth:`Document.embfile_upd`.


Copying
~~~~~~~~~~~~~~~~~~~~~~~
Copy embedded files between PDFs::

    pymupdf embed-copy -h
    usage: pymupdf embed-copy [-h] [-password PASSWORD] [-output OUTPUT] -source
                        SOURCE [-pwdsource PWDSOURCE]
                        [-name [NAME [NAME ...]]]
                        input

    --------------------- copy embedded files between PDFs --------------------

    positional arguments:
    input                 PDF to receive embedded files

    optional arguments:
    -h, --help            show this help message and exit
    -password PASSWORD    password of input
    -output OUTPUT        output PDF, incremental save to 'input' if omitted
    -source SOURCE        copy embedded files from here
    -pwdsource PWDSOURCE  password of 'source' PDF
    -name [NAME [NAME ...]]
                          restrict copy to these entries


Text Extraction 
----------------
* New in v1.18.16

Extract text from arbitrary :ref:`supported documents<Supported_File_Types>` to a textfile. Currently, there are three output formatting modes available: simple, block sorting and reproduction of physical layout.

* **Simple** text extraction reproduces all text as it appears in the document pages -- no effort is made to rearrange in any particular reading order.
* **Block sorting** sorts text blocks (as identified by MuPDF) by ascending vertical, then horizontal coordinates. This should be sufficient to establish a "natural" reading order for basic pages of text.
* **Layout** strives to reproduce the original appearance of the input pages. You can expect results like this (produced by the command `pymupdf gettext -pages 1 demo1.pdf`):

.. image:: images/img-layout-text.*
    :scale: 60

.. note:: The "gettext" command offers a functionality similar to the CLI tool `pdftotext` by XPDF software, http://www.foolabs.com/xpdf/ -- this is especially true for "layout" mode, which combines that tool's `-layout` and `-table` options.



After each page of the output file, a formfeed character, `hex(12)` is written -- even if the input page has no text at all. This behavior can be controlled via options.

.. note:: For "layout" mode, **only horizontal, left-to-right, top-to bottom** text is supported, other text is ignored. In this mode, text is also ignored, if its :data:`fontsize` is too small.

   "Simple" and "blocks" mode in contrast output **all text** for any text size or orientation.

Command::

    pymupdf gettext -h
    usage: pymupdf gettext [-h] [-password PASSWORD] [-mode {simple,blocks,layout}] [-pages PAGES] [-noligatures]
                        [-convert-white] [-extra-spaces] [-noformfeed] [-skip-empty] [-output OUTPUT] [-grid GRID]
                        [-fontsize FONTSIZE]
                        input

    ----------------- extract text in various formatting modes ----------------

    positional arguments:
    input                 input document filename

    optional arguments:
    -h, --help            show this help message and exit
    -password PASSWORD    password for input document
    -mode {simple,blocks,layout}
                            mode: simple, block sort, or layout (default)
    -pages PAGES          select pages, format: 1,5-7,50-N
    -noligatures          expand ligature characters (default False)
    -convert-white        convert whitespace characters to space (default False)
    -extra-spaces         fill gaps with spaces (default False)
    -noformfeed           write linefeeds, no formfeeds (default False)
    -skip-empty           suppress pages with no text (default False)
    -output OUTPUT        store text in this file (default inputfilename.txt)
    -grid GRID            merge lines if closer than this (default 2)
    -fontsize FONTSIZE    only include text with a larger :data:`fontsize` (default 3)

.. note:: Command options may be abbreviated as long as no ambiguities are introduced. So the following do the same:

    * `... -output text.txt -noligatures -noformfeed -convert-white -grid 3 -extra-spaces ...`
    * `... -o text.txt -nol -nof -c -g 3 -e ...`

  The output filename defaults to the input with its extension replaced by `.txt`. As with other commands, you can select page ranges **(caution: 1-based!)** in `mutool` format, as indicated above.

* **mode:** (str) select a formatting mode -- default is "layout".
* **noligatures:** (bool) corresponds to **not** :data:`TEXT_PRESERVE_LIGATURES`. If specified, ligatures (present in advanced fonts: glyphs combining multiple characters like "fi") are split up into their components (i.e. "f", "i"). Default is passing them through.
* **convert-white:** corresponds to **not** :data:`TEXT_PRESERVE_WHITESPACE`. If specified, all white space characters (like tabs) are replaced with one or more spaces. Default is passing them through.
* **extra-spaces:**  (bool) corresponds to **not** :data:`TEXT_INHIBIT_SPACES`. If specified, large gaps between adjacent characters will be filled with one or more spaces. Default is off.
* **noformfeed:**  (bool) instead of `hex(12)` (formfeed), write linebreaks ``\n`` at end of output pages.
* **skip-empty:**  (bool) skip pages with no text.
* **grid:** lines with a vertical coordinate difference of no more than this value (in points) will be merged into the same output line. Only relevant for "layout" mode. **Use with care:** 3 or the default 2 should be adequate in most cases. If **too large**, lines that are *intended* to be different in the original may be merged and will result in garbled and / or incomplete output. If **too low**, artifact separate output lines may be generated for some spans in the input line, just because they are coded in a different font with slightly deviating properties.
* **fontsize:** include text with :data:`fontsize` larger than this value only (default 3). Only relevant for "layout" option.


.. highlight:: python

.. include:: footer.rst
