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

CACHE_TIMEOUT = 18000

REGISTRATION_HTML = "<p><p>Hello <b>{name}</b>,</p><br><p>Thanks for registering on <b>QnA</b>.</p><p>You username is <b>{username}</b>.</p></p>"
