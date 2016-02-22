from django.conf.urls import url
from mcq import views

urlpatterns = [
	#URL entry for mcqQuestions Models

    url(r'^detail/(?P<pk>[0-9]+)/$', views.get_mcq_detail),
    url(r'^list/$', views.all_mcq),
    url(r'^create/$', views.create_mcq),
    url(r'^del/(?P<pk>[0-9]+)/$', views.del_mcq),
    url(r'^test/$', views.save_XLS_to_MCQ),

]