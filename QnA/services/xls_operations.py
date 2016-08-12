from home.models import InvitedUser
from pyexcel_xls import get_data
from mail_handling import send_mail
from constants import PRIVATE_TEST_ACCESS_HTML
from QnA.settings import TEST_URL
from quiz.models import Quiz

def validate_xls_file():
	pass

def save_test_private_access_from_xls(f, quiz_id):
	with open('test_private_access.xls', 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)
	data = get_data("test_private_access.xls")[1:]
	try:
		quiz = Quiz.objects.get(id = quiz_id)
		for d in data:
			user_name = d[0]
			user_email = d[1]
			inviteduser, created = InvitedUser.objects.get_or_create(user_name = user_name, user_email = user_email)
			inviteduser.add_inviteduser(quiz_id)
			html = PRIVATE_TEST_ACCESS_HTML.format(quiz_name = quiz.title, test_link = quiz.url)
			send_mail(html, user_email, subject = "Test access granted")
		return True
	except Exception as e:
		return False
