.. meta::
   :author: Artifex
   :description: PyMuPDF is a high-performance Python library for data extraction, analysis, conversion & manipulation of PDF (and other) documents.
   :keywords: PDF Text Extraction, PDF Image Extraction, PDF Conversion, PDF Tables, PDF Splitting, PDF Creation, Pyodide, PyScript

.. raw:: html

    <link rel="stylesheet" type="text/css" href="_static/prism/prism.css">

        <style>

            /* Prism Updates */

            .code-toolbar .copy-to-clipboard-button {
                background: #007aff !important;
                color: white !important;
                padding: 10px !important;
                border-radius: 5px !important;
                font-family: Arial !important;
            }

            .code-toolbar pre {
               background: #fff;
               border: #999 1px dashed;
            }

            .code-toolbar code {
               border: 0px !important;
            }

        </style>

   <script type="text/javascript" src="_static/prism/prism.js"></script>

    <div style="display:flex;justify-content:flex-start;align-items: flex-end;">
        <form class="sidebar-search-container top" method="get" action="search.html" role="search" style="width:75%">
          <input class="sidebar-search" placeholder="Search" name="q" aria-label="Search">
          <input type="hidden" name="check_keywords" value="yes">
          <input type="hidden" name="area" value="default">
        </form>
        <div style="width:25%;margin:0px 10px;"><span style="font-size:11px;">Language: </span><span><a id="printableLang" href="javascript:changeLanguage()"></a></span></div>
    </div>

    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:20px;">
        <div class="discordLink" style="display:flex;align-items:center;margin-top: -5px;">
            <a href="https://discord.gg/TSpYGBW4eq" id="findOnDiscord" target=_blank>Find <b>#pymupdf</b> on <b>Discord</b></a>
            <a href="https://discord.gg/TSpYGBW4eq" target=_blank><img src="_images/discord-mark-blue.svg" alt="Discord logo" /></a>
        </div>

        <div class="feedbackLink"><a id="feedbackLinkTop" target=_blank>Do you have any feedback on this page?</b></a></div>
    </div>

    <script>

        if (document.getElementsByTagName('html')[0].getAttribute('lang')=="ja") {
            document.getElementById("printableLang").innerHTML = "日本語";
        } else {
            document.getElementById("printableLang").innerHTML = "English";
        }

        var url_string = window.location.href;
        var a = document.getElementById('feedbackLinkTop');
        a.setAttribute("href", "https://artifex.com/contributor/feedback.php?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=header-link&url="+url_string);

        function changeLanguage() {
            var new_url;

            if (document.getElementsByTagName('html')[0].getAttribute('lang')=="ja") {
                new_url = url_string.replace("/ja/", "/en/");
            } else {
                new_url = url_string.replace("/en/", "/ja/");
            }

            window.location.replace(new_url);
        }

    </script>

