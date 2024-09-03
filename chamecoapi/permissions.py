from django.contrib.auth.models import AnonymousUser
from rest_framework import permissions


class IsUserAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        id_user = request.session.get("id_user")

        # Verifica se há um "id_user" guardado na sessão do Django
        if not id_user:
            return False

        return True
