from quiz.models import SubCategory, Category, Quiz, Question
from models import QuizStack



def get_quiz(request, quiz_id):
	'''
	Get quiz stack of questions. 
	'''
	try:
		quiz = Quiz.objects.get(pk = quiz_id)
	except Quiz.DoesNotExist as e:
		print e.args	
	quiz_stacks = QuizStack.objects.filter(quiz = quiz)
	
	for quiz_stack in quiz_stacks:
		quiz_stack.subcategory
	# if empty
	else:
		pass