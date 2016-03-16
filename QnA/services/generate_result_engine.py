from mcq.models import MCQuestion
from objective.models import ObjectiveQuestion
from quiz.models import Sitting, Quiz, Question
from .utility import QUESTION_TYPE_OPTIONS

def generate_result(section_result, sitting_id, cache_key = '78guuuFk|ykbf787|2'):
	'''{u'progressValues': {
		u'47': {u'status': u'NA', u'value': None},
		u'20': {u'status': u'NA', u'value': None}, 
		u'21': {u'status': u'NA', u'value': None},
		u'22': {u'status': u'A',u'value': 74}, 
		u'48': {u'status': u'A',u'value': u'6'}
		}
	 }'''
	print section_result
	quiz_key,user_ro_no,section_id, = tuple(cache_key.strip().split("|"))
	
	quiz = Quiz.objects.get(quiz_key = quiz_key)
	print '>>>>>>>>>>>',sitting_id
	sitting_obj = Sitting.objects.get(pk = sitting_id, quiz = quiz)
	# print sitting_obj
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
				

						

