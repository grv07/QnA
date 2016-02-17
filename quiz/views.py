from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from QnA.services.utility import get_questions_format

from django.contrib.auth.models import User
from .models import Quiz, Category, SubCategory, Question
from mcq.models import Answer
from mcq.serializer import AnswerSerializer
from serializer import QuizSerializer, CategorySerializer, SubCategorySerializer, QuestionSerializer

# >>>>>>>>>>>>>>>>>>>>>>>  Quiz Base functions  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

# @api_view(['GET'])
# def quiz_list(request, userid, format = None):
# 	"""
# 	Get all quizzes.
# 	"""
# 	try:
# 		quiz_list = Quiz.objects.filter(user=userid).order_by('id')
# 		serializer = QuizSerializer(quiz_list, many = True)
# 		return Response(serializer.data, status = status.HTTP_200_OK)
# 	except Quiz.DoesNotExist as e:
# 		print e.args
# 		return Response({'errors': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)


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
			print quiz
		except Quiz.DoesNotExist as e:
			return Response({'errors': 'Quiz not found'}, status = status.HTTP_404_NOT_FOUND)
		serializer = QuizSerializer(quiz)
		return Response(serializer.data, status = status.HTTP_200_OK)


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
		return Response(serializer.data, status = status.HTTP_200_OK)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_quiz(request, format = None):
	"""
	List all code Quiz, or create a new quiz.

	"""
	serializer = QuizSerializer(data = request.data)

	if serializer.is_valid():
		serializer.save()
		return Response(serializer.data, status = status.HTTP_200_OK)
	return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'DELETE'])
def delete_quiz(request, pk, format = None):
	"""
	Delete a quiz or GET a quiz details.
	"""
	try:
		quiz = Quiz.objects.get(pk = pk)
	except Quiz.DoesNotExist as e:
		return Response({'msg': 'Quiz not found'}, status = status.HTTP_404_NOT_FOUND)

	if request.method == 'GET':
		serializer = QuizSerializer(quiz)
		return Response(serializer.data)

	elif request.method == 'DELETE':
		quiz.delete()
		return Response(status = status.HTTP_204_NO_CONTENT)





#>>>>>>>>>>>>>>>>>>>>> Category Base Functions Start <<<<<<<<<<<<<<<<<<<#

@api_view(['POST'])
def create_category(request):
	"""
	Create a category
	"""
	try:
		serializer = CategorySerializer(data = request.data)
		if serializer.is_valid():
			serializer.save()
		return Response(serializer.data, status = status.HTTP_200_OK)
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
	except Category.DoesNotExist as e:
		return Response({'msg': 'Quiz not found'}, status = status.HTTP_404_NOT_FOUND)

	serializer = CategorySerializer(category)
	return Response(serializer.data, status = status.HTTP_200_OK)

