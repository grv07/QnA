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

from quiz.serializer import SittingSerializer
from serializer import MerchantSerializer, TestUserSerializer, UserSerializer

from token_key import generate_token
from QnA.settings import TEST_URL_THIRD_PARTY, TEST_BASE_URL, TEST_REPORT_URL

from QnA.services.utility import checkIfTrue, postNotifications, get_user_result_helper, save_test_data_to_db_helper, merge_two_dicts, make_user_hash
from QnA.services.constants import REGISTRATION_HTML, CACHE_TIMEOUT, QUESTION_TYPE_OPTIONS, BLANK_HTML, TEST_STATUSES
from QnA.services.test_authentication import TestAuthentication
from QnA.services.mail_handling import send_mail
from QnA.services.generate_result_engine import generate_result, filter_by_category, get_data_for_analysis, find_and_save_rank, get_topper_data

from quiz.models import Sitting, Quiz, Question
from home.models import TestUser, BookMarks, InvitedUser
from quizstack.models import QuizStack
from mcq.models import Answer
from comprehension.models import Comprehension, ComprehensionQuestion, ComprehensionAnswer
import ast
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
				return Response({'username':user_name,'email': user.email,'token':token, '_rest': str(user.id)+","+make_user_hash(user.id)  }, status = status.HTTP_200_OK)
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
	try:
		test_user = TestUser.objects.get(pk = test_user_id)
		get_order_by = '-current_score'
		quiz = Quiz.objects.get(quiz_key = quiz_key)
		sitting = Sitting.objects.order_by(get_order_by).get(user = test_user.user, quiz = quiz, attempt_no = attempt_no)
	except Exception as e:
		return Response({'errors':'Incorrect data'}, status = status.HTTP_400_BAD_REQUEST)
	
	if sitting.complete:
		# unanswered_questions_list = sitting.unanswered_questions.keys()
		# incorrect_question_list = sitting.get_all_incorrect_questions_keys()
		# _filter_by_category = filter_by_category(sitting)
		# print _filter_by_category
		# data = get_user_result_helper(sitting, test_user_id, quiz_key, request.GET.get('order', None), _filter_by_category, get_order_by)
		data = get_user_result_helper(sitting, test_user_id, quiz_key, request.GET.get('order', None), None, get_order_by)
		data['sitting_id'] = sitting.id
		data['rank'] = find_and_save_rank(test_user_id, quiz_key, sitting.quiz.id, sitting.current_score, sitting.time_spent)
		# topper_sitting_obj = get_topper_data(quiz_key, sitting.quiz.id)
		# print topper_sitting_obj
		data['start_time_IST'] = parse_datetime(data['start_time_IST']).strftime('%s')
		data['end_time_IST'] = parse_datetime(data['end_time_IST']).strftime('%s')
		# data['analysis'] = { 'filter_by_category':{}, 'section_wise_results' :{}, 'question_vs_time_result_topper': merge_two_dicts(topper_sitting_obj.get_timed_analysis_for_answered_questions(), topper_sitting_obj.get_timed_analysis_for_unanswered_questions()) }
		data['analysis'] = { 'filter_by_category':{}, 'section_wise_results' :{}, 'question_vs_time_result_topper': {} }
		
		# if topper_sitting_obj.id != sitting.id:
		data['analysis']['question_vs_time_result_user'] = merge_two_dicts(sitting.get_timed_analysis_for_answered_questions(), sitting.get_timed_analysis_for_unanswered_questions())
		# data['analysis']['filter_by_category'] = _filter_by_category[0]
		data['view_format'] = request.GET.get('view_format', None)

		data_for_analysis = get_data_for_analysis(quiz, sitting.unanswered_questions, sitting.incorrect_questions)
		data['analysis']['section_wise_results'] = data_for_analysis['section_wise']
		data['questions_stats'] = data_for_analysis['selected_questions']
		if data['view_format'] == 'pdf':
			return None
			# return generate_PDF(request, html)
		else:
			return Response(data, status = status.HTTP_200_OK)
	else:
		return Response({'errors':''}, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def save_sitting_user(request):
	try:
		sitting_id = request.data.get('existingSittingID')
		print sitting_id,'sitting_id'
		if not sitting_id:
			print '------------------'
			test_user_id = request.data.get('test_user')
			# sitting_id = cache.get('sitting_id'+str(test_user_id), None)
			# if not sitting_id:
			quiz = Quiz.objects.get(pk = request.data.get('quiz_id'))
			test_user_obj = TestUser.objects.get(pk = test_user_id)
			test_user_obj.no_attempt += 1
			test_user_obj.save()

			sitting_obj = Sitting.objects.create(user = test_user_obj.user, quiz = quiz, attempt_no = test_user_obj.no_attempt)
			sitting_id = sitting_obj.id
			sitting_obj.intialize()

			if not sitting_obj.complete:
				for quizstack in QuizStack.objects.filter(quiz = quiz):
					for question_id in quizstack.fetch_selected_questions():
						print question_id,'question_id'
						if quizstack.que_type == QUESTION_TYPE_OPTIONS[0][0]:
							sitting_obj.add_unanswered_mcq_question(question_id, [])
						elif quizstack.que_type == QUESTION_TYPE_OPTIONS[2][0]:
							comprehension = Comprehension.objects.get(question = question_id)
							for cq in ComprehensionQuestion.objects.filter(comprehension = comprehension):
								sitting_obj.add_unanswered_comprehension_question(question_id, cq.id, 0)

			# cache.set('sitting_id'+str(test_user_id), sitting_obj.id, timeout = CACHE_TIMEOUT)
			
			data = { 'EVENT_TYPE': 'startTest', 'test_key': quiz.quiz_key, 'sitting_id': sitting_obj.id,
					 'test_user_id': test_user_id, 'timestamp_IST': str(timezone.now()), 'username': sitting_obj.user.username,
					  'email': sitting_obj.user.email }
			
			if not postNotifications(data, sitting_obj.quiz.start_notification_url, request.data.get('toPost')):
				print 'start notification not sent'
		return Response({ 'sitting': sitting_id }, status = status.HTTP_200_OK)
	except Exception as e:
		print e.args,'----'
		return Response({}, status = status.HTTP_400_BAD_REQUEST)

# Helper function for get users cache data if exist in cache.
def test_data_helper(test_user):
	'''
	Cache data saved as -
	{
		u'sitting': 199, 
		u'comprehension_answers': {u'4': {u'value': u'3'}, u'6': {u'value': u'8'}}, 
		u'is_normal_submission': False, 
		u'answers': {u'33': {u'value': u'121'}, u'32': {u'value': u'116'}, u'46': {u'comprehension_questions': {u'4': {u'value': None}, u'6': {u'value': None}}, u'heading': u'Divide the sail', u'value': None}, u'48': {u'value': u'127'}}, 
		u'time_spent_on_questions': {u'33': {u'time': 8}, u'32': {u'time': 4}, u'46': {u'time': 13}, u'48': {u'time': 4}}, 
		u'bookmarked_questions': {u'comprehension': [4], u'mcq': [48]}, 
		u'section_no': u'1', 
		u'time_remaining': 55 
	}
	'''
	test_data = { 'isTestNotCompleted': False }
	cache_key = "A|"+str(test_user.id)+"|"+str(test_user.test_key)
	cache_value = cache.get(cache_key)
	# sitting_obj = Sitting.objects.get(user = test_user.user, quiz__quiz_key = test_user.test_key, attempt_no = test_user.no_attempt)
	if cache_value:
		test_data['existingSittingID'] = cache_value.get('sitting')
		test_data['status'] = TEST_STATUSES[0]
		test_data['isTestNotCompleted'] = True
		test_data['timeRemaining'] = cache_value.get('time_remaining')
		test_data['timeSpentOnQuestions'] = cache_value.get('time_spent_on_questions')
		test_data['sectionNoWhereLeft'] = cache_value.get('section_no')
		test_data['bookmarkedQuestions'] = cache_value.get('bookmarked_questions')
		test_data['isNormalSubmission'] = cache_value.get('is_normal_submission')
		existingAnswers = cache_value.get('answers')
		for cq_id, cq_value_dict in cache_value.get('comprehension_answers').items():
			for q_id, q_value_dict in existingAnswers.items():
				if q_value_dict.has_key('comprehension_questions') and q_value_dict['comprehension_questions'].has_key(cq_id):
					existingAnswers[q_id]['comprehension_questions'][cq_id] = cq_value_dict
		test_data['existingAnswers'] = existingAnswers
	else:
		test_data['status'] = TEST_STATUSES[1]
		test_data['existingSittingID']  = None
	return test_data


@api_view(['POST', 'GET'])
@permission_classes((AllowAny,))
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
			data['test'].update(test_data_helper(test_user))
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
					invited_user = InvitedUser.objects.get(user_name = name, user_email = email)
					if not invited_user.check_if_invited(quiz.id)[0]:
						return Response({'status':'NOT-ALLOW', 'errors': 'Unable to access this test.'}, status=status.HTTP_400_BAD_REQUEST)
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
			data['test'].update(test_data_helper(test_user))				
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
	answer = request.data.get('answer')
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
				if request.data.get('que_type') == QUESTION_TYPE_OPTIONS[0][0]:
					cache_value['answers'][question_id] = answer[question_id]
				elif request.data.get('que_type') == QUESTION_TYPE_OPTIONS[2][0]:
					cache_value['answers'][question_id].update(answer[question_id])
			else:
				cache_value['answers'].update(answer)
			cache.set(cache_key, cache_value, timeout = CACHE_TIMEOUT)
		print cache.get(cache_key),'**************'
		return Response({}, status = status.HTTP_200_OK)
	else:
		return Response({}, status = status.HTTP_400_BAD_REQUEST)
	return Response({}, status = status.HTTP_200_OK)


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
	test_key = request.data.get('test_key')
	test_data = request.data.get('test_data')
	to_post = bool(request.query_params.get('toPost'))
	print to_post,'=============='
	cache_key = "A|"+str(test_user)+"|"+str(test_key)
	cache_value = cache.get(cache_key)
	try:
		data = {}
		if test_data.get('is_normal_submission'):
			if cache_value:
				cache.delete(cache_key)
				print cache.get("A|"+str(test_user)+"|"+str(test_key)),'cache deletion after test completion'
				test_data['is_normal_submission'] = False
			data = save_test_data_to_db_helper(test_user, test_key, test_data, to_post)
			return Response({ 'attempt_no': data.get('attempt_no', {}) }, status = status.HTTP_200_OK)
		else:
			cache.set(cache_key, test_data, timeout = CACHE_TIMEOUT)
			print cache.get(cache_key),'cache.get(cache_key)'
			# print cache.delete(cache_key),'-----'
			# print cache.get(cache_key),'cache.get(cache_key)'
			return Response({}, status = status.HTTP_200_OK)
	except Exception as e:
		print e.args
		return Response({}, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def save_test_bookmarks(request):
	test_user = request.data.get('test_user')
	try:
		bookmarked_questions = request.data.get('bookmarked_questions')
		print bookmarked_questions,'bookmarks'
		existing_bookmarks = {}
		if bookmarked_questions['mcq'] or bookmarked_questions['comprehension']:
			bookmark, created = BookMarks.objects.get_or_create(user = TestUser.objects.get(id = test_user).user)
			if not created:
				existing_bookmarks = bookmark.fetch_bookmarks()
				print existing_bookmarks,'existing_bookmarks'
				for que_type in bookmarked_questions.keys():
					for question_id in bookmarked_questions[que_type]:
						if question_id not in existing_bookmarks.get(que_type, []):
							existing_bookmarks[que_type].append(question_id)
				bookmark.add_bookmark(existing_bookmarks)
			else:
				print 'created'
				bookmark.add_bookmark(bookmarked_questions)
		return Response({}, status = status.HTTP_200_OK)
	except Exception as e:
		print e.args
	return Response({}, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def get_bookmark_questions(request):
	username = request.data.get('username')
	email = request.data.get('email')
	if username and email:
		data = []
		format_dict = lambda values : {
									'figure': values[0],
									"content": values[1],
									"explanation": values[2],
									"level":values[3],
									"sub_category_name": values[4]
									}
		try:
			user = User.objects.get(username = username, email = email)
			bookmark = BookMarks.objects.get(user = user)
		except User.DoesNotExist:
			return Response({ 'errors': 'User not found.'}, status = status.HTTP_400_BAD_REQUEST)
		except BookMarks.DoesNotExist:
			return Response({ 'errors': 'Bookmarks not found.' }, status = status.HTTP_400_BAD_REQUEST)

		bookmarked_questions = bookmark.fetch_bookmarks()
		if bookmarked_questions[QUESTION_TYPE_OPTIONS[0][0]]:
			for q in bookmarked_questions[QUESTION_TYPE_OPTIONS[0][0]]:
				mcq = Question.objects.get(id = q)
				data.append(format_dict([str(mcq.figure), mcq.content, mcq.explanation, mcq.level, mcq.sub_category.sub_category_name]))
		if bookmarked_questions[QUESTION_TYPE_OPTIONS[2][0]]:
			for q in bookmarked_questions[QUESTION_TYPE_OPTIONS[2][0]]:
				cq = ComprehensionQuestion.objects.get(id = q)
				data.append(format_dict([str(cq.figure), cq.content, cq.explanation, cq.level, cq.comprehension.question.sub_category.sub_category_name]))
		if data:
			return Response({ 'bookmark_questions': data }, status = status.HTTP_200_OK)
		else:
			return Response({ 'errors': 'Bookmarks not found.' }, status = status.HTTP_400_BAD_REQUEST)
	return Response({ 'errors': 'Username or email not provided.'}, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes((AllowAny,))
def question_stats(request, sitting_id):
	count = request.data.get('count')
	try:
		data = { 'questionStats': { QUESTION_TYPE_OPTIONS[0][0]: [], QUESTION_TYPE_OPTIONS[2][0]: [] }, 'stop': False }
		sitting = Sitting.objects.get(id = sitting_id)
		if count == 0:
			all_questions = sitting.merge_user_answers_and_unanswered_questions()
			# print all_questions,'---'
			all_question_ids_keys = all_questions[QUESTION_TYPE_OPTIONS[0][0]].keys() + all_questions[QUESTION_TYPE_OPTIONS[2][0]].keys()
			data['allQuestions'] = all_questions
		else:
			all_questions = request.data.get('allQuestions')
			all_question_ids_keys = request.data.get('allQuestionIds')
		data['allQuestionIds'] = all_question_ids_keys

		# 5 is the slicing factor
		question_ids = all_question_ids_keys[count*5:(count+1)*5]
		if len(all_question_ids_keys) <= (count+1)*5:
			data['stop'] = True
		for question_id in question_ids:
			question = Question.objects.get(id = question_id)
			if question.que_type == QUESTION_TYPE_OPTIONS[0][0]:
				correct_answer_id = 0
				answer_status = 'Unattempted'
				for answer in Answer.objects.filter(question = question):
					if answer.correct == True:
						correct_answer_id = answer.id
						break
				if isinstance(all_questions[QUESTION_TYPE_OPTIONS[0][0]][str(question_id)], list):
					if all_questions[QUESTION_TYPE_OPTIONS[0][0]][str(question_id)][0] == correct_answer_id:
						answer_status = 'Correct'
					else:
						answer_status = 'Incorrect'
				data['questionStats'][QUESTION_TYPE_OPTIONS[0][0]].append({
					'content': question.content,
					'hint': question.explanation,
					'status': answer_status
					})

			elif question.que_type == QUESTION_TYPE_OPTIONS[2][0]:
				comprehension = Comprehension.objects.get(question = question)
				temp = { 'comprehension_questions': [], 'heading': comprehension.heading }
				for cq in ComprehensionQuestion.objects.filter(comprehension = comprehension):
					correct_answer_id = 0
					answer_status = 'Incorrect'
					for cqa in ComprehensionAnswer.objects.filter(question = cq):
						if cqa.correct == True:
							correct_answer_id = cqa.id
							break
					if all_questions[QUESTION_TYPE_OPTIONS[2][0]][str(question_id)][str(cq.id)] == correct_answer_id:
						answer_status = 'Correct'
					elif all_questions[QUESTION_TYPE_OPTIONS[2][0]][str(question_id)][str(cq.id)] == 0:
						answer_status = 'Unattempted'

					temp['comprehension_questions'].append({
						'content': cq.content,
						'hint': cq.explanation,
						'status': answer_status
						})
				data['questionStats'][QUESTION_TYPE_OPTIONS[2][0]].append(temp)
		return Response(data, status = status.HTTP_200_OK)
	except Sitting.DoesNotExist as e:
		print e.args
		return Response({ 'errors': '' }, status = status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((AllowAny,))
def ping(request):
	return Response({}, status = status.HTTP_200_OK)


