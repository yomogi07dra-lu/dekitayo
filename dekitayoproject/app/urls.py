from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('request_password_reset/', views.request_password_reset, name='request_password_reset'),
    path('reset_password/<uuid:token>/', views.reset_password, name='reset_password'),
    path('child_home/', views.child_home, name='child_home'),
    path('parent_home/', views.parent_home, name='parent_home'),
    path('parent_mypage/', views.parent_mypage, name='parent_mypage'),
    path('parent_item_manage/', views.parent_item_manage, name='parent_item_manage'),
    path('parent_invitation/', views.invitation, name='invitation'),
    path('child_record/', views.child_record, name='child_record'),
]