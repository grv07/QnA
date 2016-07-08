from django.utils.translation import ugettext as _

QUESTION_DIFFICULTY_OPTIONS = (
	('easy', _('EASY')),
	('medium', _('MEDIUM')),
	('hard', _('HARD'))
)

QUESTION_TYPE_OPTIONS = (
	('mcq', _('MCQ')),
	('objective', _('OBJECTIVE')),
	('comprehension', _('COMPREHENSION')),
)

ANSWER_ORDER_OPTIONS = (
    ('content', _('CONTENT')),
    ('random', _('RANDOM')),
    ('none', _('NONE'))
)

QUIZ_TYPE_OPTIONS = (
    ('DEFAULT', _('DEFAULT')),
    ('LIVE', _('LIVE'))
)

MCQ_PROBLEM_OPTIONS = (
	('correct value', _('correct value')),
    ('incorrect sentence', _('incorrect sentence')),
    ('coherent paragraph', _('coherent paragraph')),
    ('meaning', _('meaning')),
    ('antonym', _('antonym')),
    ('conclusion', _('conclusion')),
    ('relationship', _('relationship')),
    ('best option',_('best option')),
    ('argument',_('argument')),
)


SUBMISSION_TYPE = ( 'Normal', 'TimeUp', 'WindowClose', 'Retry', )

MCQ_FILE_COLS = ['category', 'sub_category', 'level', 'explanation', 'answer_order', 'option1', 'option2', 'option3' ,
'option4', 'option5', 'option6', 'correctoption', 'content', 'ideal_time', 'problem_type']

OBJECTIVE_FILE_COLS = ['sub_category', 'level', 'explanation', 'correct', 'content']

QUIZ_ACCESS_FILE_COLS = ['user_name', 'email']

BLANK_HTML = "_"*10

CACHE_TIMEOUT = 72000

REGISTRATION_HTML = "<p><p>Hello <b>{name}</b>,</p><br><p>Thanks for registering on <b>QnA</b>.</p><p>You username is <b>{username}</b>.</p></p>"

RESULT_HTML = "<p><p>Hello <b>{username}</b>,</p><br><p>You attempted a test for Quiz <b>{quiz_name}</b>.</p><br>You can view your test report here <a href='{report_link}'>report link.</a></p>"

PRIVATE_TEST_ACCESS_HTML = "<p><p>You are allowed to attempt quiz - <b>{quiz_name}</b>.</p><p><a href='{test_link}'>Click to start test</a></p>.</p>"

MAX_OPTIONS = 6

USER_COOKIE_SALT = "QnAssessment"

TEST_STATUSES = ( 'INCOMPLETE', 'ToBeTaken',)

