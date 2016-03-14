from django.conf.urls import url
from quiz import views

urlpatterns = [

	url(r'^get/(?P<userid>\d+)/(?P<quizid>[a-l0-9]+)/$', views.get_quiz),
	url(r'^create/$', views.create_quiz),
	url(r'^update/(?P<userid>\d+)/(?P<quizid>\d+)/$', views.update_quiz),
	url(r'^delete/(?P<user_id>\d+)/(?P<quiz_id>[0-9]+)/$', views.delete_quiz),
    url(r'^get/key/$', views.get_quiz_acc_key),
	
	#Category Related Urls 
	url(r'^category/create/$', views.create_category),
	url(r'^category/detail/(?P<pk>[0-9]+)/$', views.get_category),
	url(r'^category/get/(?P<userid>\d+)/(?P<categoryid>[a-l0-9]+)/$', views.category_list),
	url(r'^category/delete/(?P<pk>[0-9]+)/$', views.delete_category),

    #SubCategory Related Urls
    url(r'^subcategory/create/$', views.create_subcategory),
    url(r'^subcategory/get/(?P<userid>\d+)/(?P<categoryid>[a-l0-9]+)/$', views.get_subcategory),

    #Questions Related Urls
    url(r'^questions/get/(?P<user_id>\d+)/$', views.all_questions),
    # url(r'^questions/get/(?P<userid>\d+)/(?P<quizid>\d+)/$', views.all_questions_under_quiz),
    url(r'^questions/get/(?P<userid>\d+)/(?P<quizid>\d+)/(?P<categoryid>\d+)/$', views.all_questions_under_category),
    url(r'^questions/get/(?P<user_id>\d+)/subcategory/(?P<subcategory_id>\d+)/$', views.all_questions_under_subcategory),
    url(r'^question/(?P<userid>\d+)/(?P<questionid>\d+)/$', views.question_operations),
    url(r'^answers/(?P<userid>\d+)/(?P<questionid>\d+)/$', views.answers_operations),
    url(r'^question/download/xls/$', views.download_xls_file),
]