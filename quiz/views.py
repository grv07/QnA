from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from models import Quiz
from serializer import QuizSerializer
# from QnA.services.JSONResponse import JSONResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Quiz
from rest_framework.decorators import api_view



@api_view(['GET', 'POST'])
def quiz_list(request):
	"""
	List all code Quiz, or create a new quiz.
	
	"""
	if request.method == 'GET':
		quizzes = Quiz.objects.all()
		quizserializer = QuizSerializer(quizzes, many = True)
		return Response(quizserializer.data)


	elif request.method == 'POST':
		serializer = QuizSerializer(data = request.data)
		if serializer.is_valid():
			serializer.save()
			return JSONResponse(serializer.data, status = 201)
		return JSONResponse(serializer.errors, status = 400)
# Create your views here.
