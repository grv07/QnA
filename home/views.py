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
from QnA.services.generate_result_engine import generate_result
from quiz.models import Sitting, Quiz
from home.models import TestUser

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
@permission_classes((AllowAny,))
# @authentication_classes([TestAuthentication])
def test_user_data(request):
	data = {}
	name = request.data.get('username')
	email = request.data.get('email')
	test_key = request.data.get('test_key')
	
	try:
		user  = User.objects.get(username = name)
		create = False
	except User.DoesNotExist as e:
		user  = User.objects.create_user(username = name, email = email, password = name[::-1]+email[::-1])
		create = True

	serializer = TestUserSerializer(data = {'user': user.id, 'test_key' : test_key})
	if serializer.is_valid():
		data['status'] = 'success'
		data['username'] = name
		data['test_key'] = test_key		
		is_new = True
		if create:
			test_user = serializer.save()
		else:
			try:
				test_user = TestUser.objects.get(user = user, test_key = test_key)
				test_user.no_attempt += 1
				is_new = False
				test_user.save()
			except 	TestUser.DoesNotExist as e:
				test_user = serializer.save()

		token = generate_token(user)
		data['token'] = token
		data['is_new'] = is_new
		data['testUser'] = test_user.id
		return Response(data, status = status.HTTP_200_OK)
	else:
		print serializer.errors
		return Response({'msg': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
# @authentication_classes([TestAuthentication])
def save_test_data(request):
	cache_key = request.data.get('test_key')+"|"+str(request.data.get('test_user'))+"|"+request.data.get('section_name').replace('Section#','')
	question_id = request.data.get('answer').keys()[0]
	sitting_id = cache.get('sitting_id'+str(request.data.get('test_user')))
	if not sitting_id:
		sitting_obj = Sitting.objects.create(user = TestUser.objects.get(id = request.data.get('test_user')).user, quiz = Quiz.objects.get(id = request.data.get('quiz_id')))
		cache.set('sitting_id'+str(request.data.get('test_user')), sitting_obj.id, timeout = None)
	if request.data.get('is_save_to_db'):
		print 'db saved = '+ cache_key, sitting_id
		cache_keys_pattern = request.data.get('test_key')+"|"+str(request.data.get('test_user'))+"|**"
		print list(cache.iter_keys(cache_keys_pattern))
		for key in list(cache.iter_keys(cache_keys_pattern)):			
			# generate_result(cache.get(key), sitting_id, key)
			print cache.get(key), '------------------'
			cache.delete(key)
			print cache.get(key),'=============='
		cache.delete('sitting_id'+str(request.data.get('test_user')))
		print cache.get('sitting_id'+str(request.data.get('test_user'))),'************'
	else:
		print 'cached saved = '+ cache_key
		cache_value = cache.get(cache_key)
		if not cache_value:
			cache.set(cache_key,{ 'answers': request.data['answer'] }, timeout = None)
		else:
			if question_id in cache_value['answers'].keys():
				cache_value['answers'][question_id] = request.data['answer'][question_id]
			else:
				cache_value['answers'].update(request.data['answer'])
			cache.set(cache_key, cache_value, timeout = None)
		# print cache.get(cache_key),'************'
		print cache_key
	# cache.delete('sitting_id')
	# cache.delete(cache_key)
	return Response({}, status = status.HTTP_200_OK)


# @api_view(['POST'])
# def save_test_data_to_db(request):
# 	print request.data
# 	return Response({}, status = status.HTTP_200_OK)
