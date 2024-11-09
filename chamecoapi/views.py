import os
from datetime import datetime

import jwt
import requests
from django.core.cache import cache
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

from .business import getTokens, requestFactory, setTokens
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
)

load_dotenv()
URL_BASE = os.environ.get("urlBase")


class DefaultNumberPagination(PageNumberPagination):
    page_size = 20


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

            setTokens(id_user, response.json()["access"], response.json()["refresh"])

            usuario_cortex = UsuariosViewSet.get_usuario(
                request, {"id_cortex": id_user}
            )

            if CanLogIn().has_permission(request=request, view=self, id_user=id_user):
                request.session["id_user"] = id_user

                data = {"status": "success"}

                try:

                    usuario = Usuarios.objects.get(id_cortex=id_user)

                    data["usuario"] = usuario.id

                    if usuario_cortex.status_code == 200:
                        setores = ", ".join(usuario_cortex.json()["nome_setores"])
                        usuario.nome = usuario_cortex.json()["nome"]
                        usuario.setor = setores
                        usuario.tipo = usuario_cortex.json()["nome_tipo"]
                        usuario.email = usuario_cortex.json()["email"]

                        usuario.save()
                except:
                    pass

            else:
                data = {"status": "error", "message": "Usuário não autorizado."}
                status_code = status.HTTP_403_FORBIDDEN

        else:
            data = response.json()

        return Response(data, status=status_code)


