from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework import status

from QnA.services import answer_engine
from models import MCQuestion
from serializer import MCQuestionSerializer

#>>>>>>>>>>>>>> MCQ question <<<<<<<<<<<<<<<<<<<#

@api_view(['GET'])
@permission_classes((AllowAny,))
def save_XLS_to_MCQ(request):
	from pyexcel_xls import get_data
	data = get_data("mcq_model.xls")

	# row_names =  data[0]
	total_entries = len(data)
	import collections	
	# temp_data = ['quiz','category', 'sub_category','level','explanation','','','','','','','','','','']
	temp_data = data[0]
	# This dict contains raw-way data with specified keys from temp_data or xls keys
	data_dict = collections.OrderedDict({})
	
	data_list = []
	for row_name in temp_data:
		data_dict.update({row_name : ''})
	
	# Create empty value dict. for each mcq entry ..
	for i, list_data in enumerate(data[1:]):
		data_list.append(data_dict.copy())
		for j, mcq_data in enumerate(list_data):
			data_list[i][temp_data[j]] = str(mcq_data)
	# DONE ........
	
	print data_list
	
	return Response({'msg' : data_list}, status = status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
def create_mcq(request):
	"""
	Create a MCQuestion ... 
	"""
	serializer = MCQuestionSerializer(data = request.data)
	print serializer
	options = []
	options_data = request.data.get('optioncontent', None)
	correct_option = request.data.get('correctoption', None)

	print options_data
	print correct_option
	
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
