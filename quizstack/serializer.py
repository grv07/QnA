from rest_framework import serializers
from .models import QuizStack

class QuizStackSerializer(serializers.ModelSerializer):
	class Meta:
		model = QuizStack
		fields = '__all__'
