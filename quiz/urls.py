from django.conf.urls import url
from quiz import views

urlpatterns = [
    url(r'^$', views.home),
    url(r'^list$', views.quiz_list),
]