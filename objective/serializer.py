from rest_framework import serializers
from objective.models import ObjectiveQuestion

class ObjectiveQuestionSerializer(serializers.ModelSerializer):
	'''
	ObjectiveQuestion extands Question Module
	'''
	
	class Meta:
		model = ObjectiveQuestion
		fields = '__all__'	