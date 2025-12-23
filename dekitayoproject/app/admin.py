
from django.contrib import admin
<<<<<<< HEAD
=======
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import Family, Family_member

Users = get_user_model()

@admin.register(Users)
class CustomUserAdmin(UserAdmin):
    # 一覧で見たい列
    list_display = (
        "id",
        "username",
        "email",
        "family_member",
        "is_staff",
        "is_active",
        "is_superuser",
        "date_joined",
        "last_login",
    )

    # 右側フィルター
    list_filter = ("is_staff", "is_active", "is_superuser")

    # 上の検索窓で検索できる対象
    search_fields = ("username", "email")

    # 編集画面で表示する順序（UserAdmin標準を使いつつ追加）
    fieldsets = UserAdmin.fieldsets + (
        ("アプリ情報", {"fields": ("family_member",)}),
    )
admin.site.register(Family)
admin.site.register(Family_member)

>>>>>>> 237ad0bef178cd18770abcb55bbe6b41d1800f3c
