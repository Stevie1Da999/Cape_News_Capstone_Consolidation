REST API
========

The REST API uses Django REST Framework and token authentication. Replace
``YOUR_TOKEN`` with the real token for your account.

Common endpoints
----------------

* ``POST /api/token/``: get a login token.
* ``GET /api/articles/``: list approved articles (login needed).
* ``POST /api/articles/``: submit an article (Journalist only).
* ``GET /api/articles/<id>/``: get a story visible to your role.
* ``PUT/PATCH/DELETE /api/articles/<id>/``: edit or remove a permitted story.
* ``GET /api/articles/subscribed/``: the Reader's approved subscribed content.
* ``POST /api/approved/``: signed internal approval notice (not a public action).

Example request header::

   Authorization: Token YOUR_TOKEN

A Reader cannot see pending stories or create articles. Journalists cannot
approve their own articles. The API checks a signed header before accepting
approval messages, so a normal user cannot approve a story using that route.

If you receive ``401`` or ``403``, check that the token and account role
are correct. Invalid form data should give a validation error.
