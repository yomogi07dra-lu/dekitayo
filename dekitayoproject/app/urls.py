from django.urls import path
from .views import child, parent, auth , portfolio

urlpatterns = [
    path("", auth.signup, name="dekitayo_entry"),

    path('signup/', auth.signup, name='signup'),
    path('login/', auth.user_login, name='login'),
    path('logout/', auth.user_logout, name='logout'),

    path('request_password_reset/', auth.request_password_reset, name='request_password_reset'),
    path('password_reset_confirm/<uuid:token>/', auth.password_reset_confirm, name='password_reset_confirm'),
# 子ども用
    path('child/home/', child.child_home, name='child_home'), 
    path('child/home/<int:year>/<int:month>/<int:day>/', child.child_home, name="child_home_by_date"), #過去学習記録　slug形式 
    path('child/record/', child.child_record, name='child_record'),

    path('child/monthly_calendar/', child.child_monthly_calendar, name='child_monthly_calendar'),
    path('child/monthly_calendar/<int:year>/<int:month>/', child.child_monthly_calendar, name='child_monthly_calendar_by_month'),

    path('child/monthly_graph/', child.child_monthly_graph, name='child_monthly_graph'),
    path('child/monthly_graph/<int:year>/<int:month>/', child.child_monthly_graph, name='child_monthly_graph_by_month'),

    path('child/weekly_graph/', child.child_weekly_graph, name='child_weekly_graph'),
    path('child/weekly_graph/<int:year>/<int:month>/<int:day>', child.child_weekly_graph, name='child_weekly_graph_by_week'),

    path('child/mypage/', child.child_mypage, name='child_mypage'),
    path('child/icon_change/', child.child_icon_change, name='child_icon_change'),
    path('child/email_change/', child.child_email_change, name='child_email_change'),
    path('child/password_change/', child.child_password_change, name='child_password_change'), 


# 保護者用
    path('parent/home/', parent.parent_home, name='parent_home'),

    path('parent/daily_detail/<int:year>/<int:month>/<int:day>/', parent.parent_daily_detail, name="parent_daily_detail"),

    path('parent/mypage/', parent.parent_mypage, name='parent_mypage'),
    path('parent/invitation/', parent.invitation, name='invitation'),

    path('parent/item_manage/', parent.parent_item_manage, name='parent_item_manage'),

    path('parent/monthly_calendar/', parent.parent_monthly_calendar, name='parent_monthly_calendar'),
    path('parent/monthly_calendar/<int:year>/<int:month>/', parent.parent_monthly_calendar, name='parent_monthly_calendar_by_month'),
    
    path("parent/monthly_graph/",parent.parent_monthly_graph, name="parent_monthly_graph"),
    path("parent/monthly_graph/<int:year>/<int:month>/", parent.parent_monthly_graph, name="parent_monthly_graph_by_month"),
   
    path("parent/weekly_graph/", parent.parent_weekly_graph, name="parent_weekly_graph"),
    path("parent/weekly_graph/<int:year>/<int:month>/<int:day>/", parent.parent_weekly_graph, name="parent_weekly_graph_by_week"),


    path('parent/child_switch/', parent.parent_child_switch, name='parent_child_switch'),
    path('parent/icon_change/', parent.parent_icon_change, name='parent_icon_change'),
    path('parent/email_change/', parent.parent_email_change, name='parent_email_change'), 
    path('parent/password_change/', parent.parent_password_change, name='parent_password_change'),
    path('parent/family_list/', parent.parent_family_list, name='parent_family_list'), 
]