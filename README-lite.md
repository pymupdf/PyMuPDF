<p align="center">
  <a href="https://pymupdf.io?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=logo&utm_term=website">
    <img loading="lazy" alt="PyMuPDF" src="https://pymupdf.pro/images/py-mupdf-github-icon.png" width="96px" alt="PyMuPDF logo"/>
  </a>
</p>

# PyMuPDF Lite

<p align="center">
 <a href="https://trendshift.io/repositories/11536" target="_blank"><img src="https://trendshift.io/api/badge/repositories/11536" alt="pymupdf%2FPyMuPDF | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

[![Docs](https://img.shields.io/badge/docs-live-brightgreen)](https://pymupdf.readthedocs.io?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=badges&utm_term=docs)
[![PyPI Version](https://img.shields.io/pypi/v/pymupdf?color=blue&label=PyPI)](https://pypi.org/project/PyMuPDF/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pymupdf)](https://pypi.org/project/pymupdf/)
[![License AGPL](https://img.shields.io/github/license/pymupdf/pymupdf)](https://github.com/pymupdf/PyMuPDF/blob/master/COPYING)
[![PyPI Downloads](https://static.pepy.tech/badge/pymupdf/month)](https://pepy.tech/projects/pymupdf)
[![Github Stars](https://img.shields.io/github/stars/pymupdf/PyMuPDF?style=social)](https://github.com/pymupdf/PyMuPDF/stargazers)
[![Discord](https://img.shields.io/discord/770681584617652264?color=6A7EC2&logo=discord&logoColor=ffffff)](https://artifex.com/discord/artifex?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=badges&utm_term=discord)
[![Forum](https://img.shields.io/badge/Forum-ff6600?logo=python&logoColor=ffffff)](https://forum.mupdf.com/c/general/4?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=badges&utm_term=forum)
[![Twitter](https://img.shields.io/twitter/follow/pymupdf)](https://x.com/pymupdf)
[![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97_Hugging_Face-007ec6)](https://huggingface.co/artifex-software)


**The PDF engine behind over 50 million monthly downloads, powering AI pipelines worldwide.**

**PyMuPDF Lite** is a cut-down version of [PyMuPDF](https://pypi.org/project/pymupdf/) without the [PyMuPDF Layout engine](https://pymupdf.io/use-cases/layout).  

[![Star on GitHub](https://img.shields.io/github/stars/pymupdf/PyMuPDF.svg?style=for-the-badge&label=Star&logo=github)](https://github.com/pymupdf/PyMuPDF/)

---

## Why PyMuPDF Lite?

- **Minimal** 
	- Reduced disc space (e.g. 25MB pymupdf-lite vs 100's of MB for pymupdf and its required packages.
    - Available for more OS's, cpus and python versions, for example:
         - Pyodide
         - Musllinux
         - MacOS-x64
         - All official python versions
- **No mandatory dependencies** — `pip install pymupdf-lite` and you're done


---

## Installation

```bash
pip install pymupdf-lite
```

Wheels are available for **Windows**, **macOS**, and **Linux** on Python 3.11–3.15. If no pre-built wheel exists for your platform, pip will compile from source (requires a C/C++ toolchain).

See: [https://pypi.org/project/pymupdf-lite/#files](https://pypi.org/project/pymupdf-lite/#files) for the definitive list of available wheels.

## PyMuPDF Config

After installation, run the `pymupdf-config` command,
This will review what is installed and show information about what other packages
(Python and otherwise) may be available for your system and could improve accuracy and speed.



## Usage

Use the API just as you would use PyMuPDF, e.g.

```python
import pymupdf

doc = pymupdf.open("sample.pdf")
...
```

---

## Supported File Formats

### Input

| Category | Formats |
|---|---|
| PDF & derivatives | PDF, XPS, EPUB, CBZ, MOBI, FB2, SVG, TXT, MD |
| Images | PNG, JPEG, BMP, TIFF, GIF, and more |


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


## Supported Python versions

Python **3.11 – 3.15**. Wheels ship for:

- `manylinux` x86\_64 and aarch64
- `musllinux` x86\_64
- macOS x86\_64 and arm64
- Windows x86 and x86\_64

---

## Documentation

Full installation guide, API reference, cookbook, and tutorial at **[pymupdf.readthedocs.io](https://pymupdf.readthedocs.io?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=documentation_community&utm_term=docs)**.


---

## Licensing

PyMuPDF and MuPDF are maintained by [Artifex Software, Inc.](https://artifex.com?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=footer&utm_term=website)

- **Open source** — [GNU AGPL v3](https://www.gnu.org/licenses/agpl-3.0.html). Free for open-source projects.
- **Commercial** — separate commercial licences available from [Artifex](https://artifex.com/licensing?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=footer&utm_term=licensing) for proprietary applications.

---

## Contributing

Contributions are welcome. Please open an issue before submitting large pull requests.

- [Issue tracker](https://github.com/pymupdf/PyMuPDF/issues)
- [Discord community](https://artifex.com/discord/artifex?utm_source=github&utm_medium=referral&utm_campaign=pymupdf_github&utm_content=footer&utm_term=discord)

## ⭐ Support this project

If you find this useful, please consider giving it a star — it helps others discover it!

[![Star on GitHub](https://img.shields.io/github/stars/pymupdf/PyMuPDF.svg?style=for-the-badge&label=Star&logo=github)](https://github.com/pymupdf/PyMuPDF/)
