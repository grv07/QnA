from quiz.models import SubCategory, Category, Quiz, Question
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import QuizStack
from .serializer import QuizStackSerializer
from mcq.models import Answer, MCQuestion
from objective.models import ObjectiveQuestion
from comprehension.models import Comprehension, ComprehensionQuestion, ComprehensionAnswer
from QnA.services.constants import QUESTION_TYPE_OPTIONS, ANSWER_ORDER_OPTIONS
from QnA.services.utility import shuffleList
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
def create_quizstack(request):
	logger.info('under quizstack.create_quizstack')
	try:
		quiz = Quiz.objects.get(id = request.data.get('quiz'))
		quizstack_list = QuizStack.objects.filter(quiz = quiz)
		if not quizstack_list.filter(subcategory = request.data.get('subcategory'), level = request.data.get('level'), que_type = request.data.get('que_type')):
			serializer = QuizStackSerializer(data = request.data)
			if serializer.is_valid():
				selected_questions = [ question.id for question in Question.objects.filter(sub_category = request.data.get('subcategory'), level = request.data.get('level'), que_type = request.data.get('que_type') ).order_by('id')[:int(request.data.get('no_questions'))] ]
				if request.data.get('que_type') == QUESTION_TYPE_OPTIONS[0][0]:
					quiz.total_marks += int(request.data.get('correct_grade'))*int(request.data.get('no_questions'))
				elif request.data.get('que_type') == QUESTION_TYPE_OPTIONS[2][0]:
					for q in selected_questions:
						comprehension = Comprehension.objects.get(question = q)
						quiz.total_marks += int(request.data.get('correct_grade'))*ComprehensionQuestion.objects.filter(comprehension = comprehension).count()
				quizstack_obj = serializer.save()
				quizstack_obj.add_selected_questions(selected_questions)
				quiz.total_questions += int(request.data.get('no_questions'))
				quiz.total_duration += int(request.data.get('duration'))
				quiz.total_sections = len(set([qs.section_name for qs in quizstack_list]))
				quiz.save()
			else:
				logger.error('under quizstack.create_quizstack' +str(serializer.errors))
				return Response({ 'errors' : 'Unable to add to stack.' }, status = status.HTTP_400_BAD_REQUEST)
			return Response(serializer.data, status = status.HTTP_200_OK)
		else:
			logger.error('under quizstack.create_quizstack duplicate questions')
			return Response({ 'errors' :'Duplicate questions set is not allowed.' }, status = status.HTTP_400_BAD_REQUEST)
	except Exception as e:
		logger.error('under quizstack.create_quizstack '+str(e.args))
		return Response({'errors' : 'Cannot add to the stack.'}, status = status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((AllowAny,))
def get_quizstack(request, quiz_id, quizstack_id):
	logger.info('under quizstack.get_quizstack '+str(quizstack_id))
	if quizstack_id == 'all':
		try:
			quizstack_list = QuizStack.objects.filter(quiz=quiz_id).order_by('section_name')
			section_data = {}
			for quizstack in quizstack_list:
				if not section_data.has_key(quizstack.section_name):
					section_data[quizstack.section_name] = quizstack.subcategory.sub_category_name
			serializer = QuizStackSerializer(quizstack_list, many = True)
			result = { 'data': serializer.data, 'section_data': section_data }
			return Response(result, status = status.HTTP_200_OK)
		except QuizStack.DoesNotExist as e:
			logger.error('under quizstack.get_quizstack quiz stacks not found '+str(e.args))
			return Response({'errors': 'Quiz Stacks not found'}, status=status.HTTP_404_NOT_FOUND)
	elif quizstack_id.isnumeric():
		try:
			quizstack = QuizStack.objects.get(id = quizstack_id, quiz=quiz_id)
			serializer = QuizStackSerializer(quizstack, many = False)
			return Response(serializer.data, status = status.HTTP_200_OK)
		except QuizStack.DoesNotExist as e:
			logger.error('under quizstack.get_quizstack '+str(e.args))
			return Response({'errors': 'Quiz Stack not found'}, status = status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes((AllowAny,))
def get_quizstack_for_uncomplete_test(request):
	try:
		sectionsRemaining = request.data.get('sectionsRemaining')
		if sectionsRemaining:
			quizstack_list = []
			for section_no in sectionsRemaining:
				for quizstack in QuizStack.objects.filter(quiz = request.data.get('quiz_id'), section_name = 'Section#'+str(section_no)):
					quizstack_list += [ quizstack ]
			serializer = QuizStackSerializer(quizstack_list, many = True)
			return Response(serializer.data, status = status.HTTP_200_OK)
	except QuizStack.DoesNotExist as e:
		print e.args
		return Response({'errors': 'Quiz Stack not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
def delete_quizstack(request, quiz_id, quizstack_id):
	logger.info('under quizstack.delete_quizstack '+str(quizstack_id))	
	if quizstack_id == 'all':
		quizstack_list = QuizStack.objects.filter(quiz=quiz_id)
		if quizstack_list:
			for quizstack in quizstack_list:
				quizstack.delete()
			return Response(status = status.HTTP_200_OK)
		else:
			logger.error('under quizstack.delete_quizstack not found')	
			return Response({'errors': 'Quiz Stack not found'}, status=status.HTTP_404_NOT_FOUND)	
	elif quizstack_id.isnumeric():
		try:
			quiz = Quiz.objects.get(id = quiz_id)
			quizstack = QuizStack.objects.get(id = quizstack_id, quiz=quiz_id)
			_remove_marks = int(quizstack.correct_grade)*int(quizstack.no_questions)

			if quiz.total_questions > quizstack.no_questions:  
				quiz.total_questions -= quizstack.no_questions
				quiz.total_marks -= _remove_marks
				quiz.total_duration -= int(quizstack.duration)
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
			logger.error('under quizstack.delete_quizstack '+str(e.args))
			return Response({'errors': 'Quiz Stack not found'}, status = status.HTTP_404_NOT_FOUND)


# @api_view(['GET'])
# @permission_classes((AllowAny,))
# # Touch this on your own risk ;)
# def get_quizstack_questions(request, quiz_id):
# 	'''Create a test json with { data:[{'question_stack': [{'content': u'???', 'que_type': u'mcq', 
# 				'options': [{'content': u'op', 'id': 8}, 
# 							{'content': u'op', 'id': 9}],
# 							'id': 27, 'level': u'easy'}], 
# 							'time_duration': 150,
# 							'section_name': u'Name',
# 							'total_questions': 1}, ... , ... , ...
# 							]}'''
# 	quiz_stack_list = QuizStack.objects.filter(quiz=quiz_id).order_by('id')
# 	_added_sections = []
# 	for quiz_stack in quiz_stack_list:
# 		_questions = quiz_stack.get_quiz_questions(quiz_stack.que_type, quiz_stack.level, quiz_stack.question_order, quiz_stack.no_questions)
		
# 		# This function is for get a True >> if new section encounter or False and previous one objects for question stack entry.  
# 		def _get_section_name_for_que(_added_sections):
# 			for add_section in _added_sections:
# 			 	if add_section['section_name'] == quiz_stack.section_name:
# 			 		return (False, add_section)
# 			 	else:
# 			 		_tup_section =  (True, {'section_name':quiz_stack.section_name, 'total_questions':0, 'time_duration':0, 'question_stack':[]})
# 			else:
# 				_tup_section =  (True, {'section_name':quiz_stack.section_name, 'total_questions':0, 'time_duration':0, 'question_stack':[]})		
# 			return _tup_section
		
# 		is_new,add_section = _get_section_name_for_que(_added_sections)
		
# 		if is_new:
# 			question_stack = add_section['question_stack']
# 			add_section['total_questions'] += 1 
# 			add_section['time_duration'] += int(quiz_stack.duration)
# 			_added_sections.append(add_section)
# 		else:
# 			question_stack = add_section['question_stack']
# 			add_section['total_questions'] += 1
# 			add_section['time_duration'] += int(quiz_stack.duration)

# 		for question in _questions:
# 			_data = {
# 			'id' : question.id,
# 			'level' : question.level,
# 			'content' : question.content,
# 			'que_type' : question.que_type,
# 			'options'  : [{ 'id' : answer.id, 'content' : answer.content, 
# 			} for answer in Answer.objects.filter(question=question)]
# 			}
# 			question_stack.append(_data)
# 	return Response({'data':_added_sections}, status = status.HTTP_200_OK)	




@api_view(['GET'])
@permission_classes((AllowAny,))
def get_quizstack_questions_basedon_section(request, quiz_id):
	section_name = request.query_params.get('sectionName')
	logger.info('under quizstack.get_quizstack_questions_basedon_section section-name '+section_name)
	try:
		# data = { 'questions' : [{ 1: {'content' : '', 'options' : [] } }] } --> This format is used
		data = { 'questions' : [] }
		questions = []
		count = 0
		added_questions = [] # To avoid repeat addition of questions
		quiz_stack_list = QuizStack.objects.filter(quiz = quiz_id, section_name = section_name).order_by('id')
		for quizstack in quiz_stack_list:
			questions = quizstack.fetch_selected_questions()
			# questions = list(Question.objects.filter(sub_category = quizstack.subcategory, level = quizstack.level ).order_by('id')[:quizstack.no_questions])
			if quizstack.question_order == ANSWER_ORDER_OPTIONS[1][0]:
				questions = shuffleList(questions)
			for question_id in questions:
				question = Question.objects.get(id = int(question_id))
				if question.id not in added_questions:
					count += 1
					d = { count : { 'id': int(question_id), 'content': question.content, 'que_type': question.que_type, 'figure': None, 'status': 'NV' } }
					if question.figure:
						d[count]['figure'] = str(question.figure)
					# Check for diff. types of questions
					if question.que_type == QUESTION_TYPE_OPTIONS[0][0]:
						d[count]['options'] = [{ 'id' : answer.id, 'content' : answer.content } for answer in Answer.objects.filter(question = question)]
						d[count]['problem_type'] = MCQuestion.objects.get(question_ptr = question.id).problem_type
					elif question.que_type == QUESTION_TYPE_OPTIONS[1][0]:
						d[count]['options'] = []
					elif question.que_type == QUESTION_TYPE_OPTIONS[2][0]:
						comprehension = Comprehension.objects.get(question = question)
						d[count]['heading'] = comprehension.heading
						d[count]['comprehension_questions'] = []
						count1 = 0
						for cq in ComprehensionQuestion.objects.filter(comprehension = comprehension):
							count1 += 1
							d1 = { count1 : { 'id': cq.id, 'content': cq.content, 'figure': None, 'options': None } }
							if cq.figure:
								d1[count1]['figure'] = str(cq.figure)
							d1[count1]['options'] = [{ 'id' : ca.id, 'content' : ca.content } for ca in ComprehensionAnswer.objects.filter(question = cq)]
							d[count]['comprehension_questions'].append(d1)
					data['questions'].append(d)
				added_questions.append(question.id)
		# data['total_questions'] = count
		# print data
		return Response(data, status = status.HTTP_200_OK)
	except Exception as e:
		logger.info('under quizstack.get_quizstack_questions_basedon_section section-name '+section_name+' '+str(e.args))
		return Response({}, status = status.HTTP_400_BAD_REQUEST) 




'''
Used for selecting questions in a quiz stack row.
'''
@api_view(['GET', 'POST'])
def pre_selected_questions(request, quizstack_id):
	try:
		quizstack = QuizStack.objects.get(id = quizstack_id)
	except QuizStack.DoesNotExist as e:
		return Response({'errors': 'Quiz stack not found'}, status = status.HTTP_404_NOT_FOUND)
	if request.method == 'GET':
		data = { 'questions' : [] }
		selected_questions = quizstack.fetch_selected_questions()
		for question in Question.objects.filter(sub_category = quizstack.subcategory, level = quizstack.level):
			if str(question.id) in selected_questions:
				is_selected = True
			else:
				is_selected = False
			d = {
				'id' : question.id,
				'content' : question.content,
				'is_selected': is_selected,
				'que_type': question.que_type
				}
			if question.que_type == QUESTION_TYPE_OPTIONS[0][0]:
				d.update({ 'options'  : [{ 'id' : answer.id, 'content' : answer.content, 'correct' : answer.correct 
				} for answer in Answer.objects.filter(question = question)] })
			elif question.que_type == QUESTION_TYPE_OPTIONS[1][0]:
				d.update({ 'correct': ObjectiveQuestion.objects.get(pk = question).get_answer()  })
			data['questions'] += [d]
		return Response(data, status = status.HTTP_200_OK)
	elif request.method == 'POST':
		try:
			if request.data:
				total_already_present_questions = len(quizstack.fetch_selected_questions())
				total_new_selected_questions = len(request.data)
				if total_already_present_questions == total_new_selected_questions:
					return Response({'errors': 'Already all questions are selected.'}, status = status.HTTP_400_BAD_REQUEST)
				else:
					quizstack.selected_questions = ''
					quizstack.save()
					if total_already_present_questions > total_new_selected_questions:
						quizstack.quiz.total_questions -= abs(total_already_present_questions - total_new_selected_questions)
					elif total_already_present_questions < total_new_selected_questions:
						quizstack.quiz.total_questions += abs(total_already_present_questions - total_new_selected_questions)
					quizstack.quiz.total_marks =  quizstack.quiz.total_questions*quizstack.correct_grade
					quizstack.quiz.save()
					quizstack.add_selected_questions(request.data)
					return Response({ 'quizId': quizstack.quiz.id}, status = status.HTTP_200_OK)
			else:
				return Response({'errors': 'One question must be selected.'}, status = status.HTTP_400_BAD_REQUEST)
		except Exception as e:
			print e.args
			return Response({'errors': 'Questions cannot be saved.'}, status = status.HTTP_404_NOT_FOUND)

