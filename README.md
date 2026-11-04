# Cape News - Capstone Project Consolidation

Cape News is the Django News Application I worked on for my earlier capstone.
It has Readers, Journalists and Editors, articles that need approval, publisher
subscriptions, newsletters, email notices and a token-authenticated REST API.

This submission adds Git version control, docstrings, Sphinx documentation,
a Docker setup and instructions for running the project on another computer.

## Files worth knowing about

- `news/` - Django models, forms, website pages, API and automated tests.
- `news_project/` - Django settings and project URL configuration.
- `docs/` - Sphinx source files and HTML documentation.
- `Dockerfile` and `docker-entrypoint.sh` - build and run the app in Docker.
- `compose.mariadb.yaml` - start the app with a MariaDB container.
- `.env.example` - shows what secret values you need to provide yourself.
- `capstone.txt` - add the link to your own public GitHub repository here.

## Option 1: Run it normally using Python (Windows PowerShell)

You need Python 3.13 and an internet connection to install the packages.
Open PowerShell in the folder containing `manage.py` and run:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py check
python manage.py test
flake8 .
python manage.py runserver
```

Open http://127.0.0.1:8000/ in the browser. SQLite is the default database.
The `.venv` folder and local database do not go to GitHub.

If PowerShell blocks venv activation for this session, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

## Option 2: Run it with Docker (SQLite, quickest option)

Install Docker Desktop, start it, and open PowerShell in the project folder.
Generate a secret key and copy the output somewhere safe:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Create the image, then run it with a value you generated yourself:

```powershell
docker build -t cape-news .
docker run --rm -p 8000:8000 --name cape-news -e DJANGO_SECRET_KEY="REPLACE_WITH_YOUR_RANDOM_KEY" -e DJANGO_DEBUG=False -v cape_news_data:/app/data cape-news
```

Visit http://localhost:8000/. The `cape_news_data` volume keeps the SQLite
database when the container is stopped. Stop it with `Ctrl+C`.

The app runs migrations and collects its CSS when the container starts.
Gunicorn serves the pages and WhiteNoise serves static files.

## Option 3: Run it with Docker and MariaDB

Create your own environment file using the example:

```powershell
Copy-Item .env.example .env
notepad .env
```

Replace `DJANGO_SECRET_KEY`, `DB_PASSWORD`, and `DB_ROOT_PASSWORD` with
strong values you created. Do not upload `.env` to GitHub.

```powershell
docker compose -f compose.mariadb.yaml up --build -d
docker compose -f compose.mariadb.yaml ps
docker compose -f compose.mariadb.yaml logs web
```

The site will be at http://localhost:8000/ once the database is ready.
To create an admin user with Docker Compose:

```powershell
docker compose -f compose.mariadb.yaml exec web python manage.py createsuperuser
```

Stop the containers without deleting the database:

```powershell
docker compose -f compose.mariadb.yaml down
```

**Do not use** `down -v` unless you want to delete the MariaDB data volume.

### Using a local MariaDB installation without Docker

The database must exist first and its user needs permission to use it.
Set the following for your own PowerShell session:

```powershell
$env:DB_ENGINE="mariadb"
$env:DB_NAME="news_application"
$env:DB_USER="news_user"
$env:DB_PASSWORD="YOUR_OWN_DB_PASSWORD"
$env:DB_HOST="127.0.0.1"
$env:DB_PORT="3306"
python manage.py migrate
python manage.py runserver
```

`mysqlclient` is in `requirements.txt`. Linux machines may need MariaDB client
development headers to install it. Docker handles these for you.

## User roles and API

- **Readers** see approved stories and can follow publishers or journalists.
- **Journalists** create and manage their own articles and newsletters.
- **Editors** review stories, approve them, and manage content.

Useful routes:

| Route | What it does |
| --- | --- |
| `/register/` | Create a Reader, Journalist or Editor account |
| `/login/` | Sign in |
| `/admin/` | Django admin page |
| `/api/token/` | Get a DRF authentication token |
| `/api/articles/` | Read approved stories or create one as a Journalist |
| `/api/articles/subscribed/` | Approved stories followed by a Reader |
| `/api/articles/<id>/` | Article details and permitted changes |
| `/api/approved/` | Signed internal approval notification endpoint |

For authenticated API calls, send `Authorization: Token YOUR_TOKEN_HERE`.
Do not share your real token. An approval POST must have the signed internal
header, so it is not a public way of approving an article.

## Sphinx documentation

After installing the Python dependencies, build the documentation:

```powershell
sphinx-build -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` in a browser. The folder includes an HTML
preview so the guides can be read before a Sphinx build. Run the command
above to replace the preview with Sphinx's generated output, including the
autodoc reference for the code. Keep the finished HTML files in your repo.

## Checks before submission

Run all of these after installing the packages:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
flake8 .
sphinx-build -b html docs docs/_build/html
```

For Docker, run `docker build -t cape-news .` and open the website. Try a
Reader, a Journalist and an Editor account to check the workflow.

## Git work for this task

The supplied project has local Git history showing the requested `docs` and
`container` branches. The `docs` branch has separate commits for documented
Python scripts. Both branches are merged into `main` before this README is
committed. Use `git log --graph --all --oneline` to check the history.

Create your own **public** GitHub repository, add it as `origin`, and push all
three branches. Once it is public, replace the placeholder in `capstone.txt`
with your real repository link, then commit and push that change.

```powershell
git remote add origin https://github.com/YOUR_USERNAME/YOUR_PUBLIC_REPO.git
git push -u origin main
git push origin docs container
```

If the repository already has a remote called `origin`, update it using
`git remote set-url origin ...` instead of `git remote add origin ...`.

Please keep passwords, secret keys and tokens out of public Git commits.
The `.gitignore` and `.dockerignore` help prevent that.
