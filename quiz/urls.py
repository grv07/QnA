from django.conf.urls import url
from quiz import views

urlpatterns = [

    url(r'^detail/(?P<pk>[0-9]+)/$', views.get_quiz),
    url(r'^list/$', views.quiz_list),
    url(r'^create/$', views.create_quiz),
    url(r'^delete/(?P<pk>[0-9]+)/$', views.delete_quiz),
    
    #Category Related Urls
<<<<<<< HEAD
    url(r'^category/create/$', views.create_category),
    url(r'^category/detail/(?P<pk>[0-9]+)/$', views.get_category),
    url(r'^category/list/$', views.category_list),
    url(r'^category/delete/(?P<pk>[0-9]+)/$', views.delete_category),

=======
    url(r'^create/category/$', views.create_category),
   
    #SubCategory Related Urls
    url(r'^create/subcategory/$', views.create_subcategory),
>>>>>>> aac132096233f6c826755e2644b50ec17c573af8
]