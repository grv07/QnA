from mcq.models import MCQuestion, Answer
from objective.models import ObjectiveQuestion
from quiz.models import Sitting, Quiz, Question
from quizstack.models import QuizStack
from home.models import TestUser
from comprehension.models import Comprehension, ComprehensionQuestion, ComprehensionAnswer
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

	answered_questions = { QUESTION_TYPE_OPTIONS[0][0]:[], QUESTION_TYPE_OPTIONS[2][0]:{} }
	# quiz_key,user_ro_no,section_id, = tuple(cache_key.strip().split("|"))
	print section_result, 'section_result', cache_key
	if section_result:
		_progress_list = section_result['answers']
		print _progress_list.keys(),'_progress_list.keys()'
		for question_id in _progress_list.keys():
			_dict_data = _progress_list.get(str(question_id))
			is_correct = False
			# if not _dict_data.get('status') == 'NA' and not _dict_data.get('value') == None:
			try:
				question = Question.objects.get(pk = question_id)
				quizstack_obj = quizstack.filter(subcategory = question.sub_category, que_type = question.que_type)[0]
			except Question.DoesNotExist as e:
				print e.args
				return None
			print question.que_type,'================='
			if question.que_type == QUESTION_TYPE_OPTIONS[0][0]:
				is_correct = MCQuestion.objects.get(pk = question_id).check_if_correct(_dict_data.get('value'))
				sitting_obj.add_user_mcq_answer(question_id, [ int(_dict_data.get('value')), round(time_spent_on_question[str(question_id)], 2)] )
				if is_correct:
					sitting_obj.add_to_score(quizstack_obj.correct_grade)
				else:
					sitting_obj.add_incorrect_mcq_question(question_id, quizstack_obj.incorrect_grade)
				answered_questions[QUESTION_TYPE_OPTIONS[0][0]].append(question_id)

			elif question.que_type == QUESTION_TYPE_OPTIONS[2][0]:
				answered_questions[QUESTION_TYPE_OPTIONS[2][0]] = { question_id: [] }
				for cq in _dict_data.keys():
					print cq, '^^^^^^^^^^'
					comprehension_answer_id = int(_dict_data[str(cq)]['value'])
					print comprehension_answer_id
					sitting_obj.add_user_comprehension_answer(question_id, { cq: comprehension_answer_id }, round(time_spent_on_question[str(question_id)], 2))
					is_comprehension_correct = ComprehensionQuestion.objects.get(id = cq).check_if_correct(comprehension_answer_id)
					print cq,'cq'
					if is_comprehension_correct:
						print 'score', sitting_obj.current_score
						sitting_obj.add_to_score(quizstack_obj.correct_grade)
					else:
						print question_id,cq
						sitting_obj.add_incorrect_comprehension_question(question_id, cq, quizstack_obj.incorrect_grade)
					answered_questions[QUESTION_TYPE_OPTIONS[2][0]][question_id].append(cq)
		print answered_questions,'answered_questions'
		return answered_questions	
				

