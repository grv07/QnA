from rest_framework import serializers
from mcq.models import MCQuestion, Answer

class MCQuestionSerializer(serializers.ModelSerializer):
	'''
	MCQ extands Question Module
	'''
	
	class Meta:
		model = MCQuestion
		fields = '__all__'

class AnswerSerializer(serializers.ModelSerializer):

	class Meta:
		model = Answer
		fields = '__all__'		