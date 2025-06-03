import os
import cv2
import torch
import numpy as np
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1

from django.conf import settings
from django.core.management.base import BaseCommand
from registro.models import Treinamento, Usuario

class Command(BaseCommand):
    help = 'Reconhecimento facial em tempo real com embeddings Facenet.'

    def handle(self, *args, **kwargs):
        self.reconhecer_faces()

    def reconhecer_faces(self):
        print("Iniciando reconhecimento facial...")

        # Inicializa MTCNN e ResNet
        mtcnn = MTCNN(image_size=160, margin=20)
        resnet = InceptionResnetV1(pretrained='vggface2').eval()

        # Carrega todos os embeddings salvos
        treinamentos = Treinamento.objects.all()
        if not treinamentos:
            print("Nenhum embedding encontrado.")
            return

        base_embeddings = []
        usuarios = []

        for t in treinamentos:
            if t.embedding:
                emb_array = np.frombuffer(t.embedding, dtype=np.float32)
                if emb_array.shape[0] == 512:
                    base_embeddings.append(torch.tensor(emb_array))
                    usuarios.append(t.usuario)

        if not base_embeddings:
            print("Nenhum vetor válido de embedding encontrado.")
            return

        # Parâmetros
        threshold = 0.9  # Limite de distância para aceitar como "igual"
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Suavização das distâncias por nome de usuário
        dist_suavizadas = {}
        alpha = 0.3  # quanto menor, mais lento muda

        # Inicia câmera
        cap = cv2.VideoCapture(0)

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Erro ao acessar a câmera.")
                break

            frame = cv2.flip(frame, 1)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)

            # Detecta face
            face_tensor = mtcnn(img)

            if face_tensor is not None:
                with torch.no_grad():
                    emb_novo = resnet(face_tensor.unsqueeze(0)).squeeze(0)

                # Calcula distâncias
                distancias = [torch.norm(emb_novo - emb) for emb in base_embeddings]
                menor_dist = min(distancias)
                idx = distancias.index(menor_dist)

                if menor_dist < threshold:
                    nome = usuarios[idx].nome
                    dist = menor_dist.item()

                    # Suavização EMA por nome
                    if nome not in dist_suavizadas:
                        dist_suavizadas[nome] = dist
                    else:
                        dist_anterior = dist_suavizadas[nome]
                        dist_suavizadas[nome] = alpha * dist + (1 - alpha) * dist_anterior

                    dist_exibida = dist_suavizadas[nome]

                    # Interpretação da distância
                    if dist_exibida < 0.46:
                        interpretacao = 'Alta confianca'
                        cor = (0, 255, 0) # Verde
                    elif dist_exibida < 0.75:
                        interpretacao = 'Media alta'
                        cor = (0, 255, 0)  # Verde
                    elif dist_exibida < 0.9:
                        interpretacao = 'Baixa confianca'
                        cor = (0, 140, 255)  # Laranja
                    else:
                        interpretacao = 'Desconhecido'
                        cor = (0, 0, 255) # Vermelho

                    texto = f'{nome} ({dist_exibida:.1f} - {interpretacao})'
                    cv2.putText(frame, texto, (20, 50), font, 0.8, cor, 2)
                else:
                    cv2.putText(frame, 'Desconhecido', (20, 50), font, 0.9, (0, 0, 255), 2)
            else:
                cv2.putText(frame, 'Nenhuma face detectada', (20, 50), font, 0.9, (0, 0, 255), 2)

            # Exibe resultado
            cv2.imshow('Reconhecimento Facial - Facenet', frame)

            # Pressione 'q' para sair
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
