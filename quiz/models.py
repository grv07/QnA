from __future__ import unicode_literals

import re
import json
import string, random

from django.db import models
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.validators import MaxValueValidator
from django.utils.translation import ugettext as _
from django.utils.timezone import now
from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField


from QnA.services.constants import QUESTION_DIFFICULTY_OPTIONS, QUESTION_TYPE_OPTIONS, QUIZ_TYPE_OPTIONS

@python_2_unicode_compatible
class Quiz(models.Model):

	user = models.ForeignKey(User)

	quiz_key = models.CharField(
		verbose_name=_("Quiz Key"),
		max_length = 20, blank = True, unique = True)

	title = models.CharField(
		verbose_name=_("Title"),
		max_length=60, blank = False)

	user_picturing = models.BooleanField(default = False,
		verbose_name=_("User pict."),
		help_text=_("Take a user picture when start test?"))

	url = models.URLField(
		blank=True, help_text=_("a user friendly url"),
		verbose_name=_("user friendly url"))

	quiz_type = models.CharField(default=QUIZ_TYPE_OPTIONS[0],
		choices = QUIZ_TYPE_OPTIONS,
		max_length = 60, blank = False)

	start_notification_url = models.URLField(blank=True, null=True)
	finish_notification_url = models.URLField(blank=True, null=True)
	grade_notification_url = models.URLField(blank=True, null=True)

	no_of_attempt = models.IntegerField(
		blank=False, default=False,
		help_text=_("If yes, only one attempt by"
					" a user will be permitted."
					" Non users cannot sit this exam."),
		verbose_name=_("Single Attempt"))

	passing_percent = models.IntegerField(
		blank=True, default=10,
		verbose_name=_("Pass Percent"),
		help_text=_("Percentage required to pass exam."),
		validators=[MaxValueValidator(100)])

	success_text = models.TextField(
		blank=True, help_text=_("Displayed if user passes."),
		verbose_name=_("Success Text"))

	fail_text = models.TextField(
		verbose_name=_("Fail Text"),
		blank=True, help_text=_("Displayed if user fails."))

	total_marks = models.IntegerField(
		blank=True, default=0,
		verbose_name=_("total_marks"))

	allow_public_access = models.BooleanField(default = False,
		help_text=_("Allow all_users to take test."),blank=True
		)

	total_questions = models.IntegerField(blank=True, default=0)

	total_duration = models.IntegerField(blank=True, default=0)

	total_sections = models.IntegerField(default=0)

	show_result_on_completion = models.BooleanField(default=True)

	# draft = models.BooleanField(
	# 	blank=True, default=False,
	# 	verbose_name=_("Draft"),
	# 	help_text=_("If yes, the quiz is not displayed"
	# 				" in the quiz list and can only be"
	# 				" taken by users who can edit"
	# 				" quizzes."))

	created_date = models.DateTimeField(auto_now_add = True)
	updated_date = models.DateTimeField(auto_now = True)

	def save(self, force_insert=False, force_update=False, *args, **kwargs):
		if not self.quiz_key:
			self.quiz_key = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(10))
			self.url = settings.TEST_URL+str(self.quiz_key)
		super(Quiz, self).save(force_insert, force_update, *args, **kwargs)

	class Meta:
		unique_together = ('user', 'title',)
		verbose_name = _("Quiz")
		verbose_name_plural = _("Quizzes")
		# ordering = ['updated_date']

	def __str__(self):
		return self.title

	def get_questions(self):
		return self.question_set.all().select_subclasses()

	@property
	def get_max_score(self):
		return self.get_questions().count()

	def anon_score_id(self):
		return str(self.id) + "_score"

	def anon_q_list(self):
		return str(self.id) + "_q_list"

	def anon_q_data(self):
		return str(self.id) + "_data"


class CategoryManager(models.Manager):

	def new_category(self, category):
		new_category = self.create(category=re.sub('\s+', '-', category).lower())
		new_category.save()
		return new_category


