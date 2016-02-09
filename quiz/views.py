from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth.models import User

from .models import Quiz, Category, SubCategory, Question
from mcq.models import Answer
from serializer import QuizSerializer, CategorySerializer, SubCategorySerializer, QuestionSerializer


# >>>>>>>>>>>>>>>>>>>>>>>  Quiz Base functions  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

@api_view(['GET'])
def quiz_list(request, userid, format = None):
	"""
	Either get a single quiz or all.
	"""
	try:
		quiz_list = Quiz.objects.filter(user=userid).order_by('id')
		serializer = QuizSerializer(quiz_list, many = True)
		return Response(serializer.data, status = status.HTTP_200_OK)
	except Quiz.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET', 'POST'])
def get_quiz(request, pk ,format = None):
	"""
	Quiz detail with pk.
	
	"""
	try:
		quiz = Quiz.objects.get(pk = pk)
	except Quiz.DoesNotExist as e:
		return Response({'msg': 'Quiz not found'}, status = status.HTTP_404_NOT_FOUND)

	serializer = QuizSerializer(quiz)
	return Response(serializer.data, status = status.HTTP_200_OK)


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
def category_list(request, userid, quizid, format = None):
	"""
	Either get a single quiz or all.
	"""
	try:
		categories = []
		if quizid == 'all':
			for quiz in Quiz.objects.filter(user=userid).order_by('id'):
				for category in Category.objects.filter(quiz=quiz):
					categories.append(category)
			serializer = CategorySerializer(categories, many = True)
		else:
			if quizid.isnumeric():
				for quiz in Quiz.objects.filter(id=quizid, user=userid).order_by('id'):
					categories = Category.objects.filter(quiz=quiz)
				serializer = CategorySerializer(categories, many = True)
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
def get_subcategory(request, userid, quizid, categoryid, format = None):
	"""
	Either get all subcategories under each quiz and category or get subcategories under specifc quiz and category.
	"""
	try:
		subcategories = []
		if quizid == 'all' and categoryid == 'all':
			for quiz in Quiz.objects.filter(user=userid):
				for category in Category.objects.filter(quiz=quiz):
					for subcategory in SubCategory.objects.filter(category=category):
						subcategories.append(subcategory)
			serializer = SubCategorySerializer(subcategories, many = True)
		else:
			if quizid.isnumeric() and categoryid.isnumeric():
				subcategory = SubCategory.objects.get(category=Category.objects.get(id=categoryid, quiz=Quiz.objects.filter(id=quizid, user=userid)))
				serializer = SubCategorySerializer(subcategory, many = False)
			else:
				return Response({'errors': 'Wrong URL passed.'}, status=status.HTTP_404_NOT_FOUND)
		return Response(serializer.data, status = status.HTTP_200_OK)
	except SubCategory.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Sub-category not found'}, status=status.HTTP_404_NOT_FOUND)


#>>>>>>>>>>>>>>>>>>>>> Question Base Functions Start <<<<<<<<<<<<<<<<<<<#

@api_view(['GET'])
def all_questions(request, userid, quizid, categoryid, subcategoryid):
	"""
	Either get all questions under each quiz and category or get questions under specifc quiz and category.
	Format : 
	"""
	try:
		quizzes = {}
		questions_level_info = [0 , 0, 0, 0] # [Easy, Medium ,Hard, Total]
		if quizid == 'all' and categoryid == 'all' and subcategoryid == 'all':
			for quiz in Quiz.objects.filter(user=userid):
				quizzes[quiz.title] = {}
				categories = {}
				for category in Category.objects.filter(quiz=quiz):
					categories[category.category_name] = {}
					subcategories = {}
					for subcategory in SubCategory.objects.filter(category=category):
						subcategories[subcategory.sub_category_name] = {}
						questions = []
						for question in Question.objects.filter(sub_category=subcategory):
							d = {
								'id' : question.id,
								'level' : question.level,
								'content' : question.content,
								'options'  : [{ 'id' : answer.id, 'content' : answer.content, 'correct' : answer.correct } for answer in Answer.objects.filter(question=question)]
							}
							if question.level == 'easy':
								questions_level_info[0] = questions_level_info[0] + 1
							elif question.level == 'medium':
								questions_level_info[1] = questions_level_info[1] + 1
							else:
								questions_level_info[2] = questions_level_info[2] + 1
							questions.append(d)
						subcategories[subcategory.sub_category_name] = questions
					categories[category.category_name].update(subcategories)
				quizzes[quiz.title].update(categories)
			questions_level_info[3] = sum(questions_level_info)
			quizzes['questionsLevelInfo'] = questions_level_info
			return Response(quizzes, status = status.HTTP_200_OK)
		else:
			# if quizid.isnumeric() and categoryid.isnumeric():
			# 	subcategory = SubCategory.objects.get(category=Category.objects.get(id=categoryid, quiz=Quiz.objects.filter(id=quizid, user=userid)))
			# 	serializer = SubCategorySerializer(subcategory, many = False)
			# else:
			return Response({'errors': 'Wrong URL passed.'}, status=status.HTTP_404_NOT_FOUND)
		# return Response(serializer.data, status = status.HTTP_200_OK)
	except SubCategory.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Questions not found'}, status=status.HTTP_404_NOT_FOUND)		

@api_view(['POST'])
@permission_classes((AllowAny,))
def download_xls_file(request):
	from QnA.services.utility import MCQ_FILE_ROWS
	from pyexcel_xls import save_data
	import collections

	que_type = request.data.get('que_type')	
	sub_category_id =  request.data.get('sub_cat_info').split('>>')[0]
	sub_category_name =  request.data.get('sub_cat_info').split('>>')[1]
	
	try:
		sub_category = SubCategory.objects.get(pk = sub_category_id,sub_category_name = sub_category_name)
	except SubCategory.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Questions not found'}, status=status.HTTP_404_NOT_FOUND)
	data = collections.OrderedDict() # from collections import OrderedDict
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