@extend_schema(tags=["Usuários"])
class UsuariosViewSet(ModelViewSet):
    queryset = Usuarios.objects.all()
    serializer_class = UsuariosSerializer
    pagination_class = DefaultNumberPagination
    permission_classes = [IsTokenValid]

    http_method_names = ["get", "put", "post", "delete", "head"]

    def get_queryset(self):
        queryset = super().get_queryset()

        chave_autorizada = self.request.query_params.get("chave_autorizada")

        if chave_autorizada and chave_autorizada.isnumeric():
            queryset = queryset.filter(
                chaves_autorizadas__id=int(chave_autorizada), autorizado_emprestimo=True
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
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_usuario(request: HttpRequest, serializer: dict) -> HttpResponse:
        """
        Método feito para a busca, na API, do ID do usuário do Cortex, pois
        ele sempre precisar ser válido, tanto na criação, quanto edição do usuário
        """
        id_user = request.session.get("id_user")

        # Verifica se há um "id_user" guardado na sessão do Django
        if not id_user:
            data = {"status": "error", "detail": "Usuário não logado."}
            return Response(data, status=status.HTTP_401_UNAUTHORIZED)

        id_cortex = serializer["id_cortex"]
        url_get_user = f"{URL_BASE}cortex/api/gerusuarios/v1/users/{id_cortex}"

        # Faz um get para verificar os detalhes do usuário na API do Cortex
        response = requestFactory("get", url_get_user, id_user)

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
                data = {"status": "error", "detail": "Token de acesso inválido."}
                return Response(data, status=status.HTTP_401_UNAUTHORIZED)

        return response

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer = serializer.validated_data

        response = UsuariosViewSet.get_usuario(request, serializer)

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
            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            serializer = serializer.validated_data

            if getattr(instance, "_prefetched_objects_cache", None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}

            response = UsuariosViewSet.get_usuario(request, serializer)

            if response.status_code != 200:
                return response

            # Criando o usuário caso todas as verificações ocorram bem
            setores = ", ".join(response.json()["nome_setores"])

            usuario = Usuarios.objects.get(id=kwargs["pk"])

            usuario.nome = response.json()["nome"]
            usuario.id_cortex = response.json()["id"]
            usuario.setor = setores
            usuario.tipo = response.json()["nome_tipo"]
            usuario.autorizado_emprestimo = serializer["autorizado_emprestimo"]
            if serializer.get("chaves_autorizadas", None):
                usuario.chaves_autorizadas.set(serializer["chaves_autorizadas"])

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

        return super().get_serializer_class()

    def get_pagination_class(self):
        if self.request.query_params.get("autorizado_emprestimo", None):
            return AuthorizedsNumberPagination
        return super().pagination_class

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE", "PUT", "POST"]:
            return [IsAdmin()]

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
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE", "PUT", "POST"]:
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
        if self.request.method in ["PATCH", "DELETE", "PUT", "POST"]:
            return [IsAdmin()]

        return super().get_permissions()


@extend_schema(tags=["Chaves"])
class ChavesViewSet(ModelViewSet):
    queryset = Chaves.objects.all()
    serializer_class = ChavesSerializer
    pagination_class = DefaultNumberPagination
    permission_classes = [IsTokenValid]

    http_method_names = ["get", "post", "put", "delete", "head"]

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
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE", "PUT", "POST"]:
            return [IsAdmin()]

        return super().get_permissions()


@extend_schema(tags=["Usuários Responsáveis"])
class UsuariosResponsaveisViewSet(ModelViewSet):
    queryset = UsuariosResponsaveis.objects.all()
    serializer_class = UsuariosResponsaveisSerializer
    pagination_class = DefaultNumberPagination
    permission_classes = [IsTokenValid]

    http_method_names = ["get", "post", "put", "delete", "head"]

    def get_queryset(self):
        queryset = super().get_queryset()

        nome_superusuario = self.request.query_params.get("nome_superusuario", None)

        if nome_superusuario:
            queryset = queryset.filter(superusuario__nome__icontains=nome_superusuario)

        superusuario = self.request.query_params.get("superusuario", None)

        if superusuario and superusuario.isnumeric():
            queryset = queryset.filter(superusuario__id=superusuario)

        nome = self.request.query_params.get("nome", None)

        if nome:
            queryset = queryset.filter(nome__icontains=nome)

        if not IsAdmin().has_permission(self.request, self, default_use=False):
            id_user = self.request.session.get("id_user")

            try:
                usuario = Usuarios.objects.get(id_cortex=id_user)
            except Usuarios.DoesNotExist:
                return Response(status=status.HTTP_403_FORBIDDEN)

            queryset = queryset.filter(superusuario=usuario)

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
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

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
    pagination_class = DefaultNumberPagination
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
            queryset = queryset.filter(usuario_solicitante__nome__icontains=solicitante)

        responsavel = self.request.query_params.get("responsavel", None)

        if responsavel:
            queryset = queryset.filter(usuario_responsavel__nome__icontains=responsavel)

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
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


@extend_schema(tags=["Empréstimos"])
class RealizarEmprestimoView(GenericAPIView):
    serializer_class = RealizarEmprestimoSerializer
    http_method_names = ["post"]
    permission_classes = [CanUseSystem]

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

        if not usuario_solicitante.autorizado_emprestimo:
            data = {
                "status": "error",
                "message": "Usuário não autorizado para empréstimo.",
            }
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        if not chave.disponivel:
            data = {
                "status": "error",
                "message": "Chave não disponível para empréstimo.",
            }
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        if not PessoasAutorizadas.objects.filter(
            chave=chave, usuario=usuario_solicitante
        ).exists():
            data = {
                "status": "error",
                "message": "Usuário não autorizado para usar a chave.",
            }
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        Emprestimos.objects.create(
            chave=chave,
            usuario_solicitante=usuario_solicitante,
            usuario_responsavel=usuario_responsavel,
            horario_emprestimo=horario_emprestimo,
        )

        chave.disponivel = False
        chave.save()

        data = {"status": "success"}

        return Response(data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Empréstimos"])
class FinalizarEmprestimoView(GenericAPIView):
    serializer_class = FinalizarEmprestimoSerializer
    http_method_names = ["post"]
    permission_classes = [CanUseSystem]

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            horario_devolucao = datetime.now()

            data_serializer = serializer.validated_data

            emprestimo = Emprestimos.objects.get(pk=data_serializer["id_emprestimo"])

        except Emprestimos.DoesNotExist:
            data = {"status": "error", "message": "Emprestimo não encontrado."}
            return Response(status=status.HTTP_404_NOT_FOUND, data=data)

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

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            horario_troca = datetime.now()

            data_serializer = serializer.validated_data

            emprestimo = Emprestimos.objects.get(pk=data_serializer["id_emprestimo"])

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
            data = {"status": "error", "message": "Usuário responsável não encontrado."}
            return Response(status=status.HTTP_404_NOT_FOUND, data=data)

        if emprestimo.horario_devolucao:
            data = {
                "status": "error",
                "message": "Emprestimo já finalizado.",
            }
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        if not novo_solicitante.autorizado_emprestimo:
            data = {
                "status": "error",
                "message": "Usuário não autorizado para empréstimo.",
            }
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        if not PessoasAutorizadas.objects.filter(
            usuario=novo_solicitante, chave=emprestimo.chave
        ).exists():
            data = {
                "status": "error",
                "message": "Usuário não autorizado para usar a chave.",
            }
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

        emprestimo.horario_devolucao = horario_troca
        emprestimo.save()

        Emprestimos.objects.create(
            chave=emprestimo.chave,
            usuario_solicitante=novo_solicitante,
            usuario_responsavel=novo_responsavel,
            horario_emprestimo=horario_troca,
        )

        data = {"status": "success"}

        return Response(data, status=status.HTTP_200_OK)
