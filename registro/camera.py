import cv2

class VideoCamera(object):
    def __init__(self):
        self.video = cv2.VideoCapture(0)

        if not self.video.isOpened():
            print("Erro ao acessar câmera.")
        
    def __del__(self):
        self.video.release() # Libera a camera ao destruir a classe

    def restart(self):
        self.video.release() # Reinicia a camera
        self.video = cv2.VideoCapture(0) # Criar novamente uma outra instancia.

    def get_camera(self):
        ret, frame = self.video.read() # Leitura da camera
        if not ret:
            print("Falha ao capturar o frame.")
            return None
        
        # Inverte horizontalmente
        frame = cv2.flip(frame, 1)

        # Retorna o frame de deteccao como JPEG
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes() # Converte imagem em bytes
