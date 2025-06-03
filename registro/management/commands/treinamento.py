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
        mtcnn = MTCNN(image_size=160, margin=20, post_process=True)
        resnet = InceptionResnetV1(pretrained='vggface2').eval()

        usuarios = Usuario.objects.all()
        erro_count = 0
        total_embeddings = 0

        for usuario in usuarios:
            coletadas = ColetaFaces.objects.filter(usuario=usuario)
            embeddings = []

            for coleta in coletadas:
                image_path = os.path.join(settings.MEDIA_ROOT, 'roi', os.path.basename(coleta.image.name))

                if not os.path.exists(image_path):
                    print(f'Caminho não encontrado: {image_path}')
                    erro_count += 1
                    continue

                try:
                    img = Image.open(image_path).convert('RGB')
                    face_tensor = mtcnn(img)

                    if face_tensor is None:
                        print(f'Face não detectada em: {image_path}')
                        erro_count += 1
                        continue

                    with torch.no_grad():
                        embedding = resnet(face_tensor.unsqueeze(0))
                        embeddings.append(embedding.squeeze(0))  # Remove batch dim

                except Exception as e:
                    print(f'Erro ao processar {image_path}: {e}')
                    erro_count += 1

            if embeddings:
                # Média dos embeddings coletados
                embedding_medio = torch.stack(embeddings).mean(dim=0)

                # Salvar como bytes no banco de dados
                buffer = embedding_medio.numpy().astype('float32').tobytes()
                treinamento, _ = Treinamento.objects.get_or_create(usuario=usuario)
                treinamento.embedding = buffer
                treinamento.save()

                total_embeddings += 1
                print(f'Embedding salvo para {usuario.id_usuario} ({len(embeddings)} amostras).')

        self.stdout.write(self.style.ERROR(f'Total de erros: {erro_count}'))
        self.stdout.write(self.style.SUCCESS(f'Embeddings treinados para {total_embeddings} usuários.'))