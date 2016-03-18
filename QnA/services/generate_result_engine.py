from mcq.models import MCQuestion
from objective.models import ObjectiveQuestion
from quiz.models import Sitting, Quiz, Question
from .utility import QUESTION_TYPE_OPTIONS

def generate_result(section_result, sitting_obj, cache_key):
	'''{u'answers': {
		u'47': {u'status': u'NA', u'value': None},
		u'20': {u'status': u'NA', u'value': None}, 
		u'21': {u'status': u'NA', u'value': None},
		u'22': {u'status': u'A',u'value': 74}, 
		u'48': {u'status': u'A',u'value': u'6'}
		}
	 }'''
	 
	answered_questions_list = []
	quiz_key,user_ro_no,section_id, = tuple(cache_key.strip().split("|"))
	if section_result:
		_progress_list = section_result['answers']

		for question_id in _progress_list.keys():
			_dict_data = _progress_list.get(str(question_id))
			is_correct = False
			if not _dict_data.get('status') == 'NA' and not _dict_data.get('value') == None:
				try:
					question = Question.objects.get(pk = question_id)
				except Question.DoesNotExist as e:
					print e.args
					return None
				'''Check if given answers are correct or not'''
				sitting_obj.add_user_answer(question_id, _dict_data.get('value'))
				if question.que_type == QUESTION_TYPE_OPTIONS[0][0]:
					is_correct = MCQuestion.objects.get(pk = question_id).check_if_correct(_dict_data.get('value'))
				elif question.que_type == QUESTION_TYPE_OPTIONS[1][0]:
					is_correct = ObjectiveQuestion.objects.get(pk = question_id).check_if_correct(_dict_data.get('value'))
				if is_correct:
					sitting_obj.add_to_score(question.points)
				else:
					sitting_obj.add_incorrect_question(question_id)
				answered_questions_list.append(question.id)
		return answered_questions_list		
				

def filter_by_category(sitting):
	'''Return {'sub_cat_name':(incorrect, correct, unattemped, total), total_correct}'''
	import json
	# Cat wise filter on question, Total correct questions
	_cat_base_result = {}
	total_correct_que = 0
	_correct_ans = json.loads(sitting.user_answers)

	get_name_key = lambda que_id: Question.objects.get(pk = int(que)).sub_category.sub_category_name

	for que in set(sitting.incorrect_questions_list.split(',')):
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

	for que in set(sitting.unanswerd_question_list.split(',')):
		name_key = get_name_key(int(que))
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
		name_key = get_name_key(int(que))
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
