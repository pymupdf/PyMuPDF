
.. include:: ../header.rst



FAQ
=============


.. raw:: html

    <script>
        document.getElementById("headerSearchWidget").action = '../search.html';
    </script>



.. raw:: html

    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
    :root {
    --bg: #0f1117;
    --surface: #181a24;
    --surface-hover: #1e2130;
    --border: #2a2d3e;
    --text: #d8d8e0;
    --muted: #9898a8;
    --accent: #e8943a;
    --accent-dim: rgba(232,148,58,0.12);
    --code-bg: #141620;
    --green: #4ade80;
    --blue: #60a5fa;
    --red: #f87171;
    --purple: #c084fc;
    }

    .toc-drawer {
        display: none !important;
    }

    .main .content { 
        width:100% !important;
    }

    .main .content .container {
        padding-top:0 !important;
        margin-top:0 !important;
    } 

    #nav {
        position: sticky;
        top: 0;
    }

    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
    font-family: 'IBM Plex Sans', -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    font-size: 15px;
    line-height: 1.75;
    -webkit-font-smoothing: antialiased;
    }

    .container {
    max-width: 900px;
    margin: 0 auto;
    padding: 60px 24px;
    }

    /* Header */
    .header {
    margin-bottom: 56px;
    padding-bottom: 40px;
    border-bottom: 1px solid var(--border);
    }

    .header h1 {
    font-size: 32px;
    font-weight: 600;
    letter-spacing: -0.5px;
    margin-bottom: 12px;
    }

    /*.header h1 span { color: var(--accent); }*/

    .header .subtitle {
    font-size: 16px;
    color: var(--muted);
    line-height: 1.7;
    max-width: 700px;
    }

    .header .meta {
    margin-top: 16px;
    display: flex;
    gap: 24px;
    font-size: 13px;
    color: var(--muted);
    }

    .header .meta .stat {
    display: flex;
    align-items: center;
    gap: 6px;
    }

    .header .meta .stat strong {
    color: var(--accent);
    font-weight: 600;
    }

    /* Navigation */
    .nav {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 48px;
    }

    .nav a {
    display: inline-block;
    padding: 6px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--muted);
    text-decoration: none;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.15s;
    }

    .nav a:hover {
    color: var(--text);
    border-color: var(--accent);
    background: var(--accent-dim);
    }

    /* Section */
    .section {
    margin-bottom: 56px;
    }

    .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 28px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
    }

    .section-header h2 {
    font-size: 22px;
    font-weight: 600;
    letter-spacing: -0.3px;
    }

    .section-header .count {
    font-size: 12px;
    color: var(--accent);
    background: var(--accent-dim);
    padding: 2px 10px;
    border-radius: 12px;
    font-weight: 600;
    }

    /* FAQ Item */
    .faq {
    margin-bottom: 20px;
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    transition: border-color 0.15s;
    }

    .faq:hover { border-color: #3a3d52; }

    .faq-q {
    padding: 18px 22px;
    background: var(--surface);
    cursor: pointer;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    user-select: none;
    }

    .faq-q:hover { background: var(--surface-hover); }

    .faq-q .marker {
    color: var(--accent);
    font-weight: 600;
    font-size: 15px;
    flex-shrink: 0;
    margin-top: 1px;
    }

    .faq-q .question {
    font-weight: 500;
    font-size: 15px;
    line-height: 1.6;
    flex: 1;
    }

    .faq-q .toggle {
    color: var(--muted);
    font-size: 18px;
    flex-shrink: 0;
    transition: transform 0.2s;
    margin-top: 1px;
    }

    .faq.open .faq-q .toggle { transform: rotate(45deg); }

    .faq-a {
    display: none;
    padding: 20px 22px 22px 48px;
    border-top: 1px solid var(--border);
    background: var(--bg);
    }

    .faq.open .faq-a { display: block; }

    .faq-a p {
    margin-bottom: 14px;
    color: var(--text);
    line-height: 1.8;
    }

    .faq-a p:last-child { margin-bottom: 0; }

    .faq-a code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    background: var(--code-bg);
    border: 1px solid var(--border);
    padding: 2px 6px;
    border-radius: 4px;
    color: var(--accent);
    }

    .faq-a pre {
    background: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 18px;
    margin: 14px 0;
    overflow-x: auto;
    }

    .faq-a pre code {
    background: none;
    border: none;
    padding: 0;
    font-size: 13px;
    line-height: 1.7;
    color: var(--text);
    }

    .faq-a .tip {
    background: var(--accent-dim);
    border-left: 3px solid var(--accent);
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    margin: 14px 0;
    font-size: 14px;
    color: var(--text);
    }

    .faq-a .tip strong { color: var(--accent); }

    .faq-a a {
    color: var(--blue);
    text-decoration: none;
    border-bottom: 1px solid transparent;
    }

    .faq-a a:hover { border-bottom-color: var(--blue); }

    .faq-a .source {
    font-size: 12px;
    color: var(--muted);
    margin-top: 12px;
    font-style: italic;
    }

    /* Footer */
    .footer {
    margin-top: 64px;
    padding-top: 32px;
    border-top: 1px solid var(--border);
    font-size: 13px;
    color: var(--muted);
    line-height: 1.7;
    }

    @media (max-width: 640px) {
    .container { padding: 32px 16px; }
    .header h1 { font-size: 24px; }
    .nav { gap: 6px; }
    .nav a { font-size: 12px; padding: 5px 10px; }
    }
    </style>

    <div class="container">



    <div class="nav" id="nav">
    <a href="#installation">Installation</a>
    <a href="#text-extraction">Text Extraction</a>
    <a href="#table-extraction">Tables</a>
    <a href="#ocr">OCR</a>
    <a href="#pymupdf4llm">PyMuPDF4LLM</a>
    <a href="#images">Images</a>
    <a href="#text-insertion">Text Insertion</a>
    <a href="#annotations">Annotations</a>
    <a href="#forms">Forms & Widgets</a>
    <a href="#fonts">Fonts</a>
    <a href="#merge-split">Merge & Split</a>
    <a href="#geometry">Geometry & Coordinates</a>
    <a href="#performance">Performance</a>
    <a href="#conversion">Conversion</a>
    </div>

    <!-- ===== INSTALLATION ===== -->
    <div class="section" id="installation">
    <div class="section-header">
    <h2>Installation & Setup</h2>
    <span class="count">51 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">I installed PyMuPDF but <code>import pymupdf</code> says "no module named pymupdf". What's wrong?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>This is the single most common installation issue. A few things to check:</p>
        <p>First, make sure you installed <code>pymupdf</code> (not <code>pymypdf</code> or <code>mupdf</code>):</p>
        <pre><code>pip install pymupdf</code></pre>
        <p>Second, verify your IDE (PyCharm, VS Code, etc.) is using the same Python interpreter and virtual environment where you installed it. Try running <code>python -c "import pymupdf; print(pymupdf.__doc__)"</code> directly in a terminal to isolate IDE issues.</p>
        <p>Third, there is a separate PyPI package literally named <code>pymupdf</code> that has nothing to do with PyMuPDF. These two packages cannot coexist in the same environment. If you installed both, uninstall <code>pymupdf</code> and reinstall <code>pymupdf</code>.</p>
        <div class="tip"><strong>Note:</strong> Starting from version 1.24.0, you can also use <code>import pymupdf</code> as an alternative to <code>import pymupdf</code>.</div>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I install PyMuPDF on Apple Silicon (M1/M2/M3)?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>PyMuPDF now ships pre-built wheels for Apple Silicon. A simple <code>pip install pymupdf</code> should work. If it falls back to building from source (sdist), make sure you have SWIG installed first:</p>
        <pre><code>brew install swig
    pip install pymupdf</code></pre>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">When will PyMuPDF support the latest MuPDF version?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>PyMuPDF releases typically follow MuPDF releases by a few days. When a new MuPDF version is released, the PyMuPDF team updates bindings and pushes a new release within 1-2 days. Check the <a href="https://pymupdf.readthedocs.io/en/latest/changes.html">changelog</a> for the latest version mapping.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I install PyMuPDF in a Docker container?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Standard <code>pip install pymupdf</code> works in most Linux containers. For OCR support, you also need Tesseract language data files. A typical Dockerfile:</p>
        <pre><code>FROM python:3.11-slim
    RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-eng
    RUN pip install pymupdf</code></pre>
        <div class="tip"><strong>Performance note:</strong> OCR in Docker may be slower than on bare metal due to thread detection differences. Explicitly setting <code>OMP_THREAD_LIMIT</code> can help.</div>
    </div>
    </div>

    </div>

    <!-- ===== TEXT EXTRACTION ===== -->
    <div class="section" id="text-extraction">
    <div class="section-header">
    <h2>Text Extraction</h2>
    <span class="count">110 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">What are the different text extraction modes and when should I use each?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p><code>page.get_text()</code> accepts several output format options:</p>
        <p><code>"text"</code> — Plain text. Good for simple extraction where layout doesn't matter.</p>
        <p><code>"blocks"</code> — Returns a list of text blocks with bounding boxes. Useful for identifying paragraphs.</p>
        <p><code>"words"</code> — Individual words with positions. Good for spatial analysis.</p>
        <p><code>"dict"</code> — Structured dictionary with blocks, lines, and spans including font information. Use this when you need font names, sizes, and colors.</p>
        <p><code>"rawdict"</code> — Like "dict" but with individual character-level positions. The most detailed but largest output. Use when you need exact character placement.</p>
        <p><code>"json"</code> / <code>"rawjson"</code> — Same as dict/rawdict but as JSON strings. Easier to save to a file for inspection.</p>
        <div class="tip"><strong>Harald's advice:</strong> If you want to inspect the output structure, use <code>"json"</code> or <code>"rawjson"</code> and save to a file rather than trying to dump a deeply nested dict to CSV.</div>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">I can see text in the PDF but <code>get_text()</code> returns empty or garbled characters. Why?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Several possible causes:</p>
        <p><strong>Scanned PDF:</strong> The page is an image, not real text. You need OCR. See the <a href="#ocr">OCR section</a>.</p>
        <p><strong>Scrambled encoding:</strong> Some PDF creators intentionally scramble character sequences as copy-protection. The text looks correct visually but the internal encoding is randomized. There is no reliable way to detect this programmatically. If you see lots of <code>U+FFFD</code> (replacement characters), this is likely the cause.</p>
        <p><strong>Custom font encoding:</strong> The font does not provide a back-translation to Unicode. If the font's internal <code>/ToUnicode</code> map is missing, the information simply cannot be recovered. OCR is your fallback here.</p>
        <div class="tip"><strong>Diagnostic:</strong> Try <code>page.get_text("rawdict")</code> and inspect the character codes. If they're all <code>0xFFFD</code> or nonsensical, the encoding is broken at the PDF level, not a PyMuPDF issue.</div>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I extract text from a specific rectangular area of a page?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Use the <code>clip</code> parameter:</p>
        <pre><code>rect = pymupdf.Rect(100, 100, 400, 300)
    text = page.get_text(clip=rect)

    # With full detail:
    data = page.get_text("rawdict", clip=rect)</code></pre>
        <p>This works with all output formats ("text", "dict", "rawdict", etc.).</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Text extraction doesn't follow reading order. Columns are mixed up. How do I fix this?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Text extraction order depends entirely on how the PDF was created. The internal order may not match visual reading order. Use <code>sort=True</code> to sort blocks by position (top-left to bottom-right):</p>
        <pre><code>text = page.get_text(sort=True)</code></pre>
        <p>For multi-column layouts, this helps but isn't perfect. You may need to identify column boundaries yourself using block bounding boxes and split text accordingly. There is no universal solution because PDF creators can store text in arbitrary order.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I extract only bold (or italic) text from a PDF?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Use <code>"dict"</code> output and filter by span flags:</p>
        <pre><code>data = page.get_text("dict")
    for block in data["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                # flags: bit 0 = superscript, bit 1 = italic, 
                # bit 2 = serif, bit 3 = monospace, bit 4 = bold
                if span["flags"] & (1 << 4):  # bold
                    print(span["text"])</code></pre>
        <p>You can also check the font name. Bold fonts typically have "Bold", "Bd", or "Heavy" in their name.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I find and locate specific text on a page?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Use <code>page.search_for()</code>:</p>
        <pre><code>areas = page.search_for("your search term")
    for rect in areas:
        print(rect)  # pymupdf.Rect with coordinates</code></pre>
        <p>This returns a list of <code>Rect</code> objects showing where each occurrence appears. Note: regular expressions are not supported. If you need regex matching, first extract the full text with <code>get_text()</code>, find matches, then use <code>search_for()</code> to locate each match on the page.</p>
        <div class="tip"><strong>Performance:</strong> Adding <code>quads=True</code> is actually slightly faster than the default, because rects are internally converted from quads.</div>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Can I render specific spans from rawdict back onto a blank page?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Yes, but it requires manual work. You need to: (1) extract the font(s) used in the spans, (2) write your own positioning code using the character-level data from <code>"rawdict"</code>, and (3) use <code>TextWriter</code> or <code>insert_text()</code> to place each character. This is an advanced use case where you're essentially re-rendering specific text elements.</p>
    </div>
    </div>

    </div>

    <!-- ===== TABLE EXTRACTION ===== -->
    <div class="section" id="table-extraction">
    <div class="section-header">
    <h2>Table Extraction</h2>
    <span class="count">23 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I extract tables from a PDF into a pandas DataFrame?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <pre><code>import pymupdf
    import pandas as pd

    doc = pymupdf.open("input.pdf")
    page = doc[0]  # first page
    tables = page.find_tables()

    for table in tables:
        df = table.to_pandas()
        print(df)</code></pre>
        <p>The <code>find_tables()</code> method detects tables using vector graphics (lines and rectangles). No intermediate image conversion is involved.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">find_tables() isn't detecting my table. What can I do?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Table detection depends on how the table was constructed in the PDF. Common issues:</p>
        <p><strong>No visible borders:</strong> If the table has no drawn lines or rectangles, the detection may fail. Try the <code>strategy="text"</code> parameter for text-based detection.</p>
        <p><strong>Background colors only:</strong> Some tables use cell background colors without borders. These are harder to detect reliably.</p>
        <p>PyMuPDF's table extraction is ported from pdfplumber (chosen over alternatives like tabula for its pure-Python implementation and better accuracy). For extremely unusual table structures, you may need to combine <code>get_text("dict")</code> with your own spatial logic.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Can I extract a table, modify it, and write it back to the same location in the PDF?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>This has a very high probability of failure. You can extract and store table content, structure, and location, but writing it back only works if there are zero structural changes: no new cells, no removed cells, no cell size changes, no merged cells. Even then, there is no native "replace table" function. You would need to redact the original area and rebuild the table from scratch using text insertion and drawing commands.</p>
    </div>
    </div>

    </div>

    <!-- ===== OCR ===== -->
    <div class="section" id="ocr">
    <div class="section-header">
    <h2>OCR</h2>
    <span class="count">40 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How does OCR work in PyMuPDF? Does it use Tesseract?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Yes. MuPDF contains the Tesseract C++ code directly (it's compiled in, not called as an external process). PyMuPDF calls MuPDF functions to invoke Tesseract. The only external requirement is Tesseract language data files (tessdata). Over 100 languages are supported.</p>
        <p>There is no Python-level Tesseract dependency. Everything runs through the C/C++ layer.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I OCR an image file (not a PDF)?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <pre><code>import pymupdf

    pix = pymupdf.Pixmap("image.png")

    # Remove alpha channel if present (required for OCR)
    if pix.alpha:
        pix = pymupdf.Pixmap(pix, 0)

    # Create a 1-page PDF with OCR text layer
    doc = pymupdf.open("pdf", pix.pdfocr_tobytes())

    # Now extract the text
    text = doc[0].get_text()</code></pre>
        <div class="tip"><strong>Common error:</strong> If your image has a transparency (alpha) channel, OCR will fail. Always check and remove it with <code>pymupdf.Pixmap(pix, 0)</code> first.</div>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I OCR a specific language (e.g., Ukrainian, Chinese)?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Install the Tesseract language data file for your language, then specify it:</p>
        <pre><code># For a full page OCR:
    tp = page.get_textpage_ocr(language="ukr")  # Ukrainian
    text = page.get_text(textpage=tp)

    # For image-to-PDF OCR:
    doc = pymupdf.open("pdf", pix.pdfocr_tobytes(language="chi_sim"))  # Chinese Simplified</code></pre>
        <p>Make sure the corresponding <code>.traineddata</code> file exists in your Tesseract data directory.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">OCR is very slow in my Docker container compared to running locally. Why?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Tesseract uses OpenMP for parallelism. In Docker, thread detection may not work correctly, causing it to use fewer threads than available. Try setting <code>OMP_THREAD_LIMIT</code> environment variable explicitly. Also ensure your container has adequate CPU resources allocated.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I determine if a page needs OCR or already has extractable text?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>There's no silver bullet. A reasonable heuristic:</p>
        <pre><code>text = page.get_text().strip()
    if not text or len(text) < 10:
        # Probably needs OCR
        tp = page.get_textpage_ocr()
        text = page.get_text(textpage=tp)</code></pre>
        <p>For scrambled text (copy-protection), you might get text that looks like random characters. Checking for high rates of <code>U+FFFD</code> replacement characters can help detect this. But detecting scrambled text reliably is fundamentally difficult.</p>
    </div>
    </div>

    </div>

    <!-- ===== PYMUPDF4LLM ===== -->
    <div class="section" id="pymupdf4llm">
    <div class="section-header">
    <h2>PyMuPDF4LLM & AI Pipelines</h2>
    <span class="count">66 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Does PyMuPDF4LLM send my data to any external service or API?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p><strong>No.</strong> PyMuPDF4LLM is completely derived from PyMuPDF. There is no access to anything beyond your local machine. No calls to any AI, LLM, RAG, or cloud service. Everything works exactly the same when all internet access is blocked. It is fully GDPR-compatible in terms of data processing.</p>
        <p class="source">This is the most frequently asked question about PyMuPDF4LLM on Discord.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I get page-level metadata (like LlamaIndex documents) from PyMuPDF4LLM?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Use the <code>page_chunks</code> option:</p>
        <pre><code>import pymupdf4llm

    # Returns a list of page dictionaries (similar to LlamaIndex Document objects)
    result = pymupdf4llm.to_markdown("input.pdf", page_chunks=True)

    for page in result:
        print(page["metadata"])  # page number, etc.
        print(page["text"][:200])  # markdown content</code></pre>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">PyMuPDF4LLM merges my tables into plain text instead of markdown tables. Why?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Table detection depends on the PDF structure. Some tables are defined in unusual ways (partial borders, background colors only on some cells, inconsistent cell structures). There's a limit to how creatively a table might have been defined.</p>
        <p>Try adjusting table detection parameters. If the table structure is truly unconventional, you may need to fall back to <code>page.find_tables()</code> with custom parameters and handle table conversion to markdown separately.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">What is the licensing situation for PyMuPDF4LLM in a commercial product?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>PyMuPDF4LLM has the same license as PyMuPDF and MuPDF: either GNU AGPL or a commercial license from Artifex. If you're using it as part of a commercial product's data pipeline (even if it's just parsing PDFs for a RAG system), the AGPL obligations apply. Contact <a href="https://artifex.com/contact/">Artifex</a> to evaluate your situation and discuss commercial licensing.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Can I process multiple PDFs at once with PyMuPDF4LLM?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>The API processes one PDF at a time. For batch processing, loop over your files:</p>
        <pre><code>import pymupdf4llm
    from pathlib import Path

    for pdf in Path("./docs").glob("*.pdf"):
        md = pymupdf4llm.to_markdown(str(pdf), page_chunks=True)
        # process each result</code></pre>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Which AI frameworks use PyMuPDF for PDF parsing?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>LlamaIndex uses PyMuPDF. LangChain includes PyMuPDF as one of its PDF loader alternatives. Many RAG pipeline implementations in the ecosystem rely on PyMuPDF for the extraction layer.</p>
    </div>
    </div>

    </div>

    <!-- ===== IMAGES ===== -->
    <div class="section" id="images">
    <div class="section-header">
    <h2>Images & Pixmaps</h2>
    <span class="count">70 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Extracted images have a black background where transparency should be. How do I preserve transparency?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>When extracting images, check for an SMask (soft mask). The <code>page.extract_image(xref)</code> result dictionary has an <code>"smask"</code> key. If its value is > 0, that's the xref of the transparency mask. You need to extract both and combine them:</p>
        <pre><code>img = page.extract_image(xref)
    if img["smask"] > 0:
        mask_pix = pymupdf.Pixmap(doc, img["smask"])
        main_pix = pymupdf.Pixmap(doc, xref)
        # Combine image with its mask
        pix = pymupdf.Pixmap(main_pix, mask_pix)
    else:
        pix = pymupdf.Pixmap(doc, xref)</code></pre>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I insert an image into a page?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Use <code>page.insert_image()</code> with a target rectangle:</p>
        <pre><code># Insert from file
    rect = pymupdf.Rect(100, 100, 300, 250)
    page.insert_image(rect, filename="logo.png")

    # Use page.rect for full-page:
    page.insert_image(page.rect, filename="background.jpg")</code></pre>
        <div class="tip"><strong>Common mistake:</strong> Don't pass the filename as a positional argument. Use <code>filename=</code> explicitly. The call pattern is <code>insert_image(rect, filename=None, pixmap=None, stream=None, ...)</code>.</div>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I render a page to an image (screenshot)?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <pre><code>page = doc[0]
    pix = page.get_pixmap(dpi=150)  # default is 72 dpi
    pix.save("page.png")

    # Higher resolution:
    pix = page.get_pixmap(dpi=300)</code></pre>
        <p>You can also use a <code>Matrix</code> for more control over scaling and rotation.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Can I extract vector graphics (logos, diagrams) as images?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Vector graphics (line art) cannot be extracted as images directly because they aren't images in the PDF. PyMuPDF can extract vector drawings as path data via <code>page.get_drawings()</code>, which returns elementary drawing commands (lines, curves, rectangles). To get a visual representation, render the relevant area to a Pixmap using a clip rectangle.</p>
    </div>
    </div>

    </div>

    <!-- ===== TEXT INSERTION ===== -->
    <div class="section" id="text-insertion">
    <div class="section-header">
    <h2>Text Insertion</h2>
    <span class="count">55 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">What's the difference between <code>insert_text</code>, <code>insert_textbox</code>, and <code>insert_htmlbox</code>?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p><code>page.insert_text(point, text)</code> — Places text starting at a single point. No wrapping. You control exact position.</p>
        <p><code>page.insert_textbox(rect, text)</code> — Fills text into a rectangle with automatic line breaks. Returns a value indicating overflow (negative = text didn't fit).</p>
        <p><code>page.insert_htmlbox(rect, html)</code> — Like textbox but accepts HTML/CSS for rich formatting. Tremendously more flexible: supports mixed fonts, colors, alignment, etc. This is generally the recommended approach for complex text insertion.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">My inserted text is white (invisible). How do I make it black?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Black is the default color. If text appears white, you may be inserting on a dark background or there's a color space issue. Explicitly set color:</p>
        <pre><code>page.insert_text((100, 100), "Hello", color=pymupdf.pdfcolor["black"])

    # Or using RGB tuple (0-1 range):
    page.insert_text((100, 100), "Hello", color=(0, 0, 0))</code></pre>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I create a landscape page?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <pre><code># Use paper size with "-l" suffix for landscape
    mediabox = pymupdf.paper_rect("a4-l")
    page = doc.new_page(width=mediabox.width, height=mediabox.height)

    # See all available paper sizes:
    print(pymupdf.paper_sizes())</code></pre>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I set margins when inserting text on a new page?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Create a fill rectangle with margins subtracted from the page rectangle:</p>
        <pre><code>page = doc.new_page()
    left, top, right, bottom = 72, 72, 72, 72  # 1 inch margins
    fill_rect = page.rect + (left, top, -right, -bottom)
    page.insert_textbox(fill_rect, text, fontname="helv", fontsize=11)</code></pre>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">The Euro sign (€) and other special characters show as "?" in my text. Why?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>The built-in Base-14 fonts (like "helv") only support characters up to Unicode 256. The Euro sign is at <code>0x80</code> in this range. Either replace <code>€</code> with <code>chr(0x80)</code> in your text, or use a proper Unicode font file:</p>
        <pre><code>page.insert_text((100, 100), "Price: 50€",
        fontfile="/path/to/arial.ttf",
        fontname="arial")</code></pre>
        <p>For CJK and extended characters, use the <code>pymupdf-fonts</code> package which includes FiraGO and CJK fallback fonts.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I dynamically fit text to a rectangle (auto font size)?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Two approaches:</p>
        <p>Option 1: Reduce font size until it fits:</p>
        <pre><code>fontsize = 20
    while True:
        rc = page.insert_textbox(rect, text, fontsize=fontsize)
        if rc >= 0:  # positive = text fit
            break
        fontsize -= 0.5  # shrink and retry</code></pre>
        <p>Option 2: Use <code>insert_htmlbox()</code> which handles overflow more gracefully and gives you CSS-level control.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I add text on top of an image (with a background rectangle)?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Draw the background rectangle first, then insert text on top:</p>
        <pre><code>shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(fill=(1, 1, 0.8))  # light yellow fill
    shape.commit()

    page.insert_textbox(rect, text, fontsize=12)</code></pre>
        <p>Order matters: shapes drawn first appear behind text inserted later.</p>
    </div>
    </div>

    </div>

    <!-- ===== ANNOTATIONS ===== -->
    <div class="section" id="annotations">
    <div class="section-header">
    <h2>Annotations</h2>
    <span class="count">112 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Does MuPDF support "cloudy" border style for annotations?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>No. MuPDF only supports plain borders at the moment. The cloudy border effect (common in Adobe PDF annotations) is not implemented in MuPDF's C core, so it's not available through PyMuPDF either.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I redact (permanently remove) content from a PDF?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <pre><code># Step 1: Mark areas for redaction
    rect = page.search_for("confidential")[0]
    page.add_redact_annot(rect, fill=(1, 1, 1))  # white fill

    # Step 2: Apply redactions (permanently removes content)
    page.apply_redactions()

    doc.save("redacted.pdf")</code></pre>
        <p>After applying redactions, the original content is permanently removed from the PDF. This is a two-step process by design, so you can review before committing.</p>
        <div class="tip"><strong>Replacement text:</strong> You can also insert replacement text during redaction, but the formatting options are limited. For more control, apply the redaction to clear the area, then use <code>insert_text()</code> or <code>insert_htmlbox()</code> in a separate step.</div>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Can I "flatten" annotations so they become part of the page content?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>MuPDF has work-in-progress support for this. If you flatten annotations, they become part of the page content stream and can no longer be edited, moved, or recognized as annotations by other PDF viewers. For form fields, this means they lose interactivity.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I add a highlight annotation to found text?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <pre><code>quads = page.search_for("important text", quads=True)
    for quad in quads:
        annot = page.add_highlight_annot(quad)
        annot.set_colors(stroke=(1, 1, 0))  # yellow
        annot.update()</code></pre>
        <p>Using <code>quads=True</code> gives more precise highlighting, especially for rotated or non-horizontal text.</p>
    </div>
    </div>

    </div>

    <!-- ===== FORMS ===== -->
    <div class="section" id="forms">
    <div class="section-header">
    <h2>Forms & Widgets</h2>
    <span class="count">31 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I create a fillable form field (widget) in a PDF?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <pre><code>import pymupdf

    doc = pymupdf.open()
    page = doc.new_page()

    # Create a text input field
    widget = pymupdf.Widget()
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    widget.rect = pymupdf.Rect(50, 50, 250, 80)
    widget.field_name = "name"
    widget.field_value = "Enter name"

    annot = page.add_widget(widget)
    doc.save("form.pdf")</code></pre>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I create a date field widget?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <pre><code>widget = pymupdf.Widget()
    widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
    widget.field_flags |= pymupdf.PDF_WIDGET_TX_FORMAT_DATE
    widget.rect = pymupdf.Rect(20, 20, 160, 80)
    widget.field_name = "Date"
    widget.field_value = "12/12/2024"
    annot = page.add_widget(widget)</code></pre>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Fonts in my form fields don't render correctly on mobile devices or non-Adobe readers.</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>This is a common problem. PDF viewers that don't have the specified font will substitute or fail to render. The solution is to embed fonts in the PDF. Note that new form fields created by PyMuPDF have certain font restrictions. If you need specific fonts embedded, you may need to work at the xref level:</p>
        <pre><code># After adding a widget:
    annot = page.add_widget(widget)
    xref = annot.xref  # use this to access low-level PDF objects</code></pre>
    </div>
    </div>

    </div>

    <!-- ===== FONTS ===== -->
    <div class="section" id="fonts">
    <div class="section-header">
    <h2>Fonts</h2>
    <span class="count">70 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">What fonts are available by default without loading external font files?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>The PDF Base-14 fonts are always available:</p>
        <p><code>"helv"</code> (Helvetica), <code>"heit"</code> (Helvetica Italic), <code>"hebo"</code> (Helvetica Bold), <code>"hebi"</code> (Helvetica Bold Italic)</p>
        <p><code>"tiro"</code> (Times Roman), <code>"tiit"</code>, <code>"tibo"</code>, <code>"tibi"</code></p>
        <p><code>"cour"</code> (Courier), <code>"coit"</code>, <code>"cobo"</code>, <code>"cobi"</code></p>
        <p><code>"symb"</code> (Symbol), <code>"zadb"</code> (ZapfDingbats)</p>
        <p>These only support characters up to about Unicode 256. For CJK, extended Latin, Arabic, etc., install <code>pymupdf-fonts</code> or provide your own font files.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I get the font name of extracted text?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Use <code>"dict"</code> output format. Each span includes font information:</p>
        <pre><code>data = page.get_text("dict")
    for block in data["blocks"]:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                print(f"Font: {span['font']}, Size: {span['size']}")</code></pre>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Is there a universal fallback font that can render any character?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>No single font covers everything including emojis. FiraGO (available in <code>pymupdf-fonts</code>) covers extended Latin and many scripts not in CJK. The CJK fallback font ("Droid Sans Fallback Regular") covers Chinese, Japanese, and Korean. But you cannot change or extend the fallback font chain. For maximum coverage, use a rich font like FiraGO as your primary and accept that some exotic characters may not render.</p>
    </div>
    </div>

    </div>

    <!-- ===== MERGE & SPLIT ===== -->
    <div class="section" id="merge-split">
    <div class="section-header">
    <h2>Merging & Splitting PDFs</h2>
    <span class="count">34 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I extract specific pages from one PDF into a new PDF?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <pre><code>src = pymupdf.open("input.pdf")
    doc = pymupdf.open()  # new empty PDF
    doc.insert_pdf(src, from_page=0, to_page=4)  # pages 1-5 (0-based)
    doc.save("output.pdf")</code></pre>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">My output PDF is the same size as the original even though I only extracted 2 pages from 20. Why?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Different pages often share resources (fonts, images, etc.) that are referenced but not deduplicated on save. Use <code>ez_save()</code> instead of <code>save()</code>, or use save with garbage collection and deflation:</p>
        <pre><code># Best option for size reduction:
    doc.ez_save("output.pdf")

    # Or with explicit options:
    doc.save("output.pdf", garbage=4, deflate=True, clean=True)</code></pre>
        <p><code>clean=True</code> can also help by cleaning content streams, but note this may increase file size for some PDFs (due to decompression of already-compressed streams).</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I overlay one page on top of another (watermark / stamp)?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Use <code>page.show_pdf_page()</code> to render a source page onto a target page:</p>
        <pre><code>src = pymupdf.open("watermark.pdf")
    doc = pymupdf.open("document.pdf")

    for page in doc:
        page.show_pdf_page(page.rect, src, 0)  # overlay page 0 of watermark

    doc.save("stamped.pdf")</code></pre>
        <div class="tip"><strong>Note:</strong> <code>insert_pdf()</code> adds new pages. <code>show_pdf_page()</code> overlays content onto an existing page. These are different operations.</div>
    </div>
    </div>

    </div>

    <!-- ===== GEOMETRY ===== -->
    <div class="section" id="geometry">
    <div class="section-header">
    <h2>Geometry & Coordinates</h2>
    <span class="count">130 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">What is the coordinate system in PyMuPDF? Where is (0,0)?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>The origin (0,0) is at the <strong>top-left</strong> of the page. X increases to the right, Y increases downward. This matches screen coordinates but differs from the PDF specification (which uses bottom-left origin). PyMuPDF handles the transformation internally.</p>
        <p>An A4 page in portrait has dimensions approximately (0, 0, 595, 842) in points (1 point = 1/72 inch).</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">What's the difference between <code>page.rect</code>, <code>page.mediabox</code>, and <code>page.cropbox</code>?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p><code>page.mediabox</code> — The physical page size as defined in the PDF. This is the largest boundary.</p>
        <p><code>page.cropbox</code> — The visible area when displayed. May be smaller than mediabox. This is what viewers typically show.</p>
        <p><code>page.rect</code> — The effective page rectangle considering rotation. Use this for most operations as it reflects what you actually see.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">What does bbox mean and what order are the coordinates?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>A bounding box (bbox) is defined as <code>(x0, y0, x1, y1)</code> where <code>(x0, y0)</code> is the top-left corner and <code>(x1, y1)</code> is the bottom-right corner. This forms a <code>pymupdf.Rect</code>:</p>
        <pre><code>rect = pymupdf.Rect(x0, y0, x1, y1)
    print(rect.width)   # x1 - x0
    print(rect.height)  # y1 - y0
    print(rect.tl)      # top-left Point(x0, y0)
    print(rect.br)      # bottom-right Point(x1, y1)</code></pre>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I check if a word/block is inside a given rectangle?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Use rectangle containment or intersection:</p>
        <pre><code>region = pymupdf.Rect(100, 100, 400, 300)
    word_rect = pymupdf.Rect(word[:4])  # first 4 elements of a "words" tuple

    if word_rect in region:        # fully contained
        print("inside")
    if word_rect.intersects(region):  # overlaps
        print("overlaps")</code></pre>
    </div>
    </div>

    </div>

    <!-- ===== PERFORMANCE ===== -->
    <div class="section" id="performance">
    <div class="section-header">
    <h2>Performance & Large Files</h2>
    <span class="count">20 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I handle very large PDFs without running out of memory?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Close input/output documents at intervals to free resources. You can also shrink MuPDF's internal cache:</p>
        <pre><code>import pymupdf

    # Process in batches
    for i in range(0, total_pages, 50):
        src = pymupdf.open("huge.pdf")
        doc = pymupdf.open()
        doc.insert_pdf(src, from_page=i, to_page=min(i+49, total_pages-1))
        doc.save(f"batch_{i}.pdf")
        doc.close()
        src.close()
        pymupdf.TOOLS.store_shrink(100)  # free MuPDF cache</code></pre>
        <p>The major memory consumer is shared resources (fonts, images) that are referenced across pages. Batch processing with intermediate saves helps.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">Can I use multiprocessing with PyMuPDF?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Yes, but each process needs its own document objects. Don't share <code>pymupdf.Document</code> objects across processes. A common pattern is to split work by page ranges, let each process open the file independently, and combine results afterward.</p>
        <div class="tip"><strong>Note:</strong> Threading with GIL release was tested but found to have intolerable overhead. Multiprocessing is the better approach for parallelism.</div>
    </div>
    </div>

    </div>

    <!-- ===== CONVERSION ===== -->
    <div class="section" id="conversion">
    <div class="section-header">
    <h2>Format Conversion</h2>
    <span class="count">41 questions</span>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">How do I convert HTML to PDF?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>Use the <code>Story</code> class:</p>
        <pre><code>import pymupdf

    html = """
    &lt;h1&gt;Hello World&lt;/h1&gt;
    &lt;p&gt;This is a &lt;b&gt;bold&lt;/b&gt; paragraph.&lt;/p&gt;
    """

    story = pymupdf.Story(html)
    writer = pymupdf.DocumentWriter("output.pdf")
    mediabox = pymupdf.paper_rect("a4")

    while True:
        device = writer.begin_page(mediabox)
        more, filled = story.place(mediabox + (36, 36, -36, -36))
        story.draw(device)
        writer.end_page()
        if not more:
            break

    writer.close()</code></pre>
        <p>The Story class supports HTML and CSS for layout, including fonts, colors, and basic page flow.</p>
    </div>
    </div>

    <div class="faq">
    <div class="faq-q"><span class="marker">Q</span><span class="question">What document formats can PyMuPDF open?</span><span class="toggle">+</span></div>
    <div class="faq-a">
        <p>PDF, XPS, EPUB, MOBI, FB2, CBZ, SVG, and various image formats (PNG, JPEG, BMP, TIFF, etc.). All are opened with <code>pymupdf.open()</code>. For image formats, the result is a single-page document.</p>
    </div>
    </div>

    </div>

    <!-- Footer -->


    </div>

    <script>
    document.querySelectorAll('.faq-q').forEach(q => {
    q.addEventListener('click', () => {
        q.parentElement.classList.toggle('open');
    });
    });
    </script>

