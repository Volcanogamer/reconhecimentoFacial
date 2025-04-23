from django.urls import path
from .views import criar_usuario, criar_coleta_faces

urlpatterns = [    
    path('', criar_usuario, name='criar_usuario'),
    path('criar_coleta_faces/<int:usuario_id>', criar_coleta_faces, name='criar_coleta_faces'),
]