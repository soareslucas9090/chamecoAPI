import os
from datetime import datetime

import jwt
import requests
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .business import getTokens, requestFactory, setTokens
from .models import Blocos, Chaves, Salas, Usuarios
from .serializers import (
    BlocosSerializer,
    LoginSerializer,
    SalasSerializer,
    UsuariosSerializer,
)

URL_BASE = os.environ.get("urlBase")


class DefaultNumberPagination(PageNumberPagination):
    page_size = 20


@extend_schema(tags=["Login"])
class LoginAPIView(GenericAPIView):
    serializer_class = LoginSerializer
    http_method_names = ["post"]
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Login realizado com sucesso."
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Requisição errada."
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Credenciais incorretas."
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
                description="Erro interno."
            ),
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer = serializer.validated_data

        url = f"{URL_BASE}api/token/"
        body = {
            "cpf": serializer["cpf"],
            "password": serializer["password"],
        }

        response = requests.post(url, json=body)

        if response.status_code == 200:
            access_token = response.json()["access"]

            id_user = jwt.decode(access_token, options={"verify_signature": False})[
                "user_id"
            ]

            setTokens(id_user, response.json()["access"], response.json()["refresh"])

            request.session["id_user"] = id_user

            data = {"status": "success"}

        else:
            data = response.json()

        return Response(data, status=response.status_code)


@extend_schema(tags=["Usuários"])
class UsuariosViewSet(ModelViewSet):
    queryset = Usuarios.objects.all()
    serializer_class = UsuariosSerializer
    pagination_class = DefaultNumberPagination

    http_method_names = ["get", "post", "patch", "put", "delete", "head"]


@extend_schema(tags=["Blocos"])
class BlocosViewSet(ModelViewSet):
    queryset = Blocos.objects.all()
    serializer_class = BlocosSerializer
    pagination_class = DefaultNumberPagination

    http_method_names = ["get", "post", "patch", "put", "delete", "head"]


@extend_schema(tags=["Salas"])
class SalasViewSet(ModelViewSet):
    queryset = Salas.objects.all()
    serializer_class = SalasSerializer
    pagination_class = DefaultNumberPagination

    http_method_names = ["get", "post", "patch", "put", "delete", "head"]
