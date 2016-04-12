from rest_framework.response import Response
from django.http import HttpResponse
from django.template import Template, Context
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.decorators import authentication_classes
from django.contrib.auth.models import User
from serializer import MerchantSerializer, TestUserSerializer, UserSerializer
from token_key import generate_token
from django.core.cache import cache
from QnA.services.utility import checkIfTrue, REGISTRATION_HTML, CACHE_TIMEOUT, postNotifications
from QnA.services.test_authentication import TestAuthentication
from QnA.services.mail_handling import send_mail
from QnA.services.generate_result_engine import generate_result, filter_by_category
from quiz.models import Sitting, Quiz, Question
from quiz.serializer import SittingSerializer
from home.models import TestUser
from django.utils import timezone
from QnA.settings import TEST_URL_THIRD_PARTY
from quizstack.models import QuizStack



# Generate pdf from html
def generate_PDF(request, html):
	import xhtml2pdf.pisa as pisa
	file = open('test.pdf', "w+b")
	pisaStatus = pisa.CreatePDF(html.encode('utf-8'), dest=file,encoding='utf-8')
	file.seek(0)
	pdf = file.read()
	file.close()
	return HttpResponse(pdf, 'application/pdf')

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

def get_user_result_helper(sitting, test_user_id, quiz_key, order = None, filter_by_category = None, get_order_by = None):	
	get_order = order
	quiz = sitting.quiz
	user = sitting.user
	if not get_order == 'acending':
		_get_order_by = 'current_score'
	
	in_correct_pt  = float((len(set(sitting.incorrect_questions_list.strip().split(',')))*100)/quiz.total_questions) if len(sitting.incorrect_questions_list) > 0 else 0 

	correct_que_pt = int(filter_by_category[1]*100)/quiz.total_questions
	
	_result_status = 'Pass' if int(int(sitting.current_score)*100/int(quiz.total_marks)) > quiz.passing_percent else 'Fail'

	return {
			'quiz_id': quiz.id,
			'quiz_name':quiz.title,
			'passing_percentage': quiz.passing_percent,
			'total_questions':quiz.total_questions,
			'total_marks': quiz.total_marks,
			'marks_scored': sitting.current_score,
			'result_status':_result_status,
			'EVENT_TYPE': 'gradeTest', 
			'test_key': quiz.quiz_key, 
			'sitting_id': sitting.id, 
			'test_user_id': test_user_id, 
			'timestamp_IST': str(timezone.now()), 
			'username': sitting.user.username, 
			'attempt_no': sitting.attempt_no,
			'email': sitting.user.email,
			'correct_questions_score': correct_que_pt, 
			'incorrect_questions_score': in_correct_pt,
			'finish_mode': 'NormalSubmission',
			'start_time_IST': str(sitting.start_date),
			'end_time_IST': str(sitting.end_date)
		}



@api_view(['GET'])
@permission_classes((AllowAny,))
def get_user_result(request, test_user_id, quiz_key, attempt_no):
	test_user = TestUser.objects.get(id = test_user_id)
	get_order_by = '-current_score'
	sitting = Sitting.objects.order_by(get_order_by).get(user = test_user.user, quiz = Quiz.objects.get(quiz_key = quiz_key), attempt_no = attempt_no)
	_filter_by_category = filter_by_category(sitting)
	data = get_user_result_helper(sitting, test_user_id, quiz_key, request.GET.get('order', None), _filter_by_category, get_order_by)

	data['filter_by_category'] = _filter_by_category[0]
	data['view_format'] = request.GET.get('view_format',None)
	fp = open('QnA/services/result.html')
	t = Template(fp.read())
	fp.close()
	html = t.render(Context({'data': data }))
	if data['view_format'] == 'pdf':
		return generate_PDF(request, html)
	else:
		return HttpResponse(html)


@api_view(['POST'])
def save_sitting_user(request):
	try:
		test_user_id = request.data.get('test_user')
		sitting_id = cache.get('sitting_id'+str(test_user_id), None)
		if not sitting_id:
			quiz = Quiz.objects.get(pk = request.data.get('quiz_id'))
			test_user_obj = TestUser.objects.get(pk = test_user_id)
			sitting_obj = Sitting.objects.create(user = test_user_obj.user,  quiz = quiz)
			
			test_user_obj.no_attempt += 1
			test_user_obj.save()

			sitting_obj.attempt_no = test_user_obj.no_attempt 
			sitting_obj.save()

			if not sitting_obj.unanswerd_question_list:
				for quizstack in QuizStack.objects.filter(quiz = quiz):
					for question_id in quizstack.fetch_selected_questions():
						sitting_obj.add_unanswerd_question(question_id)
			cache.set('sitting_id'+str(test_user_id), sitting_obj.id, timeout = CACHE_TIMEOUT)
			
			data = { 'EVENT_TYPE': 'startTest', 'test_key': quiz.quiz_key, 'sitting_id': sitting_obj.id,
					 'test_user_id': test_user_id, 'timestamp_IST': str(timezone.now()), 'username': sitting_obj.user.username,
					  'email': sitting_obj.user.email }
			
			if not postNotifications(data, sitting_obj.quiz.start_notification_url):
				print 'start notification not sent'
			return Response({}, status = status.HTTP_200_OK)
		return Response({}, status = status.HTTP_200_OK)
	except Exception as e:
		print e.args
		return Response({}, status = status.HTTP_400_BAD_REQUEST)

