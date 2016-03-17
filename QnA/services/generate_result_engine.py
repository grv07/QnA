from mcq.models import MCQuestion
from objective.models import ObjectiveQuestion
from quiz.models import Sitting, Quiz, Question
from .utility import QUESTION_TYPE_OPTIONS

def generate_result(section_result, sitting_id, cache_key , na_nv_dict):
	'''{u'answers': {
		u'47': {u'status': u'NA', u'value': None},
		u'20': {u'status': u'NA', u'value': None}, 
		u'21': {u'status': u'NA', u'value': None},
		u'22': {u'status': u'A',u'value': 74}, 
		u'48': {u'status': u'A',u'value': u'6'}
		}
	 }'''

	# NA = na_nv_dict['NA'] 
	# NA = na_nv_dict['NV']
	quiz_key,user_ro_no,section_id, = tuple(cache_key.strip().split("|"))
	
	quiz = Quiz.objects.get(quiz_key = quiz_key)
	sitting_obj = Sitting.objects.get(pk = sitting_id, quiz = quiz)
	# print sitting_obj
	for q_list in na_nv_dict:
		if na_nv_dict[q_list]:
			for q_id in na_nv_dict[q_list]:
				sitting_obj.add_unanswerd_question(q_id)

	if section_result:
		_progress_list = section_result['answers']

		for question_id in _progress_list.keys():
			_dict_data = _progress_list.get(str(question_id))
			is_correct = False
			if not _dict_data.get('status') == 'NA' and not _dict_data.get('value') == None:
				try:
					question = Question.objects.get(pk = question_id)
					print question.que_type, question.id
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
			else:
				sitting_obj.add_unanswerd_question(question_id)

		sitting_obj.complete = True
		sitting_obj.save()
			# else:
				# sitting_obj.add_unanswerd_question(question_id)
		return True		
				

def filter_by_category(sitting):
	import json
	_cat_base_result = {}
	_correct_ans = json.loads(sitting.user_answers)
	
	# Lambda to get name_key
	get_name_key = lambda que_id: Question.objects.get(pk = int(que)).sub_category.sub_category_name

	for que in set(sitting.incorrect_questions_list.split(',')):
		name_key = get_name_key(int(que))
		_correct_ans.pop(que)
		if not _cat_base_result.has_key(name_key):
			_cat_base_result[name_key] = {}
			_cat_base_result[name_key]['incorrect'] = [que]
			_cat_base_result[name_key]['correct'] = []
		else:
			_cat_base_result[name_key]['incorrect'].append(que)

	for que in _correct_ans:		
		_cat_base_result[get_name_key(int(que))]['correct'].append(que)

	return _cat_base_result	
