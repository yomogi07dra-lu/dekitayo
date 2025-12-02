from django.db import models
from datetime import date, datetime
from django.contrib.auth.models import (AbstractUser)


class BaseMeta(models.Model): 
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Users(AbstractUser):
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


# class Icons(models.Model):
#     image_url = models.FileField()

#     class Meta:
#         db_table = 'icons'


class invitations(models.Model):
    code = models.CharField(max_length=10)

    class Meta:
        db_table = 'invitations'