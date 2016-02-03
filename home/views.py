from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.contrib.auth.models import User
from serializer import UserSerializer
from token_key import generate_token

@api_view(['POST'])
@permission_classes((AllowAny,))
def register_user(request):
	serializer = UserSerializer(data = request.data)
	if serializer.is_valid():
		user = User.objects.create_user(**request.data)
		if user:
			return Response({'username':request.data.get('username'),'email':request.data.get('email')}, status = status.HTTP_200_OK)
		# login_user(request)
	else:
		return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def login_user(request):
	try:
		user = User.objects.get(username = request.data.get('username'))
		if user:
			isPasswordCorrect = user.check_password(request.data.get('password'))
			if isPasswordCorrect:
				token = generate_token(user)
				return Response({'username':request.data.get('username'),'email': user.email,'token':token, 'userID':user.id}, status = status.HTTP_200_OK)
			else:
				return Response({'errors':'Incorrect credentials. Password is incorrect.'}, status = status.HTTP_400_BAD_REQUEST)
	except User.DoesNotExist as e:
		return Response({'errors':'Incorrect credentials. Username is incorrect.'}, status = status.HTTP_400_BAD_REQUEST)

 

@api_view(['POST'])
def logout_user(request, format=None):
	from django.http import JsonResponse
	from django.contrib.auth import logout
	logout(request)
	return JsonResponse({'status': 'success'}, status=204)