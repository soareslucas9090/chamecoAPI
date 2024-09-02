from datetime import datetime

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

from .models import Blocos, Chaves, Salas, Usuarios
from .serializers import BlocosSerializer, SalasSerializer, UsuariosSerializer


class DefaultNumberPagination(PageNumberPagination):
    page_size = 20


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
