from __future__ import unicode_literals
from django.utils.translation import ugettext as _

from django.db import models
from quiz.models import Quiz, SubCategory
from QnA.services.utility import ANSWER_ORDER_OPTIONS, QUESTION_DIFFICULTY_OPTIONS

# Create your models here.
'''
QuizStack model & manager
'''
class QuizStackManager(models.Manager):
	def list_all(self, uuid, start=0 , end=5):
		pass

	def get_quiz_questions(self, que_type, level, question_order, ):
		'level, que_type, no_questions, question_order'
		'''Get all questions according to given criteria.'''
		if que_type == 'mcq':
			questions = MCQQuestion.objects.filter(sub_category = self.subcategory, level = level)
		else:
			questions = ObjectiveQuestion.objects.filter(sub_category = self.subcategory, level = level)
		
		# Suffle a list if want random order
		if question_order == 'random':
			from random import shuffle
			questions = shuffle(questions[:criteria.get(no_questions)])
		# Don't shuffle just slice list
		else:
			questions = questions[:criteria.get(no_questions)]
		return questions

class QuizStack(models.Model):
	""" Model to represent Comments Database """
	quiz = models.ForeignKey(Quiz, related_name = 'quizstack_quiz')
	subcategory = models.ForeignKey(SubCategory, related_name = 'quizstack_subcategory')
	section_name = models.CharField(max_length = 30, default='section#1')
	
	# Selection criteria for questions
	level = models.CharField(max_length = 30, choices = QUESTION_DIFFICULTY_OPTIONS, default='easy')
	que_type = models.CharField(max_length = 30)
	no_questions = models.IntegerField()
	question_order = models.CharField(max_length=7, choices = ANSWER_ORDER_OPTIONS, default='random')
	# END

	correct_grade = models.IntegerField(default = 1)
	incorrect_grade = models.IntegerField(default = 0)
	istimed = models.BooleanField(default = True)

	created_date = models.DateTimeField(auto_now_add = True)
	updated_date = models.DateTimeField(auto_now = True)
	
	objects = QuizStackManager()

	class Meta:
		verbose_name = _('QuizStack')
		ordering = ['created_date']

	def __unicode__(self):
		return unicode(self.id)

	def save(self, *args, **kwargs):
		super(QuizStack, self).save(*args, **kwargs)