@python_2_unicode_compatible
class Category(models.Model):

	category_name = models.CharField(
		verbose_name=_("Category"),
		max_length=250,
		unique = True)

	user = models.ForeignKey(User)

	created_date = models.DateTimeField(auto_now_add = True)
	updated_date = models.DateTimeField(auto_now = True)

	objects = CategoryManager()

	class Meta:
		verbose_name = _("Category")
		verbose_name_plural = _("Categories")
		unique_together = ("category_name", "user",)

	def __str__(self):
		return self.category_name

	def save(self, force_insert=False, force_update=False, *args, **kwargs):
		self.category_name = re.sub('\s+', '-', self.category_name).lower()

		self.url = ''.join(letter for letter in self.category_name if
						   letter.isalnum() or letter == '-')
		
		super(Category, self).save(force_insert, force_update, *args, **kwargs)

@python_2_unicode_compatible
class SubCategory(models.Model):

	sub_category_name = models.CharField(
		verbose_name=_("Sub-Category"),
		max_length=250)

	user = models.ForeignKey(User)

	category = models.ForeignKey(
		Category,verbose_name=_("Category"), null=True, blank=True)

	created_date = models.DateTimeField(auto_now_add = True)
	updated_date = models.DateTimeField(auto_now = True)

	objects = CategoryManager()

	class Meta:
		verbose_name = _("Sub-Category")
		verbose_name_plural = _("Sub-Categories")
			#This update category to >>> null=False if set unique with category
		unique_together = ("sub_category_name", "user",)


	def __str__(self):
		return self.sub_category_name


class ProgressManager(models.Manager):

	def new_progress(self, user):
		new_progress = self.create(user=user,
								   score="")
		new_progress.save()
		return new_progress


class Progress(models.Model):
	"""
	Progress is used to track an individual signed in users score on different
	quiz's and categories

	Data stored in csv using the format:
		category, score, possible, category, score, possible, ...
	"""
	user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_("User"))

	score = models.CommaSeparatedIntegerField(max_length=1024,
											  verbose_name=_("Score"))

	objects = ProgressManager()

	class Meta:
		verbose_name = _("User Progress")
		verbose_name_plural = _("User progress records")

	@property
	def list_all_cat_scores(self):
		"""
		Returns a dict in which the key is the category name and the item is
		a list of three integers.

		The first is the number of questions correct,
		the second is the possible best score,
		the third is the percentage correct.

		The dict will have one key for every category that you have defined
		"""
		score_before = self.score
		output = {}

		for cat in Category.objects.all():
			to_find = re.escape(cat.category_name) + r",(\d+),(\d+),"
			#  group 1 is score, group 2 is highest possible

			match = re.search(to_find, self.score, re.IGNORECASE)

			if match:
				score = int(match.group(1))
				possible = int(match.group(2))

				try:
					percent = int(round((float(score) / float(possible))
										* 100))
				except:
					percent = 0

				output[cat.category_name] = [score, possible, percent]

			else:  # if category has not been added yet, add it.
				self.score += cat.category_name + ",0,0,"
				output[cat.category_name] = [0, 0]

		if len(self.score) > len(score_before):
			# If a new category has been added, save changes.
			self.save()

		return output

	def update_score(self, question, score_to_add=0, possible_to_add=0):
		"""
		Pass in question object, amount to increase score
		and max possible.

		Does not return anything.
		"""
		category_test = Category.objects.filter(category=question.category)\
										.exists()

		if any([item is False for item in [category_test,
										   score_to_add,
										   possible_to_add,
										   isinstance(score_to_add, int),
										   isinstance(possible_to_add, int)]]):
			return _("error"), _("category does not exist or invalid score")

		to_find = re.escape(str(question.category)) +\
			r",(?P<score>\d+),(?P<possible>\d+),"

		match = re.search(to_find, self.score, re.IGNORECASE)

		if match:
			updated_score = int(match.group('score')) + abs(score_to_add)
			updated_possible = int(match.group('possible')) +\
				abs(possible_to_add)

			new_score = ",".join(
				[
					str(question.category),
					str(updated_score),
					str(updated_possible), ""
				])

			# swap old score for the new one
			self.score = self.score.replace(match.group(), new_score)
			self.save()

		else:
			#  if not present but existing, add with the points passed in
			self.score += ",".join(
				[
					str(question.category),
					str(score_to_add),
					str(possible_to_add),
					""
				])
			self.save()

	def show_exams(self):
		"""
		Finds the previous quizzes marked as 'exam papers'.
		Returns a queryset of complete exams.
		"""
		return Sitting.objects.filter(user=self.user, complete=True)


