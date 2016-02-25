from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework import status

from QnA.services import answer_engine
from quiz.models import Quiz
from models import MCQuestion
from serializer import MCQuestionSerializer

#>>>>>>>>>>>>>> MCQ question <<<<<<<<<<<<<<<<<<<#

@api_view(['POST'])
def save_XLS_to_MCQ(request):
	# Touch on your risk ...
	'''
	{u'sub_category': u'5', u'answer_order': u'random', u'explanation': u'eeeeeeeeee',
	 u'level': u'easy', u'correctoption': u'1', u'content': u'eeeeeeeeee', 
	 u'optioncontent': {u'1': u'eeeeeeeeee', u'2': u'eeeeeeeeeee'}}
	'''
	from pyexcel_xls import get_data
	import collections
	from quiz.models import Category, SubCategory

	# _level_dict = {'medium': 'M', 'easy': 'E', 'hard': 'H'}
	f = request.data['figure']

	with open('mcq_read_now.xls', 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)

	data = get_data("mcq_read_now.xls")
	total_entries = len(data)

	temp_data = data[0]
	_dict_mcq_keys = ['category', 'sub_category', 'level', 'explanation', 'option_display_order_random', 'correctoption', 'content']
	# This dict contains raw-way data with specified keys from temp_data or xls keys
	data_dict = collections.OrderedDict({})
	# _quiz_id = None
	category_dict = {}
	sub_category_dict = {}
	option_check = ['option1', 'option2', 'option3', 'option4', 'option5', 'option6']
	

	data_list = []
	for row_name in _dict_mcq_keys:
		data_dict.update({row_name : ''})
	
	# Create empty value dict. for each mcq entry ..
	for i, list_data in enumerate(data[1:]):
		data_list.append(data_dict.copy())
		optioncontent = {}
		for j, mcq_data in enumerate(list_data):
			if temp_data[j] == 'correctoption':
				data_list[i][temp_data[j]] = str(mcq_data)
			# elif temp_data[j] == 'quiz':
			# 	# print str(mcq_data)
			# 	_quiz_id = [Quiz.objects.get(title = str(mcq_data)).id]
			# 	data_list[i][temp_data[j]] = _quiz_id

			# Check if row is for option then create a dict_ of options and add it on optioncontent ....
			elif temp_data[j] in option_check:
				if mcq_data:
					optioncontent[option_check.index(temp_data[j])+1] = str(mcq_data)
					data_list[i]['optioncontent'] =  optioncontent
				# data_list[i]['optioncontent'] = optioncontent[option_check.index(temp_data[j])] = str(mcq_data)

			#Check first for // key(category name) value(category id) // pair in dict. if not exist then call query.  
			elif temp_data[j] == 'category':
				if category_dict.has_key(mcq_data):
					category_id = category_dict.get(mcq_data)
				else:
					category_id = Category.objects.get(category_name = mcq_data).id
					category_dict[mcq_data] = category_id
				data_list[i][temp_data[j]] = str(category_id)

			#Check first for // key(sub_category name) value(sub_category id) // pair in dict. if not exist then call query.
			elif temp_data[j] == 'sub_category':
				if sub_category_dict.has_key(mcq_data):
					sub_category_id = sub_category_dict.get(mcq_data)
				else:
					sub_category_id = SubCategory.objects.get(sub_category_name = mcq_data).id
					sub_category_dict[mcq_data] = sub_category_id
				data_list[i][temp_data[j]] = str(sub_category_id)
			
			else:
				data_list[i][temp_data[j]] = str(mcq_data)	
	print data_list		
	# DONE ........
	 
	return create_mcq(request, data_list)
	# return Response({'msg' : data_list}, status = status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((AllowAny,))
def create_mcq(request, xls_read_data = None):
	"""
	Create a MCQuestion. 
	"""
	if xls_read_data:
		last_resp = []
		for data in xls_read_data:
			serializer = MCQuestionSerializer(data = data)
			options_data = data.get('optioncontent', None)
			correct_option = data.get('correctoption', None)
			correct_option = int(float(correct_option))
			last_resp.append(save_mcq_question(request, serializer, options_data, correct_option))
		else:
			if last_resp[::-1][0].status_code == 200:
				try:
					import os
					os.remove('mcq_read_now.xls')
				except OSError:
					pass
				return Response( {'msg': 'All questions upload successfully .',} ,status = last_resp[::-1][0].status_code)	
			else:
				return Response( {'msg': 'All questions not uploaded successfully .',} ,status = last_resp[::-1][0].status_code)
	else:
		data = {}
		data['content'] = request.data['data[content]']
		data['explanation'] = request.data['data[explanation]']
		data['correctoption'] = request.data['data[correctoption]']
		data['level'] = request.data['data[level]']
		data['sub_category'] = request.data['data[sub_category]']
		data['que_type'] = request.data['data[que_type]']
		data['answer_order'] = request.data['data[answer_order]']		
		data['figure'] = request.data.get('figure', None)
		data['options_data'] = {}
		for i in '123456789':
			if request.data.get('data[optioncontent]['+i+']', None):
				data['options_data'][i] = request.data.get('data[optioncontent]['+str(i)+']')
		serializer = MCQuestionSerializer(data = data)
		return save_mcq_question(request, serializer, data['options_data'], data['correctoption'])


@api_view(['POST'])
@permission_classes((AllowAny,))
def save_mcq_question(request, serializer, options_data, correct_option):
	options = []
	if serializer.is_valid():
		if options_data:
			for optionid, content in options_data.items():
				c = { 'content' : str(content), 'correct' : False }
				if int(optionid) == int(correct_option):
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
