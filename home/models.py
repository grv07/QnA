from __future__ import unicode_literals
from django.db import models
from quiz.models import Quiz

import string, random

from django.contrib.auth.models import User
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _



@python_2_unicode_compatible
class MerchantUser(models.Model):
    user = models.OneToOneField(User, blank=True)
    merchant_public_key = models.CharField(max_length = 10, unique = True, blank = True)
    merchant_private_key = models.CharField(max_length = 10, unique = True, blank = True)

    created_date = models.DateTimeField(auto_now_add = True)
    updated_date = models.DateTimeField(auto_now = True)


    def __str__(self):
        return self.name,self.email,self.merchant_public_key

    class Meta:
        verbose_name = _("MerchantUser")

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        self.merchant_public_key = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(8))
        self.merchant_private_key = ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(10))
        super(MerchantUser, self).save(force_insert, force_update, *args, **kwargs)


@python_2_unicode_compatible
class TestUser(models.Model):
    user = models.ForeignKey(User)
    test_key = models.CharField(max_length = 20)
    
    is_complete = models.BooleanField(default = False)
    no_attempt = models.IntegerField(default = 1)

    created_date = models.DateTimeField(auto_now_add = True)
    updated_date = models.DateTimeField(auto_now = True)


    def __str__(self):
        return self.user.username, self.user.email,self.test_key
            
    class Meta:
        verbose_name = _("TestUser")

# Create your models here.
@python_2_unicode_compatible
class TestUserDetails(models.Model):
    test_user = models.ForeignKey(TestUser, related_name = 'test_user_details')
    result = models.CharField(max_length=3000)
    time_spent = models.IntegerField()
    created_date = models.DateTimeField(auto_now_add = True)
    updated_date = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.test_user.user.email, self.test_user.test_key
        
    class Meta:
      # unique_together = ('email', 'quiz')
        verbose_name = _("TestUserDetails")
