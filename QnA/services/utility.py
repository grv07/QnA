from django.core.cache import cache
from django.utils import timezone

import requests
import json, hashlib
from random import shuffle

from QnA.settings import TEST_REPORT_URL

from quiz.models import Question, SubCategory, Sitting, Quiz
from mcq.models import Answer, MCQuestion
from quizstack.models import QuizStack
from objective.models import ObjectiveQuestion
from comprehension.models import Comprehension, ComprehensionQuestion, ComprehensionAnswer
from constants import QUESTION_TYPE_OPTIONS, RESULT_HTML, USER_COOKIE_SALT
from generate_result_engine import generate_result, filter_by_category, find_and_save_rank
from mail_handling import send_mail

from unidecode import unidecode



# UPLOAD_LOCATION = '/qna/media/'
def get_user_result_helper(sitting, test_user_id, quiz_key, order = None, filter_by_category = None, get_order_by = None):	
	get_order = order
	quiz = sitting.quiz
	user = sitting.user
	if not get_order == 'acending':
		_get_order_by = 'current_score'
	
	# incorrect_questions_length = len(sitting.get_incorrect_questions())
	# in_correct_pt  = float((incorrect_questions_length*100)/quiz.total_questions) if incorrect_questions_length > 0 else 0 

	# correct_que_pt = int(filter_by_category[1]*100)/quiz.total_questions
	correct_que_pt = 0
	in_correct_pt = 0	
	_result_status = 'Pass' if int(int(sitting.current_score)*100/int(quiz.total_marks)) > quiz.passing_percent else 'Fail'

	return {
			'quiz_id': quiz.id,
			'quiz_name':quiz.title,
			'passing_percentage': quiz.passing_percent,
			'total_questions':quiz.total_questions,
			'total_marks': quiz.total_marks,
			'marks_scored': sitting.current_score,
			'result_status':_result_status,
			'EVENT_TYPE': 'gradeTest', 
			'test_key': quiz.quiz_key, 
			'sitting_id': sitting.id, 
			'test_user_id': test_user_id, 
			'timestamp_IST': str(timezone.now()), 
			'username': sitting.user.username, 
			'attempt_no': sitting.attempt_no,
			'email': sitting.user.email,
			'correct_questions_score': correct_que_pt, 
			'incorrect_questions_score': in_correct_pt,
			'finish_mode': 'NormalSubmission',
			'start_time_IST': str(sitting.start_date),
			'end_time_IST': str(sitting.end_date)
		}


def get_questions_format(user_id, subcategory_id = None, is_have_sub_category = False):
	sca = {'subcategory' : None, 'id' : None, 'question' : None, 'questions_type_info': { 'mcq': [0, 0, 0, 0], 'comprehension': [0, 0, 0, 0] } }

	if subcategory_id:
		try:
			sc = SubCategory.objects.get(id = subcategory_id, user = user_id)
		except SubCategory.DoesNotExist as e:
			print e.args
			return None
	else:
		try:
			sc = SubCategory.objects.filter(user = user_id)[1]
		except SubCategory.DoesNotExist as e:
			print e.args
			return None
	questions = Question.objects.filter(sub_category = sc)
	sca['subcategory'] = sc.sub_category_name
	sca['id'] = sc.id
	sca['questions'] = []
	if questions:
		for question in questions:
			d = {
				'id' : question.id,
				'level' : question.level,
				'content' : question.content,
				'que_type' : question.que_type,
				}
			if question.que_type == QUESTION_TYPE_OPTIONS[0][0]:
				if not is_have_sub_category:
					d.update({ 'options'  : [{ 'id' : answer.id, 'content' : answer.content, 'correct' : answer.correct 
					} for answer in Answer.objects.filter(question = question)] })
					# d.update({ 'problem_type': MCQuestion.objects.get(question_ptr = question.id).problem_type })
				sca['questions_type_info']['mcq'][3] += 1

			elif question.que_type == QUESTION_TYPE_OPTIONS[1][0]:
				if not is_have_sub_category:
					d.update({ 'correct': ObjectiveQuestion.objects.get(pk = question).get_answer()  })
			elif question.que_type == QUESTION_TYPE_OPTIONS[2][0]:
				if not is_have_sub_category:
					d['comprehensionId'] = Comprehension.objects.get(question=question).id
				sca['questions_type_info']['comprehension'][3] += 1
			
			if question.level == 'easy':
				sca['questions_type_info'][question.que_type][0] += 1
			elif question.level == 'medium':
				sca['questions_type_info'][question.que_type][1] += 1
			else:
				sca['questions_type_info'][question.que_type][2] += 1
			
			if not is_have_sub_category:
				sca['questions'].append(d)
	else:
		print 'Not have questions <<<<<<<<<<<>>>>>>>>>>>>'
	return sca



