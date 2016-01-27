from django.http import HttpResponse

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

from serializer import QuizSerializer
from QnA.services.JSONResponse import JSONResponse
from django.views.decorators.csrf import csrf_exempt

def home(request):
	return JSONResponse({})	

@csrf_exempt
def quiz_list(request):
	"""
	List all code Quiz, or create a new quiz.
	
	"""
	if request.method == 'GET':
		quiz = Quiz.objects.all()
		serializer = QuizSerializer(snippets, many = True)
		return JSONResponse(serializer.data)

	elif request.method == 'POST':
		print 'under POST method .........'
		# data = JSONParser().parse(request) # Default code ..
		serializer = QuizSerializer(data = request.POST)
		if serializer.is_valid():
			serializer.save()
			return JSONResponse(serializer.data, status = 201)
		return JSONResponse(serializer.errors, status = 400)
# Create your views here.
