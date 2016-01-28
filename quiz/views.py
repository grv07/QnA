from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from serializer import QuizSerializer
from QnA.services.JSONResponse import JSONResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Quiz
from rest_framework.decorators import api_view

def home(request):
	return JSONResponse({})	

@csrf_exempt
@api_view(['GET', 'POST'])
def quiz_list(request):
	"""
	List all code Quiz, or create a new quiz.
	
	"""
	if request.method == 'GET':
		quizzes = Quiz.objects.all()
		quizserializer = QuizSerializer(quizzes, many = True)
		return JSONResponse(quizserializer.data)

	elif request.method == 'POST':
		# response.headers['Access-Control-Allow-Origin'] = '*'
		# response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS, PUT'
		# response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
		print 'under POST method .........'
		# data = JSONParser().parse(request) # Default code ..
		quizserializer = QuizSerializer(data = request.data)
		print request.data
		print quizserializer.is_valid()
		if quizserializer.is_valid():
			quizserializer.save()
			return JSONResponse(quizserializer.data, status = 201)
		print quizserializer.errors
		return JSONResponse(quizserializer.errors, status = 400)
# Create your views here.
