import os
from datetime import date

from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import Blocos, Chaves, Salas, Usuarios


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
        ]

        extra_kwargs = {
            "nome": {"read_only": True},
            "setor": {"read_only": True},
            "tipo": {"read_only": True},
        }


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
        ]

    # Especeficação de que o campo "sala" é um uma chave primária relacionada ao Model Salas
    # O queryset determina que o serializer aceitará apenas IDs de salas que existem
    sala = serializers.PrimaryKeyRelatedField(queryset=Salas.objects.all())

    def validate_sala(self, value):
        chave = Chaves.objects.filter(sala=value)

        if chave:
            raise serializers.ValidationError("Uma sala só possui uma chave")

        return value
