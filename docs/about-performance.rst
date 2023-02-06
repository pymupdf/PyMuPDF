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
            border-right: 1px solid #000;
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
            border-top: 1px solid #000;
            border-right: 1px solid #000;
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
        /* 4.15 seconds = 2 pixels */
        #copying-graph .about-graph-area.a {
            height: 2px;
            background: #5465FF;
        }

        /* 17.77 seconds = 9 pixels */
        #copying-graph .about-graph-area.b {
            height: 9px;
            background: #788BFF;
        }

        /* 57.24 seconds = 29 pixels */
        #copying-graph .about-graph-area.c {
            height: 29px;
            background: #9BB1FF;
        }

        /* 137.62 seconds = 69 pixels */
        #copying-graph .about-graph-area.d {
            height: 69px;
            background: #BFD7FF;
        }

        /* 492.64 seconds = 246 pixels */
        #copying-graph .about-graph-area.e {
            height: 246px;
            background: #E2FDFF;
        }

        /* scale on this is 1 pixel = 2 seconds */
        /* 8.42 seconds = 4 pixels */
        #text-graph .about-graph-area.a {
            height: 4px;
            background: #5465FF;
        }

        /* 18.77 seconds = 9 pixels */
        #text-graph .about-graph-area.b {
            height: 9px;
            background: #788BFF;
        }

        /* 127.07 seconds = 64 pixels */
        #text-graph .about-graph-area.c {
            height: 30px;
            background: #9BB1FF;
        }

        /* 245.92 seconds = 159 pixels */
        #text-graph .about-graph-area.d {
            height: 122px;
            background: #BFD7FF;
        }


        /* scale on this is 1 pixel = 2 seconds */
        /* 202.65 seconds = 101 pixels */
        #rendering-graph .about-graph-area.a {
            height: 101px;
            background: #5465FF;
        }

        /* 327.78 seconds = 163 pixels */
        #rendering-graph .about-graph-area.b {
            height: 163px;
            background: #788BFF;
        }

        /* 350.85 seconds = 175 pixels */
        #rendering-graph .about-graph-area.c {
            height: 175px;
            background: #9BB1FF;
        }


        .about-graph-x-axis {
            display: flex;
            width: 480px;
            height: 20px;
            margin-left: 45px;
            border-top: 1px solid #000;
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

            .graph {
                color: #fff;
            }

            .about-graph-y-axis {
                border-right: 1px solid #fff;
            }

            .about-graph-x-axis {
                border-top: 1px solid #fff;
            }

            .about-graph-y-axis .segment {
                border-top: 1px solid #fff;
                border-right: 1px solid #fff;
            }

        }

    </style>

    <br/>
    <dl class="simple">
    <dt><strong>Copying</strong></dt><dd><p>This refers to opening a document and then saving it to a new file. This test measures the speed of reading a <cite>PDF</cite> and re-writing as a new <cite>PDF</cite>. This process is also at the core of functions like merging / joining multiple documents. The numbers below therefore apply to <cite>PDF</cite> joining and merging. The results for all 3,800 pages are:</p>
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
                <div class="segment">100<p>&#9201;</p><div style="font-size:10px;margin-top:-20px;">seconds</div></div>
            </div>

            <div class="about-graph-y-axis">
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
            </div>

            <div class="about-column"><div class="about-graph-area a"></div><div class="text">4.15</div></div>
            <div class="about-column"><div class="about-graph-area b"></div><div class="text">17.77</div></div>
            <div class="about-column"><div class="about-graph-area c"></div><div class="text">57.24</div></div>
            <div class="about-column"><div class="about-graph-area d"></div><div class="text">137.62</div></div>
            <div class="about-column"><div class="about-graph-area e"></div><div class="text">492.64</div></div>

        </div>

        <div class="about-graph-x-axis">
            <div class="segment">PyMuPDF</div>
            <div class="segment">PDFrw</div>
            <div class="segment">PikePDF</div>
            <div class="segment">PDFtk</div>
            <div class="segment">PyPDF2</div>
        </div>

        <div class="about-graph-x-axis speed">
            <div class="segment"><i>fastest</i></div>
            <div class="segment">&#8592;</div>
            <div class="segment">&#8592;</div>
            <div class="segment">&#8592;</div>
            <div class="segment"><i>slowest</i></div>
        </div>

    </div>

    <br/>
    <dl class="simple">
    <dt><strong>Text Extraction</strong></dt><dd><p>This refers to extracting simple, plain text from every page of the document and storing it in a text file. The results for all 3,800 pages are:</p>
    </dd>
    </dl>

    <div class="graph">

        <div class="central-graph" id="text-graph">

            <div class="about-graph-y-axis-text">

                <div class="segment">400</div>
                <div class="segment">300</div>
                <div class="segment">200</div>
                <div class="segment">100<p>&#9201;</p><div style="font-size:10px;margin-top:-20px;">seconds</div></div>
            </div>

            <div class="about-graph-y-axis">

                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
            </div>

            <div class="about-column"><div class="about-graph-area a"></div><div class="text">8.42</div></div>
            <div class="about-column"><div class="about-graph-area b"></div><div class="text">18.77</div></div>
            <div class="about-column"><div class="about-graph-area c"></div><div class="text">127.07</div></div>
            <div class="about-column"><div class="about-graph-area d"></div><div class="text">245.92</div></div>

        </div>

        <div class="about-graph-x-axis">
            <div class="segment">PyMuPDF</div>
            <div class="segment">XPDF</div>
            <div class="segment">PyPDF2</div>
            <div class="segment">PDFMiner</div>
        </div>

        <div class="about-graph-x-axis speed">
            <div class="segment"><i>fastest</i></div>
            <div class="segment">&#8592;</div>
            <div class="segment">&#8592;</div>
            <div class="segment"><i>slowest</i></div>
        </div>

    </div>


    <br/>

    <dl class="simple">
    <dt><strong>Rendering</strong></dt><dd><p>This refers to making an image (like PNG) from every page of a document at a given DPI resolution. This feature is the basis for displaying a document in a GUI window. The results for all 3,800 pages are:</p>
    </dd>
    </dl>


    <div class="graph">

        <div class="central-graph" id="rendering-graph">

            <div class="about-graph-y-axis-text">
                <div class="segment">500</div>
                <div class="segment">400</div>
                <div class="segment">300</div>
                <div class="segment">200</div>
                <div class="segment">100<p>&#9201;</p><div style="font-size:10px;margin-top:-20px;">seconds</div></div>
            </div>

            <div class="about-graph-y-axis">
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
                <div class="segment"></div>
            </div>

            <div class="about-column"><div class="about-graph-area a"></div><div class="text">202.65</div></div>
            <div class="about-column"><div class="about-graph-area b"></div><div class="text">327.78</div></div>
            <div class="about-column"><div class="about-graph-area c"></div><div class="text">350.85</div></div>

        </div>

        <div class="about-graph-x-axis">
            <div class="segment">PyMuPDF</div>
            <div class="segment">PDF2JPG</div>
            <div class="segment">XPDF</div>
        </div>

        <div class="about-graph-x-axis speed">
            <div class="segment"><i>fastest</i></div>
            <div class="segment">&#8592;</div>
            <div class="segment"><i>slowest</i></div>
        </div>

    </div>


    <br/>



