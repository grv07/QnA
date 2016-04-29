from django.core.cache import cache
from django.utils import timezone

import requests
import json
from random import shuffle

from quiz.models import Question, SubCategory, Sitting, Quiz
from mcq.models import Answer
from quizstack.models import QuizStack
from objective.models import ObjectiveQuestion
from constants import QUESTION_TYPE_OPTIONS
from generate_result_engine import generate_result, filter_by_category, find_and_save_rank


# UPLOAD_LOCATION = '/qna/media/'
def get_user_result_helper(sitting, test_user_id, quiz_key, order = None, filter_by_category = None, get_order_by = None):	
	get_order = order
	quiz = sitting.quiz
	user = sitting.user
	if not get_order == 'acending':
		_get_order_by = 'current_score'
	
	in_correct_pt  = float((len(set(sitting.incorrect_questions_list.strip().split(',')))*100)/quiz.total_questions) if len(sitting.incorrect_questions_list) > 0 else 0 

	correct_que_pt = int(filter_by_category[1]*100)/quiz.total_questions
	
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
	questions_level_info = [0 , 0, 0, 0, 0] # [Easy, Medium ,Hard, Total, IdealTime]
	sca = {'subcategory' : None, 'id' : None, 'question' : None, 'questions_level_info' : None}

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
				d.update({ 'options'  : [{ 'id' : answer.id, 'content' : answer.content, 'correct' : answer.correct 
				} for answer in Answer.objects.filter(question = question)] })
			elif question.que_type == QUESTION_TYPE_OPTIONS[1][0]:
				d.update({ 'correct': ObjectiveQuestion.objects.get(pk = question).get_answer()  })
			
			if question.level == 'easy':
				questions_level_info[0] = questions_level_info[0] + 1
			elif question.level == 'medium':
				questions_level_info[1] = questions_level_info[1] + 1
			else:
				questions_level_info[2] = questions_level_info[2] + 1
			questions_level_info[4] += question.ideal_time
			
			if not is_have_sub_category:
				sca['questions'].append(d)
	else:
		print 'Not have questions <<<<<<<<<<<>>>>>>>>>>>>'
	questions_level_info[3] = sum(questions_level_info[:3])
	sca['questions_level_info'] = questions_level_info
	return sca

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
		value = str(value).replace('.0','')
	return value
		

def shuffleList(l):
	shuffle(l)
	return l


def checkIfTrue(str_value):
	if str_value == 'true':
		return True
	elif str_value == 'false':
		return False

def postNotifications(data = None, url = None):
	if data and url:
		try:
			data['notification_url'] = url
			requests.post(url, data = json.dumps(data))
			return True
		except Exception as e:
			print e.args
			return False
	return False

def save_test_data_to_db_helper(test_user, sitting_id, test_key, time_spent, host_name):
	if sitting_id and test_user and test_key and time_spent:
		# _test_user_obj = TestUser.objects.get(pk = test_user)
		sitting_obj = Sitting.objects.get(id = cache.get('sitting_id'+str(test_user)))
		un_ans_que_list = sitting_obj.unanswerd_question_list

		unanswered_questions_list = map(int, un_ans_que_list.strip().split(',')) if len(un_ans_que_list) > 0 else []
		cache_keys_pattern = test_key+"|"+str(test_user)+"|**"
		quizstack =  QuizStack.objects.filter(quiz = Quiz.objects.get(quiz_key = test_key))
		for key in list(cache.iter_keys(cache_keys_pattern)):
			answered_questions_list = generate_result(cache.get(key), sitting_obj, key, quizstack)
			if answered_questions_list:
				for question_id in answered_questions_list:
					if question_id in unanswered_questions_list: 
						unanswered_questions_list.remove(question_id) 
				cache.delete(key)
				print cache.get(key), '-----------------'

		sitting_obj.save_time_spent(time_spent)

		# Clear all unanswered_questions_list so as to modify it.
		sitting_obj.clear_all_unanswered_questions()
		for question_id in unanswered_questions_list:
			sitting_obj.add_unanswerd_question(question_id)
		sitting_obj.save()

		# test is set to complete must come after sitting_obj.add_unanswerd_question()
		sitting_obj.mark_quiz_complete()

		# find and save the rank
		if not find_and_save_rank(test_user, sitting_obj.quiz.id, sitting_obj.current_score, sitting_obj.time_spent):
			print 'Cannot be saved'

		data = { 'EVENT_TYPE': 'finishTest', 'test_key': test_key, 'sitting_id': sitting_id, 'test_user_id': test_user, 'timestamp_IST': str(timezone.now()), 'username': sitting_obj.user.username, 'email': sitting_obj.user.email, 'finish_mode': 'NormalSubmission' }
		if not postNotifications(data, sitting_obj.quiz.finish_notification_url):
			print 'finish notification not sent'
		_filter_by_category = filter_by_category(sitting_obj)
		data = get_user_result_helper(sitting_obj, test_user, test_key, 'acending', _filter_by_category, '-current_score')
		data['htmlReport'] = 'http://'+str(host_name)+'/api/user/result/'+str(test_user)+'/'+test_key+'/'+str(sitting_obj.attempt_no)
		if not postNotifications(data, sitting_obj.quiz.grade_notification_url):
			print 'grade notification not sent'
		# Clean my cache ...
		cache.delete('sitting_id'+str(test_user))
		cache.delete(test_key + "|" + str(test_user) + "time")
		# End ...
		return { 'attempt_no': sitting_obj.attempt_no }
	else:
		raise ValueError('Any None not accepted ::: test_user: {0}, sitting_id: {1}, test_key: {2}, time_spent: {3}'.format(test_user, sitting_id, test_key, time_spent))