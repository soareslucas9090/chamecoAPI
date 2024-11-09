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


class LoginSerializer(serializers.Serializer):
    cpf = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "A senha deve ter pelo menos 8 caracteres"
            )

        return value


class RetornoDeChavesEUsuariosSerializer(serializers.Serializer):
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
            "autorizado_emprestimo",
            "chaves",
            "chaves_autorizadas",
        ]

        extra_kwargs = {
            "nome": {"read_only": True},
            "setor": {"read_only": True},
            "tipo": {"read_only": True},
        }

        # Este é o campo destinado a escrita

    chaves_autorizadas = serializers.PrimaryKeyRelatedField(
        queryset=Chaves.objects.all(), many=True, write_only=True, required=False
    )

    # Este é o campo destinado a leitura
    chaves = serializers.SerializerMethodField(read_only=True)

    @extend_schema_field(
        field=serializers.ListField(
            child=RetornoDeChavesEUsuariosSerializer(),
        )
    )
    def get_chaves(self, obj):
        data = []

        queryset = PessoasAutorizadas.objects.filter(usuario=obj)

        for autorizacao in queryset:
            aux = {}
            aux["id"] = autorizacao.chave.id
            aux["nome"] = str(autorizacao.chave)
            data.append(aux)

        return data


class BlocosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blocos
        fields = "__all__"


class SalasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Salas
        fields = "__all__"

    bloco = serializers.PrimaryKeyRelatedField(queryset=Blocos.objects.all())


class ChavesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chaves
        fields = [
            "id",
            "sala",
            "disponivel",
            "usuarios_autorizados",
            "usuarios",
        ]

    # Especeficação de que o campo "sala" é um uma chave primária relacionada ao Model Salas
    # O queryset determina que o serializer aceitará apenas IDs de salas que existem
    sala = serializers.PrimaryKeyRelatedField(queryset=Salas.objects.all())

    usuarios_autorizados = serializers.PrimaryKeyRelatedField(
        queryset=Usuarios.objects.all(), many=True, write_only=True, required=False
    )

    usuarios = serializers.SerializerMethodField(read_only=True)

    # Método responsável por fornecer os dados para o campo "usuários"
    @extend_schema_field(
        field=serializers.ListField(
            child=RetornoDeChavesEUsuariosSerializer(),
        )
    )
    def get_usuarios(self, obj):
        data = []

        queryset = PessoasAutorizadas.objects.filter(chave=obj)

        for autorizacao in queryset:
            aux = {}
            aux["id"] = autorizacao.usuario.id
            aux["nome"] = str(autorizacao.usuario)
            data.append(aux)

        return data


class AutorizadosSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nome = serializers.CharField(read_only=True)


class UsuariosResponsaveisSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuariosResponsaveis
        fields = "__all__"


class EmprestimoDetalhadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Emprestimos
        fields = "__all__"

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


class FinalizarEmprestimoSerializer(serializers.Serializer):
    id_emprestimo = serializers.IntegerField(write_only=True)


class TrocarEmprestimoSerializer(serializers.Serializer):
    id_emprestimo = serializers.IntegerField(write_only=True)
    novo_solicitante = serializers.IntegerField(write_only=True)
    novo_responsavel = serializers.IntegerField(write_only=True)
