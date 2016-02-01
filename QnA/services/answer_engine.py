# from mcq.models import Answer
from mcq.serializer import AnswerSerializer


def create_answer(question, options):
	'''
	Create a answer of a MCQuestion
	ex. options = [{'content':'text','correct':True},{'content':'text','correct':False},{'content':'text','correct':False}]
	'''
	for option in options:
		serializer = AnswerSerializer(data = option)
		if serializer.is_valid():
			serializer.save()
		else:
			print serializer.errors
	return True