from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login', views.user_login, name='login'),
    path('logout', views.user_logout, name='logout'),
    path('request_password_reset', views.request_password_reset, name='request_password_reset'),
    path('reset_password/<uuid:token>/', views.reset_password, name='reset_password'),
    path('child_home/', views.child_home, name='child_home')

]