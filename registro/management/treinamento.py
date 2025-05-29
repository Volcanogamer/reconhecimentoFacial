import os
import torch
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1

from django.conf import settings
from django.core.management.base import BaseCommand
from registro.models import ColetaFaces, Treinamento, Usuario

class Command(BaseCommand):
    help = "Treina embeddings faciais com Facenet-PyTorch."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Inicializando treinamento com embeddings..."))
        self.treinamentoface()

    def treinamentoface(self):
        mtcnn = MTCNN(image_size=160, margin=20)
        resnet = InceptionResnetV1(pretrained='vggface2').eval()

        usuarios = Usuario.objects.all()
        erro_count = 0
        total_embeddings = 0

        for usuario in usuarios:
            coletadas = ColetaFaces.objects.filter(usuario=usuario)
            embeddings = []

            for coleta in coletadas:
                image_file = coleta.image.url.replace('/media/roi/', '')
                image_path = os.path.join(settings.MEDIA_ROOT, 'roi', image_file)

                if not os.path.exists(image_path):
                    print(f'Caminho não encontrado: {image_path}')
                    erro_count += 1
                    continue

                try:
                    img = Image.open(image_path).convert('RGB')
                    face = mtcnn(img)

                    if face is None:
                        print(f'Face não detectada em: {image_path}')
                        erro_count += 1
                        continue

                    with torch.no_grad():
                        embedding = resnet(face.unsqueeze(0))
                        embeddings.append(embedding.squeeze(0))

                except Exception as e:
                    print(f'Erro ao processar imagem {image_path}: {e}')
                    erro_count += 1

            if embeddings:
                embedding_medio = torch.stack(embeddings).mean(dim=0)

                # Salvar vetor no modelo Treinamento (como tensor serializado)
                buffer = embedding_medio.numpy().tobytes()
                treinamento, created = Treinamento.objects.get_or_create(usuario=usuario)
                treinamento.embedding = buffer
                treinamento.save()

                total_embeddings += 1
                print(f'Vetor de {usuario.id_usuario} treinado com {len(embeddings)} amostras.')

        self.stdout.write(self.style.ERROR(f'Total de imagens com erro: {erro_count}'))
        self.stdout.write(self.style.SUCCESS(f'Treinamento concluído para {total_embeddings} usuários.'))