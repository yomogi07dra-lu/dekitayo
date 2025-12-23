from django.db import models
from django.utils import timezone
from datetime import date, datetime
from django.contrib.auth.models import (AbstractUser)
import uuid


class BaseMeta(models.Model): 
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    email = models.EmailField(unique=True)
    family_member = models.ForeignKey(
        'Family_member',
        on_delete=models.CASCADE,
        null=True,#管理者権限画面のため
        blank=True,
        )
    # icon = models.ForeignKey(
    #     'Icons',
    #     on_delete=models.CASCADE,
    #     )

    class Meta:
        db_table = 'users'


class Family(models.Model):
    
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


class Child(models.Model):
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


class Icon(models.Model):
     image_url = models.FileField()

     class Meta:
         db_table = 'icons'


class Invitation(models.Model):
    family = models.OneToOneField(
        'Family', 
        on_delete=models.CASCADE,
        related_name='invite')
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'invitations'


class PasswordResetToken(models.Model):
    user_PasswordReset = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
        related_name='password_reset_token',
    )
    token = models.UUIDField(default=uuid.uuid4,db_index=True)
    used = models.BooleanField(default=False)


class Daily_log(models.Model):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
<<<<<<< HEAD
    child = models.ForeignKey(
        'Child',
        on_delete=models.CASCADE,
    )  
    date = models.DateField(default=timezone.localdate)
    child_comment = models.CharField(max_length=100, blank=True)
=======
    date = models.DateField(default=timezone.localdate)
    comment = models.CharField(max_length=100, blank=True)
>>>>>>> 237ad0bef178cd18770abcb55bbe6b41d1800f3c
    photo1_url = models.ImageField(upload_to="daily_logs/",blank=True,null=True)
    photo2_url = models.ImageField(upload_to="daily_logs/",blank=True,null=True)

    class Meta:
        db_table = 'daily_logs'
        #重複禁止　指定した組み合わせが1つ
        constraints = [
<<<<<<< HEAD
            models.UniqueConstraint(fields=["child", "date"], name="uniq_dailylog_user_date")
=======
            models.UniqueConstraint(fields=["user", "date"], name="uniq_dailylog_user_date")
>>>>>>> 237ad0bef178cd18770abcb55bbe6b41d1800f3c
        ]


class Item(models.Model):
<<<<<<< HEAD
    family = models.ForeignKey(
        'Family',
=======
    user = models.ForeignKey(
        'User',
>>>>>>> 237ad0bef178cd18770abcb55bbe6b41d1800f3c
        on_delete=models.CASCADE,
    )
    child = models.ForeignKey(
        'Child',
        on_delete=models.CASCADE,
    )    
    item_name = models.CharField(max_length=50)
    color_index = models.PositiveSmallIntegerField() #表示位置

    class Meta:
         db_table = 'items'


class DailyLogItem(models.Model):
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

class ParentComment(models.Model):
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
    daily_log = models.ForeignKey(
        'Daily_log',
        on_delete=models.CASCADE,
        related_name='parent_comments',
    )
    text = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'parent_comments'

