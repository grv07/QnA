# from mcq.models import Answer
from mcq.serializer import AnswerSerializer
from comprehension.serializer import ComprehensionAnswerSerializer
import logging
logger = logging.getLogger(__name__)

def create_mcq_answer(question, options):
	'''
	Create a answer of a MCQuestion
	ex. options = [{'content':'text','correct':True},{'content':'text','correct':False},{'content':'text','correct':False}]
	'''
	logger.info('QnA.services.answer_engine.create_mcq_answer')
	if any([op['correct'] for op in options]):
		for option in options:
			option.update({ 'question' : question })
			serializer = AnswerSerializer(data = option)
			if serializer.is_valid():
				serializer.save()
			else:
				logger.error('QnA.services.answer_engine.create_mcq_answer '+str(serializer.errors))
				return (False, serializer.errors,)
		return (True, None,)
	else:
		logger.error('QnA.services.answer_engine.create_mcq_answer error MAX Options size=6 and please select only one option as correct ans.')
		return (False, {'errors':'MAX Options size=6 and please select only one option as correct ans.'})


def create_comprehension_answer(question, options):
	'''
	Create a answer of a ComprehensionQuestion
	ex. options = [{'content':'text','correct':True},{'content':'text','correct':False},{'content':'text','correct':False}]
	'''
	logger.info('QnA.services.answer_engine.create_comprehension_answer')
	if any([op['correct'] for op in options]):
		for option in options:
			option.update({ 'question' : question })
			serializer = ComprehensionAnswerSerializer(data = option)
			if serializer.is_valid():
				serializer.save()
			else:
				logger.error('QnA.services.answer_engine.create_comprehension_answer '+str(serializer.errors))
				return (False, serializer.errors,)
		return (True, None,)
	else:
		logger.error('QnA.services.answer_engine.create_comprehension_answer error MAX Options size=6 and please select only one option as correct ans.')
		return (False, {'errors':'MAX Options size=6 and please select only one option as correct ans.'})
