from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from random import randint
import re

def validar_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        raise ValidationError("CPF inválido.")
    for i in range(9, 11):
        soma = sum(int(cpf[num]) * ((i+1) - num) for num in range(i))
        digito = ((soma * 10) % 11) % 10
        if digito != int(cpf[i]):
            raise ValidationError("CPF inválido.")

class Usuario(models.Model):
    id_usuario = models.SlugField(max_length=200, unique=True)
    foto_facial = models.ImageField(upload_to='foto/')
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=18, unique=True, validators=[validar_cpf])
    data_cadastro = models.DateField(auto_now_add=True)
    situacao = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.id_usuario:
            while True:
                seq = str(randint(1000000, 9999999))
                slug = slugify(seq)
                if not Usuario.objects.filter(id_usuario=slug).exists():
                    self.id_usuario = slug
                    break
        super().save(*args, **kwargs)

class ColetaFaces(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='usuario_coletas')
    image = models.ImageField(upload_to='roi/')

class Treinamento(models.Model):
    modelo = models.FileField(upload_to='treinamento/')

    class Meta:
        verbose_name = 'Treinamento'
        verbose_name_plural = 'Treinamentos'

    def __str__(self):
        return 'Classificador (frontalface)'

    def clean(self):
        model = self.__class__
        if model.objects.exclude(id=self.id).exists():
            raise ValidationError('Só pode existir um único arquivo salvo.')
