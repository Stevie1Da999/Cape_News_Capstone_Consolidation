Getting started
===============

You need Python 3.13, Git, and MariaDB if you want to use the MariaDB option.
SQLite is used by default, which is simpler when testing the project.

Windows PowerShell
------------------

Open a terminal in the folder with ``manage.py``, then run::

   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   python manage.py migrate
   python manage.py check
   python manage.py test
   python manage.py runserver

Visit ``http://127.0.0.1:8000/`` to see the homepage.

To create an admin account, run ``python manage.py createsuperuser``.

Make a file named ``.env`` only for the Docker Compose option. Never commit
that file or share real passwords. See ``.env.example`` for the variables.

Local MariaDB
-------------

After creating a MariaDB database and a user, set these variables in the
PowerShell terminal before running Django::

   $env:DB_ENGINE = "mariadb"
   $env:DB_NAME = "news_application"
   $env:DB_USER = "news_user"
   $env:DB_PASSWORD = "put-your-own-password-here"
   $env:DB_HOST = "127.0.0.1"
   $env:DB_PORT = "3306"
   python manage.py migrate

Do not put the password in a Python file or into Git.
