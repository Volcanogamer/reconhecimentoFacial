from django.contrib import admin
from .models import Usuario, Treinamento, ColetaFaces

class ColetaFacesInLine(admin.StackedInline):
    model = ColetaFaces
    extra = 0

class UsuarioAdmin(admin.ModelAdmin):
    readonly_fields = ['id_usuario', 'data_cadastro']
    inlines = (ColetaFacesInLine,)
    list_display = ('nome', 'cpf', 'situacao', 'data_cadastro')
    search_fields = ('nome', 'cpf')

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Treinamento)
