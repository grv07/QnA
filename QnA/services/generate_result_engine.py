from mcq.models import MCQuestion
from quiz.models import Sitting, Quiz

def generate_result(cache_key = '78guuuFk|ykbf787|2', section_result, sitting_id):
	'''{u'progressValues': {
		u'47': {u'status': u'NA', u'value': None},
	 	u'20': {u'status': u'NA', u'value': None}, 
	 	u'21': {u'status': u'NA', u'value': None},
	 	u'22': {u'status': u'A',u'value': 74}, 
	 	u'48': {u'status': u'A',u'value': u'6'}
	 	}
	 }'''

	quiz_key,user_ro_no,section_id, = tuple(cache_key.strip().split("|"))
	
	quiz = Quiz.objects.get(quiz_key = quiz_key)
	siting_obj = Sitting.objects.get(pk = sitting_id, quiz = quiz)
    
	if section_result:
		_progress_list = section_result['progressValues']

		for question_id in _progress_list:
			_dict_data = _progress_list.get(str(question_id))
			if not _dict_data.get('status') == 'NA' and _dict_data.get('value') == None:
				try:
					mc_que = MCQuestion.objects.get(pk = question_id)
				except MCQuestion.DoesNotExist as e:
					print e.args
					return None
				'''If given ans is correct or not'''
				siiting_obj.add_user_answer(question_id, _dict_data.get('value'))
				if mc_que.check_if_correct(_dict_data.get('value')):
					siting_obj.add_to_score(mc_que.points)
				else:
					siting_obj.add_incorrect_question(question_id)	
			else:
				siting_obj.add_unanswerd_question(question_id)
				

						

