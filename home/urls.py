from django.conf.urls import url
from home import views

urlpatterns = [
	#URL entry for mcqQuestions Models
	url(r'^login/$', views.login_user),
	url(r'^register/$', views.register_user),
]