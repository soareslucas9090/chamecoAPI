import os
from datetime import date

from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import Blocos, Chaves, PessoasAutorizadas, Salas, Usuarios


class LoginSerializer(serializers.Serializer):
    cpf = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError(
                "A senha deve ter pelo menos 8 caracteres"
            )

        return value


class UsuariosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuarios
        fields = [
            "id",
            "id_cortex",
            "nome",
            "setor",
            "tipo",
            "chaves_autorizadas",
            "chaves",
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

    def get_chaves(self, obj):
        data = []

        queryset = PessoasAutorizadas.objects.filter(usuario=obj)

        for autorizacao in queryset:
            data.append(str(autorizacao.chave))

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
            "sala",
            "disponivel",
            "usuarios_autorizados",
            "usuarios",
        ]

        # Especeficação de que o campo "sala" é um uma chave primária relacionada ao Model Salas
        # O queryset determina que o serializer aceitará apenas IDs de salas que existem
        sala = serializers.PrimaryKeyRelatedField(queryset=Salas.objects.all())

        #
        usuarios_autorizados = serializers.PrimaryKeyRelatedField(
            queryset=Usuarios.objects.all(), many=True, write_only=True, required=False
        )

        usuarios = serializers.SerializerMethodField(read_only=True)

        # Método responsável por fornecer os dados para o campo "usuários"
        def get_usuarios(self, obj):
            data = []

            queryset = PessoasAutorizadas.objects.filter(chave=obj)

            for autorizacao in queryset:
                data.append(str(autorizacao.usuario))

            return data
