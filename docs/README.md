# PyMuPDF documentation

Welcome to the PyMuPDF documentation. This documentation relies on [Sphinx](https://www.sphinx-doc.org/en/master/) to publish HTML docs from markdown files written with [restructured text](https://en.wikipedia.org/wiki/ReStructuredText) (RST).


## Sphinx version

This README assumes you have [Sphinx v5.0.2 installed](https://www.sphinx-doc.org/en/master/usage/installation.html) on your system.


## Updating the documentation

Within `docs` update the associated restructured text (`.rst`) files. These files represent the corresponding document pages. 


## Building HTML documentation

- Ensure you have the `furo` theme installed:

`pip install furo`

Furo theme, Copyright (c) 2020 Pradyun Gedam <mail@pradyunsg.me>, thank you to:

https://github.com/pradyunsg/furo/blob/main/LICENSE


- From the "docs" location run:

`sphinx-build -b html . build/html`

This then creates the HTML documentation within `build/html`. 

> Use: `sphinx-build -a -b html . build/html` to build all, including the assets in `_static` (important if you have updated CSS).


### Using Sphinx Autobuild

A better way of building the documentation if you are actively working on updates is to run:

`sphinx-autobuild . _build/html`

This will serve the docs on a localhost and auto-update the pages live as you make edits.

### Building the Japanese documentation

- From the "docs" location run:

`sphinx-build -a -b html -D language=ja . _build/html/ja`


- Updating, after changes on the `main` branch and a sync with the main `en` .rst files, from the "docs" location, do:

`sphinx-build -b gettext . _build/gettext`

then:

`sphinx-intl update -p _build/gettext -l ja`

This will update the corresponding `po` files for further edits. Then check these files for "#, fuzzy" entries as the new stuff might exist there and requires editing.


## Building PDF documentation

- First ensure you have [rst2pdf](https://pypi.org/project/rst2pdf/) installed:

`python -m pip install rst2pdf`

- Then run:

`sphinx-build -b pdf . build/pdf`

This will then generate a single PDF for all of the documentation within `build/pdf`.


---


For full details see: [Using Sphinx](https://www.sphinx-doc.org/en/master/usage/index.html) 



