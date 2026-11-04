"""Sphinx settings for the Cape News Django project."""

import os
import sys
from pathlib import Path

import django

# Sphinx runs from docs/, so it must be able to find manage.py and our apps.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "news_project.settings")
django.setup()

project = "Cape News - Django News Application"
author = "Cape News project"
copyright = "2026, Cape News project"
release = "1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "alabaster"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_show_sourcelink = False

autodoc_typehints = "none"
autoclass_content = "class"
