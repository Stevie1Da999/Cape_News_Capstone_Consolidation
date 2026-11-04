Testing and code checks
=======================

The existing ``news/tests.py`` file covers reader access, the journalist and
editor actions, subscription filtering, newsletters, API permissions, and
approval notifications.

Run these commands after installing the requirements::

   python manage.py check
   python manage.py makemigrations --check --dry-run
   python manage.py test
   flake8 .

Build the HTML documentation with Sphinx::

   sphinx-build -b html docs docs/_build/html

Open ``docs/_build/html/index.html`` in a browser to read the finished docs.
Keep the generated HTML output when uploading the project to GitHub.

The checks should be run again after making any code changes, especially if
changing database settings or Docker files.
