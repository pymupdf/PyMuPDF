The following table illustrates how :title:`PyMuPDF` compares with other typical solutions.

.. required image embeds for HTML to reference


.. image:: images/icons/icon-pdf.svg
          :width: 0
          :height: 0

.. image:: images/icons/icon-svg.svg
          :width: 0
          :height: 0

.. image:: images/icons/icon-xps.svg
          :width: 0
          :height: 0

.. image:: images/icons/icon-cbz.svg
          :width: 0
          :height: 0

.. image:: images/icons/icon-mobi.svg
          :width: 0
          :height: 0

.. image:: images/icons/icon-epub.svg
          :width: 0
          :height: 0

.. image:: images/icons/icon-image.svg
          :width: 0
          :height: 0

.. image:: images/icons/icon-fb2.svg
          :width: 0
          :height: 0

.. raw:: html

    <style>

        #feature-matrix {
            width: 100%;
            border: 1px #999 solid;
        }

        #feature-matrix th {
            border: 1px #999 solid;
            padding: 10px;
            background-color: #007aff;
            color: white;
        }

        #feature-matrix tr {

        }

        #feature-matrix td {
            border: 1px #999 solid;
            padding: 10px;
        }

        #feature-matrix tr td.yes {
            background-color: #83e57c !important;
            color: #000;
        }

        #feature-matrix tr td.yes::before {
            content: "✔︎ ";
        }

        #feature-matrix tr td.no {
            background-color: #e5887c !important;
            color: #000;
        }

        #feature-matrix tr td.no::before {
            content: "✕ ";
        }

        #feature-matrix tr td.limited {
            background-color: #e4c07b !important;
            color: #000;
        }

        #feature-matrix .icon-holder {
            line-height: 40px;
        }

        #feature-matrix .icon {
            text-indent: 45px;
            line-height: 40px;
            width: 100px;
            height: 40px;
        }

        #feature-matrix .icon.pdf {
            background: url("_images/icon-pdf.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.xps {
            background: url("_images/icon-xps.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.epub {
            background: url("_images/icon-epub.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.mobi {
            background: url("_images/icon-mobi.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.fb2 {
            background: url("_images/icon-fb2.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.cbz {
            background: url("_images/icon-cbz.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.svg {
            background: url("_images/icon-svg.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

        #feature-matrix .icon.image {
            background: url("_images/icon-image.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

    </style>

    <table id="feature-matrix">
        <tr>
            <th style="width:20%;">Feature</th>
            <th style="width:20%;">PyMuPDF</th>
            <th style="width:20%;">pikepdf</th>
            <th style="width:20%;">PyPDF2</th>
            <th style="width:20%;">pdfrw</th>
        </tr>

        <tr>
            <td><cite>Supports Multiple Document Formats</cite></td>
            <td>
                <span class="icon pdf"><cite>PDF</cite></span>
                <span class="icon xps"><cite>XPS</cite></span>
                <span class="icon epub"><cite>EPUB</cite></span>
                <span class="icon mobi"><cite>MOBI</cite></span>
                <span class="icon fb2"><cite>FB2</cite></span>
                <span class="icon cbz"><cite>CBZ</cite></span>
                <span class="icon svg"><cite>SVG</cite></span>
                <span class="icon image"><cite>Image</cite></span>
            </td>
            <td>
                <span class="icon pdf"><cite>PDF</cite></span>
            </td>
            <td>
                <span class="icon pdf"><cite>PDF</cite></span>
            </td>
            <td>
                <span class="icon pdf"><cite>PDF</cite></span>
            </td>
        </tr>

        <tr>
            <td><cite>Implementation</cite></td>
            <td><cite>C</cite> and <cite>Python</cite></td>
            <td><cite>C++</cite> and <cite>Python</cite></td>
            <td><cite>Python</cite></td>
            <td><cite>Python</cite></td>
        </tr>

        <tr>
            <td><cite>Render Document Pages</cite></td>
            <td class="yes">All document types</td>
            <td class="no">No rendering</td>
            <td class="no">No rendering</td>
            <td class="no">No rendering</td>
        </tr>

        <tr>
            <td><cite>Extract Text</cite></td>
            <td class="yes">All document types</td>
            <td class="no"></td>
            <td class="yes"><cite>PDF</cite> only</td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>Extract Vector Graphics</cite></td>
            <td class="yes">All document types</td>
            <td class="no"></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>Draw Vector Graphics (PDF)</cite></td>
            <td class="yes"></td>
            <td class="no"></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>Based on Existing, Mature Library</cite></td>
            <td class="yes"><cite>MuPDF</cite></td>
            <td class="yes"><cite>QPDF</cite></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>Automatic Repair of Damaged PDFs</cite></td>
            <td class="yes"></td>
            <td class="yes"></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>Encrypted PDFs</cite></td>
            <td class="yes"></td>
            <td class="yes"></td>
            <td class="limited">Limited</td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>Linerarized PDFs</cite></td>
            <td class="yes"></td>
            <td class="yes"></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>Incremental Updates</cite></td>
            <td class="yes"></td>
            <td class="no"></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>Integrates with Jupyter and IPython Notebooks</cite></td>
            <td class="yes"></td>
            <td class="yes"></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>Joining / Merging PDF with other Document Types</cite></td>
            <td class="yes">All document types</td>
            <td class="yes"><cite>PDF</cite> only </td>
            <td class="yes"><cite>PDF</cite> only </td>
            <td class="yes"><cite>PDF</cite> only </td>
        </tr>

        <tr>
            <td><cite>OCR API for Seamless Integration with Tesseract</cite></td>
            <td class="yes">All document types</td>
            <td class="no"></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>Integrated Checkpoint / Restart Feature (PDF)</cite></td>
            <td class="yes"></td>
            <td class="no"></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>PDF Optional Content</cite></td>
            <td class="yes"></td>
            <td class="no"></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>PDF Embedded Files</cite></td>
            <td class="yes"></td>
            <td class="yes"></td>
            <td class="limited">Limited</td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>PDF Redactions</cite></td>
            <td class="yes"></td>
            <td class="no"></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>PDF Annotations</cite></td>
            <td class="yes">Full</td>
            <td class="no"></td>
            <td class="limited">Limited</td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>PDF Form Fields</cite></td>
            <td class="yes">Create, read, update</td>
            <td class="no"></td>
            <td class="limited">Limited, no creation</td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>PDF Page Labels</cite></td>
            <td class="yes"></td>
            <td class="no"></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>

        <tr>
            <td><cite>Support Font Sub-Setting</cite></td>
            <td class="yes"></td>
            <td class="no"></td>
            <td class="no"></td>
            <td class="no"></td>
        </tr>


    </table>

    <br/>
