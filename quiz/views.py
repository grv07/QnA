from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth.models import User

from .models import Quiz, Category, SubCategory, Question
from serializer import QuizSerializer, CategorySerializer, SubCategorySerializer, QuestionSerializer


# >>>>>>>>>>>>>>>>>>>>>>>  Quiz Base functions  <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<#

@api_view(['GET'])
def quiz_list(request, userid, format = None):
	"""
	Either get a single quiz or all.
	"""
	try:
<<<<<<< HEAD
		quiz_list = Quiz.objects.filter(user=userid).order_by('id')
		serializer = QuizSerializer(quiz_list, many = True)
		
=======
		if quizid == 'all':
			quizzes = Quiz.objects.filter(user=userid).order_by('id')
			serializer = QuizSerializer(quizzes, many = True)
		else:
			if quizid.isnumeric():
				quiz = Quiz.objects.get(id = quizid, user=userid)
				serializer = QuizSerializer(quiz, many = False)
			else:
				return Response({'errors': 'Wrong URL passed.'}, status=status.HTTP_404_NOT_FOUND)
>>>>>>> 7c862d80211bc9be59bc24825cf5f93c4174bc22
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
	Either get a single subcategory or all.
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
def all_questions(request):
	"""
	List all code Quiz, or create a new quiz.

	"""
	# user =  User.objects.get(pk = 1)
	# quizs = Quiz.objects.filter(user = user)
	# questions = []
	# for quiz in quizs:
	# 	categories = Category.objects.filter(quiz = quiz)
	# 	for category in categories:
	# 		for sub_category in SubCategory.objects.filter(category = category):
	# 			print sub_category

		# print categories
	# print categories
	# for categories
	# serializer = QuizSerializer(quiz)
	# serializer = QuestionSerializer(questions)
	# if serializer.is_valid():
		# serializer.save()
	# return Response(serializer.data, status = status.HTTP_200_OK)
	# return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
