from datetime import date

from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from .models import Blocos, Chaves, PessoasAutorizadas, Salas, Usuarios


class UsuariosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuarios
        fields = ["id_cortex", "id_setor", "id_tipo", "chaves_autorizadas", "chaves"]

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
