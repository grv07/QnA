from django.contrib.auth.models import User
from rest_framework import authentication
from rest_framework import exceptions

class TestAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        key = request.META.get('HTTP_AUTHORIZATION') # get the username request header
        print key,'==========='

        # if not username: # no username passed in request headers
        #     return None # authentication did not succeed

        # try:
        #     user = User.objects.get(username=username) # get the user
        # except User.DoesNotExist:
        #     raise exceptions.AuthenticationFailed('No such user') # raise exception if user does not exist 

        return (User.objects.get(username='anshul01'), None) # authentication successful