def get_comprehension_questions_format(comprehension):
	data = { 'questions':[] }
	for cq in ComprehensionQuestion.objects.filter(comprehension = comprehension):
		d = {
			'id' : cq.id,
			'level' : cq.level,
			'content' : cq.content,
			}
		d.update({ 'options'  : [{ 'id' : answer.id, 'content' : answer.content, 'correct' : answer.correct 
				} for answer in ComprehensionAnswer.objects.filter(question = cq)] })

		data['questions'].append(d)
	return data



def validate_stack():
	'''
		{'section_name':'',
		 'sub_category_name':'',
		 'level':'',
		 'q_type':'',
		 '#qs':'',
		 'time_duration':'',
		 'is_timed':'',
		 'correct_grade':'',
		 'incorrect_grade':'',
		 }
	'''
	pass



def check_for_float(value):
	if type(value) == float:
		base, fraction = str(value).split('.')
		value = base+'.'+fraction if float(fraction) > 0 else base
	return value
		

def shuffleList(l):
	shuffle(l)
	return l


def checkIfTrue(str_value):
	if str_value == 'true':
		return True
	elif str_value == 'false':
		return False

def postNotifications(data = None, url = None, allow = False):
	if data and allow and url:
		try:
			data['notification_url'] = url
			requests.post(url, data = json.dumps(data))
			return True
		except Exception as e:
			print e.args
			return False
	return False

