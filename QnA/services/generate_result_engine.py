from mcq.models import MCQuestion, Answer
from objective.models import ObjectiveQuestion
from quiz.models import Sitting, Quiz, Question
from quizstack.models import QuizStack
from home.models import TestUser
from comprehension.models import Comprehension, ComprehensionQuestion, ComprehensionAnswer
from .constants import QUESTION_TYPE_OPTIONS

def generate_result(initial_unanswered_questions, answers, comprehension_answers, sitting_obj, quizstack, time_spent_on_question, time_spent):
	'''
	initial_unanswered_questions = {"mcq": {"11": [], "12": [], "13": [], "32": [], "33": [], "48": []}, "comprehension": {"46": {"4": 0, "6": 0}, "53": {"7": 0, "8": 0}}} 

	{u'test_key': u'93h1m9mimu', u'test_user': 142, 
	u'comprehension_answers': {u'8': {u'value': u'18'}, u'4': {u'value': u'3'}, u'7': {u'value': u'14'}, u'6': {u'value': None}}, 
	u'time_spent_on_question': {u'11': {u'time': 1}, u'13': {u'time': 84}, u'12': {u'time': 3}, u'48': {u'time': 2}, u'33': {u'time': 5}, u'32': {u'time': 2}, u'53': {u'time': 4}, u'46': {u'time': 6}}, 
	u'answers': {u'11': {u'value': None}, u'13': {u'value': None}, u'12': {u'value': u'47'}, u'48': {u'value': u'127'}, u'33': {u'value': u'121'}, u'32': {u'value': u'116'}, u'53': {u'comprehension_questions': [], u'heading': u'Elephant', u'value': None}, u'46': {u'comprehension_questions': [], u'heading': u'Divide the sail', u'value': None}}, 
	u'time_spent': 58, 
	u'bookmarked_questions': {u'comprehension': [4], u'mcq': [33, 11, 13]}}

	The data inside temp_unanswered_questions will be the final output for unanswered_questions in Sitting table.
	The data inside temp_user_answered_questions will be the final output for user_answers in Sitting table.
	The data inside temp_user_incorrect_questions will be the final output for incorrect_questions in Sitting table.
	'''


	temp_unanswered_questions = { QUESTION_TYPE_OPTIONS[0][0]:{}, QUESTION_TYPE_OPTIONS[2][0]:{} }
	temp_user_answered_questions = { QUESTION_TYPE_OPTIONS[0][0]:{}, QUESTION_TYPE_OPTIONS[2][0]:{} }
	temp_user_incorrect_questions = { QUESTION_TYPE_OPTIONS[0][0]:[], QUESTION_TYPE_OPTIONS[2][0]:{} }

	comprehension_unanswered_questions = initial_unanswered_questions[QUESTION_TYPE_OPTIONS[2][0]]
	mcq_unanswered_questions_list = initial_unanswered_questions[QUESTION_TYPE_OPTIONS[0][0]].keys()
	
	question_ids_list = mcq_unanswered_questions_list + comprehension_unanswered_questions.keys()	
	print question_ids_list,'question_ids_list'
	print time_spent_on_question
	print time_spent
	print answers
	print comprehension_answers
	current_score = 0
	try:
		for question_id in question_ids_list:
			is_correct = False
			print question_id,'question_id'
			# if not _dict_data.get('status') == 'NA' and not _dict_data.get('value') == None:
			question = Question.objects.get(id = question_id)
			quizstack_obj = quizstack.filter(subcategory = question.sub_category, que_type = question.que_type)[0]
			if time_spent_on_question.has_key(question_id):
				time_spent = round(time_spent_on_question[question_id].get('time', 0), 2)
			else:
				time_spent = 0.0
			if question.que_type == QUESTION_TYPE_OPTIONS[0][0]:
				print time_spent,'time_spent'
				if answers.has_key(question_id) and answers.get(question_id).get('value') != None:
					user_answer = int(answers.get(question_id).get('value'))
					is_correct = MCQuestion.objects.get(pk = question_id).check_if_correct(user_answer)
					temp_user_answered_questions[QUESTION_TYPE_OPTIONS[0][0]][question_id] = [ user_answer, time_spent ]
					# sitting_obj.add_user_mcq_answer(question_id, [ int(user_answer), time_spent ] )
					if is_correct:
						# sitting_obj.add_to_score(quizstack_obj.correct_grade)
						current_score += int(quizstack_obj.correct_grade)
					else:
						temp_user_incorrect_questions[QUESTION_TYPE_OPTIONS[0][0]].append(question_id)
						# sitting_obj.add_incorrect_mcq_question(question_id)
						current_score -= int(quizstack_obj.incorrect_grade)
				else:
					temp_unanswered_questions[QUESTION_TYPE_OPTIONS[0][0]][question_id] = time_spent
				# answered_questions[QUESTION_TYPE_OPTIONS[0][0]].append(question_id)

			elif question.que_type == QUESTION_TYPE_OPTIONS[2][0]:

				# answered_questions[QUESTION_TYPE_OPTIONS[2][0]] = { question_id: [] }
				for cq in comprehension_unanswered_questions.get(question_id).keys():
					print cq, 'cq'
					if comprehension_answers.has_key(cq) and comprehension_answers.get(cq).get('value') != None:
						user_comprehension_answer = int(comprehension_answers.get(cq).get('value'))
						if temp_user_answered_questions[QUESTION_TYPE_OPTIONS[2][0]].has_key(question_id):
							temp_user_answered_questions[QUESTION_TYPE_OPTIONS[2][0]][question_id].update({ cq: user_comprehension_answer })
						else:
							temp_user_answered_questions[QUESTION_TYPE_OPTIONS[2][0]][question_id] = { cq: user_comprehension_answer }
							temp_user_answered_questions[QUESTION_TYPE_OPTIONS[2][0]][question_id]['time_spent'] = time_spent
						# sitting_obj.add_user_comprehension_answer(question_id, { cq: user_comprehension_answer }, time_spent)
						is_comprehension_correct = ComprehensionQuestion.objects.get(id = cq).check_if_correct(user_comprehension_answer)
						if is_comprehension_correct:
							current_score += int(quizstack_obj.correct_grade)
							# print 'score', sitting_obj.current_score
							# sitting_obj.add_to_score(quizstack_obj.correct_grade)
						else:
							print question_id,cq
							# sitting_obj.add_incorrect_comprehension_question(question_id, cq)
							if temp_user_incorrect_questions[QUESTION_TYPE_OPTIONS[2][0]].has_key(question_id):
								temp_user_incorrect_questions[QUESTION_TYPE_OPTIONS[2][0]][question_id].append(cq)
							else:
								temp_user_incorrect_questions['comprehension'][question_id] = [ cq ]
							# self.add_to_score(incorrect_point)
							current_score -= int(quizstack_obj.incorrect_grade)
					else:
						if temp_unanswered_questions[QUESTION_TYPE_OPTIONS[2][0]].has_key(question_id):
							temp_unanswered_questions[QUESTION_TYPE_OPTIONS[2][0]][question_id].update({ cq: 0 })
						else:
							temp_unanswered_questions[QUESTION_TYPE_OPTIONS[2][0]][question_id] = { cq: 0 }

					# answered_questions[QUESTION_TYPE_OPTIONS[2][0]][question_id].append(cq)
		# print answered_questions,'answered_questions'

		# Save all properties on a single save() call on database.
		sitting_obj.unanswered_questions = temp_unanswered_questions
		sitting_obj.incorrect_questions = temp_user_incorrect_questions
		sitting_obj.user_answers = temp_user_answered_questions
		sitting_obj.current_score = current_score
		sitting_obj.complete = True
		sitting_obj.time_spent = sitting_obj.quiz.total_duration - time_spent
		sitting_obj.save()
		return True
	except Exception as e:
		print e.args,'---------'
		return False
	

				

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
