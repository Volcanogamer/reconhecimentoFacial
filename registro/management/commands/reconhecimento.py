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

        # Inicializa detector de faces (MTCNN) e extrator de embeddings (ResNet treinado com VGGFace2)
        mtcnn = MTCNN(image_size=160, margin=20)
        resnet = InceptionResnetV1(pretrained='vggface2').eval()

        # Carrega todos os embeddings do banco de dados
        treinamentos = Treinamento.objects.all()
        if not treinamentos:
            print("Nenhum embedding encontrado.")
            return

        base_embeddings = []  # Lista de embeddings salvos
        usuarios = []         # Lista de usuários correspondentes

        # Converte cada embedding armazenado em bytes para tensor
        for t in treinamentos:
            if t.embedding:
                emb_array = np.frombuffer(t.embedding, dtype=np.float32)
                if emb_array.shape[0] == 512:  # Verifica formato esperado
                    base_embeddings.append(torch.tensor(emb_array))
                    usuarios.append(t.usuario)

        if not base_embeddings:
            print("Nenhum vetor válido de embedding encontrado.")
            return

        # Parâmetros de controle
        threshold = 0.9  # Limite para decidir se é a mesma pessoa
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Dicionário para suavização das distâncias
        dist_suavizadas = {}
        alpha = 0.3  # Suavização exponencial (peso da nova medida)

        cap = cv2.VideoCapture(0)

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Erro ao acessar a câmera.")
                break
            
            # Inverte horizontalmente (espelho)
            frame = cv2.flip(frame, 1)

            # Converte BGR para RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)

            # Detecta rosto na imagem
            face_tensor = mtcnn(img)

            if face_tensor is not None:
                # Extrai o embedding da face detectada
                with torch.no_grad():
                    emb_novo = resnet(face_tensor.unsqueeze(0)).squeeze(0)

                # Calcula distância entre o embedding novo e os salvos
                distancias = [torch.norm(emb_novo - emb) for emb in base_embeddings]
                menor_dist = min(distancias)
                idx = distancias.index(menor_dist)

                if menor_dist < threshold:
                    # Se a distância for aceitável, identifica o usuário
                    nome = usuarios[idx].nome
                    dist = menor_dist.item()

                    # Aplica suavização na distância exibida
                    if nome not in dist_suavizadas:
                        dist_suavizadas[nome] = dist
                    else:
                        dist_anterior = dist_suavizadas[nome]
                        dist_suavizadas[nome] = alpha * dist + (1 - alpha) * dist_anterior

                    dist_exibida = dist_suavizadas[nome]

                    # Define nível de confiança e cor de exibição
                    if dist_exibida < 0.45:
                        interpretacao = 'Alta Confianca'
                        cor = (0, 255, 0)  # Verde
                    elif dist_exibida < 0.7:
                        interpretacao = 'Media Confianca'
                        cor = (0, 255, 0)  # Verde
                    elif dist_exibida < 0.9:
                        interpretacao = 'Baixa Confianca'
                        cor = (0, 140, 255)  # Laranja
                    else:
                        interpretacao = 'Desconhecido'
                        cor = (0, 0, 255)  # Vermelho

                    dist_exibida = (dist_exibida - 1)*(-1)

                    # Exibe nome e confiança no frame
                    texto = f'{nome} ({dist_exibida:.1f} - {interpretacao})'
                    cv2.putText(frame, texto, (20, 50), font, 0.8, cor, 2)
                else:
                    # Caso a distância não seja aceitável
                    cv2.putText(frame, 'Desconhecido', (20, 50), font, 0.9, (0, 0, 255), 2)
            else:
                # Nenhuma face foi detectada no frame
                cv2.putText(frame, 'Nenhuma face detectada', (20, 50), font, 0.9, (0, 0, 255), 2)

            cv2.imshow('Reconhecimento Facial - Facenet', frame)

            # Pressionar 'q' encerra o loop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Libera a câmera e fecha as janelas abertas
        cap.release()
        cv2.destroyAllWindows()
