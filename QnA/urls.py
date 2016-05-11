"""QnA URL Configuration
The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

#Allow a format url via append .json etc in url
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_jwt.views import obtain_jwt_token, verify_jwt_token
from django.conf.urls import url, include
from django.contrib import admin
from django.views import static
from .settings import MEDIA_ROOT

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('home.urls')),
    url(r'^quiz/', include('quiz.urls')),
    url(r'^question/mcq/', include('mcq.urls')),
    url(r'^question/objective/', include('objective.urls')),
    url(r'^question/comprehension/', include('comprehension.urls')),
    url(r'^stack/', include('quizstack.urls')),
    url(r'^api-token-auth/', obtain_jwt_token),
    url(r'^api-token-verify/', verify_jwt_token),
    url(r'^qna/media/(?P<path>.*)$', static.serve, { 'document_root': MEDIA_ROOT, }), 
]

urlpatterns = format_suffix_patterns(urlpatterns)
