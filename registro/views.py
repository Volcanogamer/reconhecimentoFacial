from django.shortcuts import render, redirect
from .forms import UsuarioForm, ColetaFacesForm
from .models import Usuario, ColetaFaces

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
    usuario = Usuario.objects.get(id=usuario_id)

    if request.method == 'POST':
        form = ColetaFacesForm(request.POST, request.FILES)
        if form.is_valid():
            #Itera sobre os arq enviados e cria uma entrada p/ cada iamgem
            for image in request.FILES.getlist('images'):
                ColetaFaces.objects.create(usuario=usuario, image=image)
    else:
        form = ColetaFacesForm()

    context = {
        'usuario': usuario,
        'form': form
    }

    return render(request, 'criar_coleta_faces.html', context)