class SittingManager(models.Manager):

	def new_sitting(self, user, quiz):
		if quiz.random_order is True:
			question_set = quiz.question_set.all() \
											.select_subclasses() \
											.order_by('?')
		else:
			question_set = quiz.question_set.all() \
											.select_subclasses()

		question_set = question_set.values_list('id', flat=True)

		if len(question_set) == 0:
			raise ImproperlyConfigured('Question set of the quiz is empty. '
									   'Please configure questions properly')

		if quiz.max_questions and quiz.max_questions < len(question_set):
			question_set = question_set[:quiz.max_questions]

		questions = ",".join(map(str, question_set)) + ","

		new_sitting = self.create(user=user,
								  quiz=quiz,
								  question_order=questions,
								  question_list=questions,
								  incorrect_questions="",
								  current_score=0,
								  complete=False,
								  user_answers='{}')
		return new_sitting

	def user_sitting(self, user, quiz):
		if quiz.single_attempt is True and self.filter(user=user,
													   quiz=quiz,
													   complete=True)\
											   .exists():
			return False

		try:
			sitting = self.get(user=user, quiz=quiz, complete=False)
		except Sitting.DoesNotExist:
			sitting = self.new_sitting(user, quiz)
		except Sitting.MultipleObjectsReturned:
			sitting = self.filter(user=user, quiz=quiz, complete=False)[0]
		return sitting


