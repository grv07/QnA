from __future__ import unicode_literals
from django.db import models
from quiz.models import Quiz

from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _


@python_2_unicode_compatible
class TestUser(models.Model):
    user_key = models.CharField(max_length = 10, unique = True)
    name = models.CharField(max_length = 100, verbose_name=_("Name"))
    email = models.CharField(max_length = 100,
                               blank=False,
                               help_text=_("User email"),
                               verbose_name=_("Email"))
    
    quiz = models.ForeignKey(Quiz, help_text=_("Use for quiz ?"), verbose_name=_("Quiz"))
    test_key = models.CharField(max_length = 20)

    attempt_no = models.IntegerField(default = 1)
    is_complete = models.BooleanField(default = False)
    
    created_date = models.DateTimeField(auto_now_add = True)
    updated_date = models.DateTimeField(auto_now = True)


    def __str__(self):
        return self.name,self.email,self.quiz.title,self.test_key

    class Meta:
        verbose_name = _("TestUser")

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        self.user_key = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(10))
        super(TestUser, self).save(force_insert, force_update, *args, **kwargs)    

# Create your models here.
@python_2_unicode_compatible
class TestUserDetails(models.Model):
    test_user = models.ForeignKey(TestUser, related_name = 'test_user_details')
    result = models.CharField(max_length=3000)
    time_spent = models.IntegerField()
    created_date = models.DateTimeField(auto_now_add = True)
    updated_date = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.test_user.email,self.test_user.quiz.title,self.test_user.test_key
        
    class Meta:
      # unique_together = ('email', 'quiz')
        verbose_name = _("TestUserDetails")
