
.. include:: ../header.rst

.. _pymupdf-pro:

.. raw:: html

    <script>
        document.getElementById("headerSearchWidget").action = '../search.html';
    </script>


.. _tesseract-language-packs:

Tesseract Language Packs
========================

.. meta::
   :description: How to install additional Tesseract language packs on macOS, Linux, and Windows.

Overview
--------

Tesseract identifies languages using three-letter `ISO 639-2 <https://en.wikipedia.org/wiki/List_of_ISO_639-2_codes>`_ codes. English (``eng``) is installed by default on most platforms. For any other language, you need to install the corresponding language pack before pymupdf4llm can use it for OCR.

A full list of supported language codes is available on the `Tesseract tessdata repository <https://github.com/tesseract-ocr/tessdata>`_.

.. tip::

   To see which languages are already installed on your system, run ``tesseract --list-langs`` in your terminal.

----

Linux
-----

Language pack installation varies slightly by distribution.

**Ubuntu / Debian**

.. code-block:: bash

   # List all available language packs
   apt-cache search tesseract-ocr

   # Install a specific language (e.g. German)
   sudo apt install tesseract-ocr-deu

   # Install all available languages at once
   sudo apt install tesseract-ocr-all

Language packages follow the naming pattern ``tesseract-ocr-<langcode>``, for example ``tesseract-ocr-fra`` for French or ``tesseract-ocr-chi-sim`` for Simplified Chinese.

**Fedora / RHEL**

.. code-block:: bash

   # Search for available language packs
   dnf search tesseract

   # Install a specific language (e.g. German)
   sudo dnf install tesseract-langpack-deu

   # Install all language packs
   sudo dnf install tesseract-langpack-*

On Fedora, packages are named ``tesseract-langpack-<langcode>``.

**Arch Linux**

.. code-block:: bash

   # Search for available language packs
   pacman -Ss tesseract-data

   # Install a specific language (e.g. German)
   sudo pacman -S tesseract-data-deu

On Arch, packages are named ``tesseract-data-<langcode>``.

Manual Installation (All Distros)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If a language pack is not available through your package manager, download the ``.traineddata`` file directly from GitHub and copy it to your Tesseract data directory:

.. code-block:: bash

   # Download language pack (e.g. French)
   curl -L https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata \
     -o fra.traineddata

   # Copy to tessdata directory (path varies by distro)
   sudo cp fra.traineddata /usr/share/tesseract-ocr/4.00/tessdata/
   # or
   sudo cp fra.traineddata /usr/share/tessdata/

Common tessdata locations on Linux:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Distribution
     - Path
   * - Ubuntu / Debian
     - ``/usr/share/tesseract-ocr/4.00/tessdata/``
   * - Fedora / RHEL
     - ``/usr/share/tesseract/tessdata/``
   * - Arch Linux
     - ``/usr/share/tessdata/``

----

Windows
-------

During Installation (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Tesseract Windows installer from `UB Mannheim <https://github.com/UB-Mannheim/tesseract/wiki>`_ lets you select additional language packs during setup. When you reach the **Choose Components** screen, expand **Additional language data** and tick the languages you need.

After Installation (Manual)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If Tesseract is already installed, download language packs manually:

1. Go to `github.com/tesseract-ocr/tessdata <https://github.com/tesseract-ocr/tessdata>`_
2. Download the ``.traineddata`` file for your language (e.g. ``fra.traineddata`` for French)
3. Copy the file into your Tesseract ``tessdata`` folder, typically:

.. code-block:: text

   C:\Program Files\Tesseract-OCR\tessdata\

.. note::

   The Chocolatey (``choco install tesseract``) package only includes English. All additional languages must be added manually using the steps above.

Verify the Install
~~~~~~~~~~~~~~~~~~

Open Command Prompt or PowerShell and run:

.. code-block:: powershell

   tesseract --list-langs

Your newly installed language should appear in the output.

----

macOS
-----

The recommended approach on macOS is `Homebrew <https://brew.sh>`_. There are two options depending on how much disk space you want to use.

Install All Languages at Once
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``tesseract-lang`` formula bundles Tesseract with every available language pack:

.. code-block:: bash

   brew install tesseract-lang

Install Specific Languages
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you only need a few languages, install ``tesseract`` first and then manually download the ``.traineddata`` files you need:

.. code-block:: bash

   # Install Tesseract engine only
   brew install tesseract

   # Find the tessdata directory
   brew info tesseract
   # Look for a line like: /opt/homebrew/share/tessdata

   # Download a specific language pack (e.g. French)
   curl -L https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata \
     -o /opt/homebrew/share/tessdata/fra.traineddata

Replace ``fra`` with your target language code and adjust the tessdata path to match what ``brew info tesseract`` reports on your machine.

.. note::

   If you installed Tesseract via MacPorts instead of Homebrew, use ``port install tesseract-<langcode>``, for example ``sudo port install tesseract-fra``.

----

Using a Language with pymupdf4llm
----------------------------------

Once a language pack is installed, pass its code to ``to_markdown()`` via the ``language`` parameter:

.. code-block:: python

   import pymupdf4llm

   # Single language
   md = pymupdf4llm.to_markdown("document.pdf", language="fra")

   # Multiple languages
   md = pymupdf4llm.to_markdown("document.pdf", language="eng+fra+deu")

----

Common Language Codes
---------------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Language
     - Code
   * - English
     - ``eng``
   * - French
     - ``fra``
   * - German
     - ``deu``
   * - Spanish
     - ``spa``
   * - Italian
     - ``ita``
   * - Portuguese
     - ``por``
   * - Simplified Chinese
     - ``chi_sim``
   * - Traditional Chinese
     - ``chi_tra``
   * - Japanese
     - ``jpn``
   * - Korean
     - ``kor``
   * - Arabic
     - ``ara``
   * - Russian
     - ``rus``
   * - Hindi
     - ``hin``

For the full list of supported languages and their codes, see the `Tesseract tessdata repository <https://github.com/tesseract-ocr/tessdata>`_.



.. include:: ../footer.rst


