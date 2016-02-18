from django.conf.urls import url
from quizstack import views

urlpatterns = [
	url(r'^create/$', views.create_quizstack),
	url(r'^delete/(?P<quiz_id>\d+)/(?P<quizstack_id>[0-9]+)/$', views.delete_quizstack),
	url(r'^get/(?P<quiz_id>\d+)/(?P<quizstack_id>[a-l0-9]+)/$', views.get_quizstack),

]