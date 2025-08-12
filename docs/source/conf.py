# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import zntrack

project = "ZnTrack"
copyright = "2025, Fabian Zills"
author = "Fabian Zills"
release = zntrack.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx.ext.viewcode",
    "sphinx_design",
    "sphinx.ext.autodoc",
    "sphinxcontrib.mermaid",
    "hoverxref.extension",
]

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_favicon = "_static/favicon_ZnTrack.png"
# html_logo = "_static/logo_ZnTrack.png"
html_title = "ZnTrack"
html_static_path = ["_static"]
html_theme_options = {
    "navigation_with_keys": True,
    "source_repository": "https://github.com/zincware/ZnTrack/",
    "source_branch": "main",
    "source_directory": "docs/source/",
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
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/brands.min.css",
]

# -- Options for hoverxref extension -----------------------------------------
# https://sphinx-hoverxref.readthedocs.io/en/latest/

hoverxref_roles = ["term"]
hoverxref_role_types = {
    "class": "tooltip",
}

# -- Options for sphinx_copybutton -------------------------------------------
# https://sphinx-copybutton.readthedocs.io/en/latest/

copybutton_prompt_text = r">>> |\.\.\. |\(.*\) \$ "
copybutton_prompt_is_regexp = True
