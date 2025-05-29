import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Usuario, ColetaFaces

@receiver(post_delete, sender=Usuario)
def deletar_fotos_usuario(sender, instance, **kwargs):
    """
    Remove arquivos temporários da pasta ./temp e imagens de roi/ associadas ao usuário.
    """
    # 1. Apagar arquivos da pasta temporária ./temp
    temp_dir = './temp'
    prefixo = instance.id_usuario

    if os.path.exists(temp_dir):
        for filename in os.listdir(temp_dir):
            if filename.startswith(prefixo):
                caminho_arquivo = os.path.join(temp_dir, filename)
                try:
                    os.remove(caminho_arquivo)
                    print(f"Imagem removida: {caminho_arquivo}")
                except Exception as e:
                    print(f"Erro ao remover {caminho_arquivo}: {e}")

    # 2. Apagar arquivos físicos da pasta media/roi/ vinculados ao usuário
    coletas = ColetaFaces.objects.filter(usuario=instance)
    for coleta in coletas:
        if coleta.image and os.path.exists(coleta.image.path):
            try:
                os.remove(coleta.image.path)
                print(f"Imagem roi removida: {coleta.image.path}")
            except Exception as e:
                print(f"Erro ao remover {coleta.image.path}: {e}")