class Sitting(models.Model):
	"""
	Used to store the progress of logged in users sitting a quiz.
	Replaces the session system used by anon users.

	Question_order is a list of integer pks of all the questions in the
	quiz, in order.

	Question_list is a list of integers which represent id's of
	the unanswered questions in csv format.

	Incorrect_questions is a list in the same format.

	Sitting deleted when quiz finished unless quiz.exam_paper is true.

	User_answers is a json object in which the question PK is stored
	with the answer the user gave.
	"""

	user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"))

	quiz = models.ForeignKey(Quiz, verbose_name=_("Quiz"))

	unanswered_questions = JSONField(verbose_name=_("Unanswered Questions"), null=True, blank=True)

	incorrect_questions = JSONField(verbose_name=_("Incorrect Questions"), null=True, blank=True, default = '')

	current_score = models.IntegerField(verbose_name=_("Current Score"), default = 0)

	complete = models.BooleanField(default=False, blank=False,
								   verbose_name=_("Complete"))

	user_answers = JSONField(blank=True, verbose_name=_("User Answers"), null=True)

	time_spent = models.IntegerField(default = 0)

	attempt_no = models.IntegerField(default = 0)
	
	start_date = models.DateTimeField(auto_now_add=True,
								 verbose_name=_("Start"))

	end_date = models.DateTimeField(auto_now = True, verbose_name=_("End"))

	objects = SittingManager()

	class Meta:
		permissions = (("view_sittings", _("Can see completed exams.")),)
	
	def intialize(self):
		self.unanswered_questions = { 'mcq': {}, 'comprehension': {} }
		self.user_answers = { 'mcq': {}, 'comprehension': {} }
		self.incorrect_questions = { 'mcq': [], 'comprehension': {} }

	def add_to_score(self, points):
		self.current_score += int(points)
		self.save()

	# data = [correct_answer_id, time_spent]
	def add_user_mcq_answer(self, question_id, data):
		self.user_answers['mcq'][question_id] = data
		self.save()

	# data = { comprehension_question_id : comprehension_answer_id, comprehension_question_id : comprehension_answer_id, ... }
	def add_user_comprehension_answer(self, question_id, data, time_spent):
		if self.user_answers['comprehension'].has_key(question_id):
			self.user_answers['comprehension'][question_id].update(data)
		else:
			self.user_answers['comprehension'][question_id] = data
			self.user_answers['comprehension'][question_id]['time_spent'] = time_spent
		self.save()

	def add_unanswered_mcq_question(self, question_id, time_spent):
		self.unanswered_questions['mcq'][question_id] = time_spent
		print self.unanswered_questions,'unanswered_questions'
		self.save()

	def add_unanswered_comprehension_question(self, question_id, comprehension_question_id, time_spent):
		if self.unanswered_questions['comprehension'].has_key(question_id):
			self.unanswered_questions['comprehension'][question_id].update({ comprehension_question_id: time_spent })
		else:
			self.unanswered_questions['comprehension'][question_id] = { comprehension_question_id: time_spent }
			print self.unanswered_questions['comprehension'][question_id], 'comprehension-unanswered-1'
		self.save()

	def add_incorrect_mcq_question(self, question_id, incorrect_point):
		self.incorrect_questions['mcq'].append(question_id)
		self.add_to_score(incorrect_point)
		self.save()

	def add_incorrect_comprehension_question(self, question_id, comprehension_question_id, incorrect_point):
		if self.incorrect_questions['comprehension'].has_key(question_id):
			self.incorrect_questions['comprehension'][question_id].append(comprehension_question_id)
		else:
			self.incorrect_questions['comprehension'][question_id] = [ comprehension_question_id ]
		self.add_to_score(incorrect_point)
		self.save()

	@property
	def get_current_score(self):
		return self.current_score

	def _question_ids(self):
		return [int(n) for n in self.question_order.split(',') if n]

	@property
	def get_percent_correct(self):
		dividend = float(self.current_score)
		divisor = len(self._question_ids())
		if divisor < 1:
			return 0            # prevent divide by zero error

		if dividend > divisor:
			return 100

		correct = int(round((dividend / divisor) * 100))

		if correct >= 1:
			return correct
		else:
			return 0

	def mark_quiz_complete(self):
		self.complete = True
		self.end_date = now()
		self.save()

	def clear_all_unanswered_questions(self):
		self.unanswered_questions = { 'mcq': {}, 'comprehension': {} }
		self.save()


	# This excludes comprehension question keys.
	def get_all_incorrect_questions_keys(self):
		return self.incorrect_questions['mcq'] + self.incorrect_questions['comprehension'].keys()

	# This excludes comprehension question keys.
	def get_all_unanswered_questions_keys(self):
		return self.incorrect_questions['mcq'] + self.incorrect_questions['comprehension'].keys()

	def get_timed_analysis_for_answered_questions(self):
		d = self.user_answers['mcq']
		for question_id, values in self.user_answers['comprehension'].items():
			d[question_id] = values['time_spent']
		return d
		
	def get_timed_analysis_for_unanswered_questions(self):
		d = self.unanswered_questions['mcq']
		for question_id, values in self.user_answers['comprehension'].items():
			d[question_id] = values['time_spent']
		return d

	def merge_user_answers_and_unanswered_questions(self):
		d = { 'mcq': {}, 'comprehension': {} }
		for question_id, values in self.user_answers['mcq'].items():
			d['mcq'][question_id] = values
		
		for question_id, values in self.unanswered_questions['mcq'].items():
			d['mcq'][question_id] = values

		for question_id, values in self.user_answers['comprehension'].items():
			d['comprehension'][question_id] = {}
			for cq_id,value in values.items():
				if cq_id!='time_spent':
					d['comprehension'][question_id][cq_id] = value

		for question_id, values in self.unanswered_questions['comprehension'].items():
			if not d['comprehension'].has_key(question_id):
				d['comprehension'][question_id] = {}
			for cq_id,value in values.items():
				d['comprehension'][question_id][cq_id] = value
		return d
		



	# def get_incorrect_comprehension_questions_list(self):
	# 	l = []
	# 	for question_id in self.incorrect_questions['comprehension'].keys():
	# 		for cq_id in self.incorrect_questions['comprehension'][question_id]:
	# 			l.append(cq_id)
	# 	return l

	# def get_incorrect_mcq_questions_list(self):
	# 	return self.incorrect_questions['mcq']

	# def get_incorrect_questions_all(self):
	# 	return self.get_incorrect_mcq_questions_list() + self.get_incorrect_comprehension_questions_list()

	# def get_unanswered_mcq_questions_list(self):
	# 	return self.unanswered_questions['mcq'].keys()

	# def get_unanswered_comprehension_questions_list(self):
	# 	l = []
	# 	for question_id in self.unanswered_questions['comprehension'].keys():
	# 		for cq_id in self.unanswered_questions['comprehension'][question_id]:
	# 			l.append(cq_id)
	# 	return l

	# def get_unanswered_questions_all(self):
	# 	return self.get_unanswered_mcq_questions_list() + self.get_unanswered_comprehension_questions_list()

	@property
	def check_if_passed(self):
		return self.get_percent_correct >= self.quiz.pass_mark

	@property
	def result_message(self):
		if self.check_if_passed:
			return self.quiz.success_text
		else:
			return self.quiz.fail_text

	def get_questions(self, with_answers=False):
		question_ids = self._question_ids()
		questions = sorted(
			self.quiz.question_set.filter(id__in=question_ids)
								  .select_subclasses(),
			key=lambda q: question_ids.index(q.id))

		if with_answers:
			user_answers = json.loads(self.user_answers)
			for question in questions:
				question.user_answer = user_answers[str(question.id)]

		return questions

	@property
	def questions_with_user_answers(self):
		return {
			q: q.user_answer for q in self.get_questions(with_answers=True)
		}

	@property
	def get_max_score(self):
		return len(self._question_ids())

	def save_time_spent(self, time_in_seconds):
		self.time_spent = self.quiz.total_duration - time_in_seconds
		self.save()
		
	def progress(self):
		"""
		Returns the number of questions answered so far and the total number of
		questions.
		"""
		answered = len(json.loads(self.user_answers))
		total = self.get_max_score
		return answered, total


