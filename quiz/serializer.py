from rest_framework import serializers
from quiz.models import Quiz, Category, SubCategory, Question

class QuizSerializer(serializers.ModelSerializer):
	class Meta:
		model = Quiz
		exclude = ('quiz_key',)


class CategorySerializer(serializers.ModelSerializer):


	def validate_category(self, value):
		import re
		category_name = re.sub('\s+', '-', value).lower()
		try:
			category_obj =  Category.objects.get(category = category_name)
			if category_obj:
				raise serializers.ValidationError("Category name must be unique")
		except Category.DoesNotExist as e:
			return category_name

	class Meta:
		model = Category
		fields = '__all__'

class SubCategorySerializer(serializers.ModelSerializer):
	class Meta:
		model = SubCategory
		fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
	class Meta:
		model = Question
		fields = '__all__'
