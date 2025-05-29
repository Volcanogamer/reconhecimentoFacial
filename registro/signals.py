import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Usuario, ColetaFaces

@receiver(post_delete, sender=Usuario)
def deletar_coletas_com_arquivos(sender, instance, **kwargs):
    coletas = ColetaFaces.objects.filter(usuario=instance)
    for coleta in coletas:
        if coleta.image and os.path.isfile(coleta.image.path):
            os.remove(coleta.image.path)
        coleta.delete()
