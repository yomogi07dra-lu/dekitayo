from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from app.models import Item


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        # 削除基準となる日付を計算する
        threshold_date = timezone.now() - timedelta(days=30)
        # 削除対象を検索する
        old_items = Item.objects.filter(
            is_active=False,
            deleted_at__isnull=False, # deleted_at が空ではない（削除日時がある）
            deleted_at__lt=threshold_date # deleted_at が 30日より前
        )
        # 実際にデータベースから削除する
        old_items.delete()

