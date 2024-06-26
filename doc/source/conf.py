# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'nmrPype'
copyright = '2024, Micah Smith and Frank Delaglio'
author = 'Micah Smith and Frank Delaglio'
release = '1.0.0'


# -- Imports -----------------------------------------------------------------
import os
import sys
try:
    pth = os.environ['PYPE_PATH']
except KeyError:
    pth = os.getcwd()+"/../.."
sys.path.insert(0, os.path.abspath(pth))


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['nbsphinx',
              'sphinx.ext.autodoc',
              'sphinx.ext.coverage',
              'sphinx.ext.napoleon',]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
