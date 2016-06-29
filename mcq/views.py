from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from rest_framework import status

from QnA.services import answer_engine
from quiz.models import Quiz, Category, SubCategory
from models import MCQuestion
from serializer import MCQuestionSerializer
from QnA.services.constants import BLANK_HTML, MAX_OPTIONS
from QnA.services.utility import verify_user_hash, ascii_safe
from pyexcel_xls import get_data
import ast
from collections import defaultdict, OrderedDict

import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
def save_XLS_to_MCQ(request):
	if verify_user_hash(request.data.get('user'), request.data.get('hash')):
		logger.info('under mcq.save_XLS_to_MCQ')
		'''
		{u'sub_category': u'5', u'answer_order': u'random', u'explanation': u'eeeeeeeeee',
		 u'level': u'easy', u'correctoption': u'1', u'content': u'eeeeeeeeee', 
		 u'optioncontent': {u'1': u'eeeeeeeeee', u'2': u'eeeeeeeeeee'}}
		'''
		# _level_dict = {'medium': 'M', 'easy': 'E', 'hard': 'H'}
		f = request.data['figure']

		with open('mcq_read_now.xls', 'wb+') as destination:
			for chunk in f.chunks():
				destination.write(chunk)

		data = get_data("mcq_read_now.xls")
		total_entries = len(data)

		temp_data = data[0]
		_dict_mcq_keys = ['category', 'sub_category', 'que_type', 'level', 'explanation', 'option_display_order_random', 'correctoption', 'content', 'ideal_time', 'problem_type']
		# This dict contains raw-way data with specified keys from temp_data or xls keys
		data_dict = OrderedDict({})
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
				mcq_data = ascii_safe(mcq_data)
				if temp_data[j] == 'correctoption':
					data_list[i][temp_data[j]] = str(mcq_data)
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
						try:
							category_id = Category.objects.get(category_name = mcq_data).id
						except Exception as e:
							logger.error('under mcq.save_XLS_to_MCQ '+str(e.args))
							category_id = None
						category_dict[mcq_data] = category_id
					data_list[i][temp_data[j]] = str(category_id)

				#Check first for // key(sub_category name) value(sub_category id) // pair in dict. if not exist then call query.
				elif temp_data[j] == 'sub_category':
					try:
						if sub_category_dict.has_key(mcq_data):
							sub_category_id = sub_category_dict.get(mcq_data)
						else:
							sub_category_id = SubCategory.objects.get(sub_category_name = mcq_data).id
							sub_category_dict[mcq_data] = sub_category_id
						data_list[i][temp_data[j]] = str(sub_category_id)
					except SubCategory.DoesNotExist as e:
						logger.error('under mcq.save_XLS_to_MCQ wrong subcategory specified '+str(e.args))
						return Response({ "errors" : "Wrong sub-category specified." } , status = status.HTTP_400_BAD_REQUEST)				
				else:
					data_list[i][temp_data[j]] = str(mcq_data)

		# DONE ........
		 
		return create_mcq(request, data_list)
		# return Response({'msg' : data_list}, status = status.HTTP_200_OK)
	else:
		logger.error('under quiz.save_XLS_to_MCQ wrong hash')
		return Response({'errors': 'Corrupted User.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def create_mcq(request, xls_read_data = None):
	"""
	Create a MCQuestion. 
	"""
	logger.info('under mcq.create_mcq xls_read_data = '+str(xls_read_data))
	if xls_read_data:
		last_resp = []
		for data in xls_read_data:
			data['que_type'] = 'mcq'
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
				except OSError as ose:
					logger.error('under mcq.create_mcq '+str(ose.args))
				return Response( {'msg': 'All questions upload successfully.',} ,status = last_resp[::-1][0].status_code)	
			else:
				logger.error('under mcq.create_mcq not uploaded successfully')
				return Response( {'msg': 'All questions not uploaded successfully.',} ,status = last_resp[::-1][0].status_code)
	else:
		if verify_user_hash(request.data.get('user'), request.data.get('hash')):
			if request.data.get('correctoption'):
				data = {}
				options_dict = ast.literal_eval((request.data.get('optioncontent')))
				data['options_data'] = options_dict if len(options_dict) <= MAX_OPTIONS else options_dict[:MAX_OPTIONS]
				serializer = MCQuestionSerializer(data = request.data)
				return save_mcq_question(request, serializer, data['options_data'], request.data.get('correctoption'))
			else:
				logger.error('under mcq.create_mcq correct option not provided')
				return Response({'optionerrors' : 'Correct answer must be provided.'}, status = status.HTTP_400_BAD_REQUEST)
		logger.error('under quiz.create_mcq wrong hash')
		return Response({'errors': 'Corrupted User.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def save_mcq_question(request, serializer, options_data, correct_option):
	logger.info('under mcq.save_mcq_question')
	options = []
	if serializer.is_valid():
		if options_data:
			for optionid, content in options_data.items():
				c = { 'content' : str(content), 'correct' : False }
				if int(optionid) == int(correct_option):
					c['correct'] = True
				options.append(c)
			mcq = serializer.save()			
			isAnswerSaved, errors = answer_engine.create_mcq_answer(mcq, options)
			if not isAnswerSaved:
				logger.error('under mcq.save_mcq_question error answer not saved '+str(errors))
				return Response(errors, status = status.HTTP_400_BAD_REQUEST)
			else:
				return Response(serializer.data, status = status.HTTP_200_OK)
		else:
			logger.error('under mcq.save_mcq_question correct option not provided')
			return Response({'optionerrors' : 'Options must be provided with correct answer.'}, status = status.HTTP_400_BAD_REQUEST)
	logger.error('under mcq.save_mcq_question error '+str(serializer.errors))
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
		print e.args
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
		mcq_question_list = MCQuestion.objects.all()
		data = defaultdict(list)
		serializer = MCQuestionSerializer(mcq_question_list, many = True)
		return Response(serializer.data, status = status.HTTP_200_OK)
	except MCQuestion.DoesNotExist as e:
		return Response({'msg': 'Question does not exist'}, status = status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		return Response({'msg': 'Something went terrible wrong'}, status = status.HTTP_400_BAD_REQUEST)

def generate_result(request):
	print 'generate result here ... ...'