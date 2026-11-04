Users and roles
===============

There are three roles in Cape News:

* **Reader**: can read approved articles and newsletters, and follow publishers
  or independent journalists. A Reader cannot create or approve content.
* **Journalist**: can create stories, edit their own articles, and put together
  newsletters. Their articles start off unapproved.
* **Editor**: can review and approve articles, and can update or delete them.

The ``User`` model saves each person's role and places them in the matching
Django group. If a Reader changes to a staff role, old Reader subscriptions
are cleared.

How an article gets approved
----------------------------

1. A journalist submits an article, which starts off unapproved.
2. An editor reviews the article on the website.
3. When the editor approves it, readers can see it in the feed.
4. The app emails subscribed readers and records the approval.
5. Signed internal API messages are checked before the approval is logged.

The website checks permissions, but the API checks them too. This means
someone cannot get extra access just by sending a request manually.
