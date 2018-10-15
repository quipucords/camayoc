# coding=utf-8
"""Sphinx documentation generator configuration file.

The full set of configuration options is listed on the Sphinx website:
http://sphinx-doc.org/config.html
"""

import os
import sys

# Add the project root directory to the system path. This allows references
# such as :mod:`camayoc.whatever` to be processed correctly.
ROOT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    os.path.pardir
))
sys.path.insert(0, ROOT_DIR)

# Project information ---------------------------------------------------------

project = 'Camayoc'
author = 'Quipucords Team'
copyright = '2017, {}'.format(author)

# The short X.Y version.
version = ''
# The full version, including alpha/beta/rc tags.
release = ''


# General configuration -------------------------------------------------------

exclude_patterns = ['_build']
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]
language = None
master_doc = 'index'
nitpick_ignore = [
    ('py:class', 'Exception'),
    ('py:class', 'object'),
    ('py:class', 'tuple'),
    ('py:class', 'unittest.case.TestCase'),
    ('py:class', 'widgetastic.widget.base.View'),
]
nitpicky = True
pygments_style = 'sphinx'
source_suffix = '.rst'
templates_path = ['_templates']
todo_include_todos = False


# Options for HTML output -----------------------------------------------------

html_theme = 'alabaster'

# Theme options are theme-specific and customize the look and feel of a theme
# further. For a list of options see:
# http://alabaster.readthedocs.io/en/latest/customization.html#theme-options
html_theme_options = {
    'github_user': 'quipucords',
    'github_repo': 'camayoc',
    'travis_button': True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Custom sidebar templates, must be a dictionary that maps document names to
# template names.
#
# See: http://alabaster.readthedocs.io/en/latest/installation.html#sidebars
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',  # needs 'show_related': True theme option to display
        'searchbox.html',
        'donate.html',
    ]
}
