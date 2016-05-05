from home.models import InvitedUser
from pyexcel_xls import get_data

def validate_xls_file():
	pass

def save_test_private_access_from_xls(f, quiz):
	with open('test_private_access.xls', 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)
	data = get_data("test_private_access.xls")[1:]
	
	for d in data:
		user_name = d[0]
		user_email = d[1]
		InvitedUser.objects.create(quiz = quiz, user_name = user_name, user_email = user_email)
	return True