# Helper function for get users cache data if exist in cache.
def test_data_helper(test_key, test_user_id):
	test_data = { 'isTestNotCompleted': False, 'sectionNoWhereLeft': None, 'sectionsRemaining': [], 'existingAnswers': { 'answers': {} } }
	if cache.get('sitting_id'+str(test_user_id), None):	
		test_data['status'] = 'INCOMPLETE'
		test_data['isTestNotCompleted'] = True
		test_data['timeRemaining'] = cache.get(test_key + "|" + str(test_user_id) + "time")['remaining_duration']
		preExistingKeys = sorted(list(cache.iter_keys(test_key+"|"+str(test_user_id)+"|**")), key=lambda k: cache.get(k)['time'])
		if preExistingKeys:
			print preExistingKeys,'-------------'
			test_data['sectionNoWhereLeft'] = preExistingKeys[len(preExistingKeys)-1].split('|')[2]
			remaining_sections = []
			total_sections_list = range(1, Quiz.objects.get(quiz_key = test_key).total_sections + 1)

			for section_no in total_sections_list:
				if test_key+"|"+str(test_user_id)+"|"+str(section_no) not in preExistingKeys:
					remaining_sections += [section_no]
			
			remaining_sections += [ int(test_data['sectionNoWhereLeft']) ]
			test_data['sectionNoWhereLeft'] = preExistingKeys[len(preExistingKeys)-1].split('|')[2]
			test_data['sectionsRemaining'] = sorted(remaining_sections)
			test_data['existingAnswers'] = { 'answers' : { 'Section#'+test_data['sectionNoWhereLeft']: cache.get(preExistingKeys[len(preExistingKeys)-1])['answers'] } }
	else:
		test_data['status'] = 'ToBeTaken'
	return test_data

