from django.db import models
from datetime import date, datetime
from django.contrib.auth.models import (AbstractUser)
import uuid


class BaseMeta(models.Model): 
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Users(AbstractUser):
    email = models.EmailField(unique=True)
    family_member = models.ForeignKey(
        'Family_members',
        on_delete=models.CASCADE,
        )
    

    # icon = models.ForeignKey(
    #     'Icons',
    #     on_delete=models.CASCADE,
    #     )

    class Meta:
        db_table = 'users'


class Families(models.Model):
    
    class Meta:
        db_table ='families'


class Family_members(models.Model):
    family = models.ForeignKey(
        'Families',
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


class Children(models.Model):
    user = models.ForeignKey(
        'Users',
        on_delete=models.CASCADE,
        )
    
    family_member = models.ForeignKey(
        'Family_members',
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = 'children'


class Icons(models.Model):
     image_url = models.FileField()

     class Meta:
         db_table = 'icons'


class Invitations(models.Model):
    family = models.OneToOneField(
        'Families', 
        on_delete=models.CASCADE,
        related_name='invite')
    code = models.CharField(max_length=10, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'invitations'


class PasswordResetToken(models.Model):
    user_PasswordReset = models.OneToOneField(
        'Users',
        on_delete=models.CASCADE,
        related_name='password_reset_token',
    )
    token = models.UUIDField(default=uuid.uuid4,db_index=True)
    used = models.BooleanField(default=False)


class Daily_logs(models.Model):
    user = models.ForeignKey(
        'Users',
        on_delete=models.CASCADE,
    )
    date = models.DateField()
    comment = models.CharField(max_length=100, blank=True)
    photo1_url1 = models.URLField(max_length=255,blank=True,null=True)
    photo2_url2 = models.URLField(max_length=255,blank=True,null=True)

    class Meta:
         db_table = 'daily_logs'


class Items(models.Model):
    user = models.ForeignKey(
        'Users',
        on_delete=models.CASCADE,
    )
    item_name = models.CharField(max_length=50)

    class Meta:
         db_table = 'items'


class DailyLogItems(models.Model):
    daily_log = models.ForeignKey(
        'Daily_logs',
        on_delete=models.CASCADE,
    )
    item = models.ForeignKey(
        'Items',
        on_delete=models.CASCADE
    )
    class Meta:
         db_table = 'daily_log_items'
