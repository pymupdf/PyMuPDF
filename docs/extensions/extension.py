import os

from sphinx.errors import ExtensionError
from sphinx.util.fileutil import copy_asset


ASSETS_FILES = {
    'minified': [
        os.path.join('js', 'rtd_sphinx_search.min.js'),
        os.path.join('css', 'rtd_sphinx_search.min.css'),
    ],
    'un-minified': [
        os.path.join('js', 'rtd_sphinx_search.js'),
        os.path.join('css', 'rtd_sphinx_search.css'),
    ]
}


def copy_asset_files(app, exception):
    if exception is None:  # build succeeded
        files = ASSETS_FILES['minified'] + ASSETS_FILES['un-minified']
        for file in files:
            path = os.path.join(os.path.dirname(__file__), 'static', file)
            copy_asset(path, os.path.join(app.outdir, '_static', file.split('.')[-1]))


def inject_static_files(app):
    """Inject correct CSS and JS files based on the value of ``rtd_sphinx_search_file_type``."""

    file_type = app.config.rtd_sphinx_search_file_type
    expected_file_type = ASSETS_FILES.keys()

    if file_type not in expected_file_type:
        raise ExtensionError(f'"{file_type}" file type is not supported')

    files = ASSETS_FILES[file_type]

    for file in files:
        if file.endswith('.js'):
            app.add_js_file(file)
        elif file.endswith('.css'):
            app.add_css_file(file)


def setup(app):

    app.add_config_value('rtd_sphinx_search_file_type', 'minified', 'html')

    app.connect('builder-inited', inject_static_files)
    app.connect('build-finished', copy_asset_files)
