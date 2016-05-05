from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.decorators import authentication_classes

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template import Template, Context
from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from quiz.serializer import SittingSerializer, QuestionSerializer
from serializer import MerchantSerializer, TestUserSerializer, UserSerializer

from token_key import generate_token
from QnA.settings import TEST_URL_THIRD_PARTY, TEST_BASE_URL, TEST_REPORT_URL

from QnA.services.utility import checkIfTrue, postNotifications, get_user_result_helper, save_test_data_to_db_helper, merge_two_dicts
from QnA.services.constants import REGISTRATION_HTML, CACHE_TIMEOUT
from QnA.services.test_authentication import TestAuthentication
from QnA.services.mail_handling import send_mail
from QnA.services.generate_result_engine import generate_result, filter_by_category, get_data_for_analysis, find_and_save_rank, get_topper_data

from quiz.models import Sitting, Quiz, Question
from home.models import TestUser, BookMarks, InvitedUser
from quizstack.models import QuizStack
from mcq.models import Answer

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

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_user_result(request, test_user_id, quiz_key, attempt_no):
	test_user = TestUser.objects.get(id = test_user_id)
	get_order_by = '-current_score'
	quiz = Quiz.objects.get(quiz_key = quiz_key)
	sitting = Sitting.objects.order_by(get_order_by).get(user = test_user.user, quiz = quiz, attempt_no = attempt_no)
	# unanswered_questions_list = sitting.unanswered_questions.keys()
	# incorrect_question_list = sitting.get_incorrect_questions()
	_filter_by_category = filter_by_category(sitting)
	data = get_user_result_helper(sitting, test_user_id, quiz_key, request.GET.get('order', None), _filter_by_category, get_order_by)
	topper_sitting_obj = get_topper_data(quiz_key, sitting.quiz.id)
	data['sitting_id'] = sitting.id
	data['rank'] = find_and_save_rank(test_user_id, quiz_key, sitting.quiz.id, sitting.current_score, sitting.time_spent)
	data['start_time_IST'] = parse_datetime(data['start_time_IST']).strftime('%s')
	data['end_time_IST'] = parse_datetime(data['end_time_IST']).strftime('%s')
	data['analysis'] = { 'filter_by_category':{}, 'section_wise_results' :{}, 'question_vs_time_result_topper': merge_two_dicts(topper_sitting_obj.user_answers, topper_sitting_obj.unanswered_questions) }
	if topper_sitting_obj.id != sitting.id:
		data['analysis']['question_vs_time_result_user'] = merge_two_dicts(sitting.user_answers, sitting.unanswered_questions)
	data['analysis']['filter_by_category'] = _filter_by_category[0]
	data['view_format'] = request.GET.get('view_format',None)
	# fp = open('QnA/services/result.html')
	# t = Template(fp.read())
	# fp.close()
	data_for_analysis = get_data_for_analysis(quiz, sitting.unanswered_questions.keys(), sitting.get_incorrect_questions())
	data['analysis']['section_wise_results'] = data_for_analysis['section_wise']
	data['questions_stats'] = data_for_analysis['selected_questions']
	# html = t.render(Context({'data': data }))
	if data['view_format'] == 'pdf':
		return
		# return generate_PDF(request, html)
	else:
		return Response(data, status = status.HTTP_200_OK)


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

			if not sitting_obj.unanswered_questions:
				for quizstack in QuizStack.objects.filter(quiz = quiz):
					for question_id in quizstack.fetch_selected_questions():
						sitting_obj.add_unanswered_question(question_id, '')
			cache.set('sitting_id'+str(test_user_id), sitting_obj.id, timeout = CACHE_TIMEOUT)
			
			data = { 'EVENT_TYPE': 'startTest', 'test_key': quiz.quiz_key, 'sitting_id': sitting_obj.id,
					 'test_user_id': test_user_id, 'timestamp_IST': str(timezone.now()), 'username': sitting_obj.user.username,
					  'email': sitting_obj.user.email }
			
			if not postNotifications(data, sitting_obj.quiz.start_notification_url):
				print 'start notification not sent'
			return Response({}, status = status.HTTP_200_OK)
		return Response({}, status = status.HTTP_200_OK)
	except Exception as e:
		print e.args,'----'
		return Response({}, status = status.HTTP_400_BAD_REQUEST)

# Helper function for get users cache data if exist in cache.
def test_data_helper(test_key, test_user_id):
	test_data = { 'isTestNotCompleted': False, 'existingAnswers': { 'answers': None } }
	if cache.get('sitting_id'+str(test_user_id), None):	
		test_data['status'] = 'INCOMPLETE'
		test_data['isTestNotCompleted'] = True
		test_data['timeRemaining'] = cache.get(test_key + "|" + str(test_user_id) + "time")['remaining_duration']
		test_data['sectionNoWhereLeft'] = 1
		preExistingKeys = sorted(list(cache.iter_keys(test_key+"|"+str(test_user_id)+"|**")))
		if preExistingKeys:
			print preExistingKeys,'-------------'
			test_data['existingAnswers']['answers'] = {}
			for key in preExistingKeys:
				test_data['existingAnswers']['answers']['Section#'+key.split('|')[2]] = cache.get(key)['answers']
			test_data['sectionNoWhereLeft'] = preExistingKeys[len(preExistingKeys)-1].split('|')[2]		
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
			# If test is not public then check private access of user.
			if not quiz.allow_public_access:
				try:
					# Is user invited check.
					invited_user = InvitedUser.objects.get(quiz = quiz, user_name = name, user_email = email)
				except InvitedUser.DoesNotExist as e:
					# User can't access this test.
					print e.args
					return Response({'status':'NOT-ALLOW', 'errors': 'Unable to access this test.'}, status=status.HTTP_400_BAD_REQUEST)
			
			user  = User.objects.get(username = name, email = email)
			create = False
		except User.DoesNotExist as e:
			try:
				user  = User.objects.create_user(username = name, email = email, password = name[::-1]+email[::-1])
				create = True
			except Exception as e:
				print e.args
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

