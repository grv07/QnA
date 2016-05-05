from mcq.models import MCQuestion, Answer
from objective.models import ObjectiveQuestion
from quiz.models import Sitting, Quiz, Question
from quizstack.models import QuizStack
from home.models import TestUser
from .constants import QUESTION_TYPE_OPTIONS

def generate_result(section_result, sitting_obj, cache_key, quizstack, time_spent_on_question):
	'''{u'answers': {
		u'47': {u'status': u'NA', u'value': None},
		u'20': {u'status': u'NA', u'value': None}, 
		u'21': {u'status': u'NA', u'value': None},
		u'22': {u'status': u'A',u'value': 74}, 
		u'48': {u'status': u'A',u'value': u'6'}
		}
	 }'''	 
	answered_questions_list = []
	# quiz_key,user_ro_no,section_id, = tuple(cache_key.strip().split("|"))
	if section_result:
		_progress_list = section_result['answers']
		for question_id in _progress_list.keys():
			_dict_data = _progress_list.get(str(question_id))
			is_correct = False
			if not _dict_data.get('status') == 'NA' and not _dict_data.get('value') == None:
				try:
					question = Question.objects.get(pk = question_id)
					quizstack_obj = quizstack.filter(subcategory = question.sub_category)[0]
				except Question.DoesNotExist as e:
					print e.args
					return None
				'''Check if given answers are correct or not'''
				sitting_obj.add_user_answer(int(question_id), [ _dict_data.get('value'), round(time_spent_on_question[question_id], 2)] )
				if question.que_type == QUESTION_TYPE_OPTIONS[0][0]:
					is_correct = MCQuestion.objects.get(pk = question_id).check_if_correct(_dict_data.get('value'))
				elif question.que_type == QUESTION_TYPE_OPTIONS[1][0]:
					is_correct = ObjectiveQuestion.objects.get(pk = question_id).check_if_correct(_dict_data.get('value'))
				if is_correct:
					sitting_obj.add_to_score(quizstack_obj.correct_grade)
				else:
					sitting_obj.add_incorrect_question(question_id, quizstack_obj.incorrect_grade)
				answered_questions_list.append(question.id)
		return answered_questions_list		
				

def filter_by_category(sitting):
	'''Return {'sub_cat_name':(incorrect, correct, unattemped, total), total_correct}'''
	# Cat wise filter on question, Total correct questions
	_cat_base_result = {}
	total_correct_que = 0
	_correct_ans = sitting.user_answers
	# Enjoy Helper functions
	get_name_key = lambda que_id: Question.objects.get(pk = int(que_id)).sub_category.sub_category_name
	get_que_set = lambda list: set(list.strip().split(',')) if len(list) > 0 else [] 
	for que in sitting.get_incorrect_questions():
		name_key = get_name_key(int(que))
		if _correct_ans.has_key(que):
			_correct_ans.pop(que)
		if not _cat_base_result.has_key(name_key):
			_cat_base_result[name_key] = [0,0,0,0]
			_cat_base_result[name_key][0] = 1
			_cat_base_result[name_key][3] = 1
		else:
			_cat_base_result[name_key][0] += 1
			_cat_base_result[name_key][3] += 1

	for que in sitting.unanswered_questions.keys():
		name_key = get_name_key(que)
		if _correct_ans.has_key(que):
			_correct_ans.pop(que)
		if not _cat_base_result.has_key(name_key):
			_cat_base_result[name_key] = [0,0,0,0]
			_cat_base_result[name_key][2] = 1
			_cat_base_result[name_key][3] = 1
		else:
			_cat_base_result[name_key][2] += 1
			_cat_base_result[name_key][3] += 1

	for que in _correct_ans:
		name_key = get_name_key(que)
		if not _cat_base_result.has_key(name_key):
			_cat_base_result[name_key] = [0,0,0,0]
			_cat_base_result[name_key][1] = 1
			_cat_base_result[name_key][3] = 1
			total_correct_que += 1 
		else:
			_cat_base_result[name_key][1] += 1
			_cat_base_result[name_key][3] += 1 
			total_correct_que += 1
	for to_tuple in _cat_base_result:
		_cat_base_result[to_tuple] = tuple(_cat_base_result[to_tuple])			
	return [_cat_base_result,total_correct_que]	