def filter_by_category(sitting):
	'''Return {'sub_cat_name':(incorrect, correct, unattemped, total), total_correct}'''
	# Cat wise filter on question, Total correct questions
	_cat_base_result = {}
	total_correct_que = 0
	_correct_ans = sitting.user_answers
	# Enjoy Helper functions
	get_name_key = lambda que_id: Question.objects.get(pk = int(que_id)).sub_category.sub_category_name
	get_que_set = lambda list: set(list.strip().split(',')) if len(list) > 0 else [] 
	for que in sitting.get_incorrect_questions_all():
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

	for que in sitting.get_unanswered_questions_all():
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
def get_data_for_analysis(quiz, unanswered_questions, incorrect_questions):
	data = { 'section_wise':{}, 'selected_questions':{} }
	# unanswerd_and_incorrect_questions_list = unanswered_questions_list + incorrect_questions_list
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
			question = Question.objects.get(id = int(q))
			if question.que_type == QUESTION_TYPE_OPTIONS[0][0]:
				if str(q) in incorrect_questions[QUESTION_TYPE_OPTIONS[0][0]]:
					d_incorrect['y'] += 1
				elif str(q) in unanswered_questions[QUESTION_TYPE_OPTIONS[0][0]]:
					d_unattempt['y'] += 1
				else:
					d_correct['y'] += 1
			elif question.que_type == QUESTION_TYPE_OPTIONS[2][0]:
				comprehension = Comprehension.objects.get(question = q)
				for cq in ComprehensionQuestion.objects.filter(comprehension = comprehension):
						if incorrect_questions[QUESTION_TYPE_OPTIONS[2][0]].has_key(str(q)) and str(cq.id) in incorrect_questions[QUESTION_TYPE_OPTIONS[2][0]][str(q)]:
							d_incorrect['y'] += 1
						elif unanswered_questions[QUESTION_TYPE_OPTIONS[2][0]].has_key(str(q)) and str(cq.id) in unanswered_questions[QUESTION_TYPE_OPTIONS[2][0]][str(q)]:
							d_unattempt['y'] += 1
						else:
							d_correct['y'] += 1			
			data['selected_questions'][q] = {
				'ideal_time' : question.ideal_time,
			}			
		data['section_wise'][section_no].append(d_correct)
		data['section_wise'][section_no].append(d_incorrect)
		data['section_wise'][section_no].append(d_unattempt)
	return data

# Calculate the rank
def get_rank(real_test_user_id, quiz_key, quiz_id, current_score, time_spent):
	all_test_users = TestUser.objects.filter(test_key = quiz_key)
	# all_sitting_objs = Sitting.objects.filter(quiz = quiz_id)
	total = all_test_users.count()
	if total == 0:
		return 1
	else:
		# total = all_test_users.exclude(rank = 0).count()
		# if total == 0:
		# 	rank = 1
		# else:
		rank = total
		for test_user in all_test_users.exclude(id = real_test_user_id):
			max_sitting_obj = get_max_sitting_obj(test_user, quiz_id)
			if max_sitting_obj:
				# print max_sitting_obj.time_spent, time_spent, max_sitting_obj.current_score, current_score
				if current_score > max_sitting_obj.current_score:
					rank -= 1
					print rank
					if test_user.rank+1 <= total:
						test_user.rank += 1
				elif current_score == max_sitting_obj.current_score:
					if time_spent < max_sitting_obj.time_spent:
						rank -= 1
						if test_user.rank+1 <= total:
							test_user.rank += 1
					elif time_spent == max_sitting_obj.time_spent:
						if int(real_test_user_id) < int(test_user.id):
							rank -= 1
							if test_user.rank <= total:
								test_user.rank += 1
				test_user.save()
			else:
				pass
		return rank

# Save rank if rank == 0 (at first attempt) otherwise check if existing rank is better or newly calculated is. Use the minimum rank and save.
def find_and_save_rank(test_user_id, quiz_key, quiz_id, current_score, time_spent):
	try:
		test_user = TestUser.objects.get(id = test_user_id)
		current_rank = test_user.rank
		calculated_rank = get_rank(test_user_id, quiz_key, quiz_id, current_score, time_spent)
		if (current_rank == 0) or (current_rank > calculated_rank):
			test_user.rank = calculated_rank
			test_user.save()
		return test_user.rank
	except Exception as e:
		print e.args
		return 0


def get_max_sitting_obj(test_user, quiz_id):
	sitting_objs = Sitting.objects.filter(user = test_user.user, quiz = quiz_id, complete = True)
	if sitting_objs:
		sitting_obj_topper = sitting_objs[0]
		if(sitting_objs.count() == 1):
			return sitting_obj_topper
		else:
			for sitting in sitting_objs[1:]:
				if sitting.current_score > sitting_obj_topper.current_score:
					sitting_obj_topper = sitting
				elif sitting.current_score == sitting_obj_topper.current_score:
					if sitting.time_spent > sitting_obj_topper.time_spent:
						sitting_obj_topper = sitting
			return sitting_obj_topper
	return None


def get_topper_data(quiz_key, quiz_id):
	try:
		test_user = TestUser.objects.get(test_key = quiz_key, rank = 1)
	except TestUser.DoesNotExist:
		test_user = TestUser.objects.get(test_key = quiz_key, rank = 0)
	return get_max_sitting_obj(test_user, quiz_id)
