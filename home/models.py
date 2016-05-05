from __future__ import unicode_literals
from django.db import models
from quiz.models import Quiz

import string, random

from django.contrib.auth.models import User
from django.utils.translation import ugettext as _



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


class TestUser(models.Model):
    user = models.ForeignKey(User)
    test_key = models.CharField(max_length = 20)
    rank = models.IntegerField(default = 0)    
    is_complete = models.BooleanField(default = False)
    no_attempt = models.IntegerField(default = 0)

    created_date = models.DateTimeField(auto_now_add = True)
    updated_date = models.DateTimeField(auto_now = True)


    def __str__(self):
        return self.user.username, self.user.email,self.test_key
            
    class Meta:
        verbose_name = _("TestUser")


class BookMarks(models.Model):
    user = models.ForeignKey(User)
    questions_list = models.CommaSeparatedIntegerField(
        max_length=1024, blank=True, verbose_name =_("Bookmarked questions"), default = '')

    created_date = models.DateTimeField(auto_now_add = True)
    updated_date = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.user.username, self.questions_list
        
    class Meta:
        verbose_name = _("BookMarks")

    def add_bookmark(self, question_id):
        if len(self.questions_list) > 0:
            self.questions_list += ','
        self.questions_list += str(question_id)
        self.save()

    def fetch_bookmarks(self):
        if self.questions_list:
            return map(int, self.questions_list.split(','))
        return []

    def remove_bookmark(self, question_id):
        current = self.fetch_bookmarks()
        current.remove(question_id)
        self.questions_list = ','.join(map(str, current))
        self.save()
