# Contributing to PyMuPDF

Thank you for your interest in contributing to **PyMuPDF**! PyMuPDF is a Python
binding for the [MuPDF](https://www.mupdf.com) library, providing fast and
feature-rich access to PDF, XPS, EPUB, and many other document formats. Every
contribution — from bug reports and documentation improvements to new features
and performance work — helps make the project better.

This document explains how to set up a development environment, run the test
suite, follow the project's coding standards, and submit a pull request.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Help](#getting-help)
3. [Reporting Bugs](#reporting-bugs)
4. [Suggesting Enhancements](#suggesting-enhancements)
5. [Development Setup](#development-setup)
6. [Building from Source](#building-from-source)
7. [Running Tests](#running-tests)
8. [Coding Style](#coding-style)
9. [Commit Messages](#commit-messages)
10. [Pull Request Process](#pull-request-process)
11. [Documentation](#documentation)
12. [Release Process](#release-process)
13. [License](#license)

---

## Code of Conduct

This project is released under the [Artifex Software Inc. License Agreement
for Use of PyMuPDF (Version 1.1)](./COPYING). By participating, you are
expected to be respectful and constructive. Maintainers reserve the right to
remove contributions that are abusive, off-topic, or otherwise inappropriate.

## Getting Help

Before opening an issue, please:

* Search the [existing issues](https://github.com/pymupdf/PyMuPDF/issues) for
  similar reports.
* Read the [official documentation](https://pymupdf.readthedocs.io/).
* Try the latest main branch — your bug may already be fixed.

If you are still stuck, open a GitHub issue with a **minimal reproducible
example**, the output of `pymupdf.__version__`, and your platform information.

## Reporting Bugs

A good bug report should include:

* A clear, descriptive title.
* The exact steps to reproduce the problem, ideally as a small Python snippet.
* The observed behaviour vs. the expected behaviour.
* Stack traces, screenshots, or sample documents (when legally shareable).
* Environment details: OS, Python version, PyMuPDF version, MuPDF backend
  version (printed by `pymupdf.mupdf_version_tuple()`).

## Suggesting Enhancements

Feature requests are welcome. Please describe the use case first and the
proposed API second — this makes it easier for reviewers to evaluate the
proposal and helps avoid premature API decisions.

---

## Development Setup

PyMuPDF is a hybrid project: most of the Python interface lives under
`src/`, while the MuPDF C source tree is fetched at build time. A typical
Linux/macOS development environment looks like:

```bash
# 1. Clone your fork
git clone https://github.com/<your-username>/PyMuPDF.git
cd PyMuPDF

# 2. (Recommended) create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install build prerequisites
pip install --upgrade pip setuptools wheel
```

### Platform prerequisites

* **Linux** — a C/C++ toolchain (`build-essential`), `swig` (≥ 4), and
  `git` are required. On Debian/Ubuntu:

  ```bash
  sudo apt-get install -y build-essential swig git
  ```

* **macOS** — Xcode Command Line Tools (`xcode-select --install`) and
  `swig` from Homebrew (`brew install swig`).

* **Windows** — Visual Studio 2019 or later with the *Desktop development
  with C++* workload, plus `swig` (available via Chocolatey:
  `choco install swig`).

## Building from Source

The build is driven by `setup.py` and `pip`. A typical editable install is:

```bash
# Fetch MuPDF source and build the extension in place
pip install -e .
```

For a wheel build (used by the CI matrix in `.github/workflows/`):

```bash
python -m pip wheel . --no-deps -w wheelhouse/
```

Useful environment variables:

| Variable          | Purpose                                                |
|-------------------|--------------------------------------------------------|
| `PYMUPDF_USE_BSD` | Use the BSD-licensed MuPDF build instead of AGPL.      |
| `PYMUPDF_MUPDF_REF` | Override the MuPDF git ref used during the build.    |
| `PYMUPDF_SKIP_PYMUPDF_C` | Skip compiling `pymupdf_c` (useful for doc-only changes). |

## Running Tests

PyMuPDF ships a comprehensive test runner at `scripts/test.py`. It manages
wheel building, optional baseline comparison, and skipping tests tagged as
flaky or platform-specific.

```bash
# Run the full test suite (builds a wheel first)
python scripts/test.py

# Pass extra arguments through to pytest
python scripts/test.py -- pytest -k 'test_pdf'

# Skip the build step and reuse an existing wheel
python scripts/test.py --skip-build
```

Test configuration lives in `pytest.ini`. Useful markers include
`@pytest.mark.limits` for resource-intensive tests and
`@pytest.mark.sample` for tests that need a sample PDF.

### Continuous Integration

CI is implemented with GitHub Actions; see `.github/workflows/`. The main
`Tests` workflow exercises `ubuntu-latest`, `windows-2022`, and the latest
macOS runners. Pull requests trigger the matrix automatically once the
required status checks are enabled on the repository.

---

## Coding Style

* **Python** — [PEP 8](https://peps.python.org/pep-0008/) with a maximum
  line length of 88 (compatible with `black` defaults). Public APIs use
  type hints.
* **C** — follow the existing MuPDF style: 4-space indentation, lower-case
  function names, and `snake_case` for variables.
* **Docstrings** — every public function, class, and module should have a
  docstring written in reStructuredText so that it renders correctly on
  Read the Docs.

We do not currently enforce formatting with a pre-commit hook, but please run
`black .` (or your editor's formatter) and `ruff check .` on Python files
before opening a pull request.

## Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/)
convention:

```
<type>(<scope>): <short summary>

<body explaining the motivation and approach>

<footer with references to issues or breaking-change notes>
```

Common types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `ci`,
`build`, `chore`, `perf`. A useful summary is 50 characters or fewer and
uses the imperative mood ("add", not "added").

## Pull Request Process

1. **Fork** the repository and create a topic branch off `main`:
   ```bash
   git checkout -b feat/my-improvement
   ```
2. **Make focused commits.** Each commit should represent a logical unit of
   work. Avoid mixing refactors with feature changes.
3. **Update tests and documentation** alongside code changes. Doc-only and
   CI-only PRs are very welcome and reviewed quickly.
4. **Run the full test suite** locally before pushing. CI will run the same
   matrix, but a green local run avoids obvious back-and-forth.
5. **Push** to your fork and open a pull request against `pymupdf:main`.
6. **Fill out the PR template** with:
   * A clear summary of the change.
   * Motivation and any trade-offs considered.
   * A test plan describing how the change was verified.
   * Linked issues (e.g., `Closes #1234`).
7. **Respond to review feedback.** Reviewers may request changes; please
   push follow-up commits to the same branch.

### Review expectations

* Pull requests require at least one maintainer approval before merge.
* The CI matrix must be green.
* Squash-merge is used by default; keep individual commits self-contained
  and clean up obvious fix-ups before requesting review.

## Documentation

* API documentation is generated from docstrings by Sphinx and hosted at
  <https://pymupdf.readthedocs.io/>.
* Narrative guides live in `docs/`; build them locally with:

  ```bash
  pip install -r docs/requirements.txt
  cd docs && make html
  ```

* When you change a public API, update the relevant entry in `docs/` and add
  a note to `changes.txt` summarising the change for the next release.

## Release Process

Releases are cut from `main` by a maintainer and published to PyPI by
GitHub Actions. The release script in `scripts/` updates the version
metadata, refreshes `changes.txt`, and tags the commit. Contributors do not
need to perform any of these steps for their PRs to land.

## License

PyMuPDF is dual-licensed. By submitting a contribution, you agree that your
work will be released under the same terms as the existing source code (see
[`COPYING`](./COPYING) for details). If your employer may claim ownership of
the work, please confirm with them before opening a pull request.

---

Thank you again for helping make PyMuPDF better. We look forward to your
pull request! 🎉