@api_view(['POST'])
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
def save_question_time(request):
	test_user = request.data.get('test_user')
	sitting_id = cache.get('sitting_id'+str(test_user))
	if sitting_id:
		qtime_spent = request.data.get('qtime_spent')
		question_id = qtime_spent.keys()[0]
		test_key = request.data.get('test_key')
		cache_key = test_key+"|"+str(test_user)+"qtime"
		cache_value = cache.get(cache_key)
		if not cache_value:			
			cache.set(cache_key,{ 'qtime': qtime_spent  }, timeout = CACHE_TIMEOUT)
		else:
			if question_id in cache_value['qtime'].keys():
				cache_value['qtime'][question_id] = qtime_spent[question_id]
			else:
				cache_value['qtime'].update(qtime_spent)
			cache.set(cache_key, cache_value, timeout = CACHE_TIMEOUT)
		print cache.get(cache_key),'++++++++++++++++++'
		return Response({}, status = status.HTTP_200_OK)
	else:
		return Response({}, status = status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def save_test_data_to_db(request):
	test_user = request.data.get('test_user')
	sitting_id = cache.get('sitting_id'+str(test_user))
	test_key = request.data.get('test_key')
	time_spent = request.data.get('time_spent')
	time_spent_on_question = cache.get(test_key + "|" + str(test_user) + "qtime")
	try:
		host_name = request.META['HTTP_HOST']
		data = save_test_data_to_db_helper(test_user, sitting_id, test_key, time_spent, host_name, time_spent_on_question['qtime'])
		return Response({ 'attempt_no': data['attempt_no'] }, status = status.HTTP_200_OK)
	except Exception as e:
		print e.args
		return Response({}, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def save_test_bookmarks(request):
	test_user = request.data.get('test_user')
	sitting_id = cache.get('sitting_id'+str(test_user))
	try:
		if sitting_id:
			bookmarked_questions_list = request.data.get('bookmarked_questions')
			existing_bookmarks = []
			if bookmarked_questions_list:
				bookmark, created = BookMarks.objects.get_or_create(user = TestUser.objects.get(id = test_user).user)
				if not created:
					existing_bookmarks = bookmark.fetch_bookmarks()
				for question_id in bookmarked_questions_list:
					if question_id not in existing_bookmarks:
						bookmark.add_bookmark(question_id)
			return Response({}, status = status.HTTP_200_OK)
		return Response({}, status = status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		print e.args
		return Response({}, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def get_bookmark_questions(request):
	username = request.data.get('username')
	email = request.data.get('email')
	if username and email:
		try:
			user = User.objects.get(username = username, email = email)
		except User.DoesNotExist:
			return Response({ 'errors': 'User not found.'}, status = status.HTTP_400_BAD_REQUEST)
		try:
			bookmark = BookMarks.objects.get(user = user)
		except BookMarks.DoesNotExist:
			return Response({ 'errors': 'Bookmarks not found.' }, status = status.HTTP_400_BAD_REQUEST)
		
		bookmarked_questions_list = bookmark.fetch_bookmarks()
		if bookmarked_questions_list:
			questionserializer = QuestionSerializer( [Question.objects.get(id = q) for q in bookmarked_questions_list], many = True)
			return Response({ 'data': { questionserializer.data } }, status = status.HTTP_200_OK)
		else:
			return Response({ 'errors': 'Bookmarks not found.' }, status = status.HTTP_400_BAD_REQUEST)
	return Response({ 'errors': 'Username or email not provided.'}, status = status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes((AllowAny,))
def question_stats(request, sitting_id):
	count = int(request.query_params.get('count'))
	try:
		data = { 'questionStats': [], 'stop': False }
		sitting = Sitting.objects.get(id = sitting_id)
		all_question_ids = merge_two_dicts(sitting.user_answers, sitting.unanswered_questions)
		all_question_ids_keys = all_question_ids.keys()
		if len(all_question_ids_keys) == (count+1)*5:
			data['stop'] = True
		question_ids = all_question_ids_keys[count*5:(count+1)*5]
		for question_id in question_ids:
			question = Question.objects.get(id = question_id)
			correct_answer_id = 0
			answer_status = 'Unattempted'
			for answer in Answer.objects.filter(question = question):
				if answer.correct == True:
					correct_answer_id = answer.id
					break
			if isinstance(all_question_ids[question_id], list):
				if all_question_ids[question_id][0] == correct_answer_id:
					answer_status = 'Correct'
				else:
					answer_status = 'Incorrect'
			data['questionStats'].append({
				'content': question.content,
				'hint': question.explanation,
				'status': answer_status
				})
		return Response(data, status = status.HTTP_200_OK)
	except Sitting.DoesNotExist as e:
		print e.args
		return Response({ 'errors': '' }, status = status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny,))
def ping(request):
	return Response({}, status = status.HTTP_200_OK)
