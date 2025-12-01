from django import forms
from .models import Users
from .models import Family_members
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class UsersModelForm(forms.ModelForm):
    
    class Meta:
        model = Users
        fields = ["email", "password","username"]
        labels = {
            'email': 'メールアドレス',
            'password': 'パスワード',
            'username': 'ユーザー名',
        }
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'test@test.com'
            }),
            'password': forms.PasswordInput(attrs={
                'placeholder': '8文字以上、英字と数字を組み合わせてください'
            }),
            'username': forms.TextInput(attrs={
                'placeholder': 'はなこ'
            }),
        }

        help_texts = {
            "username": "",
        }

        def clean(self):
            clean_date =super().clean()
            password = clean_date.get['password']
            try:
                validate_password(password, self.instance)
            except ValidationError as e:
                self.add_error('password', e)
            return clean_date
        
        def save(self,commit=False):
            user = super().save(commit=False)
            user.set_password(self.cleaned_date['password'])
            if commit:
                user.save()
            return user


class Family_membersModelForm(forms.ModelForm):

    class Meta:
        model = Family_members
        fields = ('role',)
        widgets = { 'role': forms.RadioSelect }

