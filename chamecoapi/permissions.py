import os

from django.contrib.auth.models import AnonymousUser
from dotenv import load_dotenv
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from .business import isTokenValid, requestFactory

load_dotenv()
URL_BASE = os.environ.get("urlBase")


class IsUserAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        id_user = request.session.get("id_user")

        # Verifica se há um "id_user" guardado na sessão do Django
        if not id_user:
            raise PermissionDenied(detail="É necessário autenticação.")

        return True


class IsTokenValid(permissions.BasePermission):

    def has_permission(self, request, view):
        id_user = request.session.get("id_user")

        if isTokenValid(id_user):
            return True

        raise PermissionDenied(
            detail="Não foi possível autenticar, faça login novamente."
        )


class IsAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        id_user = request.session.get("id_user")

        if not id_user:
            raise PermissionDenied(detail="É necessário autenticação.")

        url_get_user = f"{URL_BASE}api/gerusuarios/v1/users/{id_user}"

        response = requestFactory("get", url_get_user, id_user)

        if not response:
            raise PermissionDenied(detail="Usuário não encontrado.")

        permitidos = ["admin", "ti"]

        if response.json()["nome_tipo"] in permitidos:
            return True

        raise PermissionDenied(
            detail="O tipo de usuário não permite executar esta ação."
        )
