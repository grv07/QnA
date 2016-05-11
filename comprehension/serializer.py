from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Comprehension, ComprehensionQuestion, ComprehensionAnswer

class ComprehensionSerializer(serializers.ModelSerializer):
	class Meta:
		model = Comprehension

class ComprehensionQuestionSerializer(serializers.ModelSerializer):
	class Meta:
		model = ComprehensionQuestion
		exclude = ('created_date', 'updated_date',)
	
class ComprehensionAnswerSerializer(serializers.ModelSerializer):
	class Meta:
		model = ComprehensionAnswer
