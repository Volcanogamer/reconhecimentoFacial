import cv2
import os
from django.shortcuts import render, redirect  #, get_object_or_404
from .forms import UsuarioForm, ColetaFacesForm
from .models import Usuario, ColetaFaces, Treinamento, RegistroPonto
from django.http import StreamingHttpResponse
from registro.camera import VideoCamera

# ===================== API REST =====================
from rest_framework import viewsets
from registro.api.serializers import (
    UsuarioSerializer,
    ColetaFacesSerializer,
    TreinamentoSerializer,
    RegistroPontoSerializer
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly

# ViewSet da API - Usuário
class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# ViewSet da API - Coleta de Faces
class ColetaFacesViewSet(viewsets.ModelViewSet):
    queryset = ColetaFaces.objects.all()
    serializer_class = ColetaFacesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# ViewSet da API - Treinamento
class TreinamentoViewSet(viewsets.ModelViewSet):
    queryset = Treinamento.objects.all()
    serializer_class = TreinamentoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# ViewSet da API - Registro de Ponto
class RegistroPontoViewSet(viewsets.ModelViewSet):
    queryset = RegistroPonto.objects.all()
    serializer_class = RegistroPontoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# ===================== INTERFACE WEB =====================

camera_detection = VideoCamera()  # Chama classe VideoCamera

# Captura frame com a face detectada
def gen_detect_face(camera_detection):
    while True:
        frame = camera_detection.detect_face()  
        if frame is None:
            continue
        # Transmite esse frame como um stream
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

# Cria streaming para detecção facial
def face_detection(request):
    return StreamingHttpResponse(gen_detect_face(camera_detection),
                                 content_type='multipart/x-mixed-replace; \
                                     boundary=frame')

def criar_usuario(request):
    if request.method == 'POST':
        form = UsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            usuario = form.save()
            return redirect('criar_coleta_faces', usuario_id=usuario.id)
    else:
        form = UsuarioForm()

    return render(request, 'criar_usuario.html', {'form': form})

def criar_coleta_faces(request, usuario_id):

    print(usuario_id)
    usuario = Usuario.objects.get(id=usuario_id)
    
    # Tratamento quando usuario é inválido
    #usuario = get_object_or_404(Usuario, id=usuario_id)
    
    botao_clicado = request.GET.get('clicked', 'False') == 'True'

    context = {
        'usuario': usuario,  # Passa o objeto usuario p/ o template
        'face_detection': face_detection,  # Passa a camera p/ template
        'valor_botao': botao_clicado,
    }

    if botao_clicado:
        print("Cliquei em Extrair Fotos.")
        context = face_extract(context, usuario)  # Chama a função de extração

    return render(request, 'criar_coleta_faces.html', context)

# Cria uma função para extrair e retornar file_path
def extract(camera_detection, usuario):
    amostra = 0
    numeroAmostras = 10
    largura, altura = 250, 250  # Dimensiona o recorte da foto
    file_paths = []

    while amostra < numeroAmostras:
        _, frame = camera_detection.get_camera()
        crop = camera_detection.sample_faces(frame)

        # Aumento tamanho do recorte

        if crop is not None:
            amostra += 1

            face = cv2.resize(crop, (largura, altura))
            imagemCinza = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

            file_name_path = f'./temp/{usuario.id_usuario}_{amostra}.jpg'
            print(file_name_path)

            cv2.imwrite(file_name_path, imagemCinza)
            file_paths.append(file_name_path)
        else:
            print("Face não encontrada.")

    camera_detection.restart()
    return file_paths

def face_extract(context, usuario):
    num_coletas = ColetaFaces.objects.filter(usuario__id_usuario=usuario.id_usuario).count()

    print(num_coletas)

    if num_coletas >= 10:
        context['erro'] = 'Limite máximo de coletas atingido.'
    else:
        files_paths = extract(camera_detection, usuario)
        print(files_paths)  # Faces salvos

        for path in files_paths:
            # Cria uma instancia de ColetaFaces e salva imagem
            coleta_faces = ColetaFaces.objects.create(usuario=usuario)
            coleta_faces.image.save(os.path.basename(path), open(path, 'rb'))
            os.remove(path)  # Remove o arquivo temporário criado anteriormente

        # Atualiza o contexto com as coletas salvas
        context['file_paths'] = ColetaFaces.objects.filter(usuario__id_usuario=usuario.id_usuario)
        context['extracao_ok'] = True  # Sinaliza que foi um sucesso

    return context
