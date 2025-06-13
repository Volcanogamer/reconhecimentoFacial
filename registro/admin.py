from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Usuario, Treinamento, ColetaFaces

class ColetaFacesInLine(admin.StackedInline):
    model = ColetaFaces
    extra = 0
    readonly_fields = ['image_preview']
    fields = ['image', 'image_preview']

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100">')
        return "-"
    image_preview.short_description = "Prévia da Imagem"

class UsuarioAdmin(admin.ModelAdmin):
    readonly_fields = ['id_usuario', 'data_cadastro']
    inlines = (ColetaFacesInLine,)
    list_display = ('nome', 'cpf', 'situacao', 'data_cadastro')
    search_fields = ('nome', 'cpf')

    class Media:
        js = ('registro/selecionar_todas_coletas.js',)  # Caminho relativo à pasta static

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Treinamento)
