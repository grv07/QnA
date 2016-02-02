from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = '__all__'

	def validate_email(self, value):
		if User.objects.filter(email = value):
			raise serializers.ValidationError("A user with that email already exists.")
		return value

	