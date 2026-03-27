from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import BasicAuthentication


class MyBasicAuth(BasicAuthentication):
    def authenticate(self, request):
        return super().authenticate(request)

    def authenticate_credentials(self, userid, password, request=None):
        """
        Authenticate the userid and password against username and password
        with optional request for context.
        """
        if userid != settings.ONEID_USERNAME:
            raise exceptions.AuthenticationFailed("Authentication failed. Wrong username.")
        if password != settings.ONEID_PASSWORD:
            raise exceptions.AuthenticationFailed("Authentication failed. Wrong password.")

        return (True, None)
