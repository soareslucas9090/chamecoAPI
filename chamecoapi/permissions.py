import os

from django.contrib.auth.models import AnonymousUser
from dotenv import load_dotenv
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

from .business import getIdUser, isTokenValid, requestFactory

load_dotenv()
URL_BASE = os.environ.get("urlBase")


class IsUserAuthenticated(permissions.BasePermission):

    def has_permission(self, request, view):
        hash_token = request.query_params.get("token", None)

        id_user = getIdUser(hash_token)

        # Verifica se há um "id_user" guardado na sessão do Django
        if not id_user:
            raise PermissionDenied(detail="É necessário autenticação.")

        return True


class IsTokenValid(permissions.BasePermission):

    def has_permission(self, request, view):
        hash_token = request.query_params.get("token", None)

        if isTokenValid(hash_token):
            return True

        return False


class IsAdmin(permissions.BasePermission):

    def has_permission(self, request, view, default_use=True):
        serializer = view.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer = serializer.validated_data

        hash_token = serializer["token"]

        id_user = getIdUser(hash_token)

        if not id_user:
            raise PermissionDenied(detail="É necessário autenticação.")

        url_get_user = f"{URL_BASE}cortex/api/gerusuarios/v1/users/{id_user}"

        response = requestFactory("get", url_get_user, hash_token)

        if not response:
            raise PermissionDenied(detail="Usuário não encontrado.")

        tipos_permitidos = ["admin", "ti"]

        if response.json()["nome_tipo"] in tipos_permitidos:
            return True

        setores_permitidos = [
            "TI",
        ]

        setores_usuario = response.json()["nome_setores"]

        for setor in setores_permitidos:
            if setor.lower() in setores_usuario:
                return True

        if default_use:
            raise PermissionDenied(
                detail="O tipo de usuário não permite executar esta ação."
            )
        else:
            return False


class CanLogIn(permissions.BasePermission):

    def has_permission(self, request, view, hash_token):
        try:
            id_user = getIdUser(hash_token)

            url_get_user = f"{URL_BASE}cortex/api/gerusuarios/v1/users/{id_user}"

            response = requestFactory("get", url_get_user, hash_token)

            if not response:
                raise PermissionDenied(detail="Usuário não encontrado.")

            tipos_permitidos = ["admin", "ti"]

            if response.json()["nome_tipo"] in tipos_permitidos:
                return True

            setores_permitidos = ["TI", "Guarita", "Coordenacao de Disciplina"]

            setores_usuario = response.json()["nome_setores"]

            for setor in setores_permitidos:
                if setor.lower() in setores_usuario:
                    return True

            return False
        except Exception as e:
            print(e)
            return False


class CanUseSystem(permissions.BasePermission):

    def has_permission(self, request, view):
        serializer = view.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer = serializer.validated_data

        hash_token = serializer["token"]

        id_user = getIdUser(hash_token)

        if not id_user:
            raise PermissionDenied(detail="É necessário autenticação.")

        url_get_user = f"{URL_BASE}cortex/api/gerusuarios/v1/users/{id_user}"

        response = requestFactory("get", url_get_user, hash_token)

        if not response:
            raise PermissionDenied(detail="Usuário não encontrado.")

        tipos_permitidos = ["admin", "ti"]

        if response.json()["nome_tipo"] in tipos_permitidos:
            return True

        setores_permitidos = ["TI", "Guarita", "Coordenacao de Disciplina"]

        setores_usuario = response.json()["nome_setores"]

        for setor in setores_permitidos:
            if setor.lower() in setores_usuario:
                return True

        raise PermissionDenied(detail="Usuário sem permissão para executar esta ação.")
