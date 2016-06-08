from django.conf.urls import url
from home import views

urlpatterns = [
	#URL entry for mcqQuestions Models
	url(r'^login/$', views.login_user),
	url(r'^register/$', views.register_user),
	url(r'^logout/$', views.logout_user),
	url(r'^user/data/$', views.test_user_data),
	url(r'^save/sitting/user/$', views.save_sitting_user),
	url(r'^save/test/cache/$', views.save_test_data_to_cache),
	url(r'^user/result/(?P<test_user_id>\d+)/(?P<quiz_key>\w+)/(?P<attempt_no>[1-5]{1})/$', views.get_user_result),
	url(r'^save/test/db/$', views.save_test_data_to_db),
	url(r'^save/test/bookmarks/$', views.save_test_bookmarks),
	url(r'^save/time/remaining/$', views.save_time_remaining_to_cache),
	url(r'^save/question/time/$', views.save_question_time),
	url(r'^get/bookmarks/$', views.get_bookmark_questions),
	url(r'^question/stats/(?P<sitting_id>\d+)/$', views.question_stats),
	url(r'^ping/$', views.ping),
	url(r'^post/$', views.post),
]
