from django.utils.translation import ugettext as _


QUESTION_DIFFICULTY_OPTIONS = (
	('easy', _('EASY')),
	('medium', _('MEDIUM')),
	('hard', _('HARD'))
)

ANSWER_ORDER_OPTIONS = (
    ('content', _('CONTENT')),
    ('random', _('RANDOM')),
    ('none', _('NONE'))
)

MCQ_FILE_ROWS = ['quiz', 'category', 'sub_category', 'level', 'explanation', 'answer_order', 'option1', 'option2', 'option3' ,
'option4', 'option5', 'option6', 'correctoption', 'content']


def get_questions_format(user_id, subcategory_id=None, question_format=False):
	from quiz.models import Question, SubCategory
	from mcq.models import Answer
	questions_level_info = [0 , 0, 0, 0] # [Easy, Medium ,Hard, Total]
	if subcategory_id:
		sc = SubCategory.objects.get(id=subcategory_id, user=user_id)
		questions = Question.objects.filter(sub_category=sc)
	else:
		sc = SubCategory.objects.filter(user=user_id)[0]
		questions = Question.objects.filter(sub_category=sc)[:10]
	sca = {}
	sca['subcategory'] = sc.sub_category_name
	sca['id'] = sc.id
	sca['questions'] = []
	for question in questions:
		d = {
			'id' : question.id,
			'level' : question.level,
			'content' : question.content,
			'options'  : [{ 'id' : answer.id, 'content' : answer.content, 'correct' : answer.correct } for answer in Answer.objects.filter(question=question)]
		}
		if question.level == 'easy':
			questions_level_info[0] = questions_level_info[0] + 1
		elif question.level == 'medium':
			questions_level_info[1] = questions_level_info[1] + 1
		else:
			questions_level_info[2] = questions_level_info[2] + 1
		if not question_format:
			sca['questions'].append(d)
	questions_level_info[3] = sum(questions_level_info)
	sca['questions_level_info'] = questions_level_info
	return sca;
		

