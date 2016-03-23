from quiz.models import SubCategory, Category, Quiz, Question
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import QuizStack
from .serializer import QuizStackSerializer
from mcq.models import Answer
from objective.models import ObjectiveQuestion
from QnA.services.utility import QUESTION_TYPE_OPTIONS, ANSWER_ORDER_OPTIONS, shuffleList
from django.core.cache import cache

@api_view(['POST'])
def create_quizstack(request):
	try:
		print request.data
		quiz = Quiz.objects.get(id = request.data.get('quiz'))
		quizstack_list = QuizStack.objects.filter(quiz = quiz)
		if not quizstack_list.filter(subcategory = request.data.get('subcategory'), level = request.data.get('level')):
			serializer = QuizStackSerializer(data = request.data)
			if serializer.is_valid():
				serializer.save()				
				quiz.total_questions += int(request.data.get('no_questions'))
				quiz.total_marks += int(request.data.get('correct_grade'))*int(request.data.get('no_questions'))
				quiz.total_duration += int(request.data.get('duration'))*60
				quiz.total_sections = len(set([qs.section_name for qs in quizstack_list]))
				quiz.save()
			else:
				return Response({ 'errors' : serializer.errors }, status = status.HTTP_400_BAD_REQUEST)
			return Response(serializer.data, status = status.HTTP_200_OK)
		else:
			return Response({ 'errors' :'Duplicate questions not allowed.' }, status = status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		print e.args
		return Response({'errors' : 'Cannot add to the stack.'}, status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_quizstack(request, quiz_id, quizstack_id):
	if quizstack_id == 'all':
		try:
			quizstack_list = QuizStack.objects.filter(quiz=quiz_id).order_by('-id')
			serializer = QuizStackSerializer(quizstack_list, many = True)
			return Response(serializer.data, status = status.HTTP_200_OK)
		except QuizStack.DoesNotExist as e:
			print e.args
			return Response({'errors': 'Quiz Stack not found'}, status=status.HTTP_404_NOT_FOUND)
	elif quizstack_id.isnumeric():
		try:
			quizstack = QuizStack.objects.get(id = quizstack_id, quiz=quiz_id)
			serializer = QuizStackSerializer(quiz, many=False)
			return Response(serializer.data, status = status.HTTP_200_OK)
		except QuizStack.DoesNotExist as e:
			return Response({'errors': 'Quiz Stack not found'}, status = status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes((AllowAny,))
def get_quizstack_for_uncomplete_test(request, quiz_id):
	try:
		sectionNoWhereLeft = "Section#"+request.query_params.get('sectionNoWhereLeft')
		quizstack_list = QuizStack.objects.filter(quiz=quiz_id, section_name__gte=sectionNoWhereLeft).order_by('-id')
		serializer = QuizStackSerializer(quizstack_list, many = True)
		return Response(serializer.data, status = status.HTTP_200_OK)
	except QuizStack.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Quiz Stack not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def delete_quizstack(request, quiz_id, quizstack_id):
	if quizstack_id == 'all':
		try:
			quizstack_list = QuizStack.objects.filter(quiz=quiz_id)
			for quizstack in quizstack_list:
				quizstack.delete()
			return Response(status = status.HTTP_200_OK)
		except QuizStack.DoesNotExist as e:
			print e.args
			return Response({'errors': 'Quiz Stack not found'}, status=status.HTTP_404_NOT_FOUND)
	
	elif quizstack_id.isnumeric():
		try:
			quiz = Quiz.objects.get(id = quiz_id)
			quizstack = QuizStack.objects.get(id = quizstack_id, quiz=quiz_id)
			_remove_marks = int(quizstack.correct_grade)*int(quizstack.no_questions)

			if quiz.total_questions > quizstack.no_questions:  
				quiz.total_questions -= quizstack.no_questions
				quiz.total_marks -= _remove_marks
				quiz.total_duration -= int(quizstack.duration)*60
				quiz.total_sections = len(set([qs.section_name for qs in QuizStack.objects.filter(quiz = quiz) if qs.section_name!=quizstack.section_name]))
			else:
				quiz.total_questions = 0
				quiz.total_marks = 0
				quiz.total_duration = 0
				quiz.total_sections = 0
			quiz.save()
			quizstack.delete()
			return Response(status = status.HTTP_200_OK)
		except QuizStack.DoesNotExist as e:
			return Response({'errors': 'Quiz Stack not found'}, status = status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes((AllowAny,))
# Touch this on your own risk ;)
def get_quizstack_questions(request, quiz_id):
	'''Create a test json with { data:[{'question_stack': [{'content': u'???', 'que_type': u'mcq', 
				'options': [{'content': u'op', 'id': 8}, 
							{'content': u'op', 'id': 9}],
							'id': 27, 'level': u'easy'}], 
							'time_duration': 150,
							'section_name': u'Name',
							'total_questions': 1}, ... , ... , ...
							]}'''
	quiz_stack_list = QuizStack.objects.filter(quiz=quiz_id).order_by('id')
	_added_sections = []
	for quiz_stack in quiz_stack_list:
		_questions = quiz_stack.get_quiz_questions(quiz_stack.que_type, quiz_stack.level, quiz_stack.question_order, quiz_stack.no_questions)
		
		# This function is for get a True >> if new section encounter or False and previous one objects for question stack entry.  
		def _get_section_name_for_que(_added_sections):
			for add_section in _added_sections:
			 	if add_section['section_name'] == quiz_stack.section_name:
			 		return (False, add_section)
			 	else:
			 		_tup_section =  (True, {'section_name':quiz_stack.section_name, 'total_questions':0, 'time_duration':0, 'question_stack':[]})
			else:
				_tup_section =  (True, {'section_name':quiz_stack.section_name, 'total_questions':0, 'time_duration':0, 'question_stack':[]})		
			return _tup_section
		
		is_new,add_section = _get_section_name_for_que(_added_sections)
		
		if is_new:
			question_stack = add_section['question_stack']
			add_section['total_questions'] += 1 
			add_section['time_duration'] += int(quiz_stack.duration)
			_added_sections.append(add_section)
		else:
			question_stack = add_section['question_stack']
			add_section['total_questions'] += 1
			add_section['time_duration'] += int(quiz_stack.duration)

		for question in _questions:
			_data = {
			'id' : question.id,
			'level' : question.level,
			'content' : question.content,
			'que_type' : question.que_type,
			'options'  : [{ 'id' : answer.id, 'content' : answer.content, 
			} for answer in Answer.objects.filter(question=question)]
			}
			question_stack.append(_data)
	return Response({'data':_added_sections}, status = status.HTTP_200_OK)	




@api_view(['GET'])
@permission_classes((AllowAny,))
def get_quizstack_questions_basedon_section(request, quiz_id):
	section_name = request.query_params.get('sectionName')
	try:
		# data = { 'questions' : [{ 1: {'content' : '', 'options' : [] } }] } --> This format is used
		data = { 'questions' : [] }
		count = 0
		added_questions = [] # To avoid repeat addition of questions
		quiz_stack_list = QuizStack.objects.filter(quiz = quiz_id, section_name = section_name).order_by('id')
		for quizstack in quiz_stack_list:
			questions = list(Question.objects.filter(sub_category = quizstack.subcategory, level = quizstack.level ).order_by('id')[:quizstack.no_questions])
			if quizstack.question_order == ANSWER_ORDER_OPTIONS[1][0]:
				questions = shuffleList(questions)
			for question in questions:
				if question.id not in added_questions:
					if question.que_type == QUESTION_TYPE_OPTIONS[0][0]:
						options = [{ 'id' : answer.id, 'content' : answer.content, 'isSelected': False } for answer in Answer.objects.filter(question=question)]
					elif question.que_type == QUESTION_TYPE_OPTIONS[1][0]:
						options = []
					count += 1
					d = { count : { 'id': question.id, 'content': question.content, 'options': options, 'que_type': question.que_type, 'figure': None, 'status': 'NV' } }
					if question.figure:
						d[count]['figure'] = str(question.figure)
					data['questions'].append(d)
				added_questions.append(question.id)
		data['total_questions'] = range(1,count+1)
		data['added_questions'] = added_questions
		return Response(data, status = status.HTTP_200_OK)
	except Exception as e:
		print e.args
		return Response({}, status = status.HTTP_400_BAD_REQUEST) 
