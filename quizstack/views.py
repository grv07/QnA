from quiz.models import SubCategory, Category, Quiz, Question
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import QuizStack
from .serializer import QuizStackSerializer
from mcq.models import Answer

@api_view(['POST'])
def create_quizstack(request):
	try:
		serializer = QuizStackSerializer(data = request.data)
		if serializer.is_valid():
			serializer.save()
		else:
			return Response({ 'errors' : serializer.errors }, status = status.HTTP_400_BAD_REQUEST)
		return Response(serializer.data, status = status.HTTP_200_OK)
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
			quizstack = QuizStack.objects.get(id = quizstack_id, quiz=quiz_id)
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
