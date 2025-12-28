
from django.contrib import admin
from .models import User, Icon
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.html import format_html


@admin.register(Icon)
class IconAdmin(admin.ModelAdmin):
    list_display = ("id", "image_url")


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # 一覧で見たい列（まずは壊れにくい最小構成）
    list_display = (
        "id",
        "username",
        "email",
        "is_staff",
        "is_active",
        "icon_preview",
        "icon",
    )

    # 検索（メール・ユーザー名など）
    search_fields = ("username", "email")

    # 絞り込み
    list_filter = ("is_staff", "is_active", "is_superuser")

    # 編集画面に追加で見せたい項目（iconを追加）
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("追加情報", {"fields": ("icon",)}),
    )

    def icon_preview(self, obj):
        """
        static に置いたアイコンを管理画面上でプレビュー表示。
        Icon.image_url が 'icons/icon_01.png' の形式で入っている想定。
        """
        if obj.icon and obj.icon.image_url:
            return format_html(
                '<img src="/static/{}" style="width:32px;height:32px;border-radius:50%;object-fit:cover;" />',
                obj.icon.image_url,
            )
        return "-"

    icon_preview.short_description = "icon"