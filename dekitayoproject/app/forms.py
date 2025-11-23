from django import forms
from .models import Users
from .models import Family_members

class UsersModelForm(forms.ModelForm):
    
    class Meta:
        model = Users
        fields = ["username", "email", "password"]

class Family_membersModelForm(forms.ModelForm):

    class Meta:
        model = Family_members
        fields = ('role',)
