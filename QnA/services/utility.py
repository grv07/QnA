from django.utils.translation import ugettext as _


QUESTION_DIFFICULTY_OPTIONS = (
	('easy', _('EASY')),
	('medium', _('MEDIUM')),
	('hard', _('HARD'))
)

QUESTION_TYPE_OPTIONS = (
	('mcq', _('MCQ')),
	('objective', _('OBJECTIVE')),
	# ('hard', _('HARD'))
)

ANSWER_ORDER_OPTIONS = (
    ('content', _('CONTENT')),
    ('random', _('RANDOM')),
    ('none', _('NONE'))
)

MCQ_FILE_COLS = ['category', 'sub_category', 'level', 'explanation', 'answer_order', 'option1', 'option2', 'option3' ,
'option4', 'option5', 'option6', 'correctoption', 'content']

OBJECTIVE_FILE_COLS = ['sub_category', 'level', 'explanation', 'correct', 'content']

BLANK_HTML = "<<Answer>>"

# UPLOAD_LOCATION = '/qna/media/'

def get_category_format(category_list, subcategory):
	pass


def get_questions_format(user_id, subcategory_id = None, is_have_sub_category = False):
	from quiz.models import Question, SubCategory
	from mcq.models import Answer
	from objective.models import ObjectiveQuestion

	questions_level_info = [0 , 0, 0, 0] # [Easy, Medium ,Hard, Total]
	sca = {'subcategory' : None, 'id' : None, 'question' : None, 'questions_level_info' : None}

	if subcategory_id:
		try:
			sc = SubCategory.objects.get(id = subcategory_id, user = user_id)
		except SubCategory.DoesNotExist as e:
			print e.args
			return None
		questions = Question.objects.filter(sub_category = sc)
	else:
		try:
			sc = SubCategory.objects.filter(user = user_id)[1]
		except SubCategory.DoesNotExist as e:
			print e.args
			return None
		questions = Question.objects.filter(sub_category = sc)
		# questions = questions[:10] if len(questions) > 10 else None

	sca['subcategory'] = sc.sub_category_name
	sca['id'] = sc.id
	sca['questions'] = []
	print questions
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
			
			if not is_have_sub_category:
				print 'under there'
				sca['questions'].append(d)
	else:
		print 'Not have questions <<<<<<<<<<<>>>>>>>>>>>>'

	questions_level_info[3] = sum(questions_level_info)
	sca['questions_level_info'] = questions_level_info
	print sca
	return sca;

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



def shuffleList(l):
	from random import shuffle
	shuffle(l)
	return l