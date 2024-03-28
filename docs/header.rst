.. meta::
   :author: Artifex
   :description: PyMuPDF is a high-performance Python library for data extraction, analysis, conversion & manipulation of PDF (and other) documents.
   :keywords: PDF Text Extraction, PDF Image Extraction, PDF Conversion, PDF Tables, PDF Splitting, PDF Creation, Pyodide, PyScript


.. |history_begin| raw:: html

    <details>
    <summary><small style="cursor:pointer;">Show/hide history</small></summary><small>

.. |history_end| raw:: html

    </small></details>

.. |pdf_only_class| raw:: html

    <div style="width:100%; text-align:right"><b>This class is for PDF only.</b></div>

.. |PyMuPDF| raw:: html

    <cite>PyMuPDF</cite>

.. |PDF| raw:: html

    <cite>PDF</cite>

.. raw:: html

    <style>

        #languageToggle {
            width:25%;
            margin:8px 10px 0;
        }

        #button-select-en {
            padding: 5px 10px;
            background-color: #fff;
            border: 1px solid #000;
            border-radius: 10px 0 0 10px;
            font-size: 14px;
        }

        #button-select-ja {
            padding: 5px 10px;
            background-color: #fff;
            border: 1px solid #000;
            border-radius: 0px 10px 10px 0;
            border-left: 0;
            font-size: 14px;
        }

        #button-select-en , #button-select-ja, #button-select-en:hover , #button-select-ja:hover  {
            color: #fff;
            text-decoration: none;
        }

        /* small screens */
        @media all and (max-width : 768px)  {
            #languageToggle {
                width:50%;
            }
        }

        @media all and (max-width : 400px)  {
            #languageToggle {
                width:70%;
            }
        }

        @media all and (max-width : 375px)  {
            #button-select-en , #button-select-ja {
                font-size: 11px;
            }
        }

    </style>

    <div style="display:flex;justify-content:space-between;align-items: center;">
        <form class="sidebar-search-container top" method="get" action="search.html" role="search" style="width:75%">
          <input class="sidebar-search" placeholder="Search" name="q" aria-label="Search">
          <input type="hidden" name="check_keywords" value="yes">
          <input type="hidden" name="area" value="default">
        </form>
        <div id="languageToggle"><span><a id="button-select-en" href="javaScript:changeLanguage('en')">English</a></span><span><a id="button-select-ja" href="javaScript:changeLanguage('ja')">日本語</a></span></div>
    </div>

    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:20px;">
        <div class="discordLink" style="display:flex;align-items:center;margin-top: -5px;">
            <a href="https://discord.gg/TSpYGBW4eq" id="findOnDiscord" target=_blank>Find <b>#pymupdf</b> on <b>Discord</b></a>
            <a href="https://discord.gg/TSpYGBW4eq" target=_blank><img src="_images/discord-mark-blue.svg" alt="Discord logo" /></a>
        </div>

        <div class="feedbackLink"><a id="feedbackLinkTop" target=_blank>Do you have any feedback on this page?</b></a></div>
    </div>

    <script>
        // highlightSelectedLanguage

        if (document.getElementsByTagName('html')[0].getAttribute('lang')=="ja") {
            document.getElementById("button-select-ja").style.backgroundColor = "#ff6600";
            document.getElementById("button-select-en").style.color = "#000";
        } else {
            document.getElementById("button-select-en").style.backgroundColor = "#ff6600";
            document.getElementById("button-select-ja").style.color = "#000";
        }


        var url_string = window.location.href;
        var a = document.getElementById('feedbackLinkTop');
        a.setAttribute("href", "https://artifex.com/contributor/feedback.php?utm_source=rtd-pymupdf&utm_medium=rtd&utm_content=header-link&url="+url_string);

        function changeLanguage(lang) {
            var new_url;

            if (lang == "en") {
                new_url = url_string.replace("/ja/", "/en/");
            } else {
                new_url = url_string.replace("/en/", "/ja/");
            }

            window.location.replace(new_url);
        }

    </script>

