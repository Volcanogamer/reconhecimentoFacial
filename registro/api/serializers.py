from rest_framework import serializers
from registro.models import RegistroPonto, Treinamento, Usuario, ColetaFaces

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'id_usuario', 'cpf', 'nome', 'foto_facial', 'data_cadastro', 'situacao']

class RegistroPontoSerializer(serializers.ModelSerializer):
    nome_usuario = serializers.CharField(source='usuario.nome', read_only=True)

    class Meta:
        model = RegistroPonto
        fields = ['id_registro', 'usuario', 'nome_usuario', 'data', 'hora', 'tipo']
        read_only_fields = ['data', 'hora']

class TreinamentoSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source='usuario.nome', read_only=True)

    class Meta:
        model = Treinamento
        fields = ['usuario', 'usuario_nome', 'embedding']
        extra_kwargs = {
            #'embedding': {'write_only': True}  # comentar caso queira ver o conteúdo
        }

class ColetaFacesSerializer(serializers.ModelSerializer):
    nome_usuario = serializers.CharField(source='usuario.nome', read_only=True)

    class Meta:
        model = ColetaFaces
        fields = ['id', 'usuario', 'nome_usuario', 'image']