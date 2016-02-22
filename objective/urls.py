from django.conf.urls import url
from objective import views

urlpatterns = [
	#URL entry for mcqQuestions Models

    # url(r'^mcq/detail/(?P<pk>[0-9]+)/$', views.get_mcq_detail),
    # url(r'^mcq/list/$', views.all_mcq),
    url(r'^create/$', views.create_objective),
    # url(r'^mcq/del/(?P<pk>[0-9]+)/$', views.del_mcq),
    # url(r'^test/$', views.save_XLS_to_MCQ),

]