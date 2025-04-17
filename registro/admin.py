from django.contrib import admin
from .models import Usuario, Treinamento, ColetaFaces

class ColetaFacesInLine(admin.StackedInline):
    model = ColetaFaces
    extra = 0

class usuarioAdmin(admin.ModelAdmin):
    readonly_fields = []
    inlines = (ColetaFacesInLine,)

admin.site.register(Usuario,usuarioAdmin)
admin.site.register(Treinamento)