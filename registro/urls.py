from django.urls import path, include
from rest_framework.routers import DefaultRouter
from registro import views
from .views import (
    criar_usuario,
    criar_coleta_faces,
    face_detection,
    UsuarioViewSet,
    ColetaFacesViewSet,
    TreinamentoViewSet,
    RegistroPontoViewSet,
    
)

# Rotas automáticas para a API REST
router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'coletas', ColetaFacesViewSet)
router.register(r'treinamento', TreinamentoViewSet)
router.register(r'registros', RegistroPontoViewSet)

urlpatterns = [
    # Rotas Web
    path('', criar_usuario, name='criar_usuario'),
    path('criar_coleta_faces/<int:usuario_id>', criar_coleta_faces, name='criar_coleta_faces'),
    path('face_detection/', face_detection, name='face_detection'),

    # Rotas da API sob o prefixo /api/
    path('api/', include(router.urls)),

    # Reconhecimento em tempo real
    path('reconhecimento/', views.reconhecimento_view, name='reconhecimento'),
    path('video_reconhecimento/', views.video_reconhecimento, name='video_reconhecimento'),
]
