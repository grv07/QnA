from __future__ import unicode_literals

from django.db import models
from quiz.models import Quiz, SubCategory

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
    sectionname = models.CharField(max_length = 30)
    section_level = models.CharField(max_length = 30)
    q_type = models.CharField(max_length = 30)
    no_questions = models.IntegerField()
    istimed = models.BooleanField()
    correct_grade = models.IntegerField()
    incorrect_grade = models.IntegerField()
    selection = models.CharField(max_length=7)
    created_date = models.DateTimeField(auto_now_add = True)
	updated_date = models.DateTimeField(auto_now = True)
    objects = QuizStackManager()

    class Meta:
        verbose_name = _('QuizStack')
        ordering = ['-added_date']

    def __unicode__(self):
        return unicode(self.id)

    def save(self, *args, **kwargs):
        super(QuizStack, self).save(*args, **kwargs)