@api_view(['POST', 'GET'])
@permission_classes((AllowAny,))
# @authentication_classes([TestAuthentication])
def test_user_data(request):
	data = { 'test': {} }
	if request.method == 'GET':
		test_user_id = request.query_params.get('test_user_id', None)
		token = request.query_params.get('token', None)
		if test_user_id and token:
			test_user = TestUser.objects.get(id = test_user_id)
			data['status'] = 'SUCCESS'
			data['username'] = test_user.user.username
			data['test_key'] = test_user.test_key

			data['token'] = token
			data['testUser'] = test_user.id
			data['test'].update(test_data_helper(test_user.test_key, test_user_id))
			return Response(data, status = status.HTTP_200_OK)
		else:
			return Response({'errors': 'Unable to get test details.'}, status=status.HTTP_400_BAD_REQUEST)

	elif request.method == 'POST':
		'''Save data of test user if new >> then create new obj. , If found in DB then reuse it'''
		name = request.data.get('username')
		email = request.data.get('email')
		test_key = request.data.get('test_key')
		try:
			quiz = Quiz.objects.get(quiz_key = test_key)
			user  = User.objects.get(username = name, email = email)
			create = False
		except User.DoesNotExist as e:
			try:
				user  = User.objects.create_user(username = name, email = email, password = name[::-1]+email[::-1])
				create = True
			except Exception as e:
				return Response({'status':'FAIL', 'errors': 'Unable to create user.'}, status=status.HTTP_400_BAD_REQUEST)	
		except Quiz.DoesNotExist as e:
			return Response({'status':'FAIL', 'errors': 'Unable to find this test.'}, status=status.HTTP_400_BAD_REQUEST)
			
		serializer = TestUserSerializer(data = {'user': user.id, 'test_key' : test_key})
		if serializer.is_valid():
			data['status'] = 'SUCCESS'
			data['username'] = name
			data['test_key'] = test_key
			is_new = True
		
			if create:
				test_user = serializer.save()
			else:
				try:
					test_user = TestUser.objects.get(user = user, test_key = test_key)
					is_new = False
					test_user.save()
				except 	TestUser.DoesNotExist as e:
					test_user = serializer.save()
			if not test_user.no_attempt < quiz.no_of_attempt: 
				return Response({'status':'SUCCESS', 'test':{'status':'NOT_REMAINING'}, 'errors': 'There are no remaining attempts left for this test.'},
				 status = status.HTTP_400_BAD_REQUEST)				
			else:
				data['test'].update({'remaining_attempts':quiz.no_of_attempt - test_user.no_attempt })
			token = generate_token(user)
			data['token'] = token
			data['is_new'] = is_new
			data['testUser'] = test_user.id
			data['test'].update(test_data_helper(test_key, test_user.id))				
			data['test'].update({'testURL':TEST_URL_THIRD_PARTY.format(quiz_key = test_key, test_user_id = test_user.id, token = token)})
			return Response(data, status = status.HTTP_200_OK)
		else:
			print serializer.errors
			return Response({'status':'FAIL', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def save_time_remaining_to_cache(request):
	try:
		test_user = request.data.get('test_user')
		test_key = request.data.get('test_key')
		sitting_id = cache.get('sitting_id'+str(test_user), None)
		if sitting_id:
			cache_key = test_key + "|" + str(test_user) + "time"
			cache_value = cache.get(cache_key)
			if not cache_value:
				cache.set(cache_key, { 'remaining_duration': request.data.get('remaining_duration') }, timeout = CACHE_TIMEOUT)
			else:
				cache_value['remaining_duration'] = request.data.get('remaining_duration')
				cache.set(cache_key, cache_value, timeout = CACHE_TIMEOUT)
			return Response({}, status = status.HTTP_200_OK)
	except Exception as e:
		print e.args
		return Response({}, status = status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
# @authentication_classes([TestAuthentication])
def save_test_data_to_cache(request):
	test_user = request.data.get('test_user')
	sitting_id = cache.get('sitting_id'+str(test_user))
	if sitting_id:
		answer = request.data.get('answer')
		question_id = answer.keys()[0]
		test_key = request.data.get('test_key')
		section_name = request.data.get('section_name')
		cache_key = test_key+"|"+str(test_user)+"|"+section_name.replace('Section#','')
		cache_value = cache.get(cache_key)
		if not cache_value:			
			cache.set(cache_key,{ 'answers': answer , 'time': timezone.now() }, timeout = CACHE_TIMEOUT)
		else:
			if question_id in cache_value['answers'].keys():
				cache_value['answers'][question_id] = answer[question_id]
			else:
				cache_value['answers'].update(answer)
			cache.set(cache_key, cache_value, timeout = CACHE_TIMEOUT)
		print cache.get(cache_key),'**************'
		return Response({}, status = status.HTTP_200_OK)
	else:
		return Response({}, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def save_test_data_to_db(request):
	test_user = request.data.get('test_user')
	sitting_id = cache.get('sitting_id'+str(test_user))
	if sitting_id:
		test_key = request.data.get('test_key')		
		# _test_user_obj = TestUser.objects.get(pk = test_user)
		sitting_obj = Sitting.objects.get(id = cache.get('sitting_id'+str(test_user)))
		un_ans_que_list = sitting_obj.unanswerd_question_list

		unanswered_questions_list = map(int, un_ans_que_list.strip().split(',')) if len(un_ans_que_list) > 0 else []
		cache_keys_pattern = test_key+"|"+str(test_user)+"|**"
		quizstack =  QuizStack.objects.filter(quiz = Quiz.objects.get(quiz_key = test_key))
		for key in list(cache.iter_keys(cache_keys_pattern)):
			answered_questions_list = generate_result(cache.get(key), sitting_obj, key, quizstack)
			if answered_questions_list:
				for question_id in answered_questions_list:
					if question_id in unanswered_questions_list: 
						unanswered_questions_list.remove(question_id) 
				cache.delete(key)
				print cache.get(key), '-----------------'

		sitting_obj.save_time_spent(request.data.get('time_spent'))

		# Clear all unanswered_questions_list so as to modify it.
		sitting_obj.clear_all_unanswered_questions()
		for question_id in unanswered_questions_list:
			sitting_obj.add_unanswerd_question(question_id)
		sitting_obj.save()

		# test is set to complete must come after sitting_obj.add_unanswerd_question()
		sitting_obj.mark_quiz_complete()
		data = { 'EVENT_TYPE': 'finishTest', 'test_key': test_key, 'sitting_id': sitting_id, 'test_user_id': test_user, 'timestamp_IST': str(timezone.now()), 'username': sitting_obj.user.username, 'email': sitting_obj.user.email, 'finish_mode': 'NormalSubmission' }
		if not postNotifications(data, sitting_obj.quiz.finish_notification_url):
			print 'finish notification not sent'
		cache.delete('sitting_id'+str(test_user))
		cache.delete(test_key + "|" + str(test_user) + "time")
		_filter_by_category = filter_by_category(sitting_obj)
		data = get_user_result_helper(sitting_obj, test_user, test_key, 'acending', _filter_by_category, '-current_score')
		data['htmlReport'] = 'http://'+str(request.get_host())+'/api/user/result/'+str(test_user)+'/'+test_key+'/'+str(sitting_obj.attempt_no)
		if not postNotifications(data, sitting_obj.quiz.grade_notification_url):
			print 'grade notification not sent'
		return Response({ 'attempt_no': sitting_obj.attempt_no }, status = status.HTTP_200_OK)
	else:
		return Response({}, status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((AllowAny,))
def ping(request):
	return Response({}, status = status.HTTP_200_OK)
