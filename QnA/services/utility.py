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


def get_questions_format(quiz, Category, SubCategory, Question, Answer):
	# from quiz.models import SubCategory, Question
	# from mcq.models import Answer
	
	# [Easy, Medium ,Hard, Total]
	questions_level_info = [0 , 0, 0, 0]
	quizzes = []
	qz = {}
	qz['id'] = quiz.id
	qz['title'] = quiz.title
	qz['categories'] = []
	for c in Category.objects.filter(quiz=quiz):
		ca = {}
		ca['category'] = c.category_name
		ca['id'] = c.id
		ca['subcategories'] = []
		for sc in SubCategory.objects.filter(category=c):
			sca = {}
			sca['subcategory'] = sc.sub_category_name
			sca['id'] = sc.id
			sca['questions'] = []
			for question in Question.objects.filter(sub_category=sc)[:10]:
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
				sca['questions'].append(d)
			ca['subcategories'].append(sca)
		qz['categories'].append(ca)
	quizzes.append(qz)
	questions_level_info[3] = sum(questions_level_info)
	quizzes.insert(0,{'questions_level_info' : questions_level_info})

	return quizzes

