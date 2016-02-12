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


class QuizStack(models.Model):
	""" Model to represent Comments Database """
	quiz = models.ForeignKey(Quiz, related_name = 'quizstack_quiz')
	subcategory = models.ForeignKey(SubCategory, related_name = 'quizstack_subcategory')
	sectionname = models.CharField(max_length = 30, default='section#1')
	section_level = models.CharField(max_length = 30, choices = QUESTION_DIFFICULTY_OPTIONS, default='easy')
	q_type = models.CharField(max_length = 30)
	no_questions = models.IntegerField()
	istimed = models.BooleanField(default = True)
	correct_grade = models.IntegerField(default = 1)
	incorrect_grade = models.IntegerField(default = 0)
	selection = models.CharField(max_length=7, choices = ANSWER_ORDER_OPTIONS, default='random')
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