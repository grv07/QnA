from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.decorators import authentication_classes
from django.contrib.auth.models import User
from serializer import MerchantSerializer, TestUserSerializer, UserSerializer
from token_key import generate_token
from django.core.cache import cache
from QnA.services.utility import checkIfTrue, REGISTRATION_HTML
from QnA.services.test_authentication import TestAuthentication
from QnA.services.mail_handling import send_mail

@api_view(['POST'])
@permission_classes((AllowAny,))
def register_user(request):
	data = request.data
	serializer = UserSerializer(data = data)
	if serializer.is_valid():
		user = User.objects.create_user(**request.data)
		if user:
			data['user'] = user.id 
		serializer = MerchantSerializer(data = data)
		if serializer.is_valid():
			m_user = serializer.save()
			if m_user:
				html = REGISTRATION_HTML.format(name = data.get('first_name'), username = data.get('username'))
				send_mail(html, data.get('email'))
				return Response({'username':data.get('username'), 'email':data.get('email')}, status = status.HTTP_200_OK)
		else:
			user.delete()
			print serializer.errors
			return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
	else:
		print serializer.errors,'---'
		return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def login_user(request):
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
# @permission_classes((AllowAny,))
@authentication_classes([TestAuthentication])
def test_user_data(request):
	data = {}
	# token = generate_token(user)
	return Response(data, status = status.HTTP_200_OK)
	# serializer = TestUserSerializer(data = {'name':request.data.get('name'),'email':request.data.get('email'),'quiz':request.data.get('quiz'), 'test_key': request.data.get('test_key')})
	# if serializer.is_valid():
	# 	data['status'] = 'success'
	# 	data['name'] = request.data.get('name')
	# 	data['test_key'] = request.data.get('test_key')
	# 	is_new_user = True
	# 	old_obj, new_obj = serializer.get_or_create()
	# 	if old_obj:
	# 		is_new_user = False
	# 		data['attempt_no'] = old_obj.attempt_no
	# 		data['test_user'] = old_obj.user_key
	# 	else:
	# 		data['attempt_no'] = new_obj.attempt_no
	# 		data['test_user'] = new_obj.user_key
	# 	data['is_new_user'] = is_new_user
	# 	return Response(data, status = status.HTTP_200_OK)
	# else:
	# 	return Response({'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@authentication_classes([TestAuthentication])
def save_test_data(request):
	cache_key = request.query_params.get('test_key')+request.query_params.get('quiz_id')+request.query_params.get('section_name')
	question_id = request.data['answer'].keys()[0]
	if checkIfTrue(request.query_params.get('is_save_to_db')):
		print 'db saved = '+ cache_key
		print cache.get(cache_key), '------------------'
		cache.delete(cache_key)
		print cache.get(cache_key),'=============='
	else:
		print 'cache saved = '+cache_key
		cache_value = cache.get(cache_key)
		if not cache_value:
			cache.set(cache_key, request.data['answer'])
		else:
			if request.data['answer'] in cache_value:
				cache_value[question_id] = request.data['answer'][question_id]
				cache.set(cache_key, cache_value)
		print cache.get(cache_key),'************'
	return Response({}, status = status.HTTP_200_OK)


# @api_view(['POST'])
# def save_test_data_to_db(request):
# 	print request.data
# 	return Response({}, status = status.HTTP_200_OK)
