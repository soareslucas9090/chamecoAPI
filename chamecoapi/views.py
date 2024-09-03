import os
from datetime import datetime

import jwt
import requests
from django.core.cache import cache
from dotenv import load_dotenv
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (OpenApiExample, OpenApiParameter,
                                   OpenApiResponse, extend_schema)
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .business import getTokens, requestFactory, setTokens
from .models import Blocos, Chaves, Salas, Usuarios
from .permissions import IsUserAuthenticated
from .serializers import (BlocosSerializer, LoginSerializer, SalasSerializer,
                          UsuariosSerializer)

load_dotenv()
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
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer = serializer.validated_data
        
        id_user = request.session.get("id_user")
        
        # Verifica se há um "id_user" guardado na sessão do Django
        if not id_user:
            data = {"status": "error", "detail": "Usuário não logado."}
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)

        url_get_user = f"{URL_BASE}api/gerusuarios/v1/users/{serializer["id_cortex"]}"

        # Faz um get para verificar os detalhes do usuário na API do Cortex
        response = requestFactory("get", url_get_user, id_user)
        
        # Verifica se a resposta é válida
        if not response:
            try:
                # Se a resposta for inválida, testa se foi porque o usuário não existe
                if response.status_code:
                    data = {"status": "error", "detail": "ID do usuário não existe."}
                    return Response(data, status=status.HTTP_400_BAD_REQUEST)
            
            except:
                # Se a resposta for inválida, e não foi porque o usuário não existe
                # então é porque o token guardado não é válido
                data = {"status": "error", "detail": "Token de acesso inválido."}
                return Response(data, status=status.HTTP_401_UNAUTHORIZED)

        
        # Criando o usuário caso todas as verificações ocorram bem
        setores = ""
        for setor in response.json()["setores"]:
            setores += setor

        usuario = Usuarios.objects.create(
            nome=response.json()["nome"],
            id_cortex=response.json()["id"],
            setor=setores,
            tipo=response.json()["nome_tipo"]
        )

        result = {
            "status": "success",
            "detail": {
                "id": usuario.id,
                "nome": usuario.nome,
                "id_cortex": usuario.id_cortex,
                "setor": usuario.setor,
                "tipo": usuario.tipo,
            }
        }
        
        return Response(result, status=status.HTTP_201_CREATED)
            
    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE", "PUT"]:
            return [IsUserAuthenticated()]

        return super().get_permissions()    
        

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
