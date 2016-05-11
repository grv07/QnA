from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.decorators import authentication_classes

from QnA.services.constants import MAX_OPTIONS
from QnA.services.answer_engine import create_comprehension_answer
from QnA.services.utility import get_comprehension_questions_format


from quiz.models import Question
from quiz.serializer import QuestionSerializer
from .serializer import ComprehensionSerializer, ComprehensionQuestionSerializer, ComprehensionAnswerSerializer
from .models import Comprehension, ComprehensionAnswer, ComprehensionQuestion

import os
# Create your views here.


@api_view(['POST'])
def create_comprehension(request):
	try:
		data = {}
		data['content'] = request.data['data[content]']
		data['explanation'] = request.data['data[explanation]']
		data['level'] = request.data['data[level]']
		data['sub_category'] = request.data['data[sub_category]']
		data['que_type'] = request.data['data[que_type]']
		data['ideal_time'] = request.data['data[ideal_time]']		
		data['figure'] = request.data.get('figure', None)
		question_serializer = QuestionSerializer(data = data)
		if question_serializer.is_valid():
			question_serializer.save()
			comprehension_serializer = ComprehensionSerializer(data = {'question': question_serializer.data['id'], 'heading': request.data['data[heading]']})
			if comprehension_serializer.is_valid():
				comprehension_serializer.save()
				return Response(comprehension_serializer.data['id'], status = status.HTTP_200_OK)
			else:
				print comprehension_serializer.errors,'***********'
				return Response({ 'errors' : comprehension_serializer.errors }, status = status.HTTP_400_BAD_REQUEST)
		else:
			print question_serializer.errors,'-------------'
			return Response({ 'errors' : question_serializer.errors }, status = status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		print e.args
		return Response({ 'errors' : "Cannot add this question."}, status = status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def get_comprehension(request, comprehension_id):
	try:
		comprehension = Comprehension.objects.get(id = comprehension_id)
		return Response({ 'content': comprehension.question.content, 'sub_category': comprehension.question.sub_category.sub_category_name, 'heading': comprehension.heading, 'figure':str(comprehension.question.figure) }, status = status.HTTP_200_OK)
	except Comprehension.DoesNotExist as e:
		return Response({ 'errors' : "Unable to find comprehension."}, status = status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_comprehension_question(request):
	data = {}
	data['correctoption'] = request.data.get('data[correctoption]', None)
	if data['correctoption']:
		data['content'] = request.data['data[content]']
		data['comprehension'] = request.data['data[comprehension]']
		data['explanation'] = request.data['data[explanation]']
		data['ideal_time'] = request.data['data[ideal_time]']
		data['level'] = request.data['data[level]']
		data['figure'] = request.data.get('figure', None)
		data['options_data'] = {}
		for i in range(1,MAX_OPTIONS+1):
			if request.data.get('data[optioncontent]['+str(i)+']', None):
				data['options_data'][str(i)] = request.data.get('data[optioncontent]['+str(i)+']')
		serializer = ComprehensionQuestionSerializer(data = data)
		if serializer.is_valid():
			return save_comprehension_question(request, serializer, data['options_data'], data['correctoption'])
		else:
			return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
	else:
		return Response({'optionerrors' : 'Correct answer must be provided.'}, status = status.HTTP_400_BAD_REQUEST)



def save_comprehension_question(request, serializer, options_data, correct_option):
	options = []
	if options_data:
		for optionid, content in options_data.items():
			c = { 'content' : str(content), 'correct' : False }
			if int(optionid) == int(correct_option):
				c['correct'] = True
			options.append(c)
		comprehension_question = serializer.save()
		isAnswerSaved, errors = create_comprehension_answer(comprehension_question.id, options)
		if not isAnswerSaved:
			return Response(errors, status = status.HTTP_400_BAD_REQUEST)
		else:
			return Response({}, status = status.HTTP_200_OK)
	else:
		return Response({'optionerrors' : 'Options must be provided with correct answer.'}, status = status.HTTP_400_BAD_REQUEST)
	return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_comprehension_questions(request, comprehension_id):
	try:
		comprehension = Comprehension.objects.get(id = comprehension_id)
		data = get_comprehension_questions_format(comprehension)
		return Response(data, status = status.HTTP_200_OK)
	except Comprehension.DoesNotExist as e:
		return Response({ 'errors' : "Unable to find comprehension."}, status = status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def comprehension_question_operations(request, comprehension_question_id):
	try:
		comprehension_question = ComprehensionQuestion.objects.get(id = comprehension_question_id)
	except ComprehensionQuestion.DoesNotExist:
		return Response({'errors': 'Comprehension question not found.'}, status=status.HTTP_404_NOT_FOUND)
	if request.method == 'GET':
		comprehension_question_serializer = ComprehensionQuestionSerializer(comprehension_question, many = False)
		return Response(dict(comprehension_question_serializer.data), status = status.HTTP_200_OK)
	elif request.method == 'DELETE':
		if comprehension_question.figure:
			os.remove(str(comprehension_question.figure))
		# comprehension_question.delete()
		return Response({'deletedComprehensionQuestionsId': comprehension_question_id}, status = status.HTTP_200_OK)
	elif request.method == 'PUT':
		data = {}
		data['comprehension'] = comprehension_question.comprehension.id
		data['explanation'] = request.data['data[explanation]']
		data['level'] = request.data['data[level]']
		data['ideal_time'] = request.data['data[ideal_time]']
		data['content'] = request.data['data[content]']
		if request.data.get('data[figure]', None):
			data['figure'] = request.data['data[figure]']
			if comprehension_question.figure:
				os.remove(str(comprehension_question.figure))
		serializer = ComprehensionQuestionSerializer(comprehension_question, data = data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.data, status = status.HTTP_200_OK)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
def comprehension_answers_operations(request, comprehension_question_id):
	try:
		data = {}
		comprehension_question = ComprehensionQuestion.objects.get(id = comprehension_question_id)
		comprehension_answers = ComprehensionAnswer.objects.filter(question = comprehension_question_id)
	except ComprehensionQuestion.DoesNotExist:
		return Response({'errors': 'Comprehension question not found.'}, status=status.HTTP_404_NOT_FOUND)
	data['content'] = comprehension_question.content
	if request.method == 'GET':
		comprehension_answers_serializer = ComprehensionAnswerSerializer(comprehension_answers, many = True)
		data['options'] = comprehension_answers_serializer.data
		print comprehension_answers_serializer.data
		return Response(data, status = status.HTTP_200_OK)
	elif request.method == 'PUT':
		optionsContent = dict(request.data.get('optionsContent'))
		data['options'] = []
		for answer in comprehension_answers:
			d = { 'correct' : False, 'content' : optionsContent[str(answer.id)], 'question' : comprehension_question.id }
			if request.data.get('correctOption') == str(answer.id):
				d['correct'] = True
			serializer = ComprehensionAnswerSerializer(answer,data=d)
			if serializer.is_valid():
				serializer.save()
				data['options'].append(serializer.data)
			else:
				return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		return Response(data, status = status.HTTP_200_OK)


