from django.core.management.base import BaseCommand
import cv2

class Command(BaseCommand):
    help = 'Abre a câmera'

    def handle(self, *args, **kwargs):
        # Abre a câmera
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            self.stdout.write(self.style.ERROR('Erro ao abrir a câmera'))
            return

        self.stdout.write(self.style.SUCCESS('Câmera aberta com sucesso. Pressione "Q" para sair.'))

        while True:
            # Captura frame por frame
            ret, frame = cap.read()

            if not ret:
                self.stdout.write(self.style.ERROR('Erro ao capturar o frame'))
                break
            
            # inverte camera horizontalmente
            inv_frame = cv2.flip(frame, 1)

            # Exibe o frame
            cv2.imshow('camera', inv_frame)

            # Sai do loop ao pressionar 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Libera a câmera e fecha as janelas
        cap.release()
        cv2.destroyAllWindows()
        self.stdout.write(self.style.SUCCESS('Câmera fechada.'))