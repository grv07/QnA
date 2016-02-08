from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth.models import User

from .models import Quiz, Category, SubCategory, Question
from mcq.models import Answer
from mcq.serializer import AnswerSerializer
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
def all_questions(request, userid):
	"""
	Either get all questions under each quiz and category or get questions under specifc quiz and category.
	"""
	try:
		quizzes = []
		questions_level_info = [0 , 0, 0, 0] # [Easy, Medium ,Hard, Total]
		for q in Quiz.objects.filter(user=userid):
			qz = {}
			qz['title'] = q.title
			qz['categories'] = []
			for c in Category.objects.filter(quiz=q):
				ca = {}
				ca['category'] = c.category
				ca['subcategories'] = []
				for sc in SubCategory.objects.filter(category=c):
					sca = {}
					sca['subcategory'] = sc.sub_category_name
					sca['questions'] = []
					for question in Question.objects.filter(sub_category=sc):
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
						sca['questions'].append(d)
					ca['subcategories'].append(sca)
				qz['categories'].append(ca)
			quizzes.append(qz)
		questions_level_info[3] = sum(questions_level_info)
		quizzes.insert(0,{'questions_level_info' : questions_level_info})
		return Response(quizzes, status = status.HTTP_200_OK)
	except SubCategory.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Questions not found'}, status=status.HTTP_404_NOT_FOUND)		


@api_view(['GET', 'PUT'])
def get_or_update_question(request, userid, questionid):
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
		result['category'] = question.category.category
		result['sub_category'] = question.sub_category.sub_category_name
		return Response({ 'question' : result }, status = status.HTTP_200_OK)

	elif request.method == 'PUT':
		request.data.update({ 'category': question.category.id, 'sub_category': question.sub_category.id})
		serializer = QuestionSerializer(question, data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status = status.HTTP_200_OK)
		print serializer.errors
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
def get_or_update_answers(request, userid, questionid):
	"""
	Get answers to a question or update.
	"""
	try:
		question = Question.objects.get(id = questionid)
	except Question.DoesNotExist:
		return Response({'errors': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)
	if request.method == 'GET':
		answers = Answer.objects.filter(question = question)
		answerserializer = AnswerSerializer(answers, many = True)
		result = { 'content' : question.content }
		result['category'] = question.category.category
		result['sub_category'] = question.sub_category.sub_category_name
		result['options'] = answerserializer.data
		return Response({ 'answers' : result }, status = status.HTTP_200_OK)

	elif request.method == 'PUT':
		print request.data
		# serializer = QuestionSerializer(question, data=request.data)
		# if serializer.is_valid():
		# 	serializer.save()
		# 	return Response(serializer.data, status = status.HTTP_200_OK)
		# print serializer.errors
		# return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)	
