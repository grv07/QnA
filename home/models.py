from __future__ import unicode_literals
from django.db import models
from quiz.models import Quiz

from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _



@python_2_unicode_compatible
class TestUser(models.Model):
    name = models.CharField(max_length = 100, verbose_name=_("Name"))

    email = models.CharField(max_length = 100,
                               blank=False,
                               help_text=_("User email"),
                               verbose_name=_("Email"))

    quiz = models.ForeignKey(Quiz, help_text=_("Use for quiz ?"), verbose_name=_("Quiz"))

    def __str__(self):
        return self.name,self.email

        
    class Meta:
    	# unique_together = ('email', 'quiz')
        verbose_name = _("TestUserData")

# Create your models here.
