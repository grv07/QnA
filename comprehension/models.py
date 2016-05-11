from __future__ import unicode_literals
from django.db import models
from django.utils.translation import ugettext as _
from django.core.validators import MaxValueValidator

from quiz.models import SubCategory, Question
from QnA.services.constants import QUESTION_DIFFICULTY_OPTIONS


class Comprehension(models.Model):
	question = models.OneToOneField(Question,blank=False, null=False, verbose_name=_("Question"))
	heading = models.CharField(max_length=200,
							   unique = True,
							   help_text=_("Enter the heading text that "
										   "you want displayed"),
							   verbose_name=_('Comprehension'))

def figure_directory_for_comprehension_question(instance, filename):
    return '/qna/media/comprehension/{0}/{1}/{2}'.format(instance.comprehension.question.sub_category.sub_category_name, instance.comprehension.question.id, filename)


class ComprehensionQuestion(models.Model):
	comprehension = models.ForeignKey(Comprehension,blank=False, null=False, verbose_name=_("Comprehension"))

	figure = models.ImageField(upload_to=figure_directory_for_comprehension_question,
							   blank=True,
							   null=True,
							   verbose_name=_("Figure"))

	content = models.CharField(max_length=1000,
							   blank=False,
							   help_text=_("Enter the question text that "
										   "you want displayed"),
							   verbose_name=_('ComprehensionQuestion'))

	explanation = models.TextField(max_length=1000,
								   blank=True,
								   help_text=_("Explanation to be shown "
											   "after the question has "
											   "been answered."),
								   verbose_name=_('Explanation'))

	points = models.IntegerField(verbose_name=_("Marks"), default=1, blank=True)

	level = models.CharField(max_length=10,default = 'easy',
								choices=QUESTION_DIFFICULTY_OPTIONS,
								help_text=_("The difficulty level of a ComprehensionQuestion"),
								verbose_name=_("Difficulty Level"))

	ideal_time = models.PositiveSmallIntegerField(validators=[MaxValueValidator(300)])

	created_date = models.DateTimeField(auto_now_add = True)
	updated_date = models.DateTimeField(auto_now = True)


	class Meta:
		verbose_name = _("ComprehensionQuestion")
		verbose_name_plural = _("ComprehensionQuestions")

	def __str__(self):
		return self.content
		


class ComprehensionAnswer(models.Model):
    question = models.ForeignKey(ComprehensionQuestion, verbose_name=_("ComprehensionQuestion"))

    content = models.CharField(max_length=500,
                               blank=False,
                               help_text=_("Enter the answer text that "
                                           "you want displayed"),
                               verbose_name=_("Content"))

    correct = models.BooleanField(blank=False,
                                  default=False,
                                  help_text=_("Is this a correct answer?"),
                                  verbose_name=_("Correct"))

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = _("ComprehensionAnswer")
        verbose_name_plural = _("ComprehensionAnswers")

