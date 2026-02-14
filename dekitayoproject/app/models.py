from django.db import models
from django.utils import timezone
from datetime import date, datetime
from django.contrib.auth.models import (AbstractUser)
import uuid


class BaseMeta(models.Model): 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser, BaseMeta):
    username = models.CharField(
        max_length=50,
        blank=False,
        null=False,
        unique=False,  # 重複OK
    )

    USERNAME_FIELD = 'email'          
    REQUIRED_FIELDS = ['username']    

    email = models.EmailField(unique=True)


    family_member = models.ForeignKey(
        'Family_member',
        on_delete=models.CASCADE,
        null=True,#管理者権限画面のため
        blank=True,
        )
    icon = models.ForeignKey(
        'Icon',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        )

    class Meta:
        db_table = 'users'


class Family(BaseMeta):
    
    class Meta:
        db_table ='families'


class Family_member(models.Model):
    family = models.ForeignKey(
        'Family',
        on_delete=models.CASCADE,
    )

    PARENT = 0
    CHILD = 1
    ROLE_CHOICES = (
        (PARENT,"保護者"),
        (CHILD,"子ども"),
    )
    role = models.IntegerField(choices=ROLE_CHOICES, default=PARENT)

    is_admin = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'family_members'


class Child(BaseMeta):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
    
    family_member = models.ForeignKey(
        'Family_member',
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = 'children'


class Icon(BaseMeta):
     image_url = models.CharField(max_length=100) 

     class Meta:
         db_table = 'icons'


class Invitation(BaseMeta):
    family = models.OneToOneField(
        'Family', 
        on_delete=models.CASCADE,
        related_name='invite')
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'invitations'


class PasswordResetToken(BaseMeta):
    user_PasswordReset = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='password_reset_token',
    )
    token = models.UUIDField(default=uuid.uuid4,db_index=True)
    used = models.BooleanField(default=False)


class Daily_log(BaseMeta):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
    child = models.ForeignKey(
        'Child',
        on_delete=models.CASCADE,
    )  
    date = models.DateField(default=timezone.localdate)
    child_comment = models.TextField(max_length=100, blank=True)
    photo1_url = models.ImageField(upload_to="daily_logs/",blank=True,null=True,max_length=255)
    photo2_url = models.ImageField(upload_to="daily_logs/",blank=True,null=True,max_length=255)

    class Meta:
        db_table = 'daily_logs'
        #重複禁止　指定した組み合わせが1つ
        constraints = [
            models.UniqueConstraint(fields=["child", "date"], name="uniq_dailylog__date")
        ]


class Item(BaseMeta):
    family = models.ForeignKey(
        'Family',
        on_delete=models.CASCADE,
    )
    child = models.ForeignKey(
        'Child',
        on_delete=models.CASCADE,
    )    
    item_name = models.CharField(max_length=50)
    color_index = models.PositiveSmallIntegerField() #表示位置
    is_active = models.BooleanField(default=True)  # ソフトデリート用
    deleted_at = models.DateTimeField(null=True, blank=True) # 削除日時（削除した項目を自動で消すため）

    class Meta:
         db_table = 'items'


class DailyLogItem(BaseMeta):
    daily_log = models.ForeignKey(
        'Daily_log',
        on_delete=models.CASCADE,
    )
    item = models.ForeignKey(
        'Item',
        on_delete=models.CASCADE
    )
    class Meta:
         db_table = 'daily_log_items'

class ParentComment(BaseMeta):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
    daily_log = models.ForeignKey(
        'Daily_log',
        on_delete=models.CASCADE,
        related_name='parent_comments',
    )
    text = models.TextField(max_length=100)
    
    class Meta:
        db_table = 'parent_comments'

