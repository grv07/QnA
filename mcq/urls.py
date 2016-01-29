from django.conf.urls import url
from mcq import views

urlpatterns = [
	#URL entry for mcqQuestions Models

    url(r'^mcq/detail/(?P<pk>[0-9]+)/$', views.get_mcq_detail),
    url(r'^mcq/list/$', views.all_mcq),
    url(r'^mcq/create/$', views.create_mcq),
    url(r'^mcq/del/(?P<pk>[0-9]+)/$', views.del_mcq),
]