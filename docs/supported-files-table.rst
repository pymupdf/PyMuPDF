.. raw:: html

    <style>

        table {
            border-style: hidden;
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

        #feature-matrix .icon.txt {
            background: url("_images/icon-txt.svg") 0 0 transparent no-repeat;
            background-size: 40px 40px;
        }

    </style>



    <table id="feature-matrix" border="0" cellpadding="0" cellspacing="0">
        <tr>
            <th style="width:20%;"></th>
            <th style="width:20%;"><div id="trans1"></div></th>
        </tr>

        <tr>
            <td><cite><div id="trans2"></div></cite></td>
            <td>
                <span class="icon pdf"><cite>PDF</cite></span>
                <span class="icon xps"><cite>XPS</cite></span>
                <span class="icon epub"><cite>EPUB</cite></span>
                <span class="icon mobi"><cite>MOBI</cite></span>
                <span class="icon fb2"><cite>FB2</cite></span>
                <span class="icon cbz"><cite>CBZ</cite></span>
                <span class="icon svg"><cite>SVG</cite></span>
                <span class="icon txt"><cite>TXT</cite></span>
            </td>
        </tr>

        <tr>
            <td><cite><div id="trans3"></div></cite></td>
            <td>
                <span class="icon image"></span>
                <div><u><div id="trans4"></div></u> <cite>JPG/JPEG, PNG, BMP, GIF, TIFF, PNM, PGM, PBM, PPM, PAM, JXR, JPX/JP2, PSD</cite></div>
                <div><u><div id="trans5"></div></u> <cite>JPG/JPEG, PNG, PNM, PGM, PBM, PPM, PAM, PSD, PS</cite></div>
            </td>
        </tr>

    </table>

    <script>

        let lang = document.getElementsByTagName('html')[0].getAttribute('lang');

        function getTranslation(str) {
            if (lang == "ja") {
                if (str=="File type") {
                    return "ファイルタイプ";
                } else if (str=="Document Formats") {
                    return "文書のフォーマット";
                } else if (str=="Image Formats") {
                    return "画像のフォーマット";
                } else if (str=="Input formats") {
                    return "入力フォーマット";
                } else if (str=="Output formats") {
                    return "出力フォーマット";
                }

            }

            return str;
        }

        document.getElementById("trans1").innerHTML = getTranslation("File type");
        document.getElementById("trans2").innerHTML = getTranslation("Document Formats");
        document.getElementById("trans3").innerHTML = getTranslation("Image Formats");
        document.getElementById("trans4").innerHTML = getTranslation("Input formats");
        document.getElementById("trans5").innerHTML = getTranslation("Output formats");

    </script>
