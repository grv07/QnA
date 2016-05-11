from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializer import ObjectiveQuestionSerializer
from rest_framework import status
from QnA.services.constants import BLANK_HTML, OBJECTIVE_FILE_COLS
from QnA.services.utility import check_for_float

@api_view(['POST'])
def save_XLS_to_OBJECTIVE(request):
	from pyexcel_xls import get_data
	import collections
	from quiz.models import SubCategory

	# _level_dict = {'medium': 'M', 'easy': 'E', 'hard': 'H'}
	f = request.data['figure']

	with open('mcq_read_now.xls', 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)

	data = get_data("mcq_read_now.xls")
	total_entries = len(data)
	temp_data = data[0]
	# Check if columns of xls file provided are not tampered/changed.
	if temp_data == OBJECTIVE_FILE_COLS:
		try:
			# This dict contains raw-way data with specified keys from temp_data or xls keys
			# data_dict = collections.OrderedDict({})
			correct_serializers_list = []	
			d = {}
			for i in data[1:]:
				if BLANK_HTML in i[4]:
					if not d.has_key(i[0]):
						try:
							d[i[0]] = SubCategory.objects.get(sub_category_name=i[0])
						except SubCategory.DoesNotExist as e:
							return Response({ "errors" : "Wrong sub-category specified." } , status = status.HTTP_400_BAD_REQUEST)

					temp_dict = { 'sub_category':d[i[0]].id, 'level':i[1], 'explanation':'', 'correct':'', 'content':i[4], 'que_type': 'objective' }
					temp_dict['explanation'] = str(i[2])
					temp_dict['correct'] = str(i[3])
					serializer = ObjectiveQuestionSerializer(data = temp_dict)
					if serializer.is_valid():
						correct_serializers_list.append(serializer)
					else:
						return Response({ "errors" : "There is some error while saving your questions. Correct the format." } , status = status.HTTP_400_BAD_REQUEST)
				else:
					return Response({ "errors" : "There is some error while saving your questions. Correct the format." } , status = status.HTTP_400_BAD_REQUEST)
			if len(correct_serializers_list) == total_entries - 1:
				for serializer in correct_serializers_list:
					serializer.save()
			return Response({}, status = status.HTTP_200_OK)
		except Exception as e:
			print e.args
	return Response({ "errors" : "There is some error while saving your questions. Correct the format." } , status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_objective(request):
	try:
		if BLANK_HTML in request.data['data[content]']:
			data = {}
			data['content'] = request.data['data[content]']
			data['explanation'] = request.data['data[explanation]']
			data['correct'] = request.data['data[correct]']
			data['level'] = request.data['data[level]']
			data['sub_category'] = request.data['data[sub_category]']
			data['que_type'] = request.data['data[que_type]']
			data['figure'] = request.data.get('figure', None)
			serializer = ObjectiveQuestionSerializer(data = data)
			if serializer.is_valid():
				serializer.save()
				return Response(serializer.data, status = status.HTTP_200_OK)
			else:
				return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
		else:
			return Response({ "content" : ["No blank field present.Please add one."] } , status = status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		print e.args
		return Response({ "errors" : "Unable to create this question. Server error." }, status = status.HTTP_400_BAD_REQUEST)