@api_view(['GET'])
def category_list(request, userid, categoryid, format = None):
	"""
	Either get a single quiz or all.
	"""
	try:
		categories = []
		print '-------------'
		if categoryid == 'all':
			for category in Category.objects.filter(user=userid):
				categories.append(category)
			serializer = CategorySerializer(categories, many = True)
		else:
			if categoryid.isnumeric():
				category = Category.objects.filter(id=categoryid, user=userid)
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
		return Response({'msg': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

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
	Either get all subcategories under each quiz and category or get subcategories under specifc quiz and category.
	"""
	try:
		subcategories = []
		if categoryid == 'all':
			for subcategory in SubCategory.objects.filter(user=userid):
				subcategories.append(subcategory)
			serializer = SubCategorySerializer(subcategories, many = True)
		else:
			if categoryid.isnumeric():
				subcategory = SubCategory.objects.get(category=categoryid, user=userid)
				serializer = SubCategorySerializer(subcategory, many = False)
			else:
				return Response({'errors': 'Wrong URL passed.'}, status=status.HTTP_404_NOT_FOUND)
		return Response(serializer.data, status = status.HTTP_200_OK)
	except SubCategory.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Sub-category not found'}, status=status.HTTP_404_NOT_FOUND)


#>>>>>>>>>>>>>>>>>>>>> Question Base Functions Start <<<<<<<<<<<<<<<<<<<#

@api_view(['GET'])
def all_questions(request, user_id):
	"""
	Either get all questions under each quiz and category or get questions under specifc quiz and category.
	"""
	try:
		if request.query_params.get('subCategoryId'):
			subcategory_id = request.query_params.get('subCategoryId')
			if request.query_params.get('questionFormat'):
				result = get_questions_format(user_id, subcategory_id, True)
				result['section_level'] = []
				if result['questions_level_info'][0] != 0:
					result['section_level'] += ['easy']
				if result['questions_level_info'][1] != 0:
					result['section_level'] += ['medium']
				if result['questions_level_info'][2] != 0:
					result['section_level'] += ['difficult']
				result['duration'] = result['questions_level_info'][3]*2
				result['no_questions'] = result['questions_level_info'][3]
				result['correct_grade'] = 1
				result['incorrect_grade'] = 0
				result['q_type'] = 'mcq'
				result['sectionname'] = 'Section#1'
				result = [result]		# Must be a list
			else:
				result = get_questions_format(user_id, subcategory_id)
		else:
			result = get_questions_format(user_id)
		return Response(result, status = status.HTTP_200_OK)
		# quiz = Quiz.objects.filter(user=userid).order_by('id')[0]
		# quizzes = get_questions_format(quiz, Category, SubCategory, Question, Answer)
		# return Response(quizzes, status = status.HTTP_200_OK)
	except SubCategory.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Questions not found'}, status=status.HTTP_404_NOT_FOUND)		


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
		print request.query_params.get('questionFormat')
		if request.query_params.get('questionFormat'):
			quizzes = get_questions_format(user_id, subcategory_id, True)
		else:
			quizzes = get_questions_format(user_id, subcategory_id)
		print quizzes
	except SubCategory.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Questions not found'}, status = status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def filtered_questions(request, userid, categoryid, subcategoryid):
	print userid, categoryid, subcategoryid

@api_view(['GET', 'PUT', 'DELETE'])
def question_operations(request, userid, questionid):
	"""
	Get a single question or update.
	"""
	try:
		question = Question.objects.get(id = questionid)
	except Question.DoesNotExist:
		return Response({'errors': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
	if request.method == 'GET':
		questionserializer = QuestionSerializer(question, many = False)
		answers = Answer.objects.filter(question = question)
		answerserializer = AnswerSerializer(answers, many = True)
		result = dict(questionserializer.data)
		result.update( { 'options' : answerserializer.data } )
		result['sub_category'] = question.sub_category.sub_category_name
		return Response({ 'question' : result }, status = status.HTTP_200_OK)

	elif request.method == 'PUT':
		request.data.update({'sub_category': question.sub_category.id})
		serializer = QuestionSerializer(question, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status = status.HTTP_200_OK)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	elif request.method == 'DELETE':
		try:
			question.delete()
			return Response(status=status.HTTP_204_NO_CONTENT)
		except Exception as e:
			print e.args
			return Response({'errors': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)



@api_view(['GET', 'PUT'])
def answers_operations(request, userid, questionid):
	"""
	Get answers to a question or update.
	"""
	try:
		question = Question.objects.get(pk = questionid)
		answers = Answer.objects.filter(question = question)
	except Question.DoesNotExist:
		return Response({'errors': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
	if request.method == 'GET':
		answerserializer = AnswerSerializer(answers, many = True)
		result = { 'content' : question.content }
		result['sub_category'] = question.sub_category.sub_category_name
		result['options'] = answerserializer.data
		return Response({ 'answers' : result }, status = status.HTTP_200_OK)

	elif request.method == 'PUT':
		optionsContent = dict(request.data.get('optionsContent'))
		for answer in answers:
			d = { 'correct' : False, 'content' : optionsContent[str(answer.id)], 'question' : question.id }
			if request.data.get('correctOption') == str(answer.id):
				print answer.id
				d['correct'] = True
			serializer = AnswerSerializer(answer,data=d)
			if serializer.is_valid():
				serializer.save()
		return Response({}, status = status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes((AllowAny,))
def download_xls_file(request):
	from QnA.services.utility import MCQ_FILE_ROWS
	from pyexcel_xls import save_data
	from collections import OrderedDict

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
	_quiz_obj =  sub_category.category.quiz
	data.update({"Sheet 1": [MCQ_FILE_ROWS,[_quiz_obj.title, sub_category.category.category_name, sub_category_name]]})
	save_data(sub_category_name+"_file.xls", data)
	
	from django.http import FileResponse
	response = FileResponse(open(sub_category_name+"_file.xls", 'rb'))
	try:
		import os
		os.remove(sub_category_name+"_file.xls")
	except OSError:
		pass
	return response
