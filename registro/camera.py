import cv2
import os
import torch
from facenet_pytorch import MTCNN
from PIL import Image
import numpy as np

class VideoCamera(object):
    # Instancia a camera presente
    def __init__(self):
        self.video = cv2.VideoCapture(0)
        if not self.video.isOpened():
            print("Erro ao acessar câmera.")
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.mtcnn = MTCNN(keep_all=True, device=self.device)

        self.img_dir = "./temp"

        # Garantir que o diretório 'temp' foi criado
        if not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir) # Cria a pasta temp caso não exista

    # Deleta a instancia de camera
    def __del__(self):
        self.video.release()

    # Reinicia a camera
    def restart(self):
        self.video.release()
        self.video = cv2.VideoCapture(0)

    # Captura os frames da camera
    def get_camera(self):
        ret, frame = self.video.read()
        if not ret:
            print("Falha ao capturar o frame.")
            return None, None

        frame = cv2.flip(frame, 1)
        return ret, frame

    def detect_face(self):
        ret, frame = self.get_camera()
        if not ret:
            return None

        # Converte p/ formato padrão do facenet
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)

        # Centro da camera
        altura, largura, _ = frame.shape
        centro_x, centro_y = int(largura / 2), int(altura / 2)
        a, b = 140, 180

        # Detecta faces
        boxes, _ = self.mtcnn.detect(pil_image)

        # Cor padrão da elipse (vermelha)
        cor_elipse = (0, 0, 255)

        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = [int(coord) for coord in box]
                face_centro_x = int((x1 + x2) / 2)
                face_centro_y = int((y1 + y2) / 2)

                # Verifica se o centro da face está dentro da elipse
                dentro_elipse = (((face_centro_x - centro_x) ** 2) / (a ** 2)) + (((face_centro_y - centro_y) ** 2) / (b ** 2)) <= 1

                if dentro_elipse:
                    cor_elipse = (0, 255, 0)  # verde se a face estiver dentro da elipse

        # Desenha a elipse no centro com a cor definida
        cv2.ellipse(frame, (centro_x, centro_y), (a, b), 0, 0, 360, cor_elipse, 4)

        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes(), None
    
    # Recorte do rosto na camera
    def sample_faces(self, frame):
        ret, frame = self.get_camera()
        if not ret:
            return None

        frame = cv2.resize(frame, (480, 360))
        pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        boxes, _ = self.mtcnn.detect(pil_image)

        if boxes is not None:
            for box in boxes:
                if box is not None and len(box) == 4:
                    x1, y1, x2, y2 = [int(coord) for coord in box]

                    # Define o aumento em %
                    aumento = 0.10

                    largura = x2 - x1
                    altura = y2 - y1

                    # Calcula as novas coordenadas com o aumento
                    x1_aumentado = max(0, int(x1 - largura * aumento))
                    y1_aumentado = max(0, int(y1 - altura * aumento))
                    x2_aumentado = min(frame.shape[1], int(x2 + largura * aumento))
                    y2_aumentado = min(frame.shape[0], int(y2 + altura * aumento))

                    # Desenha o retângulo (opcional)
                    cv2.rectangle(frame, (x1_aumentado, y1_aumentado), (x2_aumentado, y2_aumentado), (0, 255, 0), 4)

                    cropped_face = frame[y1_aumentado:y2_aumentado, x1_aumentado:x2_aumentado]
                    return cropped_face

        return None
