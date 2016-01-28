from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from models import Quiz, Category
from serializer import QuizSerializer, CategorySerializer



# Quiz Base functions
@api_view(['GET', 'POST'])
def quiz_list(request, format = None):
	"""
	List all code Quiz, or create a new quiz.	
	"""
	if request.method == 'GET':
		quiz_list = Quiz.objects.all()
		serializer = QuizSerializer(quiz_list, many = True)
		return Response(serializer.data, status = status.HTTP_200_OK)
	return Response(status = status.HTTP_400_BAD_REQUEST)	


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
	# if request.method == 'POST':
	serializer = QuizSerializer(data = request.POST)
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
		return Response({'msg': 'Quiz not found'}, status=status.HTTP_404_NOT_FOUND)

	if request.method == 'GET':
		serializer = QuizSerializer(quiz)
		return Response(serializer.data)

	elif request.method == 'DELETE':
		quiz.delete()
		return Response(status=status.HTTP_204_NO_CONTENT)

#Quiz base Functions end

#>>>>>>>>>>>>>>>>>>>>> Category Base Functions Start <<<<<<<<<<<<<<<<<<<#

@api_view(['POST'])
def create_category(request):
	"""
	List all code Quiz, or create a new quiz.

	"""
	serializer = CategorySerializer(data = request.POST)
	if serializer.is_valid():
		serializer.save()
		return Response(serializer.data, status = status.HTTP_200_OK)
	return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

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

@api_view(['GET', 'POST'])
def category_list(request, pk ,format = None):
	"""
	List all category.
	
	"""
	category_list = Category.objects.all()
	serializer = CategorySerializer(category_list, many = True)
	
	return Response(serializer.data, status = status.HTTP_200_OK)