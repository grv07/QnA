from django.conf.urls import url
from home import views

urlpatterns = [
	#URL entry for mcqQuestions Models
	url(r'^login/$', views.login_user),
	url(r'^register/$', views.register_user),
	url(r'^logout/$', views.logout_user),
	url(r'^user/data/$', views.test_user_data),
	url(r'^save/test/cache/$', views.save_test_data_to_cache),
	url(r'^user/result/(?P<user_id>\d+)/(?P<quiz_key>\w+)/(?P<status>\w+)/$', views.get_user_result),
	url(r'^save/test/db/$', views.save_test_data_to_db),
]