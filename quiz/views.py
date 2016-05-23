from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from QnA.services.utility import get_questions_format, checkIfTrue

from django.contrib.auth.models import User
from .models import Quiz, Category, SubCategory, Question
from mcq.models import Answer
from home.models import InvitedUser

from mcq.serializer import AnswerSerializer
from objective.serializer import ObjectiveQuestionSerializer
from quizstack.serializer import QuizStackSerializer
from QnA.settings import TEST_URL

from objective.models import ObjectiveQuestion
from comprehension.models import Comprehension, ComprehensionQuestion
from comprehension.serializer import ComprehensionSerializer, ComprehensionQuestionSerializer
from serializer import QuizSerializer, CategorySerializer, SubCategorySerializer, QuestionSerializer
from QnA.services.constants import QUESTION_DIFFICULTY_OPTIONS, QUESTION_TYPE_OPTIONS

from QnA.services.xls_operations import save_test_private_access_from_xls
from QnA.services.constants import QUIZ_ACCESS_FILE_COLS, MCQ_FILE_COLS, OBJECTIVE_FILE_COLS
from pyexcel_xls import save_data
from collections import OrderedDict
import os

# >>>>>>>>>>>>>>>>>>>>>>>  Quiz Base functions  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#
@api_view(['GET'])
def get_quiz(request, userid, quizid ,format = None):
	"""
	Get a quiz.
	"""
	if quizid == 'all':
		try:
			quiz_list = Quiz.objects.filter(user=userid).order_by('id')
			serializer = QuizSerializer(quiz_list, many = True)
			return Response(serializer.data, status = status.HTTP_200_OK)
		except Quiz.DoesNotExist as e:
			print e.args
			return Response({'errors': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)
	elif quizid.isnumeric():
		try:
			quiz = Quiz.objects.get(id = quizid, user = userid)
		except Quiz.DoesNotExist as e:
			return Response({'errors': 'Quiz not found'}, status = status.HTTP_404_NOT_FOUND)
		serializer = QuizSerializer(quiz)
		serializer.data['quiz_key'] = quiz.quiz_key
		return Response(serializer.data, status = status.HTTP_200_OK)
	else:
		return Response({'errors': 'Wrong URL passed.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_quiz_acc_key(request):
	quiz_key = request.query_params.get('quiz_key')
	if quiz_key:
		try:
			quiz = Quiz.objects.get(quiz_key = quiz_key)
			serializer = QuizSerializer(quiz)
			return Response(serializer.data, status = status.HTTP_200_OK)
		except Quiz.DoesNotExist as e:
			return Response({'errors': 'Quiz not found.'}, status = status.HTTP_404_NOT_FOUND)
	else:
		return Response({'errors': 'Quiz Key not given.'}, status = status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
def update_quiz(request, userid, quizid ,format = None):
	"""
	Update a quiz.
	"""
	try:
		quiz = Quiz.objects.get(id = quizid, user = userid)
	except Quiz.DoesNotExist as e:
		return Response({'errors': 'Quiz not found'}, status = status.HTTP_404_NOT_FOUND)
	serializer = QuizSerializer(quiz, data = request.data)
	if serializer.is_valid():
		serializer.save()
		return Response({ 'updatedQuiz' : serializer.data }, status = status.HTTP_200_OK)
	else:
		print serializer.errors
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def mark_quiz_public(request, userid, quizid):
	try:
		quiz = Quiz.objects.get(id = quizid, user = userid)
		quiz.allow_public_access = False if quiz.allow_public_access else True
		quiz.save()
		return Response({ 'title':quiz.title, "allow_public_access":quiz.allow_public_access, 'id':quiz.id }, status = status.HTTP_200_OK)
	except Quiz.DoesNotExist as e:
		return Response({'errors': 'Quiz not found'}, status = status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def create_quiz(request, format = None):
	"""
	Create a new quiz.
	"""
	serializer = QuizSerializer(data = request.data)
	if serializer.is_valid():
		quiz = serializer.save()
		data = serializer.data
		data['allow_public_access'] = quiz.allow_public_access
		data['id'] = quiz.id 
		data['quiz_key'] = quiz.quiz_key 
		data['show_result_on_completion'] = quiz.show_result_on_completion 
		data['total_duration'] = quiz.total_duration 
		data['total_marks'] = quiz.total_marks 
		data['total_questions'] = quiz.total_questions 
		data['total_sections'] = quiz.total_sections 
		data['url'] = quiz.url 
		return Response(data, status = status.HTTP_200_OK)
	return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_quiz(request, user_id, quiz_id, format = None):
	"""
	Delete a quiz.
	"""
	try:
		print user_id, quiz_id, '---------'
		quiz = Quiz.objects.get(id = quiz_id, user = user_id)
	except Quiz.DoesNotExist as e:
		return Response({'errors': 'Quiz not found'}, status = status.HTTP_404_NOT_FOUND)
	quiz.delete()
	return Response({}, status = status.HTTP_200_OK)


#>>>>>>>>>>>>>>>>>>>>> Category Base Functions Start <<<<<<<<<<<<<<<<<<<#

@api_view(['POST'])
def create_category(request):
	"""
	Create a category
	"""
	# print request.data
	try:
		serializer = CategorySerializer(data = request.data)
		# print serializer
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status = status.HTTP_200_OK)
		else:
			print serializer.errors
			return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		print e.args
		return Response({'errors' : 'Cannot create the category.'}, status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def get_category(request, pk ,format = None):
	"""
	Quiz detail with pk.
	"""
	try:
		category = Category.objects.get(pk = pk)
		serializer = CategorySerializer(category)
		return Response(serializer.data, status = status.HTTP_200_OK)
	except Category.DoesNotExist as e:
		return Response({'errors': 'Quiz not found'}, status = status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def category_list(request, userid, categoryid, format = None):
	"""
	Either get a single quiz or all.
	"""
	try:
		categories = []
		if categoryid == 'all': 
			for category in Category.objects.filter(user = userid):
				categories.append(category)
			serializer = CategorySerializer(categories, many = True)
		else:
			if categoryid.isnumeric():
				category = Category.objects.filter(id = categoryid, user=userid)
				serializer = CategorySerializer(category, many = False)
			else:
				return Response({'errors': 'Wrong URL passed.'}, status=status.HTTP_404_NOT_FOUND)
		return Response(serializer.data, status = status.HTTP_200_OK)
	except Category.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'DELETE'])
def delete_category(request, pk, format = None):
	"""
	Delete a quiz or GET a quiz details.
	"""
	try:
		category = Category.objects.get(pk = pk)
	except Category.DoesNotExist as e:
		return Response({'errors': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

	if request.method == 'GET':
		serializer = CategorySerializer(category)
		return Response(serializer.data)

	elif request.method == 'DELETE':
		category.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)




#>>>>>>>>>>>>>>>>>>>>> SubCategory Base Functions Start <<<<<<<<<<<<<<<<<<<#

@api_view(['POST'])
def create_subcategory(request):
	"""
	List all code Quiz, or create a new quiz.
	"""
	serializer = SubCategorySerializer(data = request.data)
	if serializer.is_valid():
		serializer.save()
		return Response(serializer.data, status = status.HTTP_200_OK)
	return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_subcategory(request, userid, categoryid, format = None):
	"""
	If all_subcategories = True then return all else return subcategory not have any category.
	Either get all subcategories under each quiz and category or get subcategories under specifc quiz and category.
	"""
	serializer = None
	subcategories = []
	if categoryid == 'all':
		if checkIfTrue(request.query_params.get('all_subcategories')):
			subcategories = SubCategory.objects.filter(user = userid)
		else:
			subcategories = SubCategory.objects.filter(user = userid, category = None)
		serializer = SubCategorySerializer(subcategories, many = True)
		return Response(serializer.data, status = status.HTTP_200_OK) 
	elif categoryid.isnumeric():
		try:
			subcategories = SubCategory.objects.filter(category = categoryid, user = userid)
			serializer = SubCategorySerializer(subcategories, many = True)
			return Response(serializer.data, status = status.HTTP_200_OK) 
		except SubCategory.DoesNotExist as e:
			print e.args
			return Response({'errors': 'Sub-categories not found'}, status = status.HTTP_404_NOT_FOUND)
	else:
		return Response({'errors': 'Wrong URL passed.'}, status = status.HTTP_404_NOT_FOUND)


#>>>>>>>>>>>>>>>>>>>>> Question Base Functions Start <<<<<<<<<<<<<<<<<<<#

@api_view(['GET'])
def all_questions(request, user_id):
	"""
	Either get all questions under each quiz and category or get questions under specifc quiz and category.
	"""
	if request.query_params.get('subCategoryId'):
		try:
			subcategory_id = request.query_params.get('subCategoryId')
		except SubCategory.DoesNotExist as e:
			print e.args
			return Response({'errors': 'Questions not found'}, status=status.HTTP_404_NOT_FOUND)
		if request.query_params.get('questionFormat'):
			result = get_questions_format(user_id, subcategory_id, True)
			result['level'] = []
			result['que_type'] = []
			result['duration'] = 0
			result['no_questions'] = 0
			result['correct_grade'] = 1
			result['incorrect_grade'] = 0
			if result['questions_type_info']['mcq'][3] != 0:
				result['que_type'].append('mcq')
			if result['questions_type_info']['comprehension'][3] != 0:
				result['que_type'].append('comprehension')
			result['section_name'] = '1'
			result['subcategory_id'] = subcategory_id
			result = [result]		# Must be a list
		else:
			result = get_questions_format(user_id, subcategory_id)
	else:
		result = get_questions_format(user_id)
	return Response(result, status = status.HTTP_200_OK)

@api_view(['GET'])
def all_questions_under_quiz(request, userid, quizid):
	"""
	Get all questions under a quiz.
	"""
	try:
		quiz = Quiz.objects.get(id=quizid, user=userid)
		quizzes = get_questions_format(quiz, Category, SubCategory, Question, Answer)

		return Response(quizzes, status = status.HTTP_200_OK)
	except SubCategory.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Questions not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def all_questions_under_category(request, userid, quizid, categoryid):
	"""
	Get all questions under a quiz and a category.
	"""
	try:
		quiz = Quiz.objects.get(id=quizid, user=userid)
		quizzes = get_questions_format(quiz, Category, SubCategory, Question, Answer)
		return Response(quizzes, status = status.HTTP_200_OK)
	except SubCategory.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Questions not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def all_questions_under_subcategory(request, user_id, subcategory_id):
	"""
	Either get all questions under specifc subcategory.
	"""
	try:
		if not request.query_params.get('questionFormat') == 'false':
			quizzes = get_questions_format(user_id, subcategory_id, True)
		else:
			quizzes = get_questions_format(user_id, subcategory_id)
		return Response(quizzes, status = status.HTTP_200_OK)	
	except SubCategory.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Questions not found'}, status = status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'PUT', 'DELETE'])
def question_operations(request, userid, question_id):
	"""
	Get a single question, delete or update
	"""
	try:
		question = Question.objects.get(id = question_id)
	except Question.DoesNotExist:
		return Response({'errors': 'Question not found.'}, status=status.HTTP_404_NOT_FOUND)
	if request.method == 'GET':
		questionserializer = QuestionSerializer(question, many = False)
		answers = Answer.objects.filter(question = question)
		answerserializer = AnswerSerializer(answers, many = True)
		result = dict(questionserializer.data)
		if question.que_type == QUESTION_TYPE_OPTIONS[2][0]:
			result['heading'] = Comprehension.objects.get(question = question).heading
		result.update( { 'options' : answerserializer.data } )
		result['sub_category'] = question.sub_category.sub_category_name
		return Response({ 'question' : result }, status = status.HTTP_200_OK)
	elif request.method == 'PUT':
		data = {}
		result = None
		data['explanation'] = request.data['data[explanation]']
		data['level'] = request.data['data[level]']
		data['ideal_time'] = request.data['data[ideal_time]']
		if request.data.get('data[figure]', None):
			data['figure'] = request.data['data[figure]']
			if question.figure:
				os.remove(str(question.figure))
		data['sub_category'] = question.sub_category.id
		if question.que_type == QUESTION_TYPE_OPTIONS[1][0]:
			if BLANK_HTML in request.data['data[content]']:
				data['content'] = request.data['data[content]'].replace(BLANK_HTML,' <> ').replace('&nbsp;', ' ')
				serializer = ObjectiveQuestionSerializer(question, data = data)
			else:
				return Response({ "content" : ["No blank field present.Please add one."] } , status = status.HTTP_400_BAD_REQUEST)
		else:
			data['content'] = request.data['data[content]']
			serializer = QuestionSerializer(question, data = data)
			if question.que_type == QUESTION_TYPE_OPTIONS[2][0]:
				d = { 'heading': request.data['data[heading]'], 'question': question.id }
				comprehension_serializer = ComprehensionSerializer(Comprehension.objects.get(question = question), data = d)
				if comprehension_serializer.is_valid():
					comprehension_serializer.save()
					result = comprehension_serializer.data
				else:
					return Response(comprehension_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		if serializer.is_valid():
			serializer.save()
			if result:
				result.update(serializer.data)
			else:
				result = serializer.data
			return Response(result, status = status.HTTP_200_OK)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	elif request.method == 'DELETE':
		if question.figure:
			os.remove(str(question.figure))
		question.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)




@api_view(['GET', 'PUT'])
def answers_operations(request, userid, question_id):
	"""
	Get answers to a question or update.
	"""
	try:
		result = {}
		question = Question.objects.get(pk = question_id)
		if request.query_params['que_type'] == QUESTION_TYPE_OPTIONS[0][0]:
			answers = Answer.objects.filter(question = question)
		elif request.query_params['que_type'] == QUESTION_TYPE_OPTIONS[1][0]:
			answer = ObjectiveQuestion.objects.get(pk=question)
	except Question.DoesNotExist:
		return Response({'errors': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
	if request.method == 'GET':
		if request.query_params['que_type'] == QUESTION_TYPE_OPTIONS[0][0]:
			answerserializer = AnswerSerializer(answers, many = True)
			result['options'] = answerserializer.data
		elif request.query_params['que_type'] == QUESTION_TYPE_OPTIONS[1][0]:
			result['correct'] = answer.correct
		result['content'] = question.content
		result['sub_category_name'] = question.sub_category.sub_category_name
		result['sub_category'] = question.sub_category.id
		return Response({ 'answers' : result }, status = status.HTTP_200_OK)

	elif request.method == 'PUT':
		if request.query_params['que_type'] == QUESTION_TYPE_OPTIONS[0][0]:
			optionsContent = dict(request.data.get('optionsContent'))
			result['options'] = []
			result['content'] = question.content
			for answer in answers:
				d = { 'correct' : False, 'content' : optionsContent[str(answer.id)], 'question' : question.id }
				if request.data.get('correctOption') == str(answer.id):
					d['correct'] = True
				serializer = AnswerSerializer(answer,data=d)
				if serializer.is_valid():
					serializer.save()
					result['options'].append(serializer.data)
		elif request.query_params['que_type'] == QUESTION_TYPE_OPTIONS[1][0]:
			serializer = ObjectiveQuestionSerializer(answer, request.data)
			if serializer.is_valid():
				serializer.save()
				result['options'].append(serializer.data)
			else:
				return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		return Response(result, status = status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((AllowAny,))
def download_xls_file(request):
	que_type = request.data.get('que_type')	
	if request.data.get('sub_cat_info'):
		sub_category_id =  request.data.get('sub_cat_info').split('>>')[0]
		sub_category_name =  request.data.get('sub_cat_info').split('>>')[1]
	else:
		return Response({'errors': 'Select a sub-category first.'}, status=status.HTTP_400_BAD_REQUEST)

	try:
		sub_category = SubCategory.objects.get(pk = sub_category_id, sub_category_name = sub_category_name)
	except SubCategory.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Sub-category does not exist.'}, status=status.HTTP_404_NOT_FOUND)
	data = OrderedDict()
	if que_type == 'mcq':
		data.update({"Sheet 1": [MCQ_FILE_COLS,["", sub_category_name]]})
	elif que_type == 'objective':
		data.update({"Sheet 1": [OBJECTIVE_FILE_COLS,[sub_category_name]]})
	save_data(sub_category_name+"_"+que_type+"_file.xls", data)
	
	from django.http import FileResponse
	response = FileResponse(open(sub_category_name+"_"+que_type+"_file.xls", 'rb'))
	try:
		import os
		os.remove(sub_category_name+"_"+que_type+"_file.xls")
	except OSError:
		pass
	return response


@api_view(['GET','POST'])
@permission_classes((AllowAny,))
def download_access_xls_file(request):
	test_id = request.data.get('test_id')
	if test_id:
		quiz = Quiz.objects.get(pk = test_id)
	else:
		return Response({'errors': 'Invalid data here.'}, status=status.HTTP_400_BAD_REQUEST)
	data = {"Sheet 1": [QUIZ_ACCESS_FILE_COLS]}
	save_data(quiz.title+"_file.xls", data)
	
	from django.http import FileResponse
	response = FileResponse(open(quiz.title+"_file.xls", 'rb'))
	try:
		import os
		os.remove(quiz.title+"access_file.xls")
	except OSError:
		pass
	return response


@api_view(['POST'])
def upload_private_access_xls(request):
	try:
		file = request.data['file_data']
		quiz_id = request.data['quiz_id']
		if file and quiz_id and save_test_private_access_from_xls(file, quiz_id):
			return Response({'msg': 'Private access user create successfully'}, status=status.HTTP_200_OK)
	except Exception as e:
		print e
		return Response({'errors': 'Invalid data here.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes((AllowAny,))
def create_live_test(request, live_key):
	print request.data
	quiz_obj = None
	is_quiz_new = False
	# Temp data
	LIVE_TEST_CREATION_DATA = request.data['LIVE_TEST_CREATION_DATA']
	#Live test number should be start with 0 index. 
	def create_quiz_stack(quiz_stack_data, quiz_obj, sub_category_obj, live_test_number):
		questions_list = Question.objects.filter(sub_category = sub_category_obj, que_type = quiz_stack_data['que_type'])
		
		if len(questions_list)>=30*(live_test_number+1):
			questions_list = questions_list[30*live_test_number:30*(live_test_number+1)]
		else:
			questions_list = questions_list.order_by('?')[:30]

		qs = QuizStackSerializer(data = quiz_stack_data)
		if qs.is_valid():
			print quiz_stack_data['que_type'],len(questions_list)
			qs = qs.save()
			qs.add_selected_questions([que.id for que in questions_list])
			return qs
		else:
			print qs.errors
			return None
	try:
		user = User.objects.get(username = LIVE_TEST_CREATION_DATA['user_name'], email = LIVE_TEST_CREATION_DATA['user_email'])
		quiz_obj = Quiz.objects.get(user = user, title = LIVE_TEST_CREATION_DATA['title'], quiz_key = LIVE_TEST_CREATION_DATA['live_test_key'])		
	except User.DoesNotExist as e:
		print e.args
		user = User.objects.create_user(username = LIVE_TEST_CREATION_DATA['user_name'], email = LIVE_TEST_CREATION_DATA['user_email'], password = 'livetester')
		quiz_obj = Quiz.objects.get(user = user, quiz_key = LIVE_TEST_CREATION_DATA['live_test_key'], title = LIVE_TEST_CREATION_DATA['title'])
		
	except Quiz.DoesNotExist as e:
		is_quiz_new = True
		print 'Create a new quiz here'	
		quiz_serializer = QuizSerializer(data =
								{
								'user':user.id,'quiz_key':LIVE_TEST_CREATION_DATA['live_test_key'],'title':LIVE_TEST_CREATION_DATA['title'],
								'no_of_attempt': LIVE_TEST_CREATION_DATA['allow_attempt'],
								'passing_percent':LIVE_TEST_CREATION_DATA['passing_percent'],'success_text':'','fail_text':'',
								# 'total_marks':78,
								'total_questions':LIVE_TEST_CREATION_DATA['total_questions'],
								'total_sections':2
								})
		if quiz_serializer.is_valid():
			'''Add some quiz stacks of 30'''
			quiz_obj = quiz_serializer.save()
		else:
			print quiz_serializer.errors
	print '>>>>>>>',quiz_obj
	if quiz_obj and is_quiz_new:
		invited_user, is_new = InvitedUser.objects.get_or_create(user_name = user.username, user_email = user.email, defaults={})
		invited_user.add_inviteduser(quiz_obj.id)
		for category_details in LIVE_TEST_CREATION_DATA['section_details']:
			for sub_category_name,sub_category_questions_details in category_details['included_sub_category_list'].items():
				
				sub_category_data_list = sub_category_name.split(':#:')
				sub_category_obj = SubCategory.objects.get(sub_category_name = sub_category_data_list[0])

				data = {'quiz':quiz_obj.id,'subcategory':'','section_name': category_details['section_name'],
						'level':'', 'que_type':'',
						# 'duration':category_details['duration'],
						'no_questions':0,'question_order':'random'
						}
				data['subcategory'] = sub_category_obj.id
				data['que_type'] = sub_category_data_list[1]
				for question_level, no_of_questions in sub_category_questions_details.items():
					data['level'] = question_level
					data['no_questions'] = no_of_questions
					create_quiz_stack(data, quiz_obj, sub_category_obj, LIVE_TEST_CREATION_DATA['test_no'])					
		return Response({'msg': 'Live quiz created successfully.', 'access_url':TEST_URL+LIVE_TEST_CREATION_DATA['live_test_key'], 'is_quiz_new':is_quiz_new}, status=status.HTTP_200_OK)
	else:
		print 'Quiz is pre existed'
		return Response({'msg': 'Live quiz pre-created', 'access_url':TEST_URL+LIVE_TEST_CREATION_DATA['live_test_key'], 'is_quiz_new':is_quiz_new}, status=status.HTTP_200_OK)


