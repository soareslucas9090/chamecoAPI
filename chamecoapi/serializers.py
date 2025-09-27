import os
from datetime import date

from django.contrib.auth.hashers import make_password
from drf_spectacular.utils import OpenApiExample, extend_schema_field
from rest_framework import serializers

from .models import (
    Blocos,
    Chaves,
    Emprestimos,
    PessoasAutorizadas,
    Salas,
    Usuarios,
    UsuariosResponsaveis,
)


class VerifyTokenSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)


class LoginSerializer(serializers.Serializer):
    cpf = serializers.CharField(required=True)
    password = serializers.CharField(required=True)


class RetornoDeSalasEUsuariosSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nome = serializers.CharField(max_length=128)


class UsuariosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuarios
        fields = [
            "id",
            "id_cortex",
            "nome",
            "setor",
            "tipo",
            "salas",
            "salas_autorizadas",
            "token",
        ]

        extra_kwargs = {
            "nome": {"read_only": True},
            "setor": {"read_only": True},
            "tipo": {"read_only": True},
        }

        # Este é o campo destinado a escrita

    def validate_id_cortex(self, value):
        user = self.instance

        if user:
            if Usuarios.objects.filter(id_cortex=value).exclude(pk=user.pk).exists():
                raise serializers.ValidationError(
                    "Já existe um usuário com este id_cortex."
                )
        else:
            if Usuarios.objects.filter(id_cortex=value).exists():
                raise serializers.ValidationError(
                    "Já existe um usuário com este id_cortex."
                )

        return value

    token = serializers.CharField(write_only=True, required=True)

    salas_autorizadas = serializers.PrimaryKeyRelatedField(
        queryset=Salas.objects.all(), many=True, write_only=True, required=False
    )

    # Este é o campo destinado a leitura
    salas = serializers.SerializerMethodField(read_only=True)

    @extend_schema_field(
        field=serializers.ListField(
            child=RetornoDeSalasEUsuariosSerializer(),
        )
    )
    def get_salas(self, obj):
        data = []

        queryset = PessoasAutorizadas.objects.filter(usuario=obj)

        for autorizacao in queryset:
            aux = {}
            aux["id"] = autorizacao.sala.id
            aux["nome"] = str(autorizacao.sala)
            data.append(aux)

        return data


class BlocosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blocos
        fields = "__all__"

    token = serializers.CharField(write_only=True, required=True)


class SalasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salas
        fields = [
            "id",
            "nome",
            "bloco",
            "nome_bloco",
            "usuarios_autorizados",
            "usuarios",
            "token",
        ]

    token = serializers.CharField(write_only=True, required=True)

    bloco = serializers.PrimaryKeyRelatedField(queryset=Blocos.objects.all())

    nome_bloco = serializers.CharField(source="bloco.nome", read_only=True)

    usuarios_autorizados = serializers.PrimaryKeyRelatedField(
        queryset=Usuarios.objects.all(), many=True, write_only=True, required=False
    )

    usuarios = serializers.SerializerMethodField(read_only=True)

    # Método responsável por fornecer os dados para o campo "usuários"
    @extend_schema_field(
        field=serializers.ListField(
            child=RetornoDeSalasEUsuariosSerializer(),
        )
    )
    def get_usuarios(self, obj):
        data = []

        queryset = PessoasAutorizadas.objects.filter(sala=obj)

        for autorizacao in queryset:
            aux = {}
            aux["id"] = autorizacao.usuario.id
            aux["nome"] = str(autorizacao.usuario)
            data.append(aux)

        return data


class ChavesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chaves
        fields = [
            "id",
            "sala",
            "nome_sala",
            "disponivel",
            "descricao",
            "token",
        ]

    token = serializers.CharField(write_only=True, required=True)
    # Especeficação de que o campo "sala" é um uma chave primária relacionada ao Model Salas
    # O queryset determina que o serializer aceitará apenas IDs de salas que existem
    sala = serializers.PrimaryKeyRelatedField(queryset=Salas.objects.all())

    nome_sala = serializers.CharField(source="sala.nome", read_only=True)


class AutorizadosSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nome = serializers.CharField(read_only=True)


class UsuariosResponsaveisSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuariosResponsaveis
        fields = [
            "id",
            "nome",
            "superusuario",
            "token",
        ]

    token = serializers.CharField(write_only=True, required=True)

    superusuario = serializers.PrimaryKeyRelatedField(
        queryset=Usuarios.objects.all())


class EmprestimoDetalhadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emprestimos
        fields = [
            "id",
            "horario_emprestimo",
            "horario_devolucao",
            "chave",
            "usuario_responsavel",
            "usuario_solicitante",
            "observacao",
            "token",
        ]

    token = serializers.CharField(write_only=True, required=True)

    chave = serializers.PrimaryKeyRelatedField(queryset=Chaves.objects.all())
    usuario_responsavel = serializers.PrimaryKeyRelatedField(
        queryset=UsuariosResponsaveis.objects.all()
    )
    usuario_solicitante = serializers.PrimaryKeyRelatedField(
        queryset=Usuarios.objects.all()
    )


class RealizarEmprestimoSerializer(serializers.Serializer):
    chave = serializers.IntegerField(write_only=True)
    usuario_responsavel = serializers.IntegerField(write_only=True)
    usuario_solicitante = serializers.IntegerField(write_only=True)
    token = serializers.CharField(write_only=True, required=True)
    observacao = serializers.CharField(write_only=True, required=False)


class FinalizarEmprestimoSerializer(serializers.Serializer):
    id_emprestimo = serializers.IntegerField(write_only=True)
    token = serializers.CharField(write_only=True, required=True)


class TrocarEmprestimoSerializer(serializers.Serializer):
    id_emprestimo = serializers.IntegerField(write_only=True)
    novo_solicitante = serializers.IntegerField(write_only=True)
    novo_responsavel = serializers.IntegerField(write_only=True)
    token = serializers.CharField(write_only=True, required=True)
