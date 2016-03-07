from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.contrib.auth.models import User
from serializer import UserSerializer, TestUserSerializer
from token_key import generate_token

@api_view(['POST'])
@permission_classes((AllowAny,))
def register_user(request):
	serializer = UserSerializer(data = request.data)
	if serializer.is_valid():
		user = User.objects.create_user(**request.data)
		if user:
			return Response({'username':request.data.get('username'), 'email':request.data.get('email')}, status = status.HTTP_200_OK)
	else:
		return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def login_user(request):
	print request.data
	try:
		user_name = request.data.get('username')
		user_pass = request.data.get('password')
		user = User.objects.get(username = user_name)
		if user:
			isPasswordCorrect = user.check_password(user_pass)
			if isPasswordCorrect:
				token = generate_token(user)
				return Response({'username':user_name,'email': user.email,'token':token, 'userID':user.id}, status = status.HTTP_200_OK)
			else:
				return Response({'errors':'Incorrect credentials. Password is incorrect.'}, status = status.HTTP_400_BAD_REQUEST)
	except User.DoesNotExist as e:
		print e.args
		return Response({'errors':'Incorrect credentials. Username is incorrect.'}, status = status.HTTP_400_BAD_REQUEST)

 
@api_view(['POST'])
def logout_user(request, format=None):
	from django.contrib.auth import logout
	logout(request)
	return Response({'status': 'success'}, status=204)


@api_view(['POST'])
def test_user_data(request):
	serializer = TestUserSerializer(data = {'name':request.data.get('name'),'email':request.data.get('email'),'quiz':request.data.get('quiz')})
	if serializer.is_valid():
		old_obj, new_obj = serializer.get_or_create()
		if new_obj:
			return Response({'status': 'success', 'new':True,'user_name':request.data.get('name')}, status = status.HTTP_200_OK)
		else:
			return Response({'status': 'success', 'new':False, 'user_name':request.data.get('name')}, status = status.HTTP_200_OK)
	else:
		return Response({'msg': serializer.errors}, status = status.HTTP_400_BAD_REQUEST)
