import cv2
import os
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UsuarioForm, ColetaFacesForm
from .models import Usuario, ColetaFaces, Treinamento, RegistroPonto
from django.http import StreamingHttpResponse
from registro.camera import VideoCamera
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.utils import timezone
from registro.utils.reconhecimento_webcam import ReconhecimentoCamera
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.utils.timezone import localtime
import json
import base64
import numpy as np
from PIL import Image
from io import BytesIO
from django.core.management import call_command

from registro.utils.reconhecimento_webcam import ReconhecimentoCamera

# ===================== API REST =====================
from registro.api.serializers import (
    UsuarioSerializer,
    ColetaFacesSerializer,
    TreinamentoSerializer,
    RegistroPontoSerializer,
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
def gen_detect_face():
    camera = VideoCamera()
    while True:
        frame, usuario_id = camera.detect_face()
        if frame is None:
            continue

        if usuario_id is not None:
            usuario = Usuario.objects.filter(id_usuario=usuario_id).first()
            if usuario:
                RegistroPonto.objects.create(usuario=usuario, horario=timezone.now())

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n")

def face_detection(request):
    return StreamingHttpResponse(
        gen_detect_face(),
        content_type="multipart/x-mixed-replace;boundary=frame"
    )

def criar_usuario(request):
    if request.method == "POST":
        form = UsuarioForm(request.POST, request.FILES)
        if form.is_valid():
            usuario = form.save()
            return redirect("criar_coleta_faces", usuario_id=usuario.id)
    else:
        form = UsuarioForm()

    return render(request, "criar_usuario.html", {"form": form})

def criar_coleta_faces(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    botao_clicado = request.GET.get("clicked", "False") == "True"

    legendas = [
        "Olhe diretamente para a camera (frente)",
        "Incline levemente a cabeca para a esquerda",
        "Incline levemente a cabeca para a direita",
        "Levante um pouco o queixo (cabeca para cima)",
        "Abaixe um pouco o queixo (cabeca para baixo)",
        "Mantenha uma expressao neutra e relaxada",
    ]

    if "foto_passos" not in request.session:
        request.session["foto_passos"] = 0

    passo_atual = request.session["foto_passos"]

    context = {
        "usuario": usuario,
        "face_detection": face_detection,
        "valor_botao": botao_clicado,
        "extracao_ok": False,
        "file_paths": ColetaFaces.objects.filter(
            usuario__id_usuario=usuario.id_usuario
        ),
        "erro": None,
    }

    if botao_clicado:
        sucesso = face_extract(context, usuario)
        if sucesso:
            if passo_atual < 5:
                request.session["foto_passos"] = passo_atual + 1
                request.session.modified = True
                passo_atual += 1
            else:
                context["extracao_ok"] = True
                del request.session["foto_passos"]

                # Força a destruição do objeto da câmera
                global camera_detection
                del camera_detection

    # Atualiza a legenda corretamente após tirar a foto
    context["legenda_orientacao"] = legendas[passo_atual]

    return render(request, "criar_coleta_faces.html", context)

def extract(camera_detection, usuario):
    largura, altura = 200, 200
    file_paths = []

    _, frame = camera_detection.get_camera()
    crop = camera_detection.sample_faces(frame)

    if crop is not None:
        face = cv2.resize(crop, (largura, altura))
        imagemCinza = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

        qtd_atual = ColetaFaces.objects.filter(
            usuario__id_usuario=usuario.id_usuario
        ).count()
        file_name_path = f"./temp/{usuario.id_usuario}_{qtd_atual + 1}.jpg"

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

    qtd_atual = ColetaFaces.objects.filter(
        usuario__id_usuario=usuario.id_usuario
    ).count()
    if qtd_atual >= 6:
        context["erro"] = "Limite maximo de coletas atingido."
        return False

    files_paths = extract(camera_detection, usuario)
    if not files_paths:
        context["erro"] = "Nao foi possivel detectar o rosto. Tente novamente."
        return False

    for path in files_paths:
        coleta_faces = ColetaFaces.objects.create(usuario=usuario)
        with open(path, "rb") as f:
            coleta_faces.image.save(os.path.basename(path), f)
        os.remove(path)

    context["file_paths"] = ColetaFaces.objects.filter(
        usuario__id_usuario=usuario.id_usuario
    )
    return True

def reconhecimento_view(request):
    return render(request, "reconhecimento.html")

# Reconhecimento com registro automático
reconhecimento_camera = ReconhecimentoCamera()

def gen_reconhecimento(camera):
    for frame in camera.gerar_frames():
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n\r\n")

def video_reconhecimento(request):
    return StreamingHttpResponse(
        gen_reconhecimento(reconhecimento_camera),
        content_type="multipart/x-mixed-replace; boundary=frame"
    )
    
def index(request):
    return render(request, 'index.html')

def login(request):
    return render(request, 'admin/login.html')

# Dashboard -> carrega todas as informações vinculadas ao usuário
@staff_member_required
def dashboard(request):
    return render(request, 'admin/dashboard.html')

@staff_member_required
def dashboard_usuarios(request):
    usuarios = Usuario.objects.all()
    return render(request, 'admin/conteudo/usuarios.html', {'usuarios': usuarios})

@staff_member_required
def dashboard_treinamentos(request):
    treinamentos = Treinamento.objects.select_related('usuario').all()
    return render(request, 'admin/conteudo/treinamentos.html', {'treinamentos': treinamentos})

@staff_member_required
def dashboard_registros(request):
    nome = request.GET.get('nome', '')
    data = request.GET.get('data', '')
    tipo = request.GET.get('tipo', '')

    registros = RegistroPonto.objects.select_related('usuario').order_by('-data', '-hora')

    if nome:
        registros = registros.filter(usuario__nome__icontains=nome)
    if data:
        registros = registros.filter(data=data)
    if tipo:
        registros = registros.filter(tipo=tipo)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Retorna só o fragmento da tabela
        html = render_to_string('admin/conteudo/_registros_tabela.html', {'registros': registros})
        return JsonResponse({'html': html})

    # Página completa
    return render(request, 'admin/conteudo/registros.html', {'registros': registros})

# Carrega todas as infs dos usuarios no dashboard
@staff_member_required
def dashboard_usuario_detalhes(request, id_usuario):
    usuario = get_object_or_404(Usuario, id=id_usuario)
    coletas = ColetaFaces.objects.filter(usuario=usuario)

    if request.method == "POST":
        form = UsuarioForm(request.POST, request.FILES, instance=usuario)

        # Converte a string do dropdown para booleano
        situacao_valor = request.POST.get("situacao")
        if situacao_valor in ["True", "False"]:
            usuario.situacao = True if situacao_valor == "True" else False

        if form.is_valid():
            form.save()
            usuario.save()  # salva o campo situacao
    else:
        form = UsuarioForm(instance=usuario)

    return render(request, "admin/conteudo/usuario_detalhes.html", {
        "form": form,
        "usuario": usuario,
        "coletas": coletas,
    })

# Salvar/Atualizar infs do usuário no dashboard admin
def salvar_usuario(request, id):
    usuario = get_object_or_404(Usuario, id=id)

    if request.method == 'POST':
        form = UsuarioForm(request.POST, request.FILES, instance=usuario)

        # Situação vem de um campo manual
        situacao = request.POST.get("situacao") == "True"

        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.situacao = situacao
            usuario.save()
            messages.success(request, "Usuário atualizado com sucesso!")
        else:
            messages.error(request, "Erro ao salvar os dados.")
            print(form.errors)  # Para debug se necessário

    return redirect('/dashboard/')

# Remover fotos de coleta selecionadas no dashboard admin
@staff_member_required
def remover_fotos_coleta_selecionadas(request, id_usuario):
    if request.method == 'POST':
        fotos_ids = request.POST.getlist('fotos_remover')
        ColetaFaces.objects.filter(id__in=fotos_ids).delete()
        messages.success(request, "Fotos removidas com sucesso!")

    return redirect('/dashboard/')

# Treinamento dos Usuários admin
def treinar_usuarios_ativos(request):
    if request.method == 'POST':
        try:
            call_command('treinamento', ativos=True)
            return JsonResponse({"mensagem": "Treinamento concluído com sucesso."})
        except Exception as e:
            return JsonResponse({"erro": str(e)}, status=500)
    return JsonResponse({"erro": "Método não permitido"}, status=405)

@csrf_exempt
def api_reconhecimento_rosto(request):
    if request.method == 'POST':

        data = json.loads(request.body)
        imagem_base64 = data.get("imagem")

        if not imagem_base64:
            return JsonResponse({"status": "erro", "mensagem": "Imagem não enviada"}, status=400)

        imagem_base64 = imagem_base64.split(",")[1]
        imagem_bytes = base64.b64decode(imagem_base64)

        img = Image.open(BytesIO(imagem_bytes)).convert('RGB')
        frame = np.array(img)

        reconhecedor = ReconhecimentoCamera()
        usuario_id, nome = reconhecedor.reconhecer_numpy(frame)

        if usuario_id:
            return JsonResponse({"status": "ok", "id_usuario": usuario_id, "nome": nome})
        else:
            return JsonResponse({"status": "falha", "mensagem": "Usuário não reconhecido"})

    return JsonResponse({"status": "erro", "mensagem": "Método inválido"}, status=405)


@csrf_exempt
def api_registrar_ponto(request):
    print("Chamando a view registrar_ponto")
    if request.method != 'POST':
        return JsonResponse({'status': 'erro', 'mensagem': 'Método inválido'}, status=405)

    try:
        data = json.loads(request.body)
        id_usuario = data.get('id_usuario')
        if not id_usuario:
            return JsonResponse({'status': 'erro', 'mensagem': 'ID do usuário não informado'}, status=400)

        usuario = Usuario.objects.get(id=id_usuario)
        agora = localtime()

        # Verifica o último registro do dia
        ultimo_registro = RegistroPonto.objects.filter(
            usuario=usuario,
            data=agora.date()
        ).order_by('-hora').first()

        # Alterna entre entrada e saída
        if ultimo_registro and ultimo_registro.tipo == 'entrada':
            tipo = 'saida'
        else:
            tipo = 'entrada'

        RegistroPonto.objects.create(
            usuario=usuario,
            data=agora.date(),
            hora=agora.time(),
            tipo=tipo
        )

        return JsonResponse({
            'status': 'registrado',
            'nome': usuario.nome,
            'tipo': tipo,
            'hora': agora.strftime('%H:%M')
        })

    except Usuario.DoesNotExist:
        return JsonResponse({'status': 'erro', 'mensagem': 'Usuário não encontrado'}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({'status': 'erro', 'mensagem': 'JSON inválido'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'erro', 'mensagem': f'Erro interno: {str(e)}'}, status=500)
    
@csrf_exempt
def ver_resumo_reconhecimento(request):
    if request.method == "POST":
        dados = json.loads(request.body)
        imagem_base64 = dados['imagem'].split(',')[1]
        img_bytes = base64.b64decode(imagem_base64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        reconhecedor = ReconhecimentoCamera()
        usuario_id, nome = reconhecedor.reconhecer_numpy(frame)

        if usuario_id:
            registros = RegistroPonto.objects.filter(usuario_id=usuario_id).order_by('-data', '-hora')
            lista = [
                {
                    'data': r.data.strftime('%d/%m/%Y'),
                    'hora': r.hora.strftime('%H:%M:%S'),
                    'tipo': r.tipo
                } for r in registros
            ]

            return JsonResponse({
                'sucesso': True,
                'nome': nome,
                'registros': lista
            })
        else:
            return JsonResponse({'sucesso': False})

def ver_resumo(request):
    return render(request, 'ver_resumo.html')