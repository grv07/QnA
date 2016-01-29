from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from QnA.services import answer_engine
from models import MCQuestion
from serializer import MCQuestionSerializer

#>>>>>>>>>>>>>> MCQ question <<<<<<<<<<<<<<<<<<<#

@api_view(['POST'])
def create_mcq(request):
	"""
	Create a MCQuestion ... 
	"""
	serializer = MCQuestionSerializer(data = request.data)
	if serializer.is_valid():
		mcq = serializer.save()
		answer_engine.create_answer
		
		options = [{'content':'text','correct':True},
				{'content':'text','correct':False},{'content':'text','correct':False}]

		if answer_engine.create_answer(mcq, options):
				print 'Save Answer successfully'
		return Response(serializer.data, status = status.HTTP_200_OK)
	return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)	


@api_view(['GET','POST'])
def get_mcq_detail(request, pk):
	"""
	Get a MCQuestion ... 
	"""
	try:
		mcq_question = MCQuestion.objects.get(pk = pk)
		serializer = MCQuestionSerializer(mcq_question)
		return Response(serializer.data, status = status.HTTP_200_OK)
	except MCQuestion.DoesNotExist as e:
		return Response({'msg': 'Question does not exist'}, status = status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		return Response({'msg': 'Something went terrible wrong'}, status = status.HTTP_400_BAD_REQUEST)
	

@api_view(['DELETE'])
def del_mcq(request, pk):
	"""
	DELETE a MCQuestion ... 
	"""
	try:
		mcq_question = MCQuestion.objects.get(pk = pk)
		mcq_question.delete()
		return Response({'msg':'success'}, status = status.HTTP_200_OK)
	except MCQuestion.DoesNotExist as e:
		return Response({'msg': 'Question does not exist'}, status = status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		return Response({'msg': 'Something went terrible wrong'}, status = status.HTTP_400_BAD_REQUEST)
	

@api_view(['GET'])
def all_mcq(request):
	"""	
	List of all MCQuestion's.
	"""
	try:
		mcq_question_list = MCQuestion.objects.all()
		serializer = MCQuestionSerializer(mcq_question_list, many = True)
		return Response(serializer.data, status = status.HTTP_200_OK)
	except MCQuestion.DoesNotExist as e:
		return Response({'msg': 'Question does not exist'}, status = status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		return Response({'msg': 'Something went terrible wrong'}, status = status.HTTP_400_BAD_REQUEST)


#>>>>>>>>>>>>>> MCQ Answer<<<<<<<<<<<<<<<<<<<#


# Create your views here.