# Filter by section
def get_data_for_analysis(quiz, unanswered_questions_list, incorrect_questions_list):
	data = { 'section_wise':{}, 'selected_questions':{} }
	unanswerd_and_incorrect_questions_list = unanswered_questions_list + incorrect_questions_list
	quizstacks = QuizStack.objects.filter(quiz = quiz)
	for section_no in xrange(1, quiz.total_sections+1):
		data['section_wise'][section_no] = []
		d_correct = { 'y':0, 'label': 'Section '+str(section_no) }
		d_incorrect = d_correct.copy()
		d_unattempt = d_correct.copy()
		selected_questions = []
		for quizstack in quizstacks.filter(section_name = 'Section#'+str(section_no)):
			selected_questions += quizstack.fetch_selected_questions()
		for q in selected_questions:
			if q in incorrect_questions_list:
				d_incorrect['y'] += 1
			elif q in unanswered_questions_list:
				d_unattempt['y'] += 1
			else:
				d_correct['y'] += 1
			question = Question.objects.get(id = int(q))
			data['selected_questions'][q] = {}
			data['selected_questions'][q].update({
				'content' : question.content,
				'ideal_time' : question.ideal_time,
				'explanation'  : question.explanation,
				})
			correct_answer_id = 0
			for answer in Answer.objects.filter(question = question):
				if answer.correct == True:
					correct_answer_id = answer.id
					break
			data['selected_questions'][q]['correct_answer_id'] = correct_answer_id			
		data['section_wise'][section_no].append(d_correct)
		data['section_wise'][section_no].append(d_incorrect)
		data['section_wise'][section_no].append(d_unattempt)
	return data

# Calculate the rank
def get_rank(quiz_key, quiz_id, current_score, time_spent):
	all_test_users = TestUser.objects.filter(test_key = quiz_key)
	# all_sitting_objs = Sitting.objects.filter(quiz = quiz_id)
	total = len(all_test_users)
	rank = total
	for test_user in all_test_users:
		max_sitting_obj = get_max_sitting_obj(test_user, quiz_id)
		# print max_sitting_obj.time_spent, time_spent, max_sitting_obj.current_score, current_score
		if current_score > max_sitting_obj.current_score:
			rank -= 1
			if test_user.rank+1 <= total:
				test_user.rank += 1
				test_user.save()
		elif current_score == max_sitting_obj.current_score:
			if time_spent < max_sitting_obj.time_spent:
				rank -= 1
				if test_user.rank+1 <= total:
					test_user.rank += 1
					test_user.save()
	return rank

# Save rank if rank == 0 (at first attempt) otherwise check if existing rank is better or newly calculated is. Use the minimum rank and save.
def find_and_save_rank(test_user_id, quiz_key, quiz_id, current_score, time_spent):
	try:
		test_user = TestUser.objects.get(id = test_user_id)
		current_rank = test_user.rank
		calculated_rank = get_rank(quiz_key, quiz_id, current_score, time_spent)
		if (current_rank == 0) or (current_rank > calculated_rank):
			test_user.rank = calculated_rank
			test_user.save()
		return test_user.rank
	except Exception as e:
		print e.args
		return 0


def get_max_sitting_obj(test_user, quiz_id):
	sitting_objs = Sitting.objects.filter(user = test_user.user, quiz = quiz_id)
	sitting_obj_topper = sitting_objs[0]
	if(len(sitting_objs) == 1):
		return sitting_obj_topper
	else:
		for sitting in sitting_objs[1:]:
			if sitting.current_score > sitting_obj_topper.current_score:
				sitting_obj_topper = sitting
			elif sitting.current_score == sitting_obj_topper.current_score:
				if sitting.time_spent > sitting_obj_topper.time_spent:
					sitting_obj_topper = sitting
		return sitting_obj_topper


def get_topper_data(quiz_key, quiz_id):
	test_user = TestUser.objects.get(test_key = quiz_key, rank = 1)
	return get_max_sitting_obj(test_user, quiz_id)
