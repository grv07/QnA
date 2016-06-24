from rest_framework import serializers
from .models import QuizStack

class QuizStackSerializer(serializers.ModelSerializer):
	class Meta:
		model = QuizStack
		exclude = ('created_date', 'updated_date',)



# from rest_framework import serializers
# from .models import QuizStack
# from quiz.serializer import SubCategorySerializer

# class QuizStackSerializer(serializers.ModelSerializer):
# 	subcategory = SubCategorySerializer(many=False, blank=True)
# 	class Meta:
# 		model = QuizStack
# 		exclude = ('created_date', 'updated_date',)