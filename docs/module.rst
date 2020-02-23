.. _Module:

============================
Using *fitz* as a Module
============================

.. highlight:: python

*(New in version 1.16.8)*

PyMuPDF can also be used in the command line as a **module** to perform basic utility functions.

This is work in progress and subject to changes. This feature should obsolete writing some of the most basic scripts.

As a guideline we are using the feature set of MuPDF command line tools. Admittedly, there is some functional overlap. On the other hand, PDF embedded files are no longer supported by MuPDF, so PyMuPDF is offering something unique here.

Invocation
-----------

Invoke the module like this::

    python -m fitz command parameters

General remarks:

* Request help via *"-h"*, resp. command-specific help via *"command -h"*.
* Parameters may be abbreviated as long as the result is not ambiguous (Python 3.5 or later only).
* Several commands support parameters *-pages* and *-xrefs*. They are intended for down-selection. Please note that:

    - **page numbers** for this utility must be given **1-based**.
    - valid :data:`xref` numbers start at 1.
    - Specify any number of either single integers or integer ranges, separated by one comma each. A **range** is a pair of integers separated by one hyphen "-". Integers must not exceed the maximum page number or resp. :data:`xref` number. To specify that maximum, the symbolic variable "N" may be used instead of an integer. Integers or ranges may occur several times, in any sequence and may overlap. If in a range the first number is greater than the second one, the respective items will be processed in reversed order.

* You can also use the fitz module inside your script::

    >>> from fitz.__main__ import main as fitz_command
    >>> cmd = "clean input.pdf output.pdf -pages 1,N".split()  # prepare command
    >>> saved_parms = sys.argv[1:]  # save original parameters
    >>> sys.argv[1:] = cmd  # store command
    >>> fitz_command()  # execute command
    >>> sys.argv[1:] = saved_parms  # restore original parameters

* You can use the following 2-liner and compile it with `Nuitka <https://pypi.org/project/Nuitka/>`_ in either normal or standalone mode, if you want to distribute it. This will give you a command line utility with all the functions explained below::

    from fitz.__main__ import main
    main()


Cleaning and Copying
----------------------

.. highlight:: text

This command will optimize the PDF and store the result in a new file. You can use it also for encryption, decryption and creating sub documents. It is mostly similar to the MuPDF command line utility *"mutool clean"*::

    python -m fitz clean -h
    usage: fitz clean [-h] [-password PASSWORD]
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

    python -m fitz extract -h
    usage: fitz extract [-h] [-images] [-fonts] [-output OUTPUT] [-password PASSWORD]
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

.. note:: Except for output directory creation, this feature is **functionally equivalent** to and obsoletes `this script <https://github.com/pymupdf/PyMuPDF-Utilities/blob/master/extract-imga.py>`_.


Joining PDF Documents
-----------------------
To join several PDF files specify::

    python -m fitz join -h
    usage: fitz join [-h] -output OUTPUT [input [input ...]]

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

*python -m fitz join -o output.pdf file1.pdf,,N-1 file2.pdf,secret,N,1 file3.pdf,,5-N*


Low Level Information
----------------------

Display PDF internal information. Again, there are similarities to *"mutool show"*::

    python -m fitz show -h
    usage: fitz show [-h] [-password PASSWORD] [-catalog] [-trailer] [-metadata]
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

    python -m fitz show x.pdf
    PDF is password protected

    python -m fitz show x.pdf -pass hugo
    authentication unsuccessful

    python -m fitz show x.pdf -pass jorjmckie
    authenticated as owner
    file 'x.pdf', pages: 1, objects: 19, 58 MB, PDF 1.4, encryption: Standard V5 R6 256-bit AES
    Document contains 15 embedded files.

    python -m fitz show FDA-1572_508_R6_FINAL.pdf -tr -m
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

    python -m fitz embed-info -h
    usage: fitz embed-info [-h] [-name NAME] [-detail] [-password PASSWORD] input

    --------------------------- list embedded files ---------------------------

    positional arguments:
    input               PDF filename

    optional arguments:
    -h, --help          show this help message and exit
    -name NAME          if given, report only this one
    -detail             show detail information
    -password PASSWORD  password

Example::

    python -m fitz embed-info some.pdf
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

    python -m fitz embed-extract -h
    usage: fitz embed-extract [-h] -name NAME [-password PASSWORD] [-output OUTPUT]
                            input

    ---------------------- extract embedded file to disk ----------------------

    positional arguments:
    input                 PDF filename

    optional arguments:
    -h, --help            show this help message and exit
    -name NAME            name of entry
    -password PASSWORD    password
    -output OUTPUT        output filename, default is stored name

For details consult :meth:`Document.embeddedFileGet`. Example (refer to previous section)::

    python -m fitz embed-extract some.pdf -name neue.datei
    Saved entry 'neue.datei' as 'text-tester.pdf'

Deletion
~~~~~~~~~~~~~~~~~~~~~~~~
Delete an embedded file like this::

    python -m fitz embed-del -h
    usage: fitz embed-del [-h] [-password PASSWORD] [-output OUTPUT] -name NAME input

    --------------------------- delete embedded file --------------------------

    positional arguments:
    input                 PDF filename

    optional arguments:
    -h, --help            show this help message and exit
    -password PASSWORD    password
    -output OUTPUT        output PDF filename, incremental save if none
    -name NAME            name of entry to delete

For details consult :meth:`Document.embeddedFileDel`.

Insertion
~~~~~~~~~~~~~~~~~~~~~~~~
Add a new embedded file using this command::

    python -m fitz embed-add -h
    usage: fitz embed-add [-h] [-password PASSWORD] [-output OUTPUT] -name NAME -path
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

*"NAME"* **must not** already exist in the PDF. For details consult :meth:`Document.embeddedFileAdd`.

Updates
~~~~~~~~~~~~~~~~~~~~~~~
Update an existing embedded file using this command::

    python -m fitz embed-upd -h
    usage: fitz embed-upd [-h] -name NAME [-password PASSWORD] [-output OUTPUT]
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

Use this method to change meta-information of the file -- just omit the *"PATH"*. For details consult :meth:`Document.embeddedFileUpd`.


Copying
~~~~~~~~~~~~~~~~~~~~~~~
Copy embedded files between PDFs::

    python -m fitz embed-copy -h
    usage: fitz embed-copy [-h] [-password PASSWORD] [-output OUTPUT] -source
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


.. highlight:: python
