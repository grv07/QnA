from django.conf.urls import url
from quiz import views

urlpatterns = [

    url(r'^detail/(?P<pk>[0-9]+)/$', views.get_quiz),
    url(r'^list/$', views.quiz_list),
    url(r'^create/$', views.create_quiz),
    url(r'^delete/(?P<pk>[0-9]+)/$', views.delete_quiz),
    
    #Category Related Urls
    url(r'^create/category/$', views.create_category),
]