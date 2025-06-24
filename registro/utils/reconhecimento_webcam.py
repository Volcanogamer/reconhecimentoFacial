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

    def gerar_frames(self):
        while True:
            if self.registrado:
                break

            ret, frame = self.video.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)

            face_tensor = self.mtcnn(img)
            nome = 'Desconhecido'

            if face_tensor is not None:
                with torch.no_grad():
                    emb_novo = self.resnet(face_tensor.unsqueeze(0)).squeeze(0)

                distancias = [torch.norm(emb_novo - emb) for emb in self.embeddings]
                menor_dist = min(distancias)
                idx = distancias.index(menor_dist)

                if menor_dist < self.threshold:
                    usuario = self.usuarios[idx]
                    nome = usuario.nome
                    dist = menor_dist.item()

                    if nome not in self.dist_suavizadas:
                        self.dist_suavizadas[nome] = dist
                    else:
                        self.dist_suavizadas[nome] = self.alpha * dist + (1 - self.alpha) * self.dist_suavizadas[nome]

                    dist_exibida = self.dist_suavizadas[nome]
                    dist_exibida = (dist_exibida - 1)*(-1)

                    agora = datetime.now()
                    hoje = agora.date()

                    registros = RegistroPonto.objects.filter(usuario=usuario, data=hoje).order_by('-hora')

                    proximo_tipo = 'entrada'
                    registrar = True

                    if registros.exists():
                        ultimo = registros.first()
                        delta = datetime.combine(hoje, agora.time()) - datetime.combine(hoje, ultimo.hora)
                        
                        if delta.total_seconds() < 10: # Intervalo necessário após uma detecção
                            registrar = False
                            mensagem = f"Aguarde {int(10 - delta.total_seconds())}s para novo registro"
                        else:
                            proximo_tipo = 'saida' if ultimo.tipo == 'entrada' else 'entrada'
                            RegistroPonto.objects.create(
                                usuario=usuario,
                                data=hoje,
                                hora=agora.time(),
                                tipo=proximo_tipo
                            )
                            mensagem = f"{proximo_tipo.capitalize()} registrada com sucesso para {nome}"
                            self.registrado = True
                    else:
                        RegistroPonto.objects.create(
                            usuario=usuario,
                            data=hoje,
                            hora=agora.time(),
                            tipo='entrada'
                        )
                        mensagem = f"Entrada registrada com sucesso para {nome}"
                        self.registrado = True

                    cor = (0, 255, 0) if registrar else (0, 140, 255)
                    cv2.putText(frame, mensagem, (10, 50), self.font, 0.7, cor, 2)

                else:
                    cv2.putText(frame, 'Desconhecido', (10, 50), self.font, 0.9, (0, 0, 255), 2)
            else:
                cv2.putText(frame, 'Nenhuma face detectada', (10, 50), self.font, 0.9, (0, 0, 255), 2)

            ret, jpeg = cv2.imencode('.jpg', frame)
            yield jpeg.tobytes()

        # Após registro, libera a câmera
        self.video.release()

    def __del__(self):
        if hasattr(self, 'video') and self.video is not None:
            self.video.release()
