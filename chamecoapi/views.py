import os
from datetime import datetime

import jwt
import requests
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
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
from .permissions import IsAdmin, IsTokenValid, IsUserAuthenticated
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

    http_method_names = ["get", "post", "put", "delete", "head"]
    
    def get_usuario(self, request: HttpRequest, serializer: dict) -> HttpResponse:
        """
            Método feito para a busca, na API, do ID do usuário do Cortex, pois
            ele sempre precisar ser válido, tanto na criação, quanto edição do usuário
        """
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
                    data = {"status": "error", "detail": "ID do usuário não existe ou usuário não está autorizado a fazer esta ação."}
                    return Response(data, status=status.HTTP_400_BAD_REQUEST)
            
            except:
                # Se a resposta for inválida, e não foi porque o usuário não existe
                # então é porque o token guardado não é válido
                data = {"status": "error", "detail": "Token de acesso inválido."}
                return Response(data, status=status.HTTP_401_UNAUTHORIZED)
            
        return response
        
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer = serializer.validated_data
        
        response = self.get_usuario(request, serializer)
        
        if response.status_code != 200:
            return response

        # Criando o usuário caso todas as verificações ocorram bem
        setores = ', '.join(response.json()["nome_setores"])
        
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
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer = serializer.validated_data
        

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
            
        response = self.get_usuario(request, serializer)
        
        if response.status_code != 200:
            return response
        
        # Criando o usuário caso todas as verificações ocorram bem
        setores = ', '.join(response.json()["nome_setores"])

        usuario = Usuarios.objects.get(id=kwargs["pk"])
        
        usuario.nome=response.json()["nome"]
        usuario.id_cortex=response.json()["id"]
        usuario.setor=setores
        usuario.tipo=response.json()["nome_tipo"]
        if serializer.get("chaves_autorizadas", None):
            usuario.chaves_autorizadas=serializer["chaves_autorizadas"]

        usuario.save()
        
        return Response(self.get_serializer(usuario).data,status=status.HTTP_200_OK)
        
            
    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE", "PUT"]:
            return [IsUserAuthenticated()]

        return super().get_permissions()    
        

@extend_schema(tags=["Blocos"])
class BlocosViewSet(ModelViewSet):
    queryset = Blocos.objects.all()
    serializer_class = BlocosSerializer
    pagination_class = DefaultNumberPagination
    permission_classes = [IsTokenValid]

    http_method_names = ["get", "post", "put", "delete", "head"]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        nome = self.request.query_params.get("nome", None)
        
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
            
        return queryset
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="nome",
                type=OpenApiTypes.STR,
                description="Filtrar pelo nome do bloco",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_permissions(self):
        if self.request.method in ["POST", "DELETE", "PUT", ]:
            return [IsAdmin()]

        return super().get_permissions()


@extend_schema(tags=["Salas"])
class SalasViewSet(ModelViewSet): 
    queryset = Salas.objects.all()
    serializer_class = SalasSerializer
    pagination_class = DefaultNumberPagination
    permission_classes = [IsTokenValid]

    http_method_names = ["get", "post", "put", "delete", "head"]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        nome = self.request.query_params.get("nome", None)
        
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
            
        bloco = self.request.query_params.get("bloco", None)
        
        if bloco:
            queryset = queryset.filter(bloco__nome__icontains=bloco)
            
        return queryset
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="nome",
                type=OpenApiTypes.STR,
                description="Filtrar pelo nome da sala",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="bloco",
                type=OpenApiTypes.STR,
                description="Filtrar pelo nome do bloco",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_permissions(self):
        if self.request.method in ["POST", "DELETE", "PUT", ]:
            return [IsAdmin()]

        return super().get_permissions()
