import cv2
import torch
import numpy as np
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
from registro.models import Treinamento, Usuario, RegistroPonto
from datetime import datetime

class ReconhecimentoCamera:
    def __init__(self):
        self.mtcnn = MTCNN(image_size=160, margin=20)
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval()

        self.embeddings = []
        self.usuarios = []
        self.carregar_embeddings()

        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.threshold = 0.8
        self.alpha = 0.3
        self.dist_suavizadas = {}

        self.video = cv2.VideoCapture(0)
        self.registrado = False  # Flag para encerrar após registro

    def carregar_embeddings(self):
        for t in Treinamento.objects.all():
            if t.embedding:
                emb = np.frombuffer(t.embedding, dtype=np.float32)
                if emb.shape[0] == 512:
                    self.embeddings.append(torch.tensor(emb))
                    self.usuarios.append(t.usuario)

    def reconhecer_usuario(self):
        while True:
            ret, frame = self.video.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)

            face_tensor = self.mtcnn(img)

            if face_tensor is not None:
                with torch.no_grad():
                    emb_novo = self.resnet(face_tensor.unsqueeze(0)).squeeze(0)

                distancias = [torch.norm(emb_novo - emb) for emb in self.embeddings]
                menor_dist = min(distancias)
                idx = distancias.index(menor_dist)

                if menor_dist < self.threshold:
                    usuario = self.usuarios[idx]
                    self.video.release()
                    return usuario, frame

            cv2.putText(frame, 'Reconhecendo...', (10, 50), self.font, 0.9, (255, 255, 255), 2)
            cv2.imshow('Reconhecimento Facial', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.video.release()
        cv2.destroyAllWindows()
        return None, None

    def registrar_ponto(self, usuario):
        agora = datetime.now()
        hoje = agora.date()

        registros = RegistroPonto.objects.filter(usuario=usuario, data=hoje).order_by('-hora')

        if registros.exists():
            ultimo = registros.first()
            tipo = 'saida' if ultimo.tipo == 'entrada' else 'entrada'
        else:
            tipo = 'entrada'

        RegistroPonto.objects.create(
            usuario=usuario,
            data=hoje,
            hora=agora.time(),
            tipo=tipo
        )

        return tipo

    def reconhecer_numpy(self, frame):
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        face_tensor = self.mtcnn(img)

        if face_tensor is not None:
            with torch.no_grad():
                emb_novo = self.resnet(face_tensor.unsqueeze(0)).squeeze(0)

            distancias = [torch.norm(emb_novo - emb) for emb in self.embeddings]
            menor_dist = min(distancias)
            idx = distancias.index(menor_dist)

            if menor_dist < self.threshold:
                usuario = self.usuarios[idx]
                return usuario.id, usuario.nome

        return None, None

    def liberar_camera(self):
        self.video.release()
        cv2.destroyAllWindows()
