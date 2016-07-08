from quiz.models import Sitting, Question, Quiz
from mcq.models import Answer
from quizstack.models import QuizStack
from constants import QUESTION_DIFFICULTY_OPTIONS

from collections import defaultdict


def get_marks_ratios_for_previous_tests(sitting_objs, question_distribution_level_wise):
	marks_ratio = [ 0.0, 0.0, 0.0 ]
	# level_wise_questions = [ 0, 0, 0 ] # [ easy, medium, hard ]
	correct_level_wise_questions = [ 0, 0, 0 ] # [ easy, medium, hard ]
	is_correct = lambda answer_list: isinstance(answer_list, list) and Answer.objects.get(id = answer_list[0]).correct
	for sitting_obj in sitting_objs:
		user_answers = sitting_obj.merge_user_answers_and_unanswered_questions()
		for question_id, answer_list in user_answers['mcq'].items():
			question = Question.objects.get(id = question_id)
			if question.level == QUESTION_DIFFICULTY_OPTIONS[0][0]:
				# level_wise_questions[0] += 1
				if is_correct(answer_list): correct_level_wise_questions[0] += 1
			elif question.level == QUESTION_DIFFICULTY_OPTIONS[1][0]:
				# level_wise_questions[1] += 1
				if is_correct(answer_list): correct_level_wise_questions[1] += 1
			elif question.level == QUESTION_DIFFICULTY_OPTIONS[2][0]:
				# level_wise_questions[2] += 1
				if is_correct(answer_list): correct_level_wise_questions[2] += 1

	for i in xrange(3):
		if question_distribution_level_wise[i] and correct_level_wise_questions[i]:
			marks_ratio[i] += float(correct_level_wise_questions[i])/question_distribution_level_wise[i]
	return marks_ratio

		# for question_id, values in user_answers['comprehension'].items():
		# 	d['comprehension'][question_id] = {}
		# 	for cq_id,value in values.items():
		# 		if cq_id!='time_spent':
		# 			d['comprehension'][question_id][cq_id] = value


def calculate_probabilities_for_previous_tests(user_id, question_distribution_level_wise):
	sitting_objs = Sitting.objects.filter(user = user_id).select_related('quiz')
	data = {}
	temp = {}
	if sitting_objs:
		for sitting_obj in sitting_objs:
			if not temp.has_key(sitting_obj.quiz.id):
				quizstack = QuizStack.objects.filter(quiz = sitting_obj.quiz)[0]
				temp[sitting_obj.quiz.id] = quizstack.subcategory.id
			if data.has_key(temp[sitting_obj.quiz.id]):
				data[temp[sitting_obj.quiz.id]].append(sitting_obj)
			else:
				data[temp[sitting_obj.quiz.id]] = [sitting_obj]
		for subcategory_id in data.keys():
			data[subcategory_id] = get_marks_ratios_for_previous_tests(data[subcategory_id], question_distribution_level_wise[subcategory_id])
	return data



def predict_end_test_marks(user_id, quiz_key):
	try:
		quiz = Quiz.objects.get(quiz_key = quiz_key)
	except Quiz.DoesNotExist as dne:
		return -1
	question_distribution_level_wise = {}
	quizstacks = QuizStack.objects.filter(quiz = quiz)
	for quizstack in quizstacks:
		if not question_distribution_level_wise.has_key(quizstack.subcategory.id):
			question_distribution_level_wise[quizstack.subcategory.id] = [ 0, 0, 0 ] #[ easy, medium, hard ]
		if quizstack.level == QUESTION_DIFFICULTY_OPTIONS[0][0]:
		 	question_distribution_level_wise[quizstack.subcategory.id][0] += quizstack.no_questions
		elif quizstack.level == QUESTION_DIFFICULTY_OPTIONS[1][0]:
		 	question_distribution_level_wise[quizstack.subcategory.id][1] += quizstack.no_questions
		elif quizstack.level == QUESTION_DIFFICULTY_OPTIONS[2][0]:
		 	question_distribution_level_wise[quizstack.subcategory.id][2] += quizstack.no_questions
	print question_distribution_level_wise, 'question_distribution_level_wise'
	probablities_for_previous_tests = calculate_probabilities_for_previous_tests(user_id, question_distribution_level_wise)
	print probablities_for_previous_tests, 'probablities_for_previous_tests'
	predicted_marks_distribution = [ 0, 0, 0 ]
	for subcategory_id, probablities_distribution in probablities_for_previous_tests.items():
		for i in xrange(3):
			predicted_marks_distribution[i] += (probablities_distribution[i] * question_distribution_level_wise[subcategory_id][i])
	print predicted_marks_distribution, 'predicted_marks_distribution'
	print sum(predicted_marks_distribution), 'predicted marks'





