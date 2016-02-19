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
			quizstack_list = QuizStack.objects.filter(quiz=quiz_id).order_by('id')
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
# Touch this on your own risk ;)
def get_quizstack_questions(request, quiz_id):
	quiz_stack_list = QuizStack.objects.filter(quiz=quiz_id).order_by('id')
	_added_sections = []
	for quiz_stack in quiz_stack_list:
		_questions = quiz_stack.get_quiz_questions(quiz_stack.que_type, quiz_stack.level, quiz_stack.question_order, quiz_stack.no_questions)
		
		def _get_section_name_for_que(_added_sections):
			for add_section in _added_sections:
			 	if add_section['section_name'] == quiz_stack.section_name:
			 		return (False, add_section)
			 	else:
			 		_tup_section =  (True, {'section_name':quiz_stack.section_name, 'total_questions':0 ,'question_stack':[]})
			else:
				_tup_section =  (True, {'section_name':quiz_stack.section_name, 'total_questions':0, 'question_stack':[]})		
			return _tup_section

		for question in _questions:
			_data = {
			'id' : question.id,
			'level' : question.level,
			'content' : question.content,
			'que_type' : question.que_type,
			'options'  : [{ 'id' : answer.id, 'content' : answer.content, 
			} for answer in Answer.objects.filter(question=question)]
			}
			is_new,add_section = _get_section_name_for_que(_added_sections)
			if is_new:
				add_section['question_stack'].append(_data)
				add_section['total_questions'] += 1 
				_added_sections.append(add_section)
			else:
				add_section['question_stack'].append(_data)
				add_section['total_questions'] += 1
	# print _added_sections			
	return Response({'data':_added_sections}, status = status.HTTP_200_OK)			 