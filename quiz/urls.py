from django.conf.urls import url
from quiz import views

urlpatterns = [

	url(r'^detail/(?P<pk>[0-9]+)/$', views.get_quiz),
	url(r'^get/(?P<userid>\d+)/quiz/$', views.quiz_list),
	url(r'^create/$', views.create_quiz),
	url(r'^delete/(?P<pk>[0-9]+)/$', views.delete_quiz),
	
	#Category Related Urls 
	url(r'^category/create/$', views.create_category),
	url(r'^category/detail/(?P<pk>[0-9]+)/$', views.get_category),
	url(r'^category/get/(?P<userid>\d+)/(?P<quizid>[a-l0-9]+)/$', views.category_list),
	url(r'^category/delete/(?P<pk>[0-9]+)/$', views.delete_category),

    #SubCategory Related Urls
    url(r'^subcategory/create/$', views.create_subcategory),
    url(r'^subcategory/get/(?P<userid>\d+)/(?P<quizid>[a-l0-9]+)/(?P<categoryid>[a-l0-9]+)/$', views.get_subcategory),

    #Questions Related Urls
    url(r'^questions/get/(?P<userid>\d+)/$', views.all_questions),
    url(r'^question/(?P<userid>\d+)/(?P<questionid>\d+)/$', views.get_or_update_question),
    url(r'^answers/(?P<userid>\d+)/(?P<questionid>\d+)/$', views.get_or_update_answers),

]