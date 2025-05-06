from django.shortcuts import render, redirect#, get_object_or_404
from .forms import UsuarioForm, ColetaFacesForm
from .models import Usuario, ColetaFaces
from django.http import StreamingHttpResponse
from registro.camera import VideoCamera

camera_detection = VideoCamera() # Chama classe VideoCamera

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
    
    context = {
        'usuario': usuario, # Passa o objeto usuario p/ o template
        'face_detection': face_detection, # Passa a camera p/ template
    }

    return render(request, 'criar_coleta_faces.html', context)