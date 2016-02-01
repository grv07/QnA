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
		serializer.save()
		status1 = 'None'
		return Response({'username':request.data.get('username'),'email':request.data.get('email')}, status = status.HTTP_200_OK)
	else:
		return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def login_user(request):

	user = User.objects.get(username = request.data.get('username'))
	if user:
		user.check_password(request.data.get('password'))
		token = generate_token(user)
		return Response({'username':request.data.get('username'),'email':request.data.get('email'),'token':token}, status = status.HTTP_200_OK)
	else:
		return Response({'msg':'Please validate inputs'}, status = status.HTTP_400_BAD_REQUEST)
 
# Create your views here.
