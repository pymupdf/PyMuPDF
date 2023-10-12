.. raw:: html

    <style>

        * {
            -webkit-tap-highlight-color: rgba(0,0,0,0); /* make transparent link selection, adjust last value opacity 0 to 1.0 */
            -moz-box-sizing: border-box; -webkit-box-sizing: border-box; box-sizing: border-box;
        }

        .graph {
            font-family: arial;
        }

        .central-graph {
            display: flex;
        }

        .about-graph-y-axis {
            border-right: 1px solid #999;
        }

        .about-graph-y-axis-text .segment {
            height: 50px;
            width: 30px;
            text-align: right;
            font-size: 14px;
        }

        .about-graph-y-axis {
            margin-left: 5px;
            margin-top: 5px;
        }

        .about-graph-y-axis .segment {
            height: 50px;
            width: 10px;
            border-top: 1px solid #999;
            border-right: 1px solid #999;
        }

        .about-graph-area {
            margin-top: 5px;
            width: 80px;
        }

        .about-column {
            display: flex;
            margin: 0 4px 1px;
            flex-direction: column-reverse;
        }

        .about-column .text {
            font-size: 12px;
            color: #666;
            text-align: center;
            padding: 6px;
        }

        .about-graph-area {
            border-top: 1px solid #aaa;
            border-left: 1px solid #aaa;
            border-right: 1px solid #aaa;
        }



        /* scale on this is 1 pixel = 2 seconds */
        /* 3.05 seconds = 2 pixels */
        #copying-graph .about-graph-area.a {
            height: 2px;
            background: #5465FF;
        }

        /* 10.54 seconds = 5 pixels */
        #copying-graph .about-graph-area.b {
            height: 5px;
            background: #788BFF;
        }

        /* 33.57 seconds = 16 pixels */
        #copying-graph .about-graph-area.c {
            height: 16px;
            background: #9BB1FF;
        }

        /* 494.04 seconds = 247 pixels */
        #copying-graph .about-graph-area.d {
            height: 247px;
            background: #E2FDFF;
        }


        /* scale on this is 1 pixel = 2 seconds */
        /* 8.01 seconds = 4 pixels */
        #text-graph .about-graph-area.a {
            height: 4px;
            background: #5465FF;
        }

        /* 27.42 seconds = 13 pixels */
        #text-graph .about-graph-area.b {
            height: 13px;
            background: #788BFF;
        }

        /* 101.64 seconds = 50 pixels */
        #text-graph .about-graph-area.c {
            height: 50px;
            background: #9BB1FF;
        }

        /* 227.27 seconds = 113 pixels */
        #text-graph .about-graph-area.d {
            height: 113px;
            background: #BFD7FF;
        }


        /* scale on this is 1 pixel = 4 seconds */
        /* 367.04 seconds = 92 pixels */
        #rendering-graph .about-graph-area.a {
            height: 92px;
            background: #5465FF;
        }

        /* 646 seconds = 161 pixels */
        #rendering-graph .about-graph-area.b {
            height: 161px;
            background: #788BFF;
        }

        /* 851.52 seconds = 212 pixels */
        #rendering-graph .about-graph-area.c {
            height: 212px;
            background: #9BB1FF;
        }


        .about-graph-x-axis {
            display: flex;
            width: 480px;
            height: 20px;
            margin-left: 45px;
            border-top: 1px solid #999;
        }

        .about-graph-x-axis .segment {
            margin-top: 4px;
            width: 88px;
            text-align: center;
        }

        .about-graph-x-axis.speed {
            margin-top: 4px;
        }


        /* Dark mode colors */
        @media (prefers-color-scheme: dark) {



        }

    </style>

    <br/>
    <dl class="simple">
    <dt><strong id="transP1">Copying</strong></dt><dd><p id="transP2">This refers to opening a document and then saving it to a new file. This test measures the speed of reading a <cite>PDF</cite> and re-writing as a new <cite>PDF</cite>. This process is also at the core of functions like merging / joining multiple documents. The numbers below therefore apply to <cite>PDF</cite> joining and merging.</p>

    <p id="transP3">The results for all 7,031 pages are:</p>
    </dd>
    </dl>


    <div class="graph">

        <div class="central-graph" id="copying-graph">

            <div class="about-graph-y-axis-text">
                <div class="segment">600</div>
                <div class="segment">500</div>
                <div class="segment">400</div>
                <div class="segment">300</div>
                <div class="segment">200</div>
                <div class="segment">100<p>&#9201;</p><div style="font-size:10px;margin-top:-20px;" id="transP4">seconds</div></div>
            </div>

            <div class="about-graph-y-axis">
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
            </div>

            <div class="about-column"><div class="about-graph-area a"></div><div class="text">3.05</div></div>
            <div class="about-column"><div class="about-graph-area b"></div><div class="text">10.54</div></div>
            <div class="about-column"><div class="about-graph-area c"></div><div class="text">33.57</div></div>
            <div class="about-column"><div class="about-graph-area d"></div><div class="text">494.04</div></div>

        </div>

        <div class="about-graph-x-axis">
            <div class="segment">PyMuPDF</div>
            <div class="segment">PDFrw</div>
            <div class="segment">PikePDF</div>
            <div class="segment">PyPDF2</div>
        </div>

        <div class="about-graph-x-axis speed">
            <div class="segment"><i id="transP5">fastest</i></div>
            <div class="segment">&#8592;</div>
            <div class="segment">&#8592;</div>
            <div class="segment"><i id="transP6">slowest</i></div>
        </div>

    </div>

    <br/>
    <dl class="simple">
    <dt><strong id="transP7">Text Extraction</strong></dt><dd><p id="transP8">This refers to extracting simple, plain text from every page of the document and storing it in a text file.</p>

    <p id="transP9">The results for all 7,031 pages are:</p>
    </dd>
    </dl>

    <div class="graph">

        <div class="central-graph" id="text-graph">

            <div class="about-graph-y-axis-text">

                <div class="segment">400</div>
                <div class="segment">300</div>
                <div class="segment">200</div>
                <div class="segment">100<p>&#9201;</p><div style="font-size:10px;margin-top:-20px;" id="transP10">seconds</div></div>
            </div>

            <div class="about-graph-y-axis">

                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
            </div>

            <div class="about-column"><div class="about-graph-area a"></div><div class="text">8.01</div></div>
            <div class="about-column"><div class="about-graph-area b"></div><div class="text">27.42</div></div>
            <div class="about-column"><div class="about-graph-area c"></div><div class="text">101.64</div></div>
            <div class="about-column"><div class="about-graph-area d"></div><div class="text">227.27</div></div>

        </div>

        <div class="about-graph-x-axis">
            <div class="segment">PyMuPDF</div>
            <div class="segment">XPDF</div>
            <div class="segment">PyPDF2</div>
            <div class="segment">PDFMiner</div>
        </div>

        <div class="about-graph-x-axis speed">
            <div class="segment"><i id="transP11">fastest</i></div>
            <div class="segment">&#8592;</div>
            <div class="segment">&#8592;</div>
            <div class="segment"><i id="transP12">slowest</i></div>
        </div>

    </div>


    <br/>

    <dl class="simple">
    <dt><strong id="transP13">Rendering</strong></dt><dd><p id="transP14">This refers to making an image (like PNG) from every page of a document at a given DPI resolution. This feature is the basis for displaying a document in a GUI window.</p>

    <p id="transP15">The results for all 7,031 pages are:</p>

    </dd>
    </dl>


    <div class="graph">

        <div class="central-graph" id="rendering-graph">

            <div class="about-graph-y-axis-text">
                <div class="segment">1000</div>
                <div class="segment">800</div>
                <div class="segment">600</div>
                <div class="segment">400</div>
                <div class="segment">200<p>&#9201;</p><div style="font-size:10px;margin-top:-20px;" id="transP16">seconds</div></div>
            </div>

            <div class="about-graph-y-axis">
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
            </div>

            <div class="about-column"><div class="about-graph-area a"></div><div class="text">367.04</div></div>
            <div class="about-column"><div class="about-graph-area b"></div><div class="text">646</div></div>
            <div class="about-column"><div class="about-graph-area c"></div><div class="text">851.52</div></div>

        </div>

        <div class="about-graph-x-axis">
            <div class="segment">PyMuPDF</div>
            <div class="segment">XPDF</div>
            <div class="segment">PDF2JPG</div>
        </div>

        <div class="about-graph-x-axis speed">
            <div class="segment"><i id="transP17">fastest</i></div>
            <div class="segment">&#8592;</div>
            <div class="segment"><i id="transP18"slowest</i></div>
        </div>

    </div>


    <br/>

    <script>

        let langB = document.getElementsByTagName('html')[0].getAttribute('lang');

        function getTranslationB(str) {
            if (langB == "ja") {
                if (str=="Copying") {
                    return "コピー";
                } else if (str == "This refers to opening a document and then saving it to a new file. This test measures the speed of reading a <cite>PDF</cite> and re-writing as a new <cite>PDF</cite>. This process is also at the core of functions like merging / joining multiple documents. The numbers below therefore apply to <cite>PDF</cite> joining and merging.") {
                    return "以下は、ドキュメントを開いてから新しいファイルとして保存することを指します。このテストは、PDFを読み込み、新しいPDFとして再書き込む速度を測定します。このプロセスは、複数のドキュメントを結合するなどの機能の中核でもあります。したがって、以下の数字はPDFの結合とマージにも適用されます。";
                } else if (str == "The results for all 7,031 pages are:") {
                    return "全7,031ページの結果は次のとおりです：";
                } else if (str == "seconds") {
                    return "秒";
                } else if (str == "fastest") {
                    return "最速";
                } else if (str == "slowest") {
                    return "最遅";
                } else if (str == "Text Extraction") {
                    return "テキスト抽出";
                } else if (str == "This refers to extracting simple, plain text from every page of the document and storing it in a text file.") {
                    return "以下は、ドキュメントの各ページから簡単なプレーンテキストを抽出し、テキストファイルに保存することを指します。";
                } else if (str == "Rendering") {
                    return "レンダリング";
                } else if (str == "This refers to making an image (like PNG) from every page of a document at a given DPI resolution. This feature is the basis for displaying a document in a GUI window.") {
                    return "この場合、\"レンダリング\" は、指定されたDPI解像度でドキュメントの各ページから画像（PNGなど）を作成することを指します。この機能は、GUIウィンドウでドキュメントを表示するための基本となります。";
                }



            }

            return str;

        }

        document.getElementById("transP1").innerHTML = getTranslationB("Copying");
        document.getElementById("transP2").innerHTML = getTranslationB("This refers to opening a document and then saving it to a new file. This test measures the speed of reading a <cite>PDF</cite> and re-writing as a new <cite>PDF</cite>. This process is also at the core of functions like merging / joining multiple documents. The numbers below therefore apply to <cite>PDF</cite> joining and merging.");

        document.getElementById("transP3").innerHTML = getTranslationB("The results for all 7,031 pages are:");
        document.getElementById("transP4").innerHTML = getTranslationB("seconds");
        document.getElementById("transP5").innerHTML = getTranslationB("fastest");
        document.getElementById("transP6").innerHTML = getTranslationB("slowest");
        document.getElementById("transP7").innerHTML = getTranslationB("Text Extraction");
        document.getElementById("transP8").innerHTML = getTranslationB("This refers to extracting simple, plain text from every page of the document and storing it in a text file.");
        document.getElementById("transP9").innerHTML = getTranslationB("The results for all 7,031 pages are:");
        document.getElementById("transP10").innerHTML = getTranslationB("seconds");
        document.getElementById("transP11").innerHTML = getTranslationB("fastest");
        document.getElementById("transP12").innerHTML = getTranslationB("slowest");
        document.getElementById("transP13").innerHTML = getTranslationB("Rendering");
        document.getElementById("transP14").innerHTML = getTranslationB("This refers to making an image (like PNG) from every page of a document at a given DPI resolution. This feature is the basis for displaying a document in a GUI window.");
        document.getElementById("transP15").innerHTML = getTranslationB("The results for all 7,031 pages are:");
        document.getElementById("transP16").innerHTML = getTranslationB("seconds");
        document.getElementById("transP17").innerHTML = getTranslationB("fastest");
        document.getElementById("transP18").innerHTML = getTranslationB("slowest");



    </script>