def figure_directory(instance, filename):
	return '/qna/media/{0}/{1}/{2}'.format(instance.que_type, instance.sub_category.sub_category_name, filename)

@python_2_unicode_compatible
class Question(models.Model):
	"""
	Base class for all question types.
	Shared properties placed here.
	"""
	sub_category = models.ForeignKey(SubCategory,blank=False,
									null=False,
									verbose_name=_("Sub-Category"))

	figure = models.ImageField(upload_to=figure_directory,
							   blank=True,
							   null=True,
							   verbose_name=_("Figure"))

	content = models.CharField(max_length=3000,
							   blank=False,
							   help_text=_("Enter the question text that "
										   "you want displayed"),
							   verbose_name=_('Question'))

	explanation = models.TextField(max_length=2000,
								   blank=True,
								   help_text=_("Explanation to be shown "
											   "after the question has "
											   "been answered."),
								   verbose_name=_('Explanation'))

	points = models.IntegerField(verbose_name=_("Marks"), default=1, blank=True)
	
	que_type = models.CharField(max_length = 15,null= True,
								choices=QUESTION_TYPE_OPTIONS,
								help_text=_("Type of Question"),
								verbose_name=_("Question Type"))

	level = models.CharField(max_length=10,default = 'easy',
								choices=QUESTION_DIFFICULTY_OPTIONS,
								help_text=_("The difficulty level of a MCQQuestion"),
								verbose_name=_("Difficulty Level"))

	ideal_time = models.PositiveSmallIntegerField(default = 0,blank = True, validators=[MaxValueValidator(300)])

	created_date = models.DateTimeField(auto_now_add = True)
	updated_date = models.DateTimeField(auto_now = True)

	# objects = InheritanceManager()

	class Meta:
		verbose_name = _("Question")
		verbose_name_plural = _("Questions")

	def __str__(self):
		return self.content
