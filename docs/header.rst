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

.. |PyMuPDF Pro| raw:: html

    <cite>PyMuPDF Pro</cite>

.. |PDF| raw:: html

    <cite>PDF</cite>

.. |PyMuPDF4LLM| raw:: html

    <cite>PyMuPDF4LLM</cite>

.. |Markdown| raw:: html

    <cite>Markdown</cite>

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
            <a href="https://discord.gg/TSpYGBW4eq" target=_blank>
                <div style="width:30px;height:30px;margin-left:5px;">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 127.14 96.36">
                        <defs>
                            <style>.discordLogoFill{fill:#5865f2;}</style>
                        </defs>
                        <g id="Discord_Logo" data-name="Discord Logo">
                            <path class="discordLogoFill" d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.25a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/>
                        </g>
                    </svg>
                </div>
            </a>
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

