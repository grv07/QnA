from django.conf.urls import url
from quizstack import views

urlpatterns = [
	url(r'^create/$', views.create_quizstack),
	url(r'^get/(?P<quiz_id>\d+)/(?P<quizstack_id>[a-l0-9]+)/$', views.get_quizstack),
	url(r'^get/test/(?P<quiz_id>\d+)/$', views.get_quizstack_questions),
]