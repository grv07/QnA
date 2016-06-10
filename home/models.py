from __future__ import unicode_literals
from django.db import models
from quiz.models import Quiz

import string, random

from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.contrib.postgres.fields import JSONField



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
        return self.user.username
            
    class Meta:
        verbose_name = _("TestUser")




class BookMarks(models.Model):
    user = models.ForeignKey(User)
    questions = JSONField(verbose_name=_("Question List"), null=True, blank=True, default={ 'mcq':[], 'comprehension':[] })

    created_date = models.DateTimeField(auto_now_add = True)
    updated_date = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.user.username, self.questions_list
        
    class Meta:
        verbose_name = _("BookMarks")


    def add_bookmark(self, bookmarked_questions):
        self.questions = bookmarked_questions
        self.save()

    def fetch_bookmarks(self):
        return self.questions

    def remove_bookmark(self, que_type, question_id):
        current = self.fetch_bookmarks()
        del current[que_type][question_id]
        self.questions = current
        self.save()


class InvitedUser(models.Model):
    quiz_list = models.CommaSeparatedIntegerField(max_length=1024, verbose_name=_("InvitedUserQuiz"), blank=True)
    
    user_name = models.CharField(max_length=50)
    user_email = models.EmailField(max_length=50)
    
    created_date = models.DateTimeField(auto_now_add = True)
    updated_date = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.user_name, self.user_email
        
    class Meta:
        verbose_name = _("InvitedUser")  

    def fetch_quiz_list_for_inviteduser(self):
        if self.quiz_list:
            return [ int(quiz_id) for quiz_id in self.quiz_list.strip().split(',') ]
        return []

    def check_if_invited(self, quiz_id):
        quiz_list = self.fetch_quiz_list_for_inviteduser()
        if int(quiz_id) in quiz_list:
            return [ True, quiz_list ]
        return [ False, quiz_list ]

    def add_inviteduser(self, quiz_id):
        already_present, quiz_list = self.check_if_invited(quiz_id)
        print already_present, quiz_list
        if not already_present:
            if quiz_list:
                self.quiz_list += "," + str(quiz_id)
            else:
                self.quiz_list = str(quiz_id)
            self.save()
        return already_present
