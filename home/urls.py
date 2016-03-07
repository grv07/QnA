from django.conf.urls import url
from home import views

urlpatterns = [
	#URL entry for mcqQuestions Models
	url(r'^login/$', views.login_user),
	url(r'^register/$', views.register_user),
	url(r'^logout/$', views.logout_user),
	url(r'^user/data/$', views.test_user_data),
	url(r'^save/test/$', views.save_test_data),
]