def save_test_data_to_db_helper(test_user, test_key, test_data):
	sitting_id = test_data.get('sitting')
	if sitting_id:
		# _test_user_obj = TestUser.objects.get(pk = test_user)
		sitting_obj = Sitting.objects.get(id = sitting_id)
		print sitting_obj,'sitting_obj'
		if not sitting_obj.complete:
			# unanswered_questions = sitting_obj.unanswered_questions
			# print unanswered_questions, 'unanswered_questions'
			# comprehension_unanswered_questions = unanswered_questions[QUESTION_TYPE_OPTIONS[2][0]]
			# print comprehension_unanswered_questions, 'comprehension_unanswered_questions'
			# mcq_unanswered_questions_list = unanswered_questions[QUESTION_TYPE_OPTIONS[0][0]].keys()
			# cache_keys_pattern = test_key+"|"+str(test_user)+"|**"
			quizstack =  QuizStack.objects.filter(quiz = Quiz.objects.get(quiz_key = test_key))
			# for key in list(cache.iter_keys(cache_keys_pattern)):
			# 	print key,'key'
			is_saved_correctly = generate_result(sitting_obj, quizstack, test_data)

			# if answered_questions:
			# 	print comprehension_unanswered_questions,'comprehension_unanswered_questions'
			# 	print mcq_unanswered_questions_list, 'mcq_unanswered_questions_list'
			# 	for question_id in answered_questions[QUESTION_TYPE_OPTIONS[0][0]]:
			# 		print question_id,'mcq'
			# 		if question_id in mcq_unanswered_questions_list: 
			# 			mcq_unanswered_questions_list.remove(question_id)
			# 	for question_id in answered_questions[QUESTION_TYPE_OPTIONS[2][0]].keys():
			# 		for cq_id in answered_questions[QUESTION_TYPE_OPTIONS[2][0]][question_id]:
			# 			print cq_id, 'cq', comprehension_unanswered_questions[str(question_id)]
			# 			del comprehension_unanswered_questions[str(question_id)][cq_id]
			# 	cache.delete(key)
			# 	print cache.get(key), '-----------------'

			# sitting_obj.save_time_spent(time_spent)

			# Clear all unanswered_questions_list so as to modify it.
			# sitting_obj.clear_all_unanswered_questions()
			# print time_spent_on_question, mcq_unanswered_questions_list
			# for question_id in mcq_unanswered_questions_list:
			# 	qtime = time_spent_on_question.get(str(question_id), 0)
			# 	sitting_obj.add_unanswered_mcq_question(question_id, round(qtime, 2))

			# for question_id, value in comprehension_unanswered_questions.items():
			# 	# qtime = time_spent_on_question.get(str(question_id), 0)
			# 	for cq_id, time_spent in value.items():
			# 		sitting_obj.add_unanswered_comprehension_question(question_id, cq_id, time_spent)
			# sitting_obj.save()

			# test is set to complete must come after sitting_obj.add_unanswered_question()
			# sitting_obj.mark_quiz_complete()

			# find and save the rank
			if is_saved_correctly and test_data['is_normal_submission']:
				if not find_and_save_rank(test_user, test_key, sitting_obj.quiz.id, sitting_obj.current_score, sitting_obj.time_spent):
					print 'Cannot be saved'

				data = { 'EVENT_TYPE': 'finishTest', 'test_key': test_key, 'sitting_id': sitting_id, 'test_user_id': test_user, 'timestamp_IST': str(timezone.now()), 'username': sitting_obj.user.username, 'email': sitting_obj.user.email, 'finish_mode': 'NormalSubmission' }
				if not postNotifications(data, sitting_obj.quiz.finish_notification_url, test_data.get('toPost', False)):
					print 'finish notification not sent'
				# _filter_by_category = filter_by_category(sitting_obj)
				data = {}
				# data = get_user_result_helper(sitting_obj, test_user, test_key, 'acending', _filter_by_category, '-current_score')
				data['htmlReport'] = TEST_REPORT_URL.format(test_user_id = test_user, quiz_key = test_key, attempt_no = sitting_obj.attempt_no)
				if not postNotifications(data, sitting_obj.quiz.grade_notification_url, test_data.get('toPost', False)) :
					print 'grade notification not sent'
					html = RESULT_HTML.format(username = sitting_obj.user.username, quiz_name = sitting_obj.quiz.title, report_link = data['htmlReport'])
					send_mail(html, sitting_obj.user.email)
				# Clean my cache ...
				# cache.delete('sitting_id'+str(test_user))
				# cache.delete(test_key + "|" + str(test_user) + "time")
				# cache.delete(test_key + "|" + str(test_user) + "qtime")
				return { 'attempt_no': sitting_obj.attempt_no }
			else:
				return {}
		else:
			return { 'attempt_no': sitting_obj.attempt_no }

	else:
		raise ValueError('Any None not accepted ::: test_user: {0}, sitting_id: {1}, test_key: {2}, time_spent: {3}'.format(test_user, sitting_id, test_key, time_spent))


def merge_two_dicts(d1, d2):
	d = d1.copy()
	d.update(d2)
	return d



# Make a hash and check for correct hash for user ID.
def make_user_hash(user_id):
	return hashlib.md5(str(user_id)+USER_COOKIE_SALT).hexdigest()

def verify_user_hash(user_id, cookie_hash):
	if cookie_hash == make_user_hash(user_id):
		return True
	return False

def ascii_safe(data):
	try:
		temp =  str(data)
	except UnicodeEncodeError as uee:
		# print uee.args,'+++'
		temp = unidecode(data)
	return temp	