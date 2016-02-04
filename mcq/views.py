from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework import status

from QnA.services import answer_engine
from models import MCQuestion
from serializer import MCQuestionSerializer

#>>>>>>>>>>>>>> MCQ question <<<<<<<<<<<<<<<<<<<#



@api_view(['POST'])
@permission_classes((AllowAny,))
def create_mcq(request):
	"""
	Create a MCQuestion ... 
	"""
	serializer = MCQuestionSerializer(data = request.data)
	options = []
	options_data = request.data.get('optioncontent', None)
	correct_option = request.data.get('correctoption', None)
	if serializer.is_valid():
		if options_data and options_data:
			for optionid, content in options_data.items():
				c = { 'content' : str(content), 'correct' : False }
				if optionid == correct_option:
					c['correct'] = True
				options.append(c)
			mcq = serializer.save()
			isAnswerSaved, errors = answer_engine.create_answer(mcq, options)
			if not isAnswerSaved:
				return Response(errors, status = status.HTTP_400_BAD_REQUEST)
			else:
				return Response(serializer.data, status = status.HTTP_200_OK)
		else:
			return Response({'optionerrors' : 'Options must be provided with correct answer.'}, status = status.HTTP_400_BAD_REQUEST)
	return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)	


def save_XLS_to_MCQ(request):
	pass

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
@permission_classes((AllowAny,))
def all_mcq(request):
	"""	
	List of all MCQuestion's.
	"""
	try:
		from collections import defaultdict
		mcq_question_list = MCQuestion.objects.all()
		data = defaultdict(list)
		serializer = MCQuestionSerializer(mcq_question_list, many = True)
		return Response(serializer.data, status = status.HTTP_200_OK)
	except MCQuestion.DoesNotExist as e:
		return Response({'msg': 'Question does not exist'}, status = status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		return Response({'msg': 'Something went terrible wrong'}, status = status.HTTP_400_BAD_REQUEST)

#>>>>>>>>>>>>>> MCQ Answer<<<<<<<<<<<<<<<<<<<#


# Create your views here.
