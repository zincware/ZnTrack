# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import importlib
import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "ZnTrack"
copyright = "2024, Fabian Zills"
author = "Fabian Zills"
version = importlib.import_module("zntrack").__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "nbsphinx",
    "nbsphinx_link",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_favicon = "_static/favicon_ZnTrack.png"
html_logo = "_static/logo_ZnTrack.png"
html_title = "zincware package"
html_static_path = ["_static"]
html_theme_options = {
    "navigation_with_keys": True,
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/zincware/ZnTrack",
            "html": "",
            "class": "fa-brands fa-github fa-2x",
        },
    ],
}

# font-awesome logos
html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/solid.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/brands.min.css",
]
