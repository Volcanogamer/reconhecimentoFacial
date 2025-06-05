import os
import shutil
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Usuario, ColetaFaces

@receiver(post_delete, sender=Usuario)
def deletar_fotos_usuario(sender, instance, **kwargs):
    """
    Remove:
    1. Arquivos temporários em ./temp com prefixo do usuário
    2. Pasta inteira do usuário em media/roi/<id_usuario>
    """
    # 1. Apagar arquivos temporários da pasta ./temp
    temp_dir = './temp'
    prefixo = instance.id_usuario

    if os.path.exists(temp_dir):
        for filename in os.listdir(temp_dir):
            if filename.startswith(str(prefixo)):
                caminho_arquivo = os.path.join(temp_dir, filename)
                try:
                    os.remove(caminho_arquivo)
                    print(f"Imagem removida: {caminho_arquivo}")
                except Exception as e:
                    print(f"Erro ao remover {caminho_arquivo}: {e}")

    # 2. Apagar a pasta do usuário dentro de media/roi/
    roi_dir = os.path.join('media', 'roi', str(instance.id_usuario))
    if os.path.exists(roi_dir):
        try:
            shutil.rmtree(roi_dir)
            print(f"Pasta do usuário removida: {roi_dir}")
        except Exception as e:
            print(f"Erro ao remover a pasta {roi_dir}: {e}")
