from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.decorators import authentication_classes
from django.contrib.auth.models import User
from serializer import MerchantSerializer, TestUserSerializer, UserSerializer
from token_key import generate_token
from django.core.cache import cache
from QnA.services.utility import checkIfTrue, REGISTRATION_HTML, CACHE_TIMEOUT
from QnA.services.test_authentication import TestAuthentication
from QnA.services.mail_handling import send_mail
from QnA.services.generate_result_engine import generate_result, filter_by_category
from quiz.models import Sitting, Quiz, Question
from quiz.serializer import SittingSerializer
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

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_user_result(request, user_id = 29, quiz_id = 1):
	from django.template import Template, Context
	from django.http import HttpResponse

	quiz  = Quiz.objects.get(pk = quiz_id)

	sitting = Sitting.objects.filter(user_id = user_id, quiz_id = quiz_id)

	_filter_by_category = filter_by_category(sitting)
	
	in_correct_pt  = float((len(set(sitting.incorrect_questions_list.split(',')))*100)/quiz.total_questions)
	correct_que_pt = int(_filter_by_category[1]*100)/quiz.total_questions
	
	fp = open('QnA/services/result.html')
	t = Template(fp.read())
	fp.close()

	html = t.render(Context({'data': {'score':sitting.current_score, 'attempt_no':sitting.attempt_no,'pass_percentage':quiz.passing_percent, 
			'pass_percentage':quiz.passing_percent,'total_que':quiz.total_questions, 'filter_by_category':_filter_by_category[0],
			'quiz_marks': quiz.total_marks,'correct_que_pt':correct_que_pt,'in_orrect_pt':in_correct_pt, 
	 		'quiz_name':quiz.title, 'username':sitting.user.username}}))
	
	return HttpResponse(html)

@api_view(['POST'])
@permission_classes((AllowAny,))
# @authentication_classes([TestAuthentication])
def test_user_data(request):
	'''Save data of test user if new >> then create new obj. , If found in DB then reuse it'''
	data = {}
	print request.data
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
				
				if test_user.no_attempt < Quiz.objects.get(quiz_key = test_key).no_of_attempt: 
					test_user.no_attempt += 1

				else:
					return Response({'attempt_over': 'There is no remaining attempts'}, status=status.HTTP_400_BAD_REQUEST)						
				
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
def save_test_data_to_cache(request):
	# print request.data
	test_user = request.data.get('test_user')
	test_key = request.data.get('test_key')
	section_name = request.data.get('section_name')
	answer = request.data.get('answer')
	quiz_id = request.data.get('quiz_id')
	cache_key = test_key+"|"+str(test_user)+"|"+section_name.replace('Section#','')
	question_id = answer.keys()[0]

	# sitting_id = cache.get('sitting_id'+str(test_user))
	
	cache_value = cache.get(cache_key)
	# print cache_value
	if not cache_value:
		cache.set(cache_key,{ 'answers': request.data['answer'] }, timeout = CACHE_TIMEOUT)
	else:
		if question_id in cache_value['answers'].keys():
			cache_value['answers'][question_id] = request.data['answer'][question_id]
		else:
			cache_value['answers'].update(request.data['answer'])
		cache.set(cache_key, cache_value, timeout = CACHE_TIMEOUT)
	print cache.get(cache_key)
	return Response({}, status = status.HTTP_200_OK)


@api_view(['POST'])
def save_test_data_to_db(request):
	test_user = request.data.get('test_user')
	quiz_id = request.data.get('quiz_id')

	_test_user_obj = TestUser.objects.get(pk = test_user)
	sitting_obj = Sitting.objects.create(user = _test_user_obj.user,  
		quiz = Quiz.objects.get(pk = quiz_id), attempt_no = _test_user_obj.no_attempt)
	
	cache.set('sitting_id'+str(test_user), sitting_obj.id, timeout = CACHE_TIMEOUT)
	
	test_key = request.data.get('test_key')
	section_name = request.data.get('section_name')
	answer = request.data.get('answer')
	
	# question_id = answer.keys()[0]
	sitting_id = cache.get('sitting_id'+str(test_user))
	print sitting_id
	cache_keys_pattern = test_key+"|"+str(test_user)+"|**"
	
	for key in list(cache.iter_keys(cache_keys_pattern)):
		# print key
		# print cache.get(key), '================'
		na_nv_dict =  request.data['progressValues']['Section#'+key.split('|')[-1]]	
		if generate_result(cache.get(key), sitting_obj.id,key, na_nv_dict):
			cache.delete(key)
			cache.delete('sitting_id'+str(test_user))
	return Response({}, status = status.HTTP_200_OK)
