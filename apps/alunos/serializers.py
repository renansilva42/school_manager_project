from rest_framework import serializers
from .models import Aluno

class AlunoFotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aluno
        fields = ['foto']
        
    def validate_foto(self, value):
        # Validar tamanho máximo (5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('A foto deve ter menos que 5MB')
            
        # Validar extensões permitidas
        ext = value.name.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png']:
            raise serializers.ValidationError('Formato de arquivo não suportado')
            
        return value