from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from registro import views
from .views import (
    dashboard_registros,
    dashboard_usuarios,
    dashboard_treinamentos,
    index,
    dashboard,
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
    path('', index, name='index'),
    path('criar_usuario/', criar_usuario, name='criar_usuario'),
    path('criar_coleta_faces/<int:usuario_id>', criar_coleta_faces, name='criar_coleta_faces'),
    path('face_detection/', face_detection, name='face_detection'),
    
    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),
    path('login/', views.login, name='login'),
    path('dashboard/usuarios/', dashboard_usuarios, name='dashboard_usuarios'),
    path('dashboard/treinamentos/', dashboard_treinamentos, name='dashboard_treinamentos'),
    path('dashboard/registros/', dashboard_registros, name='dashboard_registros'),
    
    # Dashboard com todas as infs de cada usuario
    path('dashboard/usuarios/<int:id_usuario>/', views.dashboard_usuario_detalhes, name='dashboard_usuario_detalhes'),
    path('dashboard/remover_fotos_selecionadas/', views.remover_fotos_coleta_selecionadas, name='remover_fotos_coleta_selecionadas'),
     
    path('dashboard/usuarios/<int:id>/salvar/', views.salvar_usuario, name='salvar_usuario'),
    path('dashboard/remover_fotos_coleta/<int:id_usuario>/', views.remover_fotos_coleta_selecionadas, name='remover_fotos_coleta_selecionadas'),

    # Rotas da API sob o prefixo /api/
    path('api/', include(router.urls)),

    # Reconhecimento em tempo real
    path('reconhecimento/', views.reconhecimento_view, name='reconhecimento'),
    path('video_reconhecimento/', views.video_reconhecimento, name='video_reconhecimento'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
