from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializer import ObjectiveQuestionSerializer
from rest_framework import status

@api_view(['POST'])
def create_objective(request):
	print request.data
	try:
		print request.data
		serializer = ObjectiveQuestionSerializer(data = request.data)
		if serializer.is_valid():
			# serializer.save()
			print 'jjjj'
			return Response(serializer.data, status = status.HTTP_200_OK)
		return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		print e.args
		return Response({ "errors" : "Unable to create this question" }, status = status.HTTP_400_BAD_REQUEST)