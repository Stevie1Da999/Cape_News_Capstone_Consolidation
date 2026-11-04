Running with Docker
===================

The Docker image contains Python and the packages needed by the project.
You do not need to install Django on the computer running the container.

Quick start using SQLite
------------------------

Build the image from the folder containing ``Dockerfile``::

   docker build -t cape-news .

Run with a secret key you generated yourself::

   docker run --rm -p 8000:8000 --name cape-news \
     -e DJANGO_SECRET_KEY="your-own-long-random-secret-key" \
     -e DJANGO_DEBUG=False \
     -v cape_news_data:/app/data cape-news

For Windows PowerShell, use the one-line ``docker run`` example in README.md.
The named volume saves SQLite data when the container is restarted.

MariaDB with Docker Compose
---------------------------

Copy ``.env.example`` to ``.env`` and change all example passwords and the
Django secret key. Then run::

   docker compose -f compose.mariadb.yaml up --build -d

Stop the stack with::

   docker compose -f compose.mariadb.yaml down

Leave off ``-v`` when stopping so that the database data is not deleted.

The image runs Django migrations and collects static files at startup, and
Gunicorn serves the website. WhiteNoise serves CSS in this setup.
