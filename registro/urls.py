from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from registro import views
from .views import (
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
    path('', views.index, name='index'),
    path('criar_usuario/', views.criar_usuario, name='criar_usuario'),
    path('criar_coleta_faces/<int:usuario_id>', views.criar_coleta_faces, name='criar_coleta_faces'),
    path('face_detection/', views.face_detection, name='face_detection'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login, name='login'),
    path('dashboard/usuarios/', views.dashboard_usuarios, name='dashboard_usuarios'),
    path('dashboard/treinamentos/', views.dashboard_treinamentos, name='dashboard_treinamentos'),
    path('dashboard/registros/', views.dashboard_registros, name='dashboard_registros'),

    # Dashboard com todas as infs de cada usuario
    path('dashboard/usuarios/<int:id_usuario>/', views.dashboard_usuario_detalhes, name='dashboard_usuario_detalhes'),
    path('dashboard/remover_fotos_selecionadas/', views.remover_fotos_coleta_selecionadas, name='remover_fotos_coleta_selecionadas'),
    path('dashboard/usuarios/<int:id>/salvar/', views.salvar_usuario, name='salvar_usuario'),
    path('dashboard/remover_fotos_coleta/<int:id_usuario>/', views.remover_fotos_coleta_selecionadas, name='remover_fotos_coleta_selecionadas'),

    # Treinamento Usuarios
    path('dashboard/treinamento_ativos/', views.treinar_usuarios_ativos, name='treinar_usuarios_ativos'),

    # Reconhecimento de rosto (views manuais – mantenha essas antes do router)
    path('api/reconhecimento_rosto/', views.api_reconhecimento_rosto, name='api_reconhecimento_rosto'),
    path('api/registrar_ponto/', views.api_registrar_ponto, name='api_registrar_ponto'),

    # Reconhecimento em tempo real
    path('reconhecimento/', views.reconhecimento_view, name='reconhecimento'),
    path('video_reconhecimento/', views.video_reconhecimento, name='video_reconhecimento'),
    
    # Resumo Usuario
    path('resumo/', views.ver_resumo, name='ver_resumo'),
    path('resumo/reconhecimento/', views.ver_resumo_reconhecimento, name='ver_resumo_reconhecimento'),
    
    # Rota do DRF por último para evitar conflito
    path('api/', include(router.urls)),
]

# Para servir arquivos de mídia no modo de desenvolvimento
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
