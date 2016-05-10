from django.conf.urls import url
from comprehension import views

urlpatterns = [
	url(r'^create/$', views.create_comprehension),
	url(r'^get/(?P<comprehension_id>\d+)/$', views.get_comprehension),
	url(r'^questions/create/$', views.create_comprehension_question),
	url(r'^get/questions/(?P<comprehension_id>\d+)/$', views.get_comprehension_questions),
	url(r'^operations/(?P<comprehension_question_id>\d+)/$', views.comprehension_question_operations),
	url(r'^answers/operations/(?P<comprehension_question_id>\d+)/$', views.comprehension_answers_operations),
]
