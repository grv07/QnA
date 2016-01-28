from rest_framework import serializers
from quiz.models import Quiz, Category

class QuizSerializer(serializers.ModelSerializer):
	class Meta:
		model = Quiz
		fields = '__all__'


class CategorySerializer(serializers.ModelSerializer):

	def validate_category(self, value):
		import re
		"""
		remove all spaces with '-'' when save to DB
		"""
		category_name = re.sub('\s+', '-', value).lower()
		try:
			category_obj =  Category.objects.get(category = category_name)
			if category_obj:
				raise serializers.ValidationError("category name must be unique")
		except Category.DoesNotExist as e:
			return category_name

	class Meta:
		model = Category
		fields = '__all__'        