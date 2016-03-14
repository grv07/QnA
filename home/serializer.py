from rest_framework import serializers
from django.contrib.auth.models import User

from home.models import TestUser,MerchantUser

class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = '__all__'


class MerchantSerializer(serializers.ModelSerializer):
	class Meta:
		model = MerchantUser
		fields = '__all__'

	def validate_email(self, value):
		if User.objects.filter(email = value):
			raise serializers.ValidationError("A user with that email already exists.")
		return value
	def validate_username(self, value):
		if User.objects.filter(username = value):
			raise serializers.ValidationError("A user with that username already exists.")
		return value

class TestUserSerializer(serializers.ModelSerializer):
	class Meta:
		model = TestUser
		fields = '__all__'

	def get_or_create(self):
		defaults = self.validated_data.copy()
		name = defaults.pop('name')
		email = defaults.pop('email')
		quiz = defaults.pop('quiz')
		return TestUser.objects.get_or_create(name = name, email=email, quiz=quiz, defaults=defaults)	
	