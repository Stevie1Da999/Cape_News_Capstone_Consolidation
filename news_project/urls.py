# Main URL file that connects the website, API and Django admin.
from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("news.urls")),
    path("api/", include("news.api_urls")),

    # POST username/password here to receive a DRF token.
    path("api/token/", obtain_auth_token, name="api_token"),

    # This is useful for manual API testing in the DRF browser.
    path("api-auth/", include("rest_framework.urls")),
]
