import cv2
import os
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UsuarioForm, ColetaFacesForm
from .models import Usuario, ColetaFaces, Treinamento, RegistroPonto
from django.http import StreamingHttpResponse
from registro.camera import VideoCamera
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.utils import timezone

# ===================== API REST =====================
from registro.api.serializers import (
    UsuarioSerializer,
    ColetaFacesSerializer,
    TreinamentoSerializer,
    RegistroPontoSerializer
)

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class ColetaFacesViewSet(viewsets.ModelViewSet):
    queryset = ColetaFaces.objects.all()
    serializer_class = ColetaFacesSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class TreinamentoViewSet(viewsets.ModelViewSet):
    queryset = Treinamento.objects.all()
    serializer_class = TreinamentoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class RegistroPontoViewSet(viewsets.ModelViewSet):
    queryset = RegistroPonto.objects.all()
    serializer_class = RegistroPontoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# ===================== INTERFACE WEB =====================
camera_detection = VideoCamera()

def gen_detect_face(camera_detection):
    while True:
        frame, usuario_id = camera_detection.detect_face()
        if frame is None:
            continue

        if usuario_id is not None:
            usuario = Usuario.objects.filter(id_usuario=usuario_id).first()
            if usuario:
                RegistroPonto.objects.create(usuario=usuario, horario=timezone.now())

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

def gerar_streaming():
    return StreamingHttpResponse(gen_detect_face(camera_detection),
                                 content_type='multipart/x-mixed-replace;boundary=frame')

def face_detection(request):
    return gerar_streaming()

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
    usuario = get_object_or_404(Usuario, id=usuario_id)
    botao_clicado = request.GET.get('clicked', 'False') == 'True'

    legendas = [
        "Olhe diretamente para a camera (frente)",
        "Incline levemente a cabeca para a esquerda",
        "Incline levemente a cabeca para a direita",
        "Levante um pouco o queixo (cabeca para cima)",
        "Abaixe um pouco o queixo (cabeca para baixo)",
        "Mantenha uma expressao neutra e relaxada"
    ]

    if 'foto_passos' not in request.session:
        request.session['foto_passos'] = 0

    passo_atual = request.session['foto_passos']

    context = {
        'usuario': usuario,
        'face_detection': face_detection,
        'valor_botao': botao_clicado,
        'legenda_orientacao': legendas[passo_atual],
        'extracao_ok': False,
        'file_paths': ColetaFaces.objects.filter(usuario__id_usuario=usuario.id_usuario),
        'erro': None,
    }

    if botao_clicado:
        sucesso = face_extract(context, usuario)
        if sucesso:
            if passo_atual < 5:
                request.session['foto_passos'] = passo_atual + 1
                request.session.modified = True
            else:
                context['extracao_ok'] = True
                del request.session['foto_passos']
                
                # Força a destruição do objeto da câmera, que chama __del__()
                global camera_detection
                del camera_detection

    return render(request, 'criar_coleta_faces.html', context)

def extract(camera_detection, usuario):
    largura, altura = 200, 200
    file_paths = []

    _, frame = camera_detection.get_camera()
    crop = camera_detection.sample_faces(frame)

    if crop is not None:
        face = cv2.resize(crop, (largura, altura))
        imagemCinza = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

        qtd_atual = ColetaFaces.objects.filter(usuario__id_usuario=usuario.id_usuario).count()
        file_name_path = f'./temp/{usuario.id_usuario}_{qtd_atual + 1}.jpg'

        cv2.imwrite(file_name_path, imagemCinza)
        file_paths.append(file_name_path)
        return file_paths
    else:
        print("Face nao encontrada.")
        return None

def face_extract(context, usuario):
    coletas = ColetaFaces.objects.filter(usuario__id_usuario=usuario.id_usuario)
    for coleta in coletas:
        if coleta.image and not os.path.isfile(coleta.image.path):
            print(f"Removendo coleta invalida: {coleta.image.path}")
            coleta.delete()

    qtd_atual = ColetaFaces.objects.filter(usuario__id_usuario=usuario.id_usuario).count()
    if qtd_atual >= 6:
        context['erro'] = 'Limite maximo de coletas atingido.'
        return False

    files_paths = extract(camera_detection, usuario)
    if not files_paths:
        context['erro'] = 'Nao foi possivel detectar o rosto. Tente novamente.'
        return False

    for path in files_paths:
        coleta_faces = ColetaFaces.objects.create(usuario=usuario)
        with open(path, 'rb') as f:
            coleta_faces.image.save(os.path.basename(path), f)
        os.remove(path)

    context['file_paths'] = ColetaFaces.objects.filter(usuario__id_usuario=usuario.id_usuario)
    return True

def reconhecimento_view(request):
    return render(request, 'reconhecimento.html')

def video_reconhecimento(request):
    return gerar_streaming()