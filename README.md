<p align="center">
  <a href="https://github.com/pymupdf/PyMuPDF/">
    <img loading="lazy" alt="PyMuPDF" src="https://pymupdf.pro/images/py-mupdf-github-icon.png" width="100px"/>
  </a>
</p>

# PyMuPDF

<p align="center">
 <a href="https://trendshift.io/repositories/11536" target="_blank"><img src="https://trendshift.io/api/badge/repositories/11536" alt="pymupdf%2FPyMuPDF | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

[![Docs](https://img.shields.io/badge/docs-live-brightgreen)](https://pymupdf.readthedocs.io)
[![PyPI Version](https://img.shields.io/pypi/v/pymupdf?color=blue&label=PyPI)](https://pypi.org/project/PyMuPDF/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pymupdf)](https://pypi.org/project/pymupdf/)
[![License AGPL](https://img.shields.io/github/license/pymupdf/pymupdf)](https://github.com/pymupdf/PyMuPDF/blob/master/COPYING)
[![PyPI Downloads](https://static.pepy.tech/badge/pymupdf/month)](https://pepy.tech/projects/pymupdf)
[![Github Stars](https://img.shields.io/github/stars/pymupdf/PyMuPDF?style=social)](https://github.com/pymupdf/PyMuPDF/stargazers)
[![Discord](https://img.shields.io/discord/770681584617652264?color=6A7EC2&logo=discord&logoColor=ffffff)](https://pymupdf.io/discord/artifex/)
[![Forum](https://img.shields.io/badge/Forum-ff6600?logo=python&logoColor=ffffff)](https://forum.mupdf.com/c/general/4)
[![Twitter](https://img.shields.io/twitter/follow/pymupdf4llm)](https://x.com/pymupdf4llm)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97_Hugging_Face-007ec6)](https://huggingface.co/artifex-software)
[![Demo](https://img.shields.io/badge/PyMuPDF4LLM-live?badge&label=DEMO&logo=python&logoColor=ffffff)](https://demo.pymupdf.io)

**The PDF engine behind over 50 million monthly downloads, powering AI pipelines worldwide.**

**PyMuPDF is a high-performance Python library for data extraction, analysis, conversion, rendering and manipulation of PDF (and other) documents.** Built on top of MuPDF — a lightweight, fast C engine — PyMuPDF gives you precise, low-level control over documents alongside high-level convenience APIs. No mandatory external dependencies.

[![Star on GitHub](https://img.shields.io/github/stars/pymupdf/PyMuPDF.svg?style=for-the-badge&label=Star&logo=github)](https://github.com/pymupdf/PyMuPDF/)

---

## Why PyMuPDF?

- **Fast** — powered by [MuPDF](https://mupdf.com/), a best-in-class C rendering engine
- **Accurate** — pixel-perfect text extraction with font, color, and position metadata
- **Versatile** — read, write, annotate, redact, merge, split, and convert documents
- **LLM-ready** — native Markdown output via [PyMuPDF4LLM](https://pypi.org/project/pymupdf4llm/) for RAG and AI pipelines
- **No mandatory dependencies** — `pip install pymupdf` and you're done

---

## Installation

```bash
pip install pymupdf
```

Wheels are available for **Windows**, **macOS**, and **Linux** on Python 3.10–3.14. If no pre-built wheel exists for your platform, pip will compile from source (requires a C/C++ toolchain).

### Optional extras

| Package | Purpose |
|---|---|
| `pymupdf-fonts` | Extended font collection for text output |
| `pymupdf4llm` | LLM/RAG-optimised Markdown and JSON extraction |
| `pymupdfpro` | Adds Office document support |
| `tesseract-ocr` | OCR for scanned pages and images (separate install) |

```bash
# More fonts
pip install pymupdf-fonts

# LLM-ready extraction
pip install pymupdf4llm

# Office support
pip install pymupdfpro

# OCR (Tesseract must be installed separately)
# macOS
brew install tesseract

# Ubuntu / Debian
sudo apt install tesseract-ocr
```

---

## Supported File Formats

### Input

| Category | Formats |
|---|---|
| PDF & derivatives | PDF, XPS, EPUB, CBZ, MOBI, FB2, SVG, TXT |
| Images | PNG, JPEG, BMP, TIFF, GIF, and more |
| Microsoft Office *(Pro)* | DOC, DOCX, XLS, XLSX, PPT, PPTX |
| Korean Office *(Pro)* | HWP, HWPX |

### Output

| Format | Notes |
|---|---|
| PDF | Full fidelity conversion from Office formats |
| SVG | Vector page rendering |
| Image (PNG, JPEG, …) | Page rasterisation at any DPI |
| Markdown | Structure-aware, LLM-ready |
| JSON | Bounding boxes, layout data, per-element detail |
| Plain text | Fast, lightweight extraction |

---


## Quick start

### Extract text

```python
import pymupdf

doc = pymupdf.open("document.pdf")
for page in doc:
    print(page.get_text())
```

### Extract text with layout metadata

```python
import pymupdf

doc = pymupdf.open("document.pdf")
page = doc[0]

blocks = page.get_text("dict")["blocks"]
for block in blocks:
    if block["type"] == 0:  # text block
        for line in block["lines"]:
            for span in line["spans"]:
                print(f"{span['text']!r}  font={span['font']}  size={span['size']:.1f}")
```

### Extract tables

```python
import pymupdf

doc = pymupdf.open("spreadsheet.pdf")
page = doc[0]

tables = page.find_tables()
for table in tables:
    print(table.to_markdown())

    # or get as Pandas DataFrame
    df = table.to_pandas()
```

### Render a page to an image

```python
import pymupdf

doc = pymupdf.open("document.pdf")
page = doc[0]

pixmap = page.get_pixmap(dpi=150)
pixmap.save("page_0.png")
```

### OCR a scanned document

```python
import pymupdf

doc = pymupdf.open("scanned.pdf")
page = doc[0]

# Requires Tesseract installed and on PATH
text = page.get_textpage_ocr(language="eng").extractText()
print(text)
```

### Convert to Markdown for LLMs

```python
import pymupdf4llm

md = pymupdf4llm.to_markdown("report.pdf")
# Pass directly to your LLM or vector store
print(md)
```

### Annotate and redact

```python
import pymupdf

doc = pymupdf.open("contract.pdf")
page = doc[0]

# Add a highlight annotation
rect = pymupdf.Rect(72, 100, 400, 120)
page.add_highlight_annot(rect)

# Add a redaction and apply it
page.add_redact_annot(rect)
page.apply_redactions()

doc.save("contract_redacted.pdf")
```

### Merge PDFs

```python
import pymupdf

merger = pymupdf.open()
for path in ["part1.pdf", "part2.pdf", "part3.pdf"]:
    merger.insert_pdf(pymupdf.open(path))

merger.save("merged.pdf")
```

### Convert an Office document to PDF

```python
import pymupdf.pro

pymupdf.pro.unlock("YOUR-LICENSE-KEY")

doc = pymupdf.open("presentation.pptx")
pdf_bytes = doc.convert_to_pdf()

with open("output.pdf", "wb") as f:
    f.write(pdf_bytes)
```

### Extract LLM-ready Markdown from a Word document

```python
import pymupdf4llm
import pymupdf.pro

pymupdf.pro.unlock("YOUR-LICENSE-KEY")

md = pymupdf4llm.to_markdown("document.docx")
print(md)
```

---

## Features

### Core capabilities

| Feature | Description |
|---|---|
| **Text extraction** | Plain text, rich dict (font, size, color, bbox), HTML, XML, raw blocks |
| **Table detection** | `find_tables()` — locate, extract, and export tables as Markdown or structured data |
| **Image extraction** | Extract embedded images and render any page to a high-resolution `Pixmap` |
| **Rendering** | Render PDF pages to images or `Pixmap` data for use in UI or other workflows |
| **OCR** | Tesseract integration — full-page or partial OCR, configurable language |
| **Annotations** | Read and write highlights, underlines, squiggly lines, sticky notes, free text, ink, stamps |
| **Redaction** | Add and permanently apply redaction annotations |
| **Forms** | Read and fill PDF AcroForm fields |
| **PDF editing** | Insert, delete, and reorder pages; set metadata; merge and split documents |
| **Drawing** | Draw lines, curves, rectangles, and circles; insert HTML boxes |
| **Encryption** | Open password-protected PDFs; save with RC4 or AES encryption |
| **Links** | Extract hyperlinks, internal cross-references, and URI targets |
| **Bookmarks** | Read and write the outline / table of contents tree |
| **Metadata** | Title, author, creation date, producer, subject, and custom entries |
| **Color spaces** | RGB, CMYK, greyscale; color space conversion |

### LLM & AI output (via PyMuPDF4LLM)

| Output | API |
|---|---|
| Markdown | `pymupdf4llm.to_markdown(path)` |
| JSON | `pymupdf4llm.to_json(path)` |
| Plain text | `pymupdf4llm.to_text(path)` |

Supports multi-column layouts, natural reading order and page chunking.


[![Demo](https://img.shields.io/badge/Pymupdf4llm-live?style=for-the-badge&label=DEMO&logo=python&logoColor=ffffff)](https://demo.pymupdf.io)

---

## Supported Python versions

Python **3.10 – 3.14** (as of v1.27.x). Wheels ship for:

- `manylinux` x86\_64 and aarch64
- `musllinux` x86\_64
- macOS x86\_64 and arm64
- Windows x86 and x86\_64

---

## Performance

PyMuPDF is built on MuPDF — one of the fastest PDF rendering engines available. Typical benchmarks against pure-Python PDF libraries show **10–50× speed improvements** for text extraction and **100× or more** for page rendering, with a minimal memory footprint.

For AI workloads, PyMuPDF4LLM processes documents **without a GPU**, cutting infrastructure costs significantly compared to vision-based LLM approaches.

---

## Recipes

<details>
<summary>Extract all images from a PDF</summary>

```python
import pymupdf
from pathlib import Path

doc = pymupdf.open("document.pdf")
out = Path("images")
out.mkdir(exist_ok=True)

for page_index, page in enumerate(doc):
    for img_index, img in enumerate(page.get_images()):
        xref = img[0]
        pix = pymupdf.Pixmap(doc, xref)
        if pix.n > 4:  # convert CMYK
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        pix.save(out / f"page{page_index}_img{img_index}.png")
```
</details>

<details>
<summary>Search for text across a document</summary>

```python
import pymupdf

doc = pymupdf.open("document.pdf")
needle = "confidential"

for page in doc:
    hits = page.search_for(needle)
    if hits:
        print(f"Page {page.number}: {len(hits)} occurrence(s)")
        for rect in hits:
            page.add_highlight_annot(rect)

doc.save("highlighted.pdf")
```
</details>

<details>
<summary>Split a PDF into individual pages</summary>

```python
import pymupdf

doc = pymupdf.open("document.pdf")
for i, page in enumerate(doc):
    out = pymupdf.open()
    out.insert_pdf(doc, from_page=i, to_page=i)
    out.save(f"page_{i + 1}.pdf")
```
</details>

<details>
<summary>Insert a watermark on every page</summary>

```python
import pymupdf

doc = pymupdf.open("document.pdf")
for page in doc:
    page.insert_text(
        point=pymupdf.Point(72, page.rect.height / 2),
        text="DRAFT",
        fontsize=72,
        color=(0.8, 0.8, 0.8),
        rotate=45,
    )

doc.save("watermarked.pdf")
```
</details>

---

## Office Document Processing

PyMuPDF can be extended with PyMuPDF Pro. This adds a conversion layer that handles Microsoft and Korean Office formats natively — no Office installation, no COM interop, no LibreOffice subprocess.

Once unlocked, `pymupdf.open()` accepts Office files exactly like PDFs:

```python
import pymupdf.pro
pymupdf.pro.unlock("YOUR-LICENSE-KEY")

# Works identically regardless of format
for fmt in ["contract.docx", "data.xlsx", "deck.pptx", "report.hwpx"]:
    doc = pymupdf.open(fmt)
    for page in doc:
        print(page.get_text())
```

[Get a trial license key for PyMuPDF Pro](https://pymupdf.pro/try-pro) 

**What you can do with Office documents:**

- Extract text and images page-by-page
- Convert to PDF with `doc.convert_to_pdf()`
- Rasterise pages to PNG/JPEG for visual inspection
- Feed directly into PyMuPDF4LLM for AI-ready output



### Restrictions Without a License Key

When `pymupdf.pro.unlock()` is called **without** a key, the following restrictions apply:

| Restriction | Detail |
|---|---|
| Page limit | Only the **first 3 pages** of any document are accessible |
| Time limit | Evaluation period — functionality expires after a set duration |

All other Pro features work normally within these constraints, making it straightforward to prototype before purchasing a license.


---



## Frequently Asked Questions

### Can I use PyMuPDF, PyMuPDF4LLM and PyMuPDF Pro without sending data to the cloud?

Yes, absolutely — and this is one of PyMuPDF's most significant advantages.

PyMuPDF runs entirely locally. It is a native Python library built on top of the MuPDF C engine. When you call `pymupdf.open()`, `page.get_text()`, `page.find_tables()`, or any other method, everything executes in-process on your own machine. No data is transmitted anywhere.


There are no telemetry calls, no licence validation callbacks, no cloud dependencies of any kind in the open-source AGPL build or the commercial build. Once the package is installed, it works fully air-gapped.

This makes PyMuPDF well-suited for:

- Regulated industries — healthcare (HIPAA), finance, legal, government, where documents cannot leave a controlled environment
- On-premise deployments — servers with no outbound internet access
- Air-gapped systems — classified or sensitive environments
- Self-hosted RAG pipelines — processing confidential documents locally before feeding an on-premise LLM
- Saving on token costs for document pre-processing before sending data to your LLM

The only thing you need an internet connection for is the initial `pip install`. After that, the package and all its capabilities are entirely self-contained.


### Should I `import pymupdf` or `import fitz`?

Use `import pymupdf`. The `fitz` name is a legacy alias that still works as of v1.24.0+, but `import pymupdf` is the recommended and future-proof approach. The two are interchangeable in existing code:

```python
import pymupdf          # recommended
# import fitz           # legacy alias — still works but avoid for new code
```

### Does PyMuPDF work with Korean, Japanese, or Chinese documents?

Yes — PyMuPDF has solid CJK support

### How do I extract Markdown from PDF for LLM?

Let PyMuPDF4LLM do everything (recommended for RAG).

PyMuPDF4LLM is a high-level wrapper that outputs standard text and table content together in an integrated Markdown-formatted string across all document pages PyMuPDF — tables are detected, converted to GitHub-compatible Markdown, and interleaved with surrounding text in the correct reading order. This is the best starting point for feeding an LLM or building a RAG pipeline.

```python
import pymupdf4llm

md = pymupdf4llm.to_markdown("report.pdf")
print(md)
# Tables appear as Markdown | col1 | col2 | ... inline with the text
```


### Text extraction returns garbled characters or empty output. Why?

This usually means the PDF uses custom font encodings without a proper character map (CMAP). The font's glyphs are present but cannot be mapped back to Unicode. In these cases:

- Use OCR as a fallback (`page.get_textpage_ocr()`)
- Consider that scanned PDFs will always need OCR — text extraction on scans returns nothing



### How do I extract text from a specific area of a page?

Pass a `clip` rectangle to `get_text()`:

```python
import pymupdf

doc = pymupdf.open("input.pdf")
page = doc[0]

# Define the area you want (x0, y0, x1, y1) in points
clip = pymupdf.Rect(50, 100, 400, 300)
text = page.get_text("text", clip=clip)
```



### How do I search for text and find its location on the page?

```python
import pymupdf

doc = pymupdf.open("input.pdf")
page = doc[0]

# Returns a list of Rect objects surrounding each match
locations = page.search_for("invoice number")
for rect in locations:
    print(rect)  # e.g. Rect(72.0, 120.5, 210.0, 134.0)
```



### `get_images` shows no images but I can clearly see charts in the PDF. Why?

Charts and diagrams created by tools like matplotlib, Excel, or R are typically rendered as vector graphics (PDF drawing commands), not raster images. `get_images` only lists embedded raster image objects and will not detect vector graphics. To capture these, rasterise the entire page with `page.get_pixmap()`.



### How does OCR work in PyMuPDF? Does it require a separate Tesseract installation?

PyMuPDF uses MuPDF's built-in Tesseract-based OCR support, so there is no Python-level `pytesseract` dependency. However, PyMuPDF still needs access to the **Tesseract language data files** (`tessdata`), and automatic tessdata discovery may invoke the `tesseract` executable (for example, to list available languages) if you do not explicitly provide a tessdata path. In practice, the recommended setup is to either install Tesseract so discovery works automatically, or configure the tessdata location yourself via the `tessdata` parameter or the `TESSDATA_PREFIX` environment variable. Over 100 languages are supported.

```python
import pymupdf

doc = pymupdf.open("scanned.pdf")
page = doc[0]

# Get a text page using OCR
tp = page.get_textpage_ocr(language="eng")
text = page.get_text(textpage=tp)
print(text)
```


### How do I run OCR on a standalone image file (not a PDF)?

```python
import pymupdf

pix = pymupdf.Pixmap("image.png")
if pix.alpha:
    pix = pymupdf.Pixmap(pix, 0)  # remove alpha channel — required for OCR

# Wrap in a 1-page PDF and OCR it
doc = pymupdf.open()
page = doc.new_page(width=pix.width, height=pix.height)
page.insert_image(page.rect, pixmap=pix)
tp = page.get_textpage_ocr()
text = page.get_text(textpage=tp)
```


### How do I highlight text in a PDF?

```python
import pymupdf

doc = pymupdf.open("input.pdf")
page = doc[0]

# Use quads=True for accurate highlights on non-horizontal text
quads = page.search_for("important term", quads=True)
page.add_highlight_annot(quads)

doc.save("highlighted.pdf")
```

PyMuPDF supports all standard PDF text markers: highlight, underline, strikeout, and squiggly.



### How do I permanently redact (remove) content from a PDF?

Redaction is a deliberate two-step process so you can review before committing:

```python
import pymupdf

doc = pymupdf.open("input.pdf")
page = doc[0]

# Step 1: Mark the area(s) to redact
rect = page.search_for("confidential")[0]
page.add_redact_annot(rect, fill=(1, 1, 1))  # white fill

# Step 2: Apply — permanently removes the underlying content
page.apply_redactions()

doc.save("redacted.pdf")
```

After `apply_redactions()`, the original content is gone. It cannot be recovered from the saved file.





### How do I read form field values from a PDF?

```python
import pymupdf

doc = pymupdf.open("form.pdf")
page = doc[0]

for field in page.widgets():
    print(f"{field.field_name}: {field.field_value}")
```



### How do I fill in a PDF form programmatically?

```python
import pymupdf

doc = pymupdf.open("form.pdf")
page = doc[0]

for field in page.widgets():
    if field.field_name == "First Name":
        field.field_value = "Ada"
        field.update()

doc.save("filled_form.pdf")
```



### Can I use multithreading with PyMuPDF?

No. PyMuPDF does not support multithreaded use, even with Python's newer free-threading mode. The underlying MuPDF library only provides partial thread safety, and a fully thread-safe PyMuPDF implementation would still impose a single-threaded overhead — negating the benefit.

**Use multiprocessing instead.** Each process opens the file independently and works on its own page range:

```python
from multiprocessing import Pool
import pymupdf

def process_pages(args):
    path, start, end = args
    doc = pymupdf.open(path)  # each process opens its own handle
    results = []
    for i in range(start, end):
        results.append(doc[i].get_text())
    return results

with Pool(4) as pool:
    chunks = [("input.pdf", 0, 25), ("input.pdf", 25, 50), ...]
    all_results = pool.map(process_pages, chunks)
```



### How can I speed up repeated text extraction on the same page?

Reuse a `TextPage` object. Creating a `TextPage` is the expensive part — once created, switching between extraction formats is cheap:

```python
import pymupdf

page = doc[0]
tp = page.get_textpage()  # create once

text  = page.get_text("text",    textpage=tp)
words = page.get_text("words",   textpage=tp)
data  = page.get_text("dict",    textpage=tp)
```

This can reduce execution time by 50–95% for repeated extractions on the same page.




### How do I read and write PDF metadata?

```python
import pymupdf

doc = pymupdf.open("input.pdf")

# Read
print(doc.metadata)
# {'title': '...', 'author': '...', 'subject': '...', 'keywords': '...', ...}

# Write
doc.set_metadata({
    "title": "Annual Report 2025",
    "author": "Finance Team",
    "keywords": "annual, finance, 2025"
})
doc.save("output.pdf")
```


### How do I read or set the table of contents / bookmarks?

```python
import pymupdf

doc = pymupdf.open("input.pdf")

# Read — returns a list of [level, title, page_number] entries
toc = doc.get_toc()
for level, title, page in toc:
    print(" " * level, title, "→ page", page)

# Write
new_toc = [
    [1, "Introduction",  1],
    [1, "Methods",       5],
    [2, "Data sources",  6],
]
doc.set_toc(new_toc)
doc.save("output.pdf")
```



---

## Documentation

Full installation guide, API reference, cookbook, and tutorial at **[pymupdf.readthedocs.io](https://pymupdf.readthedocs.io)**.

- [Installation guide](https://pymupdf.readthedocs.io/en/latest/installation.html)
- [API reference](https://pymupdf.readthedocs.io/en/latest/classes.html)
- [Cookbook](https://pymupdf.readthedocs.io/en/latest/the-basics.html)
- [Tutorial](https://pymupdf.readthedocs.io/en/latest/tutorial.html)
- [Changelog](https://pymupdf.readthedocs.io/en/latest/changes.html)
- [PyMuPDF4LLM docs](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/)
- [PyMuPDF Pro docs](https://pymupdf.readthedocs.io/en/latest/pymupdf-pro/index.html)

---


## Related projects

| Project | Description |
|---|---|
| [PyMuPDF4LLM](https://github.com/pymupdf/pymupdf4llm) | LLM/RAG-optimised Markdown and JSON extraction |
| [PyMuPDF Pro](https://pymupdf.io/pro) | Adds Office and HWP document support |
| [pymupdf-fonts](https://pypi.org/project/pymupdf-fonts/) | Extended font collection for PyMuPDF text output |

---

## Licensing

PyMuPDF and MuPDF are maintained by [Artifex Software, Inc.](https://artifex.com)

- **Open source** — [GNU AGPL v3](https://www.gnu.org/licenses/agpl-3.0.html). Free for open-source projects.
- **Commercial** — separate commercial licences available from [Artifex](https://artifex.com/licensing) for proprietary applications.

---

## Contributing

Contributions are welcome. Please open an issue before submitting large pull requests.

- [Issue tracker](https://github.com/pymupdf/PyMuPDF/issues)
- [Discord community](https://pymupdf.pro/discord/artifex/)

## ⭐ Support this project

If you find this useful, please consider giving it a star — it helps others discover it!

[![Star on GitHub](https://img.shields.io/github/stars/pymupdf/PyMuPDF.svg?style=for-the-badge&label=Star&logo=github)](https://github.com/pymupdf/PyMuPDF/)
