from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('request_password_reset/', views.request_password_reset, name='request_password_reset'),
    path('reset_password/<uuid:token>/', views.reset_password, name='reset_password'),
# 子ども用
    path('child/home/', views.child_home, name='child_home'),
    path('child/mypage/', views.child_mypage, name='child_mypage'),    
    path('child/record/', views.child_record, name='child_record'),

    path('child/monthly_calendar/', views.child_monthly_calendar, name='child_monthly_calendar'),
    path('child/monthly_graph/', views.child_monthly_graph, name='child_monthly_graph'),
    path('child/weekly_graph/', views.child_weekly_graph, name='child_weekly_graph'),
# 保護者用
    path('parent/home/', views.parent_home, name='parent_home'),
    path("parent/home/<int:child_id>/", views.parent_home, name="parent_home_with_child"),

    path('parent/mypage/', views.parent_mypage, name='parent_mypage'),
    path('parent/item_manage/', views.parent_item_manage, name='parent_item_manage'),
    path("parent/item_manage/<int:child_id>/", views.parent_item_manage, name="parent_item_manage_with_child"),
    path('parent/invitation/', views.invitation, name='invitation'),

    path('parent/monthly_calendar/', views.parent_monthly_calendar, name='parent_monthly_calendar'),
    path('parent/monthly_graph/', views.parent_monthly_graph, name='parent_monthly_graph'),
    path('parent/weekly_graph/', views.parent_weekly_graph, name='parent_weekly_graph'),
    path('parent/child_switch/', views.parent_child_switch, name='parent_child_switch'),    
]