import hashlib
import os
from datetime import datetime

import jwt
import requests
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from dotenv import load_dotenv
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import mixins, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from .business import (
    getIdUser,
    getTokens,
    isTokenValid,
    requestFactory,
    setIdUser,
    setTokens,
)
from .models import (
    Blocos,
    Chaves,
    Emprestimos,
    PessoasAutorizadas,
    Salas,
    Usuarios,
    UsuariosResponsaveis,
)
from .permissions import (
    CanLogIn,
    CanUseSystem,
    IsAdmin,
    IsTokenValid,
    IsUserAuthenticated,
)
from .serializers import (
    AutorizadosSerializer,
    BlocosSerializer,
    ChavesSerializer,
    EmprestimoDetalhadoSerializer,
    FinalizarEmprestimoSerializer,
    LoginSerializer,
    RealizarEmprestimoSerializer,
    SalasSerializer,
    TrocarEmprestimoSerializer,
    UsuariosResponsaveisSerializer,
    UsuariosSerializer,
    VerifyTokenSerializer,
)

from .bases import (
    tipos_usa_sistema_livremente,
    setores_usa_sistema_livremente,
)

load_dotenv()
URL_BASE = os.environ.get("urlBase")


class DefaultNumberPagination(PageNumberPagination):
    page_size = 5


class DynamicPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'pagination'
    max_page_size = 100

    def get_page_size(self, request):
        if self.page_size_query_param:
            try:
                page_size = int(
                    request.query_params[self.page_size_query_param]
                )

                if page_size > 0 and page_size <= self.max_page_size:
                    return page_size
            except (KeyError, ValueError):
                pass

        return self.page_size


class AuthorizedsNumberPagination(PageNumberPagination):
    page_size = 9999


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

        url = f"{URL_BASE}cortex/api/token/"
        body = {
            "cpf": serializer["cpf"],
            "password": serializer["password"],
        }

        response = requests.post(url, json=body)
        status_code = response.status_code
        data = {}

        if response.status_code == 200:
            access_token = response.json()["access"]

            id_user = jwt.decode(access_token, options={"verify_signature": False})[
                "user_id"
            ]

            hash_token = hashlib.sha256(
                str(
                    response.json()["access"] +
                    response.json()["refresh"]
                ).encode()
            ).hexdigest()

            setTokens(hash_token, response.json()[
                      "access"], response.json()["refresh"])

            setIdUser(hash_token, id_user)

            usuario_cortex = UsuariosViewSet.get_usuario(
                request, {"id_cortex": id_user}, hash_token
            )

            if CanLogIn().has_permission(
                request=request, view=self, hash_token=hash_token
            ):
                data = {"status": "success"}

                try:

                    usuario, created = Usuarios.objects.get_or_create(
                        id_cortex=id_user
                    )

                    if usuario_cortex.status_code == 200:
                        setores = ", ".join(
                            usuario_cortex.json()["nome_setores"]
                        )
                        usuario.nome = usuario_cortex.json()["nome"]
                        usuario.setor = setores
                        usuario.tipo = usuario_cortex.json()["nome_tipo"]
                        usuario.email = usuario_cortex.json()["email"]

                        usuario.save()

                        data["usuario"] = usuario.id
                        data["setor"] = usuario.setor
                        data["tipo"] = usuario.tipo
                        data["nome"] = usuario.nome

                        if CanUseSystem().has_permission(
                            request=request, view=self, hash_token=hash_token
                        ):
                            data["token"] = hash_token
                except:
                    pass

            else:
                data = {"status": "error",
                        "message": "Usuário não autorizado."}
                status_code = status.HTTP_403_FORBIDDEN

        else:
            data = response.json()

        return Response(data, status=status_code)


@extend_schema(tags=["Login"])
class VerifyTokenAPIView(GenericAPIView):
    serializer_class = VerifyTokenSerializer
    http_method_names = ["post"]
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            status.HTTP_200_OK: OpenApiResponse(description="Token válido."),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Token inválido."
            ),
        }
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer = serializer.validated_data

        if isTokenValid(serializer["token"]):
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        else:
            return Response(
                {"status": "error", "message": "Token inválido."},
                status=status.HTTP_401_UNAUTHORIZED,
            )


@extend_schema(tags=["Usuários"])
class UsuariosViewSet(ModelViewSet):
    queryset = Usuarios.objects.all()
    serializer_class = UsuariosSerializer
    pagination_class = DynamicPagination
    permission_classes = [IsTokenValid]

    http_method_names = ["get", "put", "post", "delete", "head"]

    def get_queryset(self):
        queryset = super().get_queryset()

        sala_autorizada = self.request.query_params.get("sala_autorizada")

        if sala_autorizada and sala_autorizada.isnumeric():
            queryset = queryset.filter(
                salas_autorizadas__id=int(sala_autorizada)
            ).distinct()

        nome = self.request.query_params.get("nome")
        tipo = self.request.query_params.get("tipo")
        setor = self.request.query_params.get("setor")

        if nome:
            queryset = queryset.filter(nome__icontains=nome)

        if tipo:
            queryset = queryset.filter(tipo__icontains=tipo)

        if setor:
            queryset = queryset.filter(setor__icontains=setor)

        return queryset

    @extend_schema(
        description="Filtros de usários do sistema",
        parameters=[
            OpenApiParameter(
                name="chave_autorizada",
                type=OpenApiTypes.INT,
                description="Filtra os usuários pela possibilidade de pedir empréstimo ou não de determinada chave.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="nome",
                type=OpenApiTypes.STR,
                description="Filtra os usuários pela nome.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="tipo",
                type=OpenApiTypes.STR,
                description="Filtra os usuários pelo tipo.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="setor",
                type=OpenApiTypes.STR,
                description="Filtra os usuários pelos setores.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="pagination",
                type=OpenApiTypes.INT,
                description="Define o número de itens por página (máximo 100, padrão 5).",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        description="Campos obrigatórios para obter resposta do endpoint.",
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_usuario(
        request: HttpRequest, serializer: dict, hash_token: str
    ) -> HttpResponse:
        """
        Método feito para a busca, na API, do ID do usuário do Cortex, pois
        ele sempre precisar ser válido, tanto na criação, quanto edição do usuário
        """
        id_user = getIdUser(hash_token)

        # Verifica se há um "id_user" guardado no banco do Django
        if not id_user:
            data = {"status": "error", "detail": "Usuário não logado."}
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)

        id_cortex = serializer["id_cortex"]
        url_get_user = f"{URL_BASE}cortex/api/gerusuarios/v1/users/{id_cortex}"

        # Faz um get para verificar os detalhes do usuário na API do Cortex
        response = requestFactory("get", url_get_user, hash_token)

        # Verifica se a resposta é válida
        if not response:
            try:
                # Se a resposta for inválida, testa se foi porque o usuário não existe
                if response.status_code:
                    data = {
                        "status": "error",
                        "detail": "ID do usuário não existe ou usuário não está autorizado a fazer esta ação.",
                    }
                    return Response(data, status=status.HTTP_400_BAD_REQUEST)

            except:
                # Se a resposta for inválida, e não foi porque o usuário não existe
                # então é porque o token guardado não é válido
                data = {"status": "error",
                        "detail": "Token de acesso inválido."}
                return Response(data, status=status.HTTP_401_UNAUTHORIZED)

        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer = serializer.validated_data

        hash_token = serializer["token"]

        response = UsuariosViewSet.get_usuario(request, serializer, hash_token)

        if response.status_code != 200:
            return response

        # Criando o usuário caso todas as verificações ocorram bem
        setores = ", ".join(response.json()["nome_setores"])

        usuario = Usuarios.objects.create(
            nome=response.json()["nome"],
            id_cortex=response.json()["id"],
            setor=setores,
            tipo=response.json()["nome_tipo"],
            email=response.json()["email"],
        )

        result = {
            "status": "success",
            "detail": {
                "id": usuario.id,
                "nome": usuario.nome,
                "id_cortex": usuario.id_cortex,
                "setor": usuario.setor,
                "tipo": usuario.tipo,
            },
        }

        return Response(result, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            serializer = serializer.validated_data

            if getattr(instance, "_prefetched_objects_cache", None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            hash_token = serializer["token"]

            response = UsuariosViewSet.get_usuario(
                request, serializer, hash_token)

            if response.status_code != 200:
                return response

            # Criando o usuário caso todas as verificações ocorram bem
            setores = ", ".join(response.json()["nome_setores"])

            usuario = Usuarios.objects.get(id=kwargs["pk"])

            usuario.nome = response.json()["nome"]
            usuario.id_cortex = response.json()["id"]
            usuario.setor = setores
            usuario.tipo = response.json()["nome_tipo"]
            if serializer.get("salas_autorizadas", None):
                usuario.salas_autorizadas.set(
                    serializer["salas_autorizadas"])

            usuario.save()

            return Response(
                self.get_serializer(usuario).data, status=status.HTTP_200_OK
            )
        except Exception as e:
            print(e)
            return Response(
                {"status": "error", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get_serializer_class(self):
        if self.request.query_params.get("autorizado", None):
            return AutorizadosSerializer

        if self.request.method == "DELETE":
            return None

        return super().get_serializer_class()

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE", "PUT", "POST"]:
            return [IsAdmin()]

        return super().get_permissions()

    @extend_schema(
        description="Campo para passagem do token",
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


@extend_schema(tags=["Blocos"])
class BlocosViewSet(ModelViewSet):
    queryset = Blocos.objects.all()
    serializer_class = BlocosSerializer
    pagination_class = DynamicPagination
    permission_classes = [IsTokenValid]

    http_method_names = ["get", "post", "put", "delete", "head"]

    def perform_update(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def perform_create(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def get_queryset(self):
        queryset = super().get_queryset()

        nome = self.request.query_params.get("nome", None)

        if nome:
            queryset = queryset.filter(nome__icontains__iexact=nome)

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
            OpenApiParameter(
                name="pagination",
                type=OpenApiTypes.INT,
                description="Define o número de itens por página (máximo 100, padrão 5).",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        description="Campos obrigatórios para obter resposta do endpoint.",
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        description="Campo para passagem do token",
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == "DELETE":
            return None

        return super().get_serializer_class()

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE", "PUT", "POST"]:
            return [IsAdmin()]

        return super().get_permissions()


@extend_schema(tags=["Salas"])
class SalasViewSet(ModelViewSet):
    queryset = Salas.objects.all()
    serializer_class = SalasSerializer
    pagination_class = DynamicPagination
    permission_classes = [IsTokenValid]

    http_method_names = ["get", "post", "put", "delete", "head"]

    def perform_update(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def perform_create(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

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
            OpenApiParameter(
                name="pagination",
                type=OpenApiTypes.INT,
                description="Define o número de itens por página (máximo 100, padrão 5).",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        description="Campos obrigatórios para obter resposta do endpoint.",
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        description="Campo para passagem do token",
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == "DELETE":
            return None

        return super().get_serializer_class()

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE", "PUT", "POST"]:
            return [IsAdmin()]

        return super().get_permissions()


@extend_schema(tags=["Chaves"])
class ChavesViewSet(ModelViewSet):
    queryset = Chaves.objects.all()
    serializer_class = ChavesSerializer
    pagination_class = DynamicPagination
    permission_classes = [IsTokenValid]

    http_method_names = ["get", "post", "put", "delete", "head"]

    def perform_update(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def perform_create(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def get_queryset(self):
        queryset = super().get_queryset()

        sala = self.request.query_params.get("sala", None)

        if sala:
            queryset = queryset.filter(sala__nome__icontains=sala)

        bloco = self.request.query_params.get("bloco", None)

        if bloco:
            queryset = queryset.filter(bloco__nome__icontains=bloco)

        disponivel = self.request.query_params.get("disponivel")

        if disponivel:
            if disponivel.lower() == "false":
                disponivel = False

            elif disponivel.lower() == "true":
                disponivel = True

            queryset = queryset.filter(disponivel=disponivel)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="sala",
                type=OpenApiTypes.STR,
                description="Filtrar pelo nome da sala.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="bloco",
                type=OpenApiTypes.STR,
                description="Filtrar pelo nome do bloco.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="disponivel",
                type=OpenApiTypes.BOOL,
                description="Filtrar pela disponibilidade da chave.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="pagination",
                type=OpenApiTypes.INT,
                description="Define o número de itens por página (máximo 100, padrão 5).",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        description="Campos obrigatórios para obter resposta do endpoint.",
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        description="Campo para passagem do token",
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == "DELETE":
            return None

        return super().get_serializer_class()

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE", "PUT", "POST"]:
            return [IsAdmin()]

        return super().get_permissions()


@extend_schema(tags=["Usuários Responsáveis"])
class UsuariosResponsaveisViewSet(ModelViewSet):
    queryset = UsuariosResponsaveis.objects.all()
    serializer_class = UsuariosResponsaveisSerializer
    pagination_class = DynamicPagination
    permission_classes = [IsTokenValid]

    http_method_names = ["get", "post", "put", "delete", "head"]

    def perform_update(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def perform_create(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def get_queryset(self):
        queryset = super().get_queryset()

        nome_superusuario = self.request.query_params.get(
            "nome_superusuario", None)

        if nome_superusuario:
            queryset = queryset.filter(
                superusuario__nome__icontains=nome_superusuario)

        superusuario = self.request.query_params.get("superusuario", None)

        if superusuario and superusuario.isnumeric():
            queryset = queryset.filter(superusuario__id=superusuario)

        nome = self.request.query_params.get("nome", None)

        if nome:
            queryset = queryset.filter(nome__icontains=nome)

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="superusuario",
                type=OpenApiTypes.INT,
                description="Filtrar pelo id do superusuário.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="nome_superusuario",
                type=OpenApiTypes.STR,
                description="Filtrar pelo nome do superusuário.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="nome",
                type=OpenApiTypes.STR,
                description="Filtrar pelo nome do usuário responsável.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="pagination",
                type=OpenApiTypes.INT,
                description="Define o número de itens por página (máximo 100, padrão 5).",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        description="Campos obrigatórios para obter resposta do endpoint.",
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        description="Campo para passagem do token",
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.request.method == "DELETE":
            return None

        return super().get_serializer_class()

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE", "PUT", "POST"]:
            return [IsAdmin()]

        return super().get_permissions()


@extend_schema(tags=["Empréstimos"])
class EmprestimoDetalhadoViewSet(
    GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin
):
    queryset = Emprestimos.objects.all()
    serializer_class = EmprestimoDetalhadoSerializer
    pagination_class = DynamicPagination
    permission_classes = [IsTokenValid]

    http_method_names = ["get"]

    def get_queryset(self):
        queryset = super().get_queryset()

        data = self.request.query_params.get("data")
        format = "%Y-%m-%d"
        data_formatada = None

        try:
            data_formatada = datetime.strptime(data, format)
        except:
            data_formatada = None

        if data_formatada:
            queryset = queryset.filter(horario_emprestimo__date=data_formatada)

        solicitante = self.request.query_params.get("solicitante", None)

        if solicitante:
            queryset = queryset.filter(
                usuario_solicitante__nome__icontains=solicitante)

        responsavel = self.request.query_params.get("responsavel", None)

        if responsavel:
            queryset = queryset.filter(
                usuario_responsavel__nome__icontains=responsavel)

        finalizados = self.request.query_params.get("finalizados", None)

        if finalizados:
            if finalizados.lower() == "false":
                finalizados = False

            elif finalizados.lower() == "true":
                finalizados = True

            if finalizados:
                queryset = queryset.filter(horario_devolucao__isnull=False)
                queryset = queryset.order_by("-id")
            else:
                queryset = queryset.filter(horario_devolucao__isnull=True)
                queryset = queryset.order_by("-id")

        return queryset

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="data",
                type=OpenApiTypes.STR,
                description="Filtrar pela data do empréstimo.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="solicitante",
                type=OpenApiTypes.STR,
                description="Filtrar pelo nome do usuário solicitante.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="responsavel",
                type=OpenApiTypes.STR,
                description="Filtrar pelo nome do usuário responsável.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="finalizados",
                type=OpenApiTypes.BOOL,
                description="Filtrar pelo status de emprestimo finalizado ou não.",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="pagination",
                type=OpenApiTypes.INT,
                description="Define o número de itens por página (máximo 100, padrão 5).",
                required=False,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        description="Campos obrigatórios para obter resposta do endpoint.",
        parameters=[
            OpenApiParameter(
                name="token",
                type=OpenApiTypes.STR,
                description="Campo obrigatório para uso do endpoint.",
                required=True,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


@extend_schema(tags=["Empréstimos"])
class RealizarEmprestimoView(GenericAPIView):
    serializer_class = RealizarEmprestimoSerializer
    http_method_names = ["post"]
    permission_classes = [CanUseSystem]

    def perform_update(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def perform_create(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            horario_emprestimo = datetime.now()

            data_serializer = serializer.validated_data

            chave = Chaves.objects.get(pk=data_serializer["chave"])

            usuario_solicitante = Usuarios.objects.get(
                pk=data_serializer["usuario_solicitante"]
            )

            usuario_responsavel = UsuariosResponsaveis.objects.get(
                pk=data_serializer["usuario_responsavel"]
            )
        except Chaves.DoesNotExist:
            data = {"status": "error", "message": "Chave não encontrada."}
            return Response(status=status.HTTP_404_NOT_FOUND, data=data)

        except Usuarios.DoesNotExist:
            data = {
                "status": "error",
                "message": "Usuário solicitante não encontrado.",
            }
            return Response(status=status.HTTP_404_NOT_FOUND, data=data)
        except UsuariosResponsaveis.DoesNotExist:
            data = {
                "status": "error",
                "message": "Usuário responsável não encontrado.",
            }
            return Response(status=status.HTTP_404_NOT_FOUND, data=data)

        if not chave.disponivel:
            data = {
                "status": "error",
                "message": "Chave não disponível para empréstimo.",
            }
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        setor_consta = False
        for setor in usuario_solicitante.setor.split(","):
            if setor.strip().lower() in setores_usa_sistema_livremente:
                setor_consta = True
                break

        if not (usuario_solicitante.tipo.lower() in tipos_usa_sistema_livremente or setor_consta):
            if not PessoasAutorizadas.objects.filter(
                sala=chave.sala, usuario=usuario_solicitante
            ).exists():
                data = {
                    "status": "error",
                    "message": "Usuário não autorizado para usar a sala.",
                }
                return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        emprestimo = Emprestimos.objects.create(
            chave=chave,
            usuario_solicitante=usuario_solicitante,
            usuario_responsavel=usuario_responsavel,
            horario_emprestimo=horario_emprestimo,
            observacao=data_serializer.get("observacao", None),
        )

        chave.disponivel = False
        chave.save()

        data = {"status": "success", "emprestimo": emprestimo.id}

        return Response(data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Empréstimos"])
class FinalizarEmprestimoView(GenericAPIView):
    serializer_class = FinalizarEmprestimoSerializer
    http_method_names = ["post"]
    permission_classes = [CanUseSystem]

    def perform_update(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def perform_create(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            horario_devolucao = datetime.now()

            data_serializer = serializer.validated_data

            emprestimo = Emprestimos.objects.get(
                pk=data_serializer["id_emprestimo"])

        except Emprestimos.DoesNotExist:
            data = {"status": "error", "message": "Emprestimo não encontrado."}
            return Response(status=status.HTTP_404_NOT_FOUND, data=data)

        if emprestimo.horario_devolucao:
            data = {"status": "error", "message": "Emprestimo já finalizado."}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        emprestimo.horario_devolucao = horario_devolucao
        emprestimo.save()

        chave = emprestimo.chave
        chave.disponivel = True
        chave.save()

        data = {"status": "success"}

        return Response(data, status=status.HTTP_200_OK)


@extend_schema(tags=["Empréstimos"])
class TrocarEmprestimoView(GenericAPIView):
    serializer_class = TrocarEmprestimoSerializer
    http_method_names = ["post"]
    permission_classes = [CanUseSystem]

    def perform_update(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def perform_create(self, serializer):
        serializer.validated_data.pop("token")
        serializer.save()

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            horario_troca = datetime.now()

            data_serializer = serializer.validated_data

            emprestimo = Emprestimos.objects.get(
                pk=data_serializer["id_emprestimo"]
            )

            novo_solicitante = Usuarios.objects.get(
                pk=data_serializer["novo_solicitante"]
            )

            novo_responsavel = UsuariosResponsaveis.objects.get(
                pk=data_serializer["novo_responsavel"]
            )

        except Emprestimos.DoesNotExist:
            data = {"status": "error", "message": "Emprestimo não encontrado."}
            return Response(status=status.HTTP_404_NOT_FOUND, data=data)

        except Usuarios.DoesNotExist:
            data = {"status": "error", "message": "Usuário não encontrado."}
            return Response(status=status.HTTP_404_NOT_FOUND, data=data)

        except UsuariosResponsaveis.DoesNotExist:
            data = {"status": "error",
                    "message": "Usuário responsável não encontrado."}
            return Response(status=status.HTTP_404_NOT_FOUND, data=data)

        if emprestimo.horario_devolucao:
            data = {
                "status": "error",
                "message": "Emprestimo já finalizado.",
            }
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        setor_consta = False
        for setor in usuario_solicitante.setor.split(","):
            if setor.strip().lower() in setores_usa_sistema_livremente:
                setor_consta = True
                break

        if not (usuario_solicitante.tipo.lower() in tipos_usa_sistema_livremente or setor_consta):
            if not PessoasAutorizadas.objects.filter(
                usuario=novo_solicitante, sala=emprestimo.chave.sala
            ).exists():
                data = {
                    "status": "error",
                    "message": "Usuário não autorizado para usar a sala.",
                }
                return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        emprestimo.horario_devolucao = horario_troca
        emprestimo.save()

        emprestimo = Emprestimos.objects.create(
            chave=emprestimo.chave,
            usuario_solicitante=novo_solicitante,
            usuario_responsavel=novo_responsavel,
            horario_emprestimo=horario_troca,
        )

        data = {"status": "success"}

        return Response(data, status=status.HTTP_200_OK)
