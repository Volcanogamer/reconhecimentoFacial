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
        # Inicializa o detector de faces (MTCNN) e o extrator de embeddings (InceptionResnetV1)
        mtcnn = MTCNN(image_size=160, margin=20, post_process=True)
        resnet = InceptionResnetV1(pretrained='vggface2').eval()

        usuarios = Usuario.objects.all()  # Busca todos os usuários no banco
        erro_count = 0
        total_embeddings = 0

        for usuario in usuarios:
            coletadas = ColetaFaces.objects.filter(usuario=usuario)  # Pega todas as imagens coletadas do usuário
            embeddings = []

            for coleta in coletadas:
                image_path = os.path.join(settings.MEDIA_ROOT, coleta.image.name)

                # Verifica se o arquivo existe
                if not os.path.exists(image_path):
                    print(f'Caminho não encontrado: {image_path}')
                    erro_count += 1
                    continue

                try:
                    # Abre a imagem e converte para RGB
                    img = Image.open(image_path).convert('RGB')

                    # Detecta e recorta a face
                    face_tensor = mtcnn(img)

                    if face_tensor is None:
                        print(f'Face não detectada em: {image_path}')
                        erro_count += 1
                        continue

                    # Gera o embedding com a rede neural
                    with torch.no_grad():
                        embedding = resnet(face_tensor.unsqueeze(0))  # Adiciona dimensão de batch

                    # Remove a dimensão de batch e adiciona à lista
                    embeddings.append(embedding.squeeze(0))

                except Exception as e:
                    print(f'Erro ao processar {image_path}: {e}')
                    erro_count += 1

            if embeddings:
                # Calcula a média dos embeddings para o usuário
                embedding_medio = torch.stack(embeddings).mean(dim=0)

                # Converte para bytes para armazenar no banco de dados
                buffer = embedding_medio.numpy().astype('float32').tobytes()

                # Cria ou atualiza o registro de treinamento do usuário
                treinamento, _ = Treinamento.objects.get_or_create(usuario=usuario)
                treinamento.embedding = buffer
                treinamento.save()

                total_embeddings += 1
                print(f'Embedding salvo para {usuario.id_usuario} ({len(embeddings)} amostras).')

        # Mostra quantos erros ocorreram e quantos usuários foram processados com sucesso
        self.stdout.write(self.style.ERROR(f'Total de erros: {erro_count}'))
        self.stdout.write(self.style.SUCCESS(f'Embeddings treinados para {total_embeddings} usuários.'))
