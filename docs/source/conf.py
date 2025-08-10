# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import datetime

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "flarchitect"
copyright = f"{datetime.datetime.now().year}, arched.dev (Lewis Morris)"
author = "arched.dev (Lewis Morris)"
release = "0.1.2"

html_logo = "../logo.png"

html_title = "flarchitect"


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
html_static_path = ["./_static"]
html_css_files = [
    "colours.css",
    "custom.css",
    "https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,100..800;1,100..800&display=swap",
]
colors = {
    "bg0": " #fbf1c7",
    "bg1": " #ebdbb2",
    "bg2": " #d5c4a1",
    "bg3": " #bdae93",
    "bg4": " #a89984",
    "gry": " #928374",
    "fg4": " #7c6f64",
    "fg3": " #665c54",
    "fg2": " #504945",
    "fg1": " #3c3836",
    "fg0": " #282828",
    "red": " #cc241d",
    "red2": " #9d0006",
    "orange": " #d65d0e",
    "orange2": " #af3a03",
    "yellow": " #d79921",
    "yellow2": " #b57614",
    "green": " #98971a",
    "green2": " #79740e",
    "aqua": " #689d6a",
    "aqua2": " #427b58",
    "blue": " #458588",
    "blue2": " #076678",
    "purple": " #b16286",
    "purple2": " #8f3f71",
}

html_theme = "furo"
html_theme_options = {
    "light_css_variables": {
        "font-stack": "JetBrains Mono, sans-serif",
        "font-stack--monospace": "JetBrains Mono, monospace",
        "color-brand-primary": colors["purple2"],
        "color-brand-content": colors["blue2"],
    },
    "dark_css_variables": {
        "color-brand-primary": colors["purple"],
        "color-brand-content": colors["blue"],
        "color-background-primary": colors["fg1"],
        "color-background-secondary": colors["fg0"],
        "color-foreground-primary": colors["bg0"],
        "color-foreground-secondary": colors["bg1"],
        "color-highlighted-background": colors["yellow"],
        "color-highlight-on-target": colors["fg2"],
    },
}

highlight_language = "python3"
pygments_style = "gruvbox-light"
pygments_dark_style = "gruvbox-dark"

extensions = [
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinxext.opengraph",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx_design",
]

extlinks = {
    "github": ("https://github.com/arched-dev/flarchitect", "GitHub "),
    "issue": ("https://github.com/arched-dev/flarchitect/issues", "issue "),
}

autosummary_generate = True


rst_epilog = """
.. _Flask: https://flask.palletsprojects.com/en/latest/
.. _Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/en/
.. _Flask-Limiter: https://flask-limiter.readthedocs.io/en/stable/
.. _Flask-Caching: https://flask-caching.readthedocs.io/en/latest/
.. _SQLAlchemy: https://docs.sqlalchemy.org/en/latest/
.. _ReDoc: https://redocly.github.io/redoc/
.. _Jinja: https://jinja.palletsprojects.com/en/3.1.x/
.. _SQLAlchemy ORM: https://docs.sqlalchemy.org/
.. _repo: https://github.com/arched-dev/flarchitect
.. _HTTP method: https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods
.. _Marshmallow: https://marshmallow.readthedocs.io/en/stable/
"""


templates_path = ["_templates"]
exclude_patterns = []

html